import os
import sys
import logging
from typing import List

import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure src is importable when running the app from the project root
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, "src"))

from recommender import load_songs, recommend_songs, Recommender, UserProfile
from src.ui_helpers import render_fallback_banner, song_feature_radar, render_song_card


def extract_fallback_notes(explanation: str) -> str:
    if not explanation:
        return ""
    if "Semantic fallback" in explanation:
        try:
            return explanation.split('. Recommended because')[0]
        except Exception:
            return explanation
    return ""


# --- Main App ---
def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger(__name__)

    st.set_page_config(page_title="MoodBeam — Music Recommender", layout="wide")
    st.title("MoodBeam — Interactive Music Recommender")
    st.markdown("""A modern, interactive UI that demonstrates the content-based recommender and
    semantic fallback logic (when a requested genre or mood isn't in the catalog). Use the demo profiles
    or type your own preferences to explore recommendations.""")

    # --- API Key Check ---
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    anthropic_model = os.getenv("ANTHROPIC_MODEL")
    if not anthropic_api_key:
        st.warning(
            "**Anthropic API key not found.**\n\n"
            "Enhanced explanations are disabled. To enable them:\n"
            "1. Create a file named `.env` in the project root.\n"
            "2. Add this line to it: `ANTHROPIC_API_KEY='your-key-here'`\n"
            "3. Restart the app.",
            icon="🔒"
        )
    elif not anthropic_model:
        st.warning(
            "**Anthropic model not configured.**\n\n"
            "Enhanced explanations are disabled. To enable them:\n"
            "1. Add `ANTHROPIC_MODEL='your-model-name'` to your `.env`.\n"
            "2. Restart the app.\n\n"
            "You can find available model names in your Anthropic console.",
            icon="🧠"
        )

    # Load catalog once
    csv_path = os.path.join(project_root, "data", "songs-v2.csv")
    songs = load_songs(csv_path)

    # Sidebar controls for user profile
    with st.sidebar:
        st.header("User Profile")
        catalog_genres = sorted({s.genre for s in songs}) if songs else []
        catalog_moods = sorted({s.mood for s in songs}) if songs else []

        # Demo profiles
        demo_profiles = {
            "Country / Nostalgic (Edge)": {
                "favorite_genre": "country",
                "favorite_mood": "nostalgic",
                "target_energy": 0.6,
                "target_valence": 0.65,
                "target_tempo_bpm": 100,
                "target_danceability": 0.65,
                "likes_acoustic": True,
            },
            "High-Energy Pop Enthusiast": {
                "favorite_genre": "pop",
                "favorite_mood": "happy",
                "target_energy": 0.75,
                "target_valence": 0.72,
                "target_tempo_bpm": 115,
                "target_danceability": 0.7,
                "likes_acoustic": False,
            },
            "Chill Lofi Listener": {
                "favorite_genre": "lofi",
                "favorite_mood": "chill",
                "target_energy": 0.35,
                "target_valence": 0.55,
                "target_tempo_bpm": 80,
                "target_danceability": 0.5,
                "likes_acoustic": True,
            },
        }

        chosen_demo = st.selectbox("Demo profiles", ["<custom>"] + list(demo_profiles.keys()))

        if chosen_demo != "<custom>":
            demo = demo_profiles[chosen_demo]
            favorite_genre = st.text_input("Favorite genre", value=demo["favorite_genre"])
            favorite_mood = st.text_input("Favorite mood", value=demo["favorite_mood"])
            target_energy = st.slider("Target energy", 0.0, 1.0, demo["target_energy"], 0.01)
            target_valence = st.slider("Target valence", 0.0, 1.0, demo["target_valence"], 0.01)
            target_tempo = st.slider("Target tempo (bpm)", 40, 200, demo["target_tempo_bpm"], 1)
            target_danceability = st.slider("Target danceability", 0.0, 1.0, demo["target_danceability"], 0.01)
            likes_acoustic = st.checkbox("Likes acoustic", value=demo["likes_acoustic"])
        else:
            favorite_genre = st.text_input("Favorite genre", value="country")
            favorite_mood = st.text_input("Favorite mood", value="nostalgic")
            target_energy = st.slider("Target energy", 0.0, 1.0, 0.6, 0.01, key="energy_custom")
            target_valence = st.slider("Target valence", 0.0, 1.0, 0.72, 0.01, key="valence_custom")
            target_tempo = st.slider("Target tempo (bpm)", 40, 200, 115, 1, key="tempo_custom")
            target_danceability = st.slider("Target danceability", 0.0, 1.0, 0.65, 0.01, key="danceability_custom")
            likes_acoustic = st.checkbox("Likes acoustic", value=True, key="acoustic_custom")
        k = st.slider("Top K", 1, 20, 5)

        st.markdown("---")
        st.header("API to use")
        api_choice = st.radio(
            "API to use",
            ["Functional (recommend_songs)", "Recommender (with explanations)"],
            label_visibility="collapsed"
        )
        
        anthropic_enabled = bool(anthropic_api_key and anthropic_model)
        use_anthropic_explanations = st.checkbox(
            "✨ Use Enhanced Explanations (Claude)",
            disabled=not anthropic_enabled,
        )
        if use_anthropic_explanations and not anthropic_enabled:
            st.caption("Please set your ANTHROPIC_API_KEY and ANTHROPIC_MODEL to enable.")
        elif not anthropic_enabled:
            st.caption("Enhanced explanations require ANTHROPIC_API_KEY and ANTHROPIC_MODEL.")

    # --- Load Data ---
    songs = load_songs("data/songs-v2.csv")

    # Action button
    if st.sidebar.button("Get Recommendations"):
        user_prefs = {
            "favorite_genre": favorite_genre,
            "favorite_mood": favorite_mood,
            "target_energy": target_energy,
            "likes_acoustic": likes_acoustic,
            "target_valence": target_valence,
            "target_tempo_bpm": target_tempo,
            "target_danceability": target_danceability,
        }

        if api_choice.startswith("Functional"):
            scored = recommend_songs(user_prefs, songs, k=k, use_anthropic=use_anthropic_explanations)
        else:
            rec = Recommender(songs)
            scored = rec.recommend_with_explanations(UserProfile(
                favorite_genre=favorite_genre,
                favorite_mood=favorite_mood,
                target_energy=target_energy,
                likes_acoustic=likes_acoustic,
                target_valence=target_valence,
                target_tempo_bpm=target_tempo,
                target_danceability=target_danceability,
            ), k=k, use_anthropic=use_anthropic_explanations)

        if not scored:
            st.warning("No recommendations were produced.")
            return

        # Show fallback notes if any
        fallback_set = []
        for _song, _score, explanation in scored:
            note = extract_fallback_notes(explanation)
            if note and note not in fallback_set:
                fallback_set.append(note)

        render_fallback_banner(fallback_set)

        # Display recommendations as attractive cards with radar charts
        st.subheader("Top Recommendations")
        for i, (song, score, explanation) in enumerate(scored, start=1):
            with st.container():
                left, right = st.columns([2, 3])
                with left:
                    render_song_card(song, score, explanation)
                with right:
                    fig = song_feature_radar(song, UserProfile(
                        favorite_genre=favorite_genre,
                        favorite_mood=favorite_mood,
                        target_energy=target_energy,
                        likes_acoustic=likes_acoustic,
                        target_valence=target_valence,
                        target_tempo_bpm=target_tempo,
                        target_danceability=target_danceability,
                    ))
                    st.plotly_chart(fig, use_container_width=True)
            st.markdown("---")

        # Offer CSV download
        try:
            import pandas as pd

            df = pd.DataFrame([
                {
                    "rank": i + 1,
                    "title": s.title,
                    "artist": s.artist,
                    "genre": s.genre,
                    "mood": s.mood,
                    "score": f"{sc:.2f}",
                    "explanation": expl,
                }
                for i, (s, sc, expl) in enumerate(scored)
            ])
            st.download_button("Download CSV", df.to_csv(index=False), file_name="recommendations.csv")
        except Exception as e:
            logger.exception(f"Could not prepare CSV: {e}")


if __name__ == "__main__":
    main()
