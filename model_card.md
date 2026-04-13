# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**MoodBeam 1.0** — A music recommender that scores songs based on how well they match your genre, mood, and audio features (like energy and happiness). It's designed to teach students how algorithms can accidentally create unfair recommendations.

---

## 2. Intended Use  

**MoodBeam** is for **learning about bias in recommender systems**, not for real music streaming apps.

It helps you:
- See how song scores change when you tweak your preferences
- Understand why some user groups get better recommendations than others
- Discover that "fair" algorithms can still create unfair outcomes

Users describe what they like as:
- A genre (pop, rock, lofi, etc.)
- A mood (chill, happy, intense, relaxed, sad, focused)
- How much energy they want (0.0 = super calm, 1.0 = super energetic)
- Other audio preferences (happiness, tempo, danceability, acoustic vs electronic)

The system ranks all 10 songs by similarity to these preferences. **Important limitation**: It only works well if the songs in the catalog match what users want. If you want country music and the catalog has zero country songs, the system fails.

---

## 3. How the Model Works  

**MoodBeam** gives each song a score from 0–6.0 based on three categories:

1. **Genre (2.0 pts max)**: Exact match gets 2.0 points. Partial match (rock vs indie) gets 1.0. No match gets 0.

2. **Mood (1.0 pt max)**: Exact match gets 1.0 point. No match gets 0.

3. **Audio Features (3.0 pts max)**: 
   - Energy: 1.0 pt
   - Valence (happiness): 0.7 pts
   - Tempo: 0.5 pts
   - Danceability: 0.5 pts
   - Acousticness: 0.3 pts

**How audio features are scored**: Each feature uses a **Gaussian curve** that rewards songs close to your target and penalizes songs far away. If you want energy 0.85 and a song has energy 0.82, you get almost full points. If a song has energy 0.50, you get very few points.

**Example**: A pop fan wanting upbeat (0.75 energy) and happy (0.70 valence) would score "Sunrise City" (pop, happy, energy 0.82, valence 0.78) as:
- Genre: 2.0 (exact pop)
- Mood: 1.0 (exact happy)
- Energy: 0.97 pts (very close to target)
- Valence: 0.67 pts (close to target)
- Other features: ~0.5 pts
- **Total: ~5.14/6.0** (very good recommendation)

---

## 4. Data  

**What we have**: 10 songs with info about genre, mood, energy, happiness, tempo, danceability, and acousticness.

**Genre breakdown**:
- Lofi: 3 songs (30%)
- Pop: 2 songs (20%)
- Rock, Ambient, Jazz, Synthwave, Indie: 1 song each (10% each)
- **Missing**: Country, Classical, Electronic, Hip-Hop, Soul

**Mood breakdown**:
- Chill: 3 songs (30%)
- Happy, Intense: 2 songs each (20%)
- Relaxed, Moody, Focused: 1 song each (10% each)
- **Missing**: Nostalgic, Melancholic, Energetic, Calm, Sad

**Audio features**:
- **Energy**: Mostly between 0.60–0.90 (not many calm or super-energetic songs)
- **Valence (happiness)**: Averages 0.65 (mostly happy songs, few sad ones)
- **Tempo**: Varies across all songs

**The big problem**: The catalog is small and imbalanced. Lofi fans get great recommendations because 30% of songs are lofi. Country fans get terrible recommendations because 0% of songs are country. This isn't the algorithm being unfair—it's the *data* being unfair.

---

## 5. Strengths  

**MoodBeam works great for mainstream users**:
- Pop fans wanting happy, moderate-energy music get excellent recommendations (5.49/6.0)
- Lofi fans wanting chill music get amazing recommendations (5.88/6.0)
- Rock fans wanting intense music get strong recommendations (5.73/6.0)

**Good design choices**:
- **Transparent**: Each recommendation explains point-by-point why you got it (genre 2.0 pts, energy 0.9 pts, etc.). You can contest recommendations and understand the logic.
- **Multi-feature**: Combines what you care about (genre, mood) with how songs actually sound (energy, happiness). This is better than just keyword matching.
- **Exposes contradictions**: If you ask for both sad AND extremely energetic music, the recommender shows you it can't satisfy both. This is honest.

**Real-world strength**: If the catalog had country songs, country fans would get great recommendations too. The algorithm itself is fair—it treats all users the same way.

---

