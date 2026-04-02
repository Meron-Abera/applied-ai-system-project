# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

TThis project builds a simple, content-based music recommender that follows the same two-step approach used in real streaming platforms: first generating a set of candidate songs, and then ranking them for the user. While real systems use a mix of signals like user behavior, embeddings, and session data, this version focuses on being easy to understand and reproducible.

Instead of collaborative filtering, I mainly use content-based features like genre, mood, and numeric “vibe” attributes (energy, valence, etc.). This makes it easier to explain why a song is recommended, while still allowing some diversity through adjustable weights.

For the data, each song includes fields like id, title, artist, genre, mood, and numeric features such as energy, tempo, valence, danceability, and acousticness. The user profile includes preferences like favorite genre, favorite mood, a target energy level, and whether they prefer acoustic songs.

For scoring, each song is compared to the user’s preferences. Numeric features are scored based on how close they are to the user’s target values using a smooth function, so closer matches get higher scores. On top of that, I add bonuses if the song matches the user’s preferred genre or mood.

The final score is a weighted combination of all these factors (for example, numeric features might count for around 60%, genre 25%, and mood 15%). After scoring, songs are ranked, and I apply simple rules like limiting repeated artists or adding some exploration to keep the recommendations varied.

### Song fields 
id (int)
title (str)
artist (str)
genre (str) — categorical (e.g., "pop", "lofi")
mood (str) — categorical (e.g., "chill", "happy", "intense")
energy (float, 0–1) — perceived intensity
tempo_bpm (float) — tempo in beats per minute
valence (float, 0–1) — musical positivity/happy vs sad
danceability (float, 0–1) — suitability for dancing / groove
acousticness (float, 0–1) — acoustic vs electronic/produced

### UserProfile fields 
favorite_genre (str)
favorite_mood (str)
target_energy (float, 0–1)
likes_acoustic (bool)
---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this


---

## 7. `model_card_template.md`

Combines reflection and model card framing from the Module 3 guidance. :contentReference[oaicite:2]{index=2}  

```markdown
# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

Give your recommender a name, for example:

> VibeFinder 1.0

---

## 2. Intended Use

- What is this system trying to do
- Who is it for

Example:

> This model suggests 3 to 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It is for classroom exploration only, not for real users.

---

## 3. How It Works (Short Explanation)

Describe your scoring logic in plain language.

- What features of each song does it consider
- What information about the user does it use
- How does it turn those into a number

Try to avoid code in this section, treat it like an explanation to a non programmer.

---

## 4. Data

Describe your dataset.

- How many songs are in `data/songs.csv`
- Did you add or remove any songs
- What kinds of genres or moods are represented
- Whose taste does this data mostly reflect

---

## 5. Strengths

Where does your recommender work well

You can think about:
- Situations where the top results "felt right"
- Particular user profiles it served well
- Simplicity or transparency benefits

---

## 6. Limitations and Bias

Where does your recommender struggle

Some prompts:
- Does it ignore some genres or moods
- Does it treat all users as if they have the same taste shape
- Is it biased toward high energy or one genre by default
- How could this be unfair if used in a real product

---

## 7. Evaluation

How did you check your system

Examples:
- You tried multiple user profiles and wrote down whether the results matched your expectations
- You compared your simulation to what a real app like Spotify or YouTube tends to recommend
- You wrote tests for your scoring logic

You do not need a numeric metric, but if you used one, explain what it measures.

---

## 8. Future Work

If you had more time, how would you improve this recommender

Examples:

- Add support for multiple users and "group vibe" recommendations
- Balance diversity of songs instead of always picking the closest match
- Use more features, like tempo ranges or lyric themes

---

## 9. Personal Reflection

A few sentences about what you learned:

- What surprised you about how your system behaved
- How did building this change how you think about real music recommenders
- Where do you think human judgment still matters, even if the model seems "smart"

