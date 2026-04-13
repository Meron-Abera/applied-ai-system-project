"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


def main() -> None:
    # Load all songs from CSV
    songs = load_songs("data/songs.csv")
    
    if not songs:
        print("No songs loaded. Exiting.")
        return

    # Improved user profile per Claude's feedback:
    # - Widened sigma from 0.10 -> 0.15
    # - Lower target_valence from 0.80 -> 0.72 (less extreme)
    # - Include target_tempo_bpm and likes_acoustic
    user_prefs = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.75,
        "target_valence": 0.72,  # Adjusted down from 0.80
        "target_tempo_bpm": 115,
        "likes_acoustic": False,
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print("\n" + "="*60)
    print("🎵 Music Recommender Simulation - Top 5 Recommendations")
    print("="*60)
    print(f"User Profile: Pop enthusiast, happy mood, moderate-high energy")
    print(f"Target Energy: {user_prefs['target_energy']}, Valence: {user_prefs['target_valence']}")
    print("="*60 + "\n")
    
    for i, rec in enumerate(recommendations, 1):
        song, score, explanation = rec
        print(f"{i}. {song.title} - {song.artist}")
        print(f"   Genre: {song.genre} | Mood: {song.mood}")
        print(f"   Energy: {song.energy:.2f} | Valence: {song.valence:.2f} | Tempo: {song.tempo_bpm:.0f} bpm")
        print(f"   Score: {score:.3f}")
        print(f"   {explanation}")
        print()


if __name__ == "__main__":
    main()
