import sys
import os
from typing import List, Tuple

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from recommender import Recommender, UserProfile, Song, load_songs

def run_consistency_checks(songs: List[Song]):
    """
    Runs a series of checks to ensure the recommender system is reliable.
    """
    print("--- Running Consistency Checks ---")
    
    recommender = Recommender(songs)
    
    # 1. Check for stability: Running the recommender twice with the same profile should yield identical results.
    print("\n[Check 1/6] Stability: Multiple runs with the same profile...")
    profile = UserProfile("pop", "happy", 0.8, False)
    
    recommendations_run1 = recommender.recommend(profile, k=5)
    recommendations_run2 = recommender.recommend(profile, k=5)
    
    assert [s.id for s in recommendations_run1] == [s.id for s in recommendations_run2], "Stability check failed: Recommendations differ across identical runs."
    print("  ✅ Passed: Recommendations are stable across multiple runs.")

    # 2. Check for sensitivity: A small, relevant change should predictably alter the recommendations.
    print("\n[Check 2/6] Sensitivity: A small change to user preferences...")
    
    # Change mood from "happy" to "upbeat" (another mood in the catalog)
    profile_mood_change = UserProfile("pop", "upbeat", 0.8, False)
    recommendations_mood_change = recommender.recommend(profile_mood_change, k=5)
    
    # The recommendations should change, but not be entirely different.
    assert [s.id for s in recommendations_run1] != [s.id for s in recommendations_mood_change], "Sensitivity check failed: A mood change did not alter recommendations."
    print("  ✅ Passed: A small change in mood correctly altered the recommendations.")

    # 3. Check semantic fallback consistency
    print("\n[Check 3/6] Semantic Fallback: A non-catalog genre should consistently map to the same fallback.")
    profile_fallback = UserProfile("hip-hop", "energetic", 0.8, False)
    
    # Run with explanations to check the fallback reason
    _, _, explanation1 = recommender.recommend_with_explanations(profile_fallback, k=1)[0]
    _, _, explanation2 = recommender.recommend_with_explanations(profile_fallback, k=1)[0]

    assert explanation1 == explanation2, "Semantic fallback is not consistent."
    print("  ✅ Passed: Semantic fallback is consistent across multiple runs.")

    # 4. Check boundary conditions
    print("\n[Check 4/6] Boundary Conditions: Extreme preference values...")
    profile_low_energy = UserProfile("pop", "happy", 0.0, False)
    recommendations_low_energy = recommender.recommend(profile_low_energy, k=1)
    
    profile_high_energy = UserProfile("pop", "happy", 1.0, False)
    recommendations_high_energy = recommender.recommend(profile_high_energy, k=1)

    assert recommendations_low_energy[0].id != recommendations_high_energy[0].id, "Boundary condition check failed: Extreme energy preferences did not change the top recommendation."
    print("  ✅ Passed: Extreme energy preferences correctly altered recommendations.")

    # 5. Check acoustic preference sensitivity
    print("\n[Check 5/6] Acoustic Preference: Toggling 'likes_acoustic'...")
    profile_likes_acoustic = UserProfile("pop", "happy", 0.5, True)
    recommendations_acoustic = recommender.recommend(profile_likes_acoustic, k=5)
    
    profile_dislikes_acoustic = UserProfile("pop", "happy", 0.5, False)
    recommendations_not_acoustic = recommender.recommend(profile_dislikes_acoustic, k=5)

    # This check assumes there's a mix of acoustic/non-acoustic songs in the catalog
    assert [s.id for s in recommendations_acoustic] != [s.id for s in recommendations_not_acoustic], "Acoustic preference check failed: Toggling the preference did not alter recommendations."
    print("  ✅ Passed: Toggling 'likes_acoustic' correctly altered recommendations.")

    # 6. Check for noisy input handling (misspelling)
    print("\n[Check 6/6] Noisy Input: Handling misspelled genre...")
    profile_noisy = UserProfile("acustic", "chill", 0.5, True) # "acustic" is a misspelling
    _, _, explanation_noisy = recommender.recommend_with_explanations(profile_noisy, k=1)[0]

    assert "acoustic" in explanation_noisy, "Noisy input check failed: Misspelled genre was not handled by semantic fallback."
    print("  ✅ Passed: Semantic fallback correctly handled a misspelled genre.")
    
    print("\n--- All Consistency Checks Passed ---")


if __name__ == "__main__":
    # Load the song catalog
    songs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'songs-v2.csv'))
    songs = load_songs(songs_path)
    
    if songs:
        run_consistency_checks(songs)

