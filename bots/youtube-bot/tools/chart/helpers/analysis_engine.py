import base64
import anthropic
import os
from tools.chart.prompts.analysis_prompt import ANALYSIS_SYSTEM, ANALYSIS_USER
from shared.claude import MODEL_VISION

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_KEY"])


def analyse_chart(image_bytes: bytes, symbol: str, exchange: str,
                  interval: str, metadata: dict, session: dict) -> str:
    """
    Send chart image to Claude Vision for TA analysis.
    Returns structured analysis text.
    """
    try:
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        prompt = ANALYSIS_USER.format(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            date_from=metadata.get("date_from", ""),
            date_to=metadata.get("date_to", ""),
            last_price=metadata.get("last_price", ""),
            period_high=metadata.get("period_high", ""),
            period_low=metadata.get("period_low", ""),
        )

        response = client.messages.create(
            model=MODEL_VISION,
            max_tokens=2000,
            system=ANALYSIS_SYSTEM,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type":       "base64",
                            "media_type": "image/png",
                            "data":       image_b64,
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )

        _track(session, response.usage)
        return response.content[0].text

    except Exception as e:
        print(f"Analysis engine error: {e}")
        return f"Could not generate analysis: {e}"


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
