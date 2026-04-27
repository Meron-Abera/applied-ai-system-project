import os
import sys

# Ensure project src is on the path when script run directly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, "src"))

from recommender import Song, UserProfile, Recommender


def make_small_recommender():
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


if __name__ == '__main__':
    rec = make_small_recommender()
    user = UserProfile(
        favorite_genre="country",
        favorite_mood="nostalgic",
        target_energy=0.6,
        likes_acoustic=True,
    )

    results = rec.recommend_with_explanations(user, k=2)
    for i, (song, score, explanation) in enumerate(results, 1):
        print(f"Result {i}: {song.title} ({song.genre}, {song.mood}) -> {score:.2f}")
        print("Explanation:", explanation)
        print('-' * 60)