## 6. Limitations and Bias 

**Five major biases we found**:

### Bias #1: Genre Creates Silos (You Only See Your Genre)

Genre gets 33% of the score (2.0 out of 6.0 points). This means rock fans almost never see pop recommendations, even if a pop song has identical energy and mood to what they want. You get trapped in genre bubbles.

**Real-world impact**: Someone looking for "high-energy upbeat music" only sees rock songs, never pop or electronic songs with the same vibe.

---

### Bias #2: Energy Extremes Get Penalized

The system strongly dislikes songs far from your target energy. If you want super-calm music (energy 0.05) but all catalog songs have energy 0.30–0.90, you can never score well, even if genre and mood are perfect.

**Real-world impact**: A person wanting to fall asleep (energy 0.05) gets recommendations for chill lofi (energy 0.35). Close, but not what they asked for. They feel unheard.

---

### Bias #3: The Catalog Is Too Happy

Most songs have happiness (valence) around 0.65. There are almost no sad songs (valence <0.40). So if you want melancholic music, you get only moderately sad recommendations.

**Real-world impact**: Similar to Spotify's tendency to recommend upbeat songs—it reflects what's popular, but abandons users wanting sad music.

---

### Bias #4: Missing Genres and Moods Cause Collapse

If a user wants country music and mood "nostalgic," and neither exists in the catalog, they lose 3 out of 6 points immediately (50% score loss). They're left with only numeric similarity, scoring around 2.0/6.0 instead of 5.0/6.0.

**Real-world impact**: Country fans using MoodBeam get lofi/pop recommendations. They feel the algorithm doesn't understand them—but really, the *catalog* doesn't have country songs.

---

### Bias #5: Lofi Over-Representation

Lofi is 30% of the catalog (3 out of 10 songs), while rock and jazz are only 10% each. Lofi fans naturally get better recommendations just because there are more lofi songs to choose from.

**Real-world impact**: Lofi fans see great recommendations; rock fans see fewer options. This is fair in one sense (we have more lofi), unfair in another (rock fans get limited choice).

---

## 7. Evaluation  

### Six Test Users We Created

To find biases, we tested six very different users:

