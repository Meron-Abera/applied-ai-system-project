import csv
import math
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from anthropic_client import generate_anthropic_explanation

# Lazy-load sentence-transformers and numpy for faster app startup
_sentence_transformer_model = None
_util = None

def _get_sentence_transformer():
    """Lazy-loads and returns the sentence transformer model."""
    global _sentence_transformer_model, _util
    if _sentence_transformer_model is None:
        try:
            from sentence_transformers import SentenceTransformer, util
            _sentence_transformer_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
            _util = util
        except ImportError:
            raise ImportError("SentenceTransformers is not installed. Please `pip install sentence-transformers`.")
    return _sentence_transformer_model, _util



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
    target_danceability: float = 0.65


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
    s_danceability = gaussian_similarity(song.danceability, user.target_danceability, sigma_danceability)
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


def build_explanation(song: Song, reasons: List[str], user: UserProfile = None, use_anthropic: bool = False) -> str:
    """
    Generate a human-readable explanation from the reasons list.
    Optionally uses Anthropic's Claude for a more creative explanation.
    """
    if use_anthropic:
        # This is a network call, so it will be slower.
        return generate_anthropic_explanation(song, reasons, user)
    
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
        # Precompute catalog genres and moods for quick lookup
        self._catalog_genres = {s.genre.lower() for s in songs}
        self._catalog_moods = {s.mood.lower() for s in songs}

        # For semantic search
        self._model = None
        self._genre_embeddings = None
        self._mood_embeddings = None
        self._catalog_genres_list = None
        self._catalog_moods_list = None

    def _initialize_semantic_search(self):
        """Initializes the model and embeddings for semantic search."""
        if self._model is None:
            self._model, _ = _get_sentence_transformer()
            self._catalog_genres_list = sorted(list(self._catalog_genres))
            self._catalog_moods_list = sorted(list(self._catalog_moods))
            self._genre_embeddings = self._model.encode(self._catalog_genres_list, convert_to_tensor=True)
            self._mood_embeddings = self._model.encode(self._catalog_moods_list, convert_to_tensor=True)

    def _semantic_search(self, query: str, search_type: str) -> Optional[str]:
        """
        Performs semantic search to find the best matching genre or mood.
        """
        self._initialize_semantic_search()
        model, util = _get_sentence_transformer()

        if search_type == "genre":
            corpus_embeddings = self._genre_embeddings
            corpus = self._catalog_genres_list
        else:
            corpus_embeddings = self._mood_embeddings
            corpus = self._catalog_moods_list

        query_embedding = model.encode(query, convert_to_tensor=True)
        
        # Find the most similar item in the corpus
        cos_scores = util.pytorch_cos_sim(query_embedding, corpus_embeddings)[0]
        top_result_idx = cos_scores.argmax().item()
        
        # Return the best match if the score is above a threshold
        if cos_scores[top_result_idx] > 0.3: # Similarity threshold
            return corpus[top_result_idx]
        return None

    # --- Semantic fallback mappings ---
    # Simple, interpretable mapping for moods/genres to similar catalog-friendly terms.
    FALLBACK_MOOD_MAP = {
        "nostalgic": ["chill", "lofi", "ambient"],
        "melancholic": ["ambient", "relaxed", "chill"],
        "energetic": ["happy", "party", "dance"],
    }

    FALLBACK_GENRE_MAP = {
        "country": ["folk", "acoustic", "pop"],
        "singer-songwriter": ["folk", "acoustic"],
        "edm": ["dance", "electronic", "pop"],
    }

    def _retrieve_similar(self, term: str, mapping: Dict[str, List[str]], catalog_terms: set) -> Tuple[Optional[str], List[str]]:
        """
        Given an input term and a mapping, return the first mapped candidate that exists in the catalog_terms.
        Returns (chosen, candidates). chosen is None if nothing in the mapping matches the catalog.
        """
        if not term:
            return None, []
        
        # Try semantic search first
        semantic_match = self._semantic_search(term, "genre" if catalog_terms == self._catalog_genres else "mood")
        if semantic_match:
            return semantic_match, [semantic_match]

        term_lower = term.lower()
        candidates = mapping.get(term_lower, [])
        # Also include simple substring heuristics (e.g., "indie pop" -> "pop")
        # by adding any catalog term that contains the term tokens.
        if not candidates:
            tokens = [t for t in term_lower.split() if len(t) > 2]
            for c in catalog_terms:
                for tok in tokens:
                    if tok in c:
                        candidates.append(c)
                        break

        # Choose the first candidate available in catalog_terms
        for cand in candidates:
            if cand.lower() in catalog_terms:
                return cand, candidates

        # If none of the mapped candidates are in the catalog, return the full candidate list (for explanation)
        return None, candidates

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """
        Recommend top-k songs for a user, sorted by score (descending).
        """
        # Apply semantic fallback for genre/mood if user's preferences are not in catalog
        fallback_reasons = []
        # Work on a shallow copy so we don't mutate the caller's profile
        user_copy = UserProfile(**{**user.__dict__})

        # Genre fallback
        if user_copy.favorite_genre and user_copy.favorite_genre.lower() not in self._catalog_genres:
            chosen_genre, candidates = self._retrieve_similar(user_copy.favorite_genre, self.FALLBACK_GENRE_MAP, self._catalog_genres)
            if chosen_genre:
                fallback_reasons.append(f"genre '{user.favorite_genre}' not in catalog → using '{chosen_genre}' (candidates: {candidates})")
                user_copy.favorite_genre = chosen_genre
            elif candidates:
                fallback_reasons.append(f"genre '{user.favorite_genre}' not in catalog → mapped candidates {candidates} (none found in catalog)")

        # Mood fallback
        if user_copy.favorite_mood and user_copy.favorite_mood.lower() not in self._catalog_moods:
            chosen_mood, candidates = self._retrieve_similar(user_copy.favorite_mood, self.FALLBACK_MOOD_MAP, self._catalog_moods)
            if chosen_mood:
                fallback_reasons.append(f"mood '{user.favorite_mood}' not in catalog → using '{chosen_mood}' (candidates: {candidates})")
                user_copy.favorite_mood = chosen_mood
            elif candidates:
                fallback_reasons.append(f"mood '{user.favorite_mood}' not in catalog → mapped candidates {candidates} (none found in catalog)")

        scored_songs = []
        for song in self.songs:
            score, reasons = score_song(song, user_copy, self.catalog_stats)
            explanation = build_explanation(song, reasons, user_copy)
            # Prefix fallback reasoning so it's visible to downstream callers / UI
            if fallback_reasons:
                explanation = "Semantic fallback: " + "; ".join(fallback_reasons) + ". " + explanation
            scored_songs.append((song, score, explanation))
        # Sort by score descending, then by id for stability
        scored_songs.sort(key=lambda x: (-x[1], x[0].id))
        # Return only Song objects to preserve existing API. Use recommend_with_explanations for richer output.
        return [song for song, score, _ex in scored_songs[:k]]

    def recommend_with_explanations(self, user: UserProfile, k: int = 5, max_per_artist: int = 2, use_anthropic: bool = False) -> List[Tuple[Song, float, str]]:
        """
        Rich recommendation API that returns (song, score, explanation) tuples.
        This mirrors the functional `recommend_songs` behavior and includes semantic fallback reasoning when applied.
        Includes a diversity filter to limit songs per artist.
        """
        # Duplicate the logic above but return full tuples
        fallback_reasons = []
        user_copy = UserProfile(**{**user.__dict__})

        if user_copy.favorite_genre and user_copy.favorite_genre.lower() not in self._catalog_genres:
            chosen_genre, candidates = self._retrieve_similar(user_copy.favorite_genre, self.FALLBACK_GENRE_MAP, self._catalog_genres)
            if chosen_genre:
                fallback_reasons.append(f"genre '{user.favorite_genre}' not in catalog → using '{chosen_genre}' (candidates: {candidates})")
                user_copy.favorite_genre = chosen_genre
            elif candidates:
                fallback_reasons.append(f"genre '{user.favorite_genre}' not in catalog → mapped candidates {candidates} (none found in catalog)")

        if user_copy.favorite_mood and user_copy.favorite_mood.lower() not in self._catalog_moods:
            chosen_mood, candidates = self._retrieve_similar(user_copy.favorite_mood, self.FALLBACK_MOOD_MAP, self._catalog_moods)
            if chosen_mood:
                fallback_reasons.append(f"mood '{user.favorite_mood}' not in catalog → using '{chosen_mood}' (candidates: {candidates})")
                user_copy.favorite_mood = chosen_mood
            elif candidates:
                fallback_reasons.append(f"mood '{user.favorite_mood}' not in catalog → mapped candidates {candidates} (none found in catalog)")

        scored = []
        for song in self.songs:
            score, reasons = score_song(song, user_copy, self.catalog_stats)
            explanation = build_explanation(song, reasons, user_copy, use_anthropic=use_anthropic)
            # Prefix fallback reasoning so it's visible to downstream callers / UI
            if fallback_reasons:
                explanation = "Semantic fallback: " + "; ".join(fallback_reasons) + ". " + explanation
            scored.append((song, score, explanation))

        scored.sort(key=lambda x: -x[1])
        
        # Apply diversity filter
        final_recommendations = []
        artist_counts = {}
        for song, score, explanation in scored:
            if len(final_recommendations) >= k:
                break
            
            artist_name = song.artist
            if artist_counts.get(artist_name, 0) < max_per_artist:
                final_recommendations.append((song, score, explanation))
                artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1
        
        return final_recommendations

    def explain_recommendation(self, user: UserProfile, song: Song, use_anthropic: bool = False) -> str:
        """Generate an explanation for why a song was recommended to a user."""
        _, reasons = score_song(song, user, self.catalog_stats)
        return build_explanation(song, reasons, user, use_anthropic=use_anthropic)


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


def recommend_songs(user_prefs: Dict, songs: List[Song], k: int = 5, use_anthropic: bool = False) -> List[Tuple[Song, float, str]]:
    """
    Functional-style wrapper for the Recommender class.
    user_prefs: dict with keys like favorite_genre, favorite_mood, target_energy, etc.
    Returns: list of (song, score, explanation) tuples, sorted by score descending.
    """
    logger = logging.getLogger(__name__)
    if not songs:
        logger.info("No songs provided to recommend_songs")
        return []

    # Build UserProfile from dict
    user = UserProfile(
        favorite_genre=user_prefs.get("favorite_genre", "pop"),
        favorite_mood=user_prefs.get("favorite_mood", "happy"),
        target_energy=user_prefs.get("target_energy", 0.75),
        likes_acoustic=user_prefs.get("likes_acoustic", False),
        target_valence=user_prefs.get("target_valence", 0.72),
        target_tempo_bpm=user_prefs.get("target_tempo_bpm", 115),
        target_danceability=user_prefs.get("target_danceability", 0.65),
    )

    # Use the Recommender class to ensure consistent logic
    recommender = Recommender(songs)
    return recommender.recommend_with_explanations(user, k=k, use_anthropic=use_anthropic)
