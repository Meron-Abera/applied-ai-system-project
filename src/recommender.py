import csv
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    target_valence: float = 0.72  # Adjusted per Claude feedback
    target_tempo_bpm: float = 115


def gaussian_similarity(value: float, target: float, sigma: float) -> float:
    """
    Compute Gaussian closeness: exp(-0.5 * ((value - target) / sigma)^2)
    Returns a score in [0, 1] where 1 = perfect match, 0 = far away.
    """
    if sigma <= 0:
        return 0.0
    z = (value - target) / sigma
    return math.exp(-0.5 * z * z)


def normalize_tempo(tempo_bpm: float, catalog_min: float = 60, catalog_max: float = 180) -> float:
    """Normalize tempo to [0, 1] range."""
    if catalog_max <= catalog_min:
        return 0.5
    return (tempo_bpm - catalog_min) / (catalog_max - catalog_min)


def partial_genre_match(song_genre: str, user_favorite_genre: str) -> float:
    """
    Return 1.0 for exact match, 0.5 for partial match, 0.0 otherwise.
    Example: "indie pop" partially matches "pop".
    """
    song_genre_lower = song_genre.lower()
    user_genre_lower = user_favorite_genre.lower()
    
    if song_genre_lower == user_genre_lower:
        return 1.0
    # Check if one is a substring of the other (partial match)
    if user_genre_lower in song_genre_lower or song_genre_lower in user_genre_lower:
        return 0.5
    return 0.0


def score_song(song: Song, user: UserProfile, catalog_stats: Dict = None) -> Tuple[float, Dict]:
    """
    Compute a final recommendation score for a song given a user profile.
    Returns (final_score, component_dict) where component_dict shows breakdown.
    
    Architecture (per Claude's suggestions):
    - Gaussian similarity for numeric features (energy, valence, tempo, danceability, acousticness)
    - Partial genre matching (1.0 exact, 0.5 partial, 0.0 none)
    - Exact mood matching (1.0 match, 0.0 no match)
    - Acousticness influenced by user's likes_acoustic preference
    """
    if catalog_stats is None:
        catalog_stats = {"tempo_min": 60, "tempo_max": 180}
    
    tempo_min = catalog_stats.get("tempo_min", 60)
    tempo_max = catalog_stats.get("tempo_max", 180)
    
    # Widened sigma per Claude: 0.10 -> 0.15
    sigma_energy = 0.15
    sigma_valence = 0.15
    sigma_tempo = 0.15
    sigma_danceability = 0.15
    sigma_acousticness = 0.20  # Include acousticness with its own sigma
    
    # Numeric feature similarities
    s_energy = gaussian_similarity(song.energy, user.target_energy, sigma_energy)
    s_valence = gaussian_similarity(song.valence, user.target_valence, sigma_valence)
    
    tempo_norm = normalize_tempo(song.tempo_bpm, tempo_min, tempo_max)
    target_tempo_norm = normalize_tempo(user.target_tempo_bpm, tempo_min, tempo_max)
    s_tempo = gaussian_similarity(tempo_norm, target_tempo_norm, sigma_tempo)
    
    s_danceability = gaussian_similarity(song.danceability, 0.65, sigma_danceability)  # Neutral target
    
    # Acousticness: if user likes_acoustic, prefer high acousticness (close to 1.0)
    # If not, prefer low acousticness (close to 0.0)
    acoustic_target = 0.7 if user.likes_acoustic else 0.1
    s_acousticness = gaussian_similarity(song.acousticness, acoustic_target, sigma_acousticness)
    
    # Aggregate numeric score (equal weights)
    numeric_weights = {
        "energy": 0.25,
        "valence": 0.25,
        "tempo": 0.20,
        "danceability": 0.15,
        "acousticness": 0.15,
    }
    numeric_score = (
        numeric_weights["energy"] * s_energy +
        numeric_weights["valence"] * s_valence +
        numeric_weights["tempo"] * s_tempo +
        numeric_weights["danceability"] * s_danceability +
        numeric_weights["acousticness"] * s_acousticness
    )
    
    # Categorical matches
    genre_match = partial_genre_match(song.genre, user.favorite_genre)
    mood_match = 1.0 if song.mood.lower() == user.favorite_mood.lower() else 0.0
    
    # Final score (top-level weights per original design)
    w_numeric = 0.60
    w_genre = 0.25
    w_mood = 0.15
    
    final_score = (
        w_numeric * numeric_score +
        w_genre * genre_match +
        w_mood * mood_match
    )
    
    components = {
        "energy": s_energy,
        "valence": s_valence,
        "tempo": s_tempo,
        "danceability": s_danceability,
        "acousticness": s_acousticness,
        "numeric_score": numeric_score,
        "genre_match": genre_match,
        "mood_match": mood_match,
        "final_score": final_score,
    }
    
    return final_score, components