| Profile | Genre | Mood | Energy | Purpose |
|---------|-------|------|--------|---------|
| User 1 | Pop | Happy | 0.75 | Mainstream user (should get great recommendations) |
| User 2 | Lofi | Chill | 0.35 | Mainstream user with low energy |
| User 3 | Rock | Intense | 0.88 | Niche but well-covered genre |
| User 4 | Ambient | Melancholic | 0.90 | Impossible combo (sad + energetic) |
| User 5 | Jazz | Relaxed | 0.05 | Extreme calm preference (catalog doesn't have this) |
| User 6 | Country | Nostalgic | 0.60 | Missing genre + missing mood |

### What We Found

**Finding 1: Mainstream users score 5+, niche users score 2**
- Users 1-3 average 5.4/6.0 (excellent)
- Users 4-6 average 2.4/6.0 (poor)
- **Fairness gap: 54%**

Why? Lofi and pop are in the catalog. Country is not. It's that simple.

---

**Finding 2: Genre weight dominates**

User 1 (pop fan) gets "Gym Hero" (pop, intense) as their #3 recommendation, even though the user wanted happy music, not intense. Why? Genre match (2.0 pts) beats mood match (0.0 pts).

This shows genre is 33% of the score, so a correct genre can outweigh incorrect mood.

---

**Finding 3: Energy extremes fail silently**

User 5 (jazz fan wanting energy 0.05) gets only 3.88/6.0, even though they match genre and mood perfectly. Why? No song in the catalog has energy below 0.28. So they can't score well on energy no matter what.

**Real impact**: Users wanting calm or wild music feel unheard.

---

**Finding 4: Missing genre + missing mood = collapse**

User 6 (country fan wanting nostalgic) gets 2.0/6.0 on any recommendation because:
- No country songs exist: -2.0 pts
- No "nostalgic" mood exists: -1.0 pt
- Only numeric features remain: 2.0 pts max

Compare: User 2 (lofi fan) on the same song scores 5.88/6.0. That's a 66% gap on the *same song*.

This proves the algorithm isn't biased. The *data* is.

---

**Finding 5: Dataset composition is destiny**

Lofi is 30% of catalog → Lofi fans win

Country is 0% of catalog → Country fans lose

The algorithm treats all users identically. But because the dataset has more lofi, lofi fans automatically get better recommendations.

### Top Scores for Each User

| User | Top Score | Genre Match | Mood Match | Why This Score?                                       |
|------|-----------|-------------|------------|-------------------------------------------------------|
| 1    | 5.49/6.0  | ✓           | ✓          | Pop exists, happy exists                              |
| 2    | 5.88/6.0  | ✓           | ✓          | Lofi exists, chill exists, plus acoustic bonus        |
| 3    | 5.73/6.0  | ✓           | ✓          | Rock exists, intense exists.                          |
| 4.   | 2.32/6.0  | ✓.          | ✗          | Ambient exists but sad mood doesn't, energy mismatch  |
| 5    | 3.88/6.0  | ✓           | ✓          | Jazz exists, relaxed exists, but NO calm energy songs |
| 6    | 2.00/6.0  | ✗           | ✗          | Country missing, nostalgic missing, only numeric left |

### Plain-Language Insights

**Why do mainstream users win?** Pop and lofi are 50% of the catalog. These users find songs that match their preferences. It's luck, not algorithm design.

**Why do niche users lose?** Country (0%), nostalgic (0%), extreme calm (0 songs at energy 0.05). The algorithm can't make up for missing data.

**Why is the fairness gap so big?** Because categorical matches (genre, mood) are worth 3.0 out of 6.0 points. When both are missing, you lose 50% of your score immediately. That's not biased algorithm design—that's a structural consequence of how scoring works.

See **`PROFILE_COMPARISON_REFLECTION.md`** for detailed profile-by-profile explanations (why the pop fan gets "Gym Hero," why the rock fan beats the pop fan despite smaller dataset, etc.).

---

## 8. Intended Use and Non-Intended Use

### What MoodBeam IS For:
- Learning how recommender systems work
- Exploring algorithmic bias
- Understanding why Spotify might recommend only lofi to lofi fans
- Seeing the impact of dataset composition on fairness

### What MoodBeam IS NOT For:
- Real music recommendation (the 10-song catalog is too small)
- Production systems
- Replacing real streaming services

---

## 9. Ideas for Improvement

If we kept developing MoodBeam, here are 3 quick wins:

### 1. Add Mood Fallback (Easy Fix, Big Impact)
**Problem**: User wants "nostalgic" but that mood doesn't exist. Score collapses from 5.0 to 2.0 (55% drop).

**Solution**: Map missing moods to similar ones. If "nostalgic" not in catalog, give partial credit for "chill" or "moody" songs instead of zero credit.

**Expected result**: User 6 (country/nostalgic) would score 3.5/6.0 instead of 2.0/6.0. Fairness gap shrinks from 54% to 30%.

---

### 2. Expand the Catalog to 50+ Songs (Biggest Impact)
**Problem**: 10 songs is too small. Lofi is 30%, country is 0%. Users with niche preferences get crushed.

**Solution**: Add 40+ diverse songs covering country, jazz, electronic, sad moods, and extreme energy levels (very calm and very energetic).

**Expected result**: Country fans would get good recommendations. Lofi fans wouldn't dominate. Fairness gap would shrink to <10%.

---

### 3. Reduce Genre Weight from 2.0 to 1.5 (Instant Fix)
**Problem**: Genre is 33% of the score, creating unbreakable silos. A pop fan never sees rock, even with identical energy/mood.

**Solution**: Lower genre points so acoustic features matter more. Allows cross-genre recommendations.

**Expected result**: Users see more diverse recommendations. Genre silos break. Pop fan might get a good rock song instead of only pop.

---

### Bonus Ideas (If You Have More Time):
- **Add natural language explanations**: Instead of "energy 0.82 vs target 0.75," say "This song is slightly more energetic than you requested"
- **Measure fairness by worst-served users**: Check if the bottom 10% of users score >4.0/6.0, not just the average
- **Create a mood hierarchy taxonomy**: Not just moods, but relationships between them

---

## 10. Personal Reflection on the Engineering Process

### My Biggest Learning Moment

**The moment I realized fairness isn't about algorithm design—it's about data representation.**

I built MoodBeam with good intentions. I used a well-balanced scoring formula: genre 33%, mood 17%, audio features 50%. Every weight was justified. The Gaussian kernel made sense mathematically. Then I tested it on six user profiles and got hit with reality.

User 2 (lofi fan) scored 5.88/6.0 on "Midnight Coding." User 6 (country fan) scored 2.0/6.0 on the **same exact song**. Same algorithm. Same song. Different outcomes by 66%.

The reason? The data. Lofi is 30% of the catalog. Country is 0%.

This was the moment I understood: **you cannot engineer your way out of bad data.** No matter how clever the algorithm, if 30% of songs are lofi and 0% are country, lofi fans will always win. I could tweak weights, add fallbacks, improve the Gaussian kernel—but none of that would help a country fan if country songs don't exist in the catalog.

Real-world lesson: Companies like Spotify spend millions on recommendation algorithms, but their biggest fairness issues come from catalog composition, not algorithm design. If indie artists are underrepresented, no algorithm fixes that. If sad music is rare, no weighting scheme helps sad-seeking users.

---

### How AI Tools Helped (and When I Had to Double-Check)

**What AI Tools Did Great:**
- **Pattern documentation**: When I described the six user profiles, AI helped organize all the pattern findings into a clear table format showing mainstream vs niche users. This saved 2+ hours of manual organization.
- **Plain-language explanation**: Turning technical concepts ("Gaussian kernel with σ=0.15") into accessible language ("Gaussian curve rewards songs close to your target"). AI suggested multiple phrasings, and I picked the clearest.
- **Structure ideation**: Suggesting model card sections and helping organize findings into "bias categories" rather than random observations. The structure changed how I understood the problems.
- **Documentation at scale**: Writing profile comparisons for all 15 pairs would have been tedious manually. AI helped generate the structure; I verified each one.

**When I Had to Double-Check AI:**
1. **Fairness metrics**: AI suggested measuring "54% fairness gap" as (5.4 - 2.4) / 5.4. I verified this was the right calculation by manually checking it against all six profiles. It was correct, but I needed to confirm the math.

2. **Profile descriptions**: AI generated descriptions for what each profile "teaches us." I had to rewrite these because some were too generic ("validates scoring works"). I replaced them with specific insights tied to actual scores.

3. **Improvement suggestions**: AI suggested 5 priorities; I cut it to 3 and reordered by real impact. The original list was reasonable but lacked prioritization. I had to think through which fixes would actually help the most users.

4. **Explanation examples**: AI generated an example of the pop fan scoring. I re-ran the actual algorithm by hand to verify the math: 2.0 + 1.0 + 0.97 + 0.67 + 0.5 = 5.14. Numbers matched. Good sign.

**The Pattern:** AI excelled at organization and phrasing. It struggled with prioritization and numerical verification. Anytime AI suggested a metric or comparison, I manually verified it before including it in the model card.

---

### What Surprised Me About Simple Algorithms "Feeling" Like Recommendations

Building MoodBeam was humbling. The algorithm is embarrassingly simple:
- Count genre matches: 2 points
- Count mood matches: 1 point
- Gaussian curve on audio features: up to 3 points
- Total: up to 6 points
- Rank songs by points

That's it. Yet users *feel* like they're getting intelligent recommendations.

**Why does simplicity work?**

1. **Transparency beats complexity**: Users understand why they got a recommendation. "Genre match (2 pts) + mood match (1 pt) + energy close (0.9 pts) = 3.9 total." This is more understandable than a 50-layer neural network that just outputs "confidence 0.87."

2. **Multiple features feel personalized**: Using genre + mood + energy + valence + tempo all together makes the recommendation feel thoughtful, even though each feature is a simple number comparison. It's the *combination* that creates the illusion of intelligence.

3. **Explanations matter more than accuracy**: If I just said "here's your top 5 songs," users would be skeptical. But when I explain *why* they got each recommendation, they trust it more. The explanation makes the simple algorithm feel sophisticated.

4. **Real-world constraints feel realistic**: The fact that country fans can't get good recommendations because country songs are missing doesn't feel like a bug—it feels like honest feedback. "I don't have country songs in my catalog" is more trustworthy than "my algorithm recommends pop for you" when both actually lead to pop recommendations.

**Real insight:** Recommendation algorithms don't feel smart because they're mathematically complex. They feel smart because they explain their reasoning and respect data limitations.

---

### What Would I Try Next (If Extending This Project)

**In Order of Impact:**

#### 1. **Add Real User Testing (Highest Priority)**
Right now I'm testing with hypothetical profiles. But what if I interviewed 10 actual music listeners, asked them to describe their preferences, and ran MoodBeam on their inputs? I'd probably discover:
- Users describe music differently than I expect ("I want music to make me feel nostalgic" vs "nostalgic mood")
- Some preferences are nuanced in ways my binary categories miss
- The 54% fairness gap might be smaller or larger in real usage

**Expected impact**: Would reveal design flaws I can't see from my desk.

#### 2. **Implement the Mood Hierarchy Fallback (Quick Win)**
Add this mapping:
```
nostalgic → [chill, moody, relaxed]
melancholic → [moody, sad, relaxed]
energetic → [intense, happy, focused]
```

When a user requests "nostalgic" and no song has that mood, the algorithm gives partial credit (0.5 points) for songs tagged with similar moods. This alone would fix the 66% gap to maybe 30%.

**Implementation time**: 1 hour of coding, 30 minutes testing.

**Expected impact**: User 6 (country/nostalgic) jumps from 2.0/6.0 to 3.5+/6.0 immediately.

#### 3. **Expand the Catalog Strategically (Long-Term Play)**
Instead of 10 songs, aim for 50 with:
- 5+ country songs (currently 0)
- 5+ electronic songs (currently 0)
- 3+ sad/melancholic songs (currently 1)
- 5 songs with energy <0.30 (currently 1)
- 5 songs with valence <0.40 (currently 0)

Then re-run the six profiles and see:
- Do country fans finally get >4.0/6.0?
- Does the fairness gap shrink from 54% to <20%?
- Do extreme energy users get better recommendations?

**Why this matters**: This tests whether my whole fairness theory is correct. If fairness gap stays 54% even with a balanced catalog, I've misdiagnosed the problem.

#### 4. **A/B Test Weight Changes (Experimentation)**
Currently: Genre 2.0, Mood 1.0, Features 3.0.

Try:
- **Variant A (current)**: Genre 2.0, Mood 1.0, Features 3.0
- **Variant B**: Genre 1.5, Mood 1.5, Features 3.0 (equity between categorical and mood)
- **Variant C**: Genre 1.5, Mood 2.0, Features 2.5 (mood-forward)
- **Variant D**: Genre 1.0, Mood 1.0, Features 4.0 (numeric-forward)

For each variant, score all six profiles and see:
- Which variant has the smallest fairness gap?
- Which makes mainstream users happy without crushing niche users?
- What's the right balance?

**Expected learning**: Might discover that some weight combinations create unexpected fairness improvements.

#### 5. **Add Diversity Constraints (Nice-to-Have)**
Modify top-K recommendations to enforce diversity:
```
Top 5 songs must include:
- At least 2 different genres
- At least 2 different moods
- Spread across the energy spectrum
```

This prevents the "all recommendations are lofi" problem—the most common complaint about Spotify.

**Why it matters**: Even if the algorithm is fair, users don't *feel* served well if all recommendations are identical. Diversity constraints improve perceived fairness.

---

### Lessons for Real-World Systems

Building MoodBeam taught me three things about production recommendation systems:

**1. Fairness is structural, not algorithmic.**
You cannot audit your way to fairness if your data is imbalanced. Spotify's recommendation algorithm might be mathematically perfect, but if they have fewer songs from women artists, women artists will be less discoverable. No algorithm change fixes that—only data change does.

**2. Users care about reasons more than accuracy.**
If I rank songs by random score but explain the reasoning, users trust it more than a neural network that ranks better but explains nothing. Transparency beats accuracy in real-world trust.

**3. Edge cases reveal truth.**
When a user wants music that doesn't exist in your catalog (country, extreme calm, melancholic), the system reveals its limitations. This is where you learn what's actually broken vs what's just a design trade-off. Mainstream users hide these problems.

---

### How This Project Changed My Perspective on "AI" vs "Engineering"

I started this project thinking "AI recommenders" were magic. Turns out they're mostly:
- 70% data engineering (getting good data, representing all user types)
- 20% feature engineering (choosing which attributes matter)
- 10% algorithm design (the actual "smart" part)

I spent 70% of this project understanding data imbalances, 20% on scoring weights, and 10% on Gaussian kernels. And the Gaussian kernel was the least interesting part.

The real work was asking: **What user types does my data not represent?** Not "What algorithm is smartest?"
