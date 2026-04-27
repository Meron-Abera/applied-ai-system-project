import os
import anthropic

_anthropic_client = None
_anthropic_model = None
_NO_MODEL_SENTINEL = "__none__"


def _get_model_candidates():
    env_models = os.environ.get("ANTHROPIC_MODEL", "").strip()
    candidates = []
    if env_models:
        candidates.extend([model.strip() for model in env_models.split(",") if model.strip()])
    candidates.extend(
        [
            "claude-3-5-sonnet-20240620",
            "claude-3-5-haiku-20241022",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]
    )

    seen = set()
    deduped = []
    for model in candidates:
        if model not in seen:
            deduped.append(model)
            seen.add(model)
    return deduped


def _is_model_not_found(error: Exception) -> bool:
    message = str(error)
    return "not_found_error" in message or "model:" in message or "404" in message

def get_anthropic_client():
    """Initializes and returns the Anthropic client, reusing it if already created."""
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set.")
        _anthropic_client = anthropic.Anthropic(api_key=api_key)
    return _anthropic_client

def generate_anthropic_explanation(song, reasons, user_profile):
    """
    Uses Anthropic's Claude to generate a more creative and personalized
    recommendation explanation.
    """
    client = get_anthropic_client()

    # Combine the structured reasons into a more readable format for the prompt
    reasons_str = ", ".join(reasons)

    prompt = (
        f"You are a friendly and knowledgeable music expert named MoodBeam. "
        f"A user, whose preferences are for {user_profile.favorite_genre} music with a {user_profile.favorite_mood} mood, "
        f"has been recommended the song '{song.title}' by {song.artist}.\n\n"
        f"The technical reasons for this recommendation are: {reasons_str}.\n\n"
        f"Based on this, write a short, engaging, and personalized explanation (1-2 sentences) for why the user might enjoy this song. "
        f"Speak directly to the user. For example: 'Since you like... you might love...'."
    )

    global _anthropic_model

    if _anthropic_model == _NO_MODEL_SENTINEL:
        return "Recommended because: " + reasons_str + "."

    models_to_try = [_anthropic_model] if _anthropic_model else _get_model_candidates()
    last_error = None

    for model in models_to_try:
        try:
            message = client.messages.create(
                model=model,
                max_tokens=100,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )
            _anthropic_model = model
            return message.content[0].text
        except Exception as e:
            last_error = e
            if _is_model_not_found(e):
                continue
            print(f"Error calling Anthropic API: {e}")
            return "Recommended because: " + reasons_str + "."

    if last_error:
        print(
            "Error calling Anthropic API: no available model found. "
            "Set ANTHROPIC_MODEL to a model your account can access."
        )
        _anthropic_model = _NO_MODEL_SENTINEL
    # Fallback to the simple explanation if the API call fails
    return "Recommended because: " + reasons_str + "."
