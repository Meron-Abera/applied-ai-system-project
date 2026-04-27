from src.recommender import Song, UserProfile, Recommender

def make_small_recommender() -> Recommender:
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


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


def test_semantic_fallback_for_missing_genre_and_mood():
    """If the user's favorite genre/mood are not in the catalog, the recommender should attempt a semantic fallback
    and expose that reasoning in the explanation returned by `recommend_with_explanations`.
    """
    rec = make_small_recommender()
    # Use a genre and mood that are not present in the small catalog
    user = UserProfile(
        favorite_genre="country",
        favorite_mood="nostalgic",
        target_energy=0.6,
        likes_acoustic=True,
    )

    results = rec.recommend_with_explanations(user, k=2)
    assert len(results) == 2

    # Each result should be a tuple (Song, score, explanation)
    song, score, explanation = results[0]
    assert isinstance(explanation, str)
    assert "Semantic fallback" in explanation
    # Should mention the original requested genre/mood in the fallback explanation
    assert "country" in explanation.lower()
    assert "nostalgic" in explanation.lower()


def test_functional_recommend_songs_applies_fallback():
    # Prepare the same small catalog
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

    user_prefs = {
        "favorite_genre": "country",
        "favorite_mood": "nostalgic",
        "target_energy": 0.6,
        "likes_acoustic": True,
    }

    results = __import__('src.recommender', fromlist=['recommend_songs']).recommend_songs(user_prefs, songs, k=2)
    assert len(results) == 2
    song, score, explanation = results[0]
    assert isinstance(explanation, str)
    assert "semantic fallback" in explanation.lower()
