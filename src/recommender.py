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


def score_song(song: Song, user: UserProfile, catalog_stats: Dict = None) -> Tuple[float, List[str]]:
    """
    Compute a point-based recommendation score for a song given a user profile.
    Returns (total_score: float, reasons: List[str]) for transparency.
    
    Scoring breakdown:
    - Genre match: +2.0 (exact) or +1.0 (partial)
    - Mood match: +1.0 (exact)
    - Numeric features: weighted Gaussian closeness on energy, valence, tempo, danceability, acousticness
    - Maximum possible raw score: 6.0 (2 + 1 + 3 numeric)
    """
    if catalog_stats is None:
        catalog_stats = {"tempo_min": 60, "tempo_max": 180}
    
    reasons = []
    total_points = 0.0
    
    # ===== 1. Genre Match (categorical) =====
    genre_score = partial_genre_match(song.genre, user.favorite_genre)
    if genre_score == 1.0:
        total_points += 2.0
        reasons.append(f"genre match ({song.genre}) (+2.0)")
    elif genre_score == 0.5:
        total_points += 1.0
        reasons.append(f"genre match ({song.genre}) (+1.0)")
    
    # ===== 2. Mood Match (categorical) =====
    if song.mood.lower() == user.favorite_mood.lower():
        total_points += 1.0
        reasons.append(f"mood match ({song.mood}) (+1.0)")
    
    # ===== 3. Numeric Feature Scoring (Gaussian closeness) =====
    # Sigmas control tolerance; widened per Claude's feedback
    sigma_energy = 0.15
    sigma_valence = 0.15
    sigma_tempo = 0.15
    sigma_danceability = 0.15
    sigma_acousticness = 0.20
    
    # Feature max points (sum to 3.0 total numeric)
    energy_max = 1.0
    valence_max = 0.7
    tempo_max = 0.5
    danceability_max = 0.5
    acousticness_max = 0.3
    
    # Energy
    s_energy = gaussian_similarity(song.energy, user.target_energy, sigma_energy)
    energy_points = energy_max * s_energy
    total_points += energy_points
    if energy_points > 0.1:
        reasons.append(f"energy similarity (+{energy_points:.2f})")
    
    # Valence
    s_valence = gaussian_similarity(song.valence, user.target_valence, sigma_valence)
    valence_points = valence_max * s_valence
    total_points += valence_points
    if valence_points > 0.1:
        reasons.append(f"valence similarity (+{valence_points:.2f})")
    
    # Tempo (normalized first)
    tempo_min = catalog_stats.get("tempo_min", 60)
    tempo_max_cat = catalog_stats.get("tempo_max", 180)
    tempo_norm = normalize_tempo(song.tempo_bpm, tempo_min, tempo_max_cat)
    target_tempo_norm = normalize_tempo(user.target_tempo_bpm, tempo_min, tempo_max_cat)
    s_tempo = gaussian_similarity(tempo_norm, target_tempo_norm, sigma_tempo)
    tempo_points = tempo_max * s_tempo
    total_points += tempo_points
    if tempo_points > 0.1:
        reasons.append(f"tempo similarity (+{tempo_points:.2f})")
    
    # Danceability
    s_danceability = gaussian_similarity(song.danceability, 0.65, sigma_danceability)
    danceability_points = danceability_max * s_danceability
    total_points += danceability_points
    if danceability_points > 0.1:
        reasons.append(f"danceability similarity (+{danceability_points:.2f})")
    
    # Acousticness (influenced by user preference)
    acoustic_target = 0.7 if user.likes_acoustic else 0.1
    s_acousticness = gaussian_similarity(song.acousticness, acoustic_target, sigma_acousticness)
    acousticness_points = acousticness_max * s_acousticness
    total_points += acousticness_points
    if acousticness_points > 0.1:
        reasons.append(f"acousticness similarity (+{acousticness_points:.2f})")
    
    # If no strong reasons, add a generic catch-all
    if not reasons:
        reasons.append("general match")
    
    return total_points, reasons


def build_explanation(song: Song, reasons: List[str], user: UserProfile = None) -> str:
    """Generate a human-readable explanation from the reasons list."""
    if not reasons:
        return "Recommended match."
    return "Recommended because: " + ", ".join(reasons) + "."


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
        _, reasons = score_song(song, user, self.catalog_stats)
        return build_explanation(song, reasons, user)


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
        score, reasons = score_song(song, user, catalog_stats)
        explanation = build_explanation(song, reasons, user)
        scored.append((song, score, explanation))
    
    # Sort by score descending
    scored.sort(key=lambda x: -x[1])
    
    return scored[:k]
