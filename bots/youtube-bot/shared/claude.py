import os
import anthropic
from shared.utils import trim_to_budget

ANTHROPIC_KEY     = os.environ["ANTHROPIC_KEY"]
CACHE_TTL_SECONDS = 600
MAX_HISTORY       = 10

# ── Model configuration ───────────────────────────────────────────
# Update these when Anthropic releases new models
MODEL_TEXT     = "claude-haiku-4-5-20251001"   # NLP parsing — fast, cheap
MODEL_VISION   = "claude-sonnet-4-5-20250929"  # Chart analysis — best quality
MODEL_FOLLOWUP = "claude-sonnet-4-5-20250929"  # Follow-up Q&A — best quality
# ─────────────────────────────────────────────────────────────────

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

def build_system(transcript: str, context_label: str = "") -> list[dict]:
    label = f"You are discussing: {context_label}\n\n" if context_label else ""
    return [
        {
            "type": "text",
            "text": f"{label}You are a helpful assistant. Be concise — responses will be sent via Telegram.\n\n"
        },
        {
            "type": "text",
            "text": f"CONTENT:\n{trim_to_budget(transcript)}",
            "cache_control": {"type": "ephemeral"}
        }
    ]

def ask(transcript, history, question, session, context_label="",
        model=MODEL_TEXT, max_tokens=1024):
    import time
    messages = history[-MAX_HISTORY:] + [{"role": "user", "content": question}]
    system   = build_system(transcript, context_label)
    try:
        response = client.messages.create(
            model=model, max_tokens=max_tokens,
            system=system, messages=messages
        )
        session["cache_written_at"] = time.time()
        _track(session, response.usage)
        return response.content[0].text
    except anthropic.BadRequestError as e:
        if "context_length_exceeded" in str(e):
            system = build_system(transcript[:len(transcript)//2], context_label)
            response = client.messages.create(
                model=model, max_tokens=max_tokens,
                system=system, messages=messages
            )
            session["cache_written_at"] = time.time()
            _track(session, response.usage)
            return response.content[0].text + "\n\n_(Note: content was trimmed due to length)_"
        raise

def ask_json(content, prompt, session, model=MODEL_TEXT, max_tokens=1200):
    import re, time
    system = [
        {
            "type": "text",
            "text": "You are a helpful assistant. Respond ONLY with valid JSON. No markdown, no preamble.\n\n"
        },
        {
            "type": "text",
            "text": f"CONTENT:\n{trim_to_budget(content, 150_000)}",
            "cache_control": {"type": "ephemeral"}
        }
    ]
    response = client.messages.create(
        model=model, max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )
    session["cache_written_at"] = time.time()
    _track(session, response.usage)
    raw = response.content[0].text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return raw

def _track(session: dict, usage) -> None:
    u = session.setdefault("usage", _empty_usage())
    u["input_tokens"]       += getattr(usage, "input_tokens", 0)
    u["output_tokens"]      += getattr(usage, "output_tokens", 0)
    u["cache_write_tokens"] += getattr(usage, "cache_creation_input_tokens", 0)
    u["cache_read_tokens"]  += getattr(usage, "cache_read_input_tokens", 0)
    u["api_calls"]          += 1

def _empty_usage():
    return {
        "input_tokens": 0, "output_tokens": 0,
        "cache_write_tokens": 0, "cache_read_tokens": 0,
        "api_calls": 0
    }