def build_explanation(song: Song, components: Dict, user: UserProfile) -> str:
    """Generate a human-readable explanation for why a song was recommended."""
    reasons = []
    
    if components["genre_match"] > 0.5:
        if components["genre_match"] == 1.0:
            reasons.append(f"matches your favorite genre ({song.genre})")
        else:
            reasons.append(f"related to your favorite genre ({song.genre})")
    
    if components["mood_match"] > 0.5:
        reasons.append(f"fits your mood preference ({song.mood})")
    
    # Find the strongest numeric contributor
    numeric_components = {
        "energy": components["energy"],
        "valence": components["valence"],
        "tempo": components["tempo"],
    }
    strongest_numeric = max(numeric_components.items(), key=lambda x: x[1])
    if strongest_numeric[1] > 0.5:
        reasons.append(f"strong {strongest_numeric[0]} match ({strongest_numeric[1]:.2f})")
    
    if not reasons:
        reasons.append("interesting match in your vibe")
    
    return "Recommended because: " + ", and ".join(reasons) + "."


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs
        # Compute catalog stats for normalization
        tempos = [s.tempo_bpm for s in songs]
        self.catalog_stats = {
            "tempo_min": min(tempos) if tempos else 60,
            "tempo_max": max(tempos) if tempos else 180,
        }

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """
        Recommend top-k songs for a user, sorted by score (descending).
        """
        scored_songs = [
            (song, score_song(song, user, self.catalog_stats)[0])
            for song in self.songs
        ]
        # Sort by score descending, then by id for stability
        scored_songs.sort(key=lambda x: (-x[1], x[0].id))
        return [song for song, score in scored_songs[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Generate an explanation for why a song was recommended to a user."""
        _, components = score_song(song, user, self.catalog_stats)
        return build_explanation(song, components, user)


def load_songs(csv_path: str) -> List[Song]:
    """
    Loads songs from a CSV file and returns a list of Song objects.
    Expected CSV columns: id, title, artist, genre, mood, energy, tempo_bpm, valence, danceability, acousticness
    """
    songs = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                song = Song(
                    id=int(row["id"]),
                    title=row["title"],
                    artist=row["artist"],
                    genre=row["genre"],
                    mood=row["mood"],
                    energy=float(row["energy"]),
                    tempo_bpm=float(row["tempo_bpm"]),
                    valence=float(row["valence"]),
                    danceability=float(row["danceability"]),
                    acousticness=float(row["acousticness"]),
                )
                songs.append(song)
    except FileNotFoundError:
        print(f"Error: Could not find file {csv_path}")
        return []
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return []
    
    print(f"Loaded {len(songs)} songs from {csv_path}")
    return songs


def recommend_songs(user_prefs: Dict, songs: List[Song], k: int = 5) -> List[Tuple[Song, float, str]]:
    """
    Functional implementation of recommendation logic.
    user_prefs: dict with keys like favorite_genre, favorite_mood, target_energy, likes_acoustic, target_valence, target_tempo_bpm
    Returns: list of (song, score, explanation) tuples, sorted by score descending.
    """
    if not songs:
        return []
    
    # Build UserProfile from dict
    user = UserProfile(
        favorite_genre=user_prefs.get("favorite_genre", "pop"),
        favorite_mood=user_prefs.get("favorite_mood", "happy"),
        target_energy=user_prefs.get("target_energy", 0.75),
        likes_acoustic=user_prefs.get("likes_acoustic", False),
        target_valence=user_prefs.get("target_valence", 0.72),
        target_tempo_bpm=user_prefs.get("target_tempo_bpm", 115),
    )
    
    # Compute catalog stats
    tempos = [s.tempo_bpm for s in songs]
    catalog_stats = {
        "tempo_min": min(tempos) if tempos else 60,
        "tempo_max": max(tempos) if tempos else 180,
    }
    
    # Score all songs
    scored = []
    for song in songs:
        score, components = score_song(song, user, catalog_stats)
        explanation = build_explanation(song, components, user)
        scored.append((song, score, explanation))
    
    # Sort by score descending
    scored.sort(key=lambda x: -x[1])
    
    return scored[:k]
