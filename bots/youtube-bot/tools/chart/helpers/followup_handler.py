import anthropic
import os
from tools.chart.prompts.analysis_prompt import FOLLOWUP_SYSTEM, FOLLOWUP_USER
from shared.claude import MODEL_TEXT

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_KEY"])


def answer_followup(question: str, state: dict, session: dict) -> str:
    """
    Answer a follow-up question using stored chart context + analysis.
    """
    try:
        # Build analysis section
        analysis = state.get("last_analysis")
        if analysis:
            analysis_section = f"Previous analysis:\n{analysis}"
        else:
            analysis_section = (
                "(No full analysis available — answering from chart metadata only)"
            )

        # Build history string (last 3 exchanges)
        history      = state.get("chat_history", [])
        history_text = ""
        for msg in history[-6:]:
            role          = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"

        metadata = state.get("metadata", {})

        prompt = FOLLOWUP_USER.format(
            symbol=state.get("last_symbol", ""),
            exchange=state.get("last_exchange", ""),
            interval=state.get("last_interval", ""),
            date_from=metadata.get("date_from", ""),
            date_to=metadata.get("date_to", ""),
            last_price=metadata.get("last_price", ""),
            period_high=metadata.get("period_high", ""),
            period_low=metadata.get("period_low", ""),
            analysis_section=analysis_section,
            history=history_text if history_text else "None",
            question=question,
        )

        response = client.messages.create(
            model=MODEL_TEXT,
            max_tokens=800,
            system=FOLLOWUP_SYSTEM,
            messages=[{"role": "user", "content": prompt}]
        )

        _track(session, response.usage)
        return response.content[0].text

    except Exception as e:
        print(f"Followup handler error: {e}")
        return f"Could not answer question: {e}"


def _track(session: dict, usage) -> None:
    u = session.setdefault("usage", _empty_usage())
    u["input_tokens"]       += getattr(usage, "input_tokens", 0)
    u["output_tokens"]      += getattr(usage, "output_tokens", 0)
    u["cache_write_tokens"] += getattr(usage, "cache_creation_input_tokens", 0)
    u["cache_read_tokens"]  += getattr(usage, "cache_read_input_tokens", 0)
    u["api_calls"]          += 1


def _empty_usage() -> dict:
    return {
        "input_tokens": 0, "output_tokens": 0,
        "cache_write_tokens": 0, "cache_read_tokens": 0,
        "api_calls": 0
    }
