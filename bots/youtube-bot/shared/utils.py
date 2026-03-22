CHARS_PER_TOKEN = 4

def estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN

def trim_to_budget(text: str, max_tokens: int = 178_000) -> str:
    max_chars = max_tokens * CHARS_PER_TOKEN
    if len(text) <= max_chars:
        return text
    trimmed = text[:max_chars]
    last_period = trimmed.rfind(". ")
    if last_period > max_chars * 0.8:
        trimmed = trimmed[:last_period + 1]
    return trimmed