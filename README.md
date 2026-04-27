# MoodBeam: An Interactive Music Recommender with Semantic Fallback

This project transforms a foundational content-based music recommender into an intelligent, interactive, and resilient AI system. It features a web-based UI built with Streamlit and introduces a semantic fallback mechanism to gracefully handle user inputs that don't exist in the song catalog.

### Original Project Summary

The original project from Modules 1-3 was a Python-based music recommender. Its primary goal was to recommend songs from a small, static catalog based on a user's stated preferences for genre, mood, and other musical attributes like energy and tempo. The system used a scoring algorithm to rank songs based on how well they matched the user's query.

## Architecture Overview

The system is designed with a clear separation of concerns, from the user interface to the core AI logic.

1.  **Input**: A user provides their music preferences (e.g., favorite genre "Rap") via the Streamlit web interface.
2.  **Processing**: The `Recommender` receives the input. It checks if "Rap" exists in the `Song Catalog`. Since it doesn't, the `Semantic Fallback Engine` uses a `Sentence Transformer` model to find the most similar genre in the catalog (e.g., "reggae"). The `Scoring Engine` then ranks songs based on this adjusted preference.
3.  **Output**: The UI displays the top-ranked songs with a clear explanation of *why* they were recommended, including a note about the semantic fallback that was applied.
4.  **Evaluation**: The system is validated through both implicit `Human Review` (does the user like the recommendations?) and an automated `Consistency Tester` script that ensures the AI's behavior is reliable and predictable.

## Setup Instructions

To run this project locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-directory>
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **(Optional) Configure Anthropic for enhanced explanations:**
    Create a `.env` file (or export environment variables) with your API key.
    You can also set `ANTHROPIC_MODEL` to a model your account can access.
    ```bash
    ANTHROPIC_API_KEY='your-key-here'
    ANTHROPIC_MODEL='claude-3-5-sonnet-20240620'
    ```

5.  **Run the Streamlit application:**
    ```bash
    streamlit run app.py
    ```
    The application will open in your web browser.

## Sample Interactions

Here are a few examples of how the system responds to different user inputs.

### 1. Semantic Fallback for an Unknown Genre

*   **User Input**:
    *   Favorite Genre: `Rap`
    *   Favorite Mood: `energetic`
*   **AI Output**:
    *   **Explanation**: `Semantic fallback: genre 'Rap' not in catalog → using 'reggae'; mood 'energetic' not in catalog → using 'aggressive'`
    *   **Top Recommendation**: A song with the "reggae" genre that best matches the "aggressive" mood and other preferences.

### 2. Direct Match with No Fallback

*   **User Input**:
    *   Favorite Genre: `Pop`
    *   Favorite Mood: `upbeat`
*   **AI Output**:
    *   **Explanation**: `Recommended because: genre match (pop) (+2.0), mood match (upbeat) (+1.0), energy similarity (+0.98)`
    *   **Top Recommendation**: A "pop" song with an "upbeat" mood that scores highly on the user's other preferences.

## Design Decisions

*   **Content-Based Filtering**: I chose a content-based approach because it doesn't require user history, making it effective even for new users ("cold start" problem). The trade-off is that it cannot discover recommendations outside of a user's stated preferences without a mechanism like semantic fallback.
*   **Streamlit for UI**: I used Streamlit to rapidly develop an interactive and modern user interface. This allowed me to focus on the AI logic while still providing an effective way to demonstrate the system's capabilities.
*   **Semantic Search for Robustness**: Instead of simply failing when a user enters an unknown genre or mood, I implemented a semantic fallback system using a sentence-transformer model. This makes the application more robust and user-friendly. The trade-off is a slight increase in complexity and the introduction of a dependency on the `sentence-transformers` library.
*   **Explanations for Transparency**: The system doesn't just give a recommendation; it explains *why* a song was chosen. This builds user trust and makes the AI system's decisions transparent and interpretable.

## Testing Summary

To ensure the system's reliability, I created a testing script at `scripts/test_consistency.py`.

*   **What Worked**: The script successfully confirmed that the recommender is:
    1.  **Stable**: It produces the same recommendations every time for the same input.
    2.  **Sensitive**: Small changes to a user's profile correctly lead to different recommendations.
    3.  **Consistent**: The semantic fallback mechanism reliably maps an unknown genre to the same fallback genre on every run.

*   **What Didn't Work Initially**: During development, I encountered a `NotImplementedError: Cannot copy out of meta tensor` when running the app on an M-series Mac. This was caused by `torch` and `sentence-transformers` having trouble moving model tensors to the 'mps' device. I resolved this by explicitly telling the `SentenceTransformer` to use the `cpu` device, which fixed the issue without a noticeable impact on performance for this use case.

*   **What I Learned**: Testing is not just about finding bugs; it's about verifying that an AI system behaves as expected under different conditions. For AI, this includes checking for consistency and predictable responses, which is crucial for building trust and ensuring reliability.

## Responsible AI and Collaboration Reflection

### Limitations and Biases

The primary limitation of this system is its **catalog bias**. The recommendations are only as diverse as the `songs-v2.csv` file, which is very small and not representative of the vast world of music. This creates a significant bias towards the genres present in the catalog (like pop and reggae) and fails to serve users with tastes in underrepresented genres. While the semantic fallback mechanism makes the system more robust, it can't recommend a "classical" song if none exist in the dataset; it can only map the query to the "closest" available option, reinforcing the catalog's inherent bias.

### Potential for Misuse and Prevention

The risk of misuse for a music recommender is relatively low, but not zero. A system like this could be manipulated to create **auditory echo chambers**, pushing users towards a narrow set of artists or genres and limiting their musical discovery. If this system were used commercially, it could also be altered to unfairly promote certain artists over others.

To prevent this, I would implement:
1.  **Algorithmic Transparency**: Ensure the recommendation logic is documented and auditable.
2.  **Diversity Metrics**: Introduce metrics to measure and encourage the diversity of recommended artists and genres, preventing any single one from dominating.
3.  **User Controls**: Allow users to explicitly block artists or genres they don't like and provide feedback on recommendations.

### Surprises During Reliability Testing

During testing  the **unintended robustness of the semantic fallback**. I initially designed it to handle missing genres, but during testing, I discovered it could also correct minor user misspellings (like "acustic" for "acoustic"). This highlighted how embedding-based models can add a layer of intelligence that goes beyond the explicitly programmed rules. On the other hand, I was also surprised by a hardware-specific bug (`NotImplementedError` on Apple Silicon), which was a stark reminder that AI systems are not just abstract models but are deeply tied to the hardware they run on.

### Collaboration with AI

Throughout this project, I collaborated with GitHub Copilot. 

*   **Helpful Suggestion**: When I decided to build a testing script, Copilot provided a functional template for `scripts/test_consistency.py`. 

*   **Flawed Suggestion**: Initially, when trying to resolve the `sentence-transformers` import error, Copilot suggested installing the package globally using `pip` and `pip3`. This was incorrect because the project is set up with a specific Python virtual environment (`.venv`). The correct solution, which I had to implement, was to use the virtual environment's Python interpreter to install the package (`.venv/bin/python -m pip install ...`). This instance served as a crucial reminder that while AI can write excellent code, it doesn't always have the full context of the development environment, and human expertise is required to guide its suggestions.

