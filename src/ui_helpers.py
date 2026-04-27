from typing import List, Dict
import streamlit as st
import plotly.graph_objects as go


def render_fallback_banner(fallback_notes: List[str]):
    """Show an info banner listing fallback reasons."""
    if not fallback_notes:
        return
    with st.container():
        st.info("Semantic fallback applied: ")
        for note in fallback_notes:
            st.write(f"- {note}")


def song_feature_radar(song, user_profile):
    """Render a radar chart comparing song features to user targets.

    song: object with attributes energy, valence, danceability, acousticness, tempo_bpm
    user_profile: object with target_energy, target_valence, target_tempo_bpm, likes_acoustic
    """
    # Normalize tempo roughly to 0-1 using common BPM range 40-200
    def norm_tempo(t):
        return max(0.0, min(1.0, (t - 40) / (200 - 40)))

    song_vals = [
        song.energy,
        song.valence,
        song.danceability,
        song.acousticness,
        norm_tempo(song.tempo_bpm),
    ]
    user_vals = [
        user_profile.target_energy,
        user_profile.target_valence,
        0.65,  # target danceability heuristic
        0.7 if user_profile.likes_acoustic else 0.1,
        norm_tempo(user_profile.target_tempo_bpm),
    ]
    categories = ["Energy", "Valence", "Danceability", "Acousticness", "Tempo"]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=song_vals, theta=categories, fill='toself', name=song.title))
    fig.add_trace(go.Scatterpolar(r=user_vals, theta=categories, fill='toself', name='User Target'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=True)
    return fig


def render_song_card(song, score, explanation):
    """Render a compact song card with title/artist/genre/mood and a short explanation."""
    st.markdown(f"### {song.title} — {song.artist}")
    st.markdown(f"**Genre:** {song.genre} | **Mood:** {song.mood} | **Score:** {score:.2f}/6.0")
    short = explanation if len(explanation) < 200 else explanation[:200] + "..."
    st.write(short)
    with st.expander("Full explanation"):
        st.write(explanation)
