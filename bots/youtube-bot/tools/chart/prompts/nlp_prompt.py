import json
import re
import anthropic
import os
from tools.chart.prompts.nlp_prompt import NLP_SYSTEM, NLP_USER
from shared.claude import MODEL_TEXT

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_KEY"])

def parse_intent(message: str) -> dict:
    """
    Parse user message into structured chart intent.
    Returns dict with: type, symbol, exchange, interval, period, raw_name
    """
    try:
        response = client.messages.create(
            model=MODEL_TEXT,
            max_tokens=300,
            system=NLP_SYSTEM,
            messages=[{
                "role": "user",
                "content": NLP_USER.format(message=message)
            }]
        )
        raw = response.content[0].text.strip()
        print(f"NLP raw repr: {repr(raw)}")
        # Strip markdown code blocks if present
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        raw = raw.strip()
        print(f"NLP after strip: {repr(raw)}")
        return json.loads(raw)
    except Exception as e:
        print(f"NLP parser error: {e}")
        return {
            "type":     "followup",
            "symbol":   None,
            "exchange": None,
            "interval": None,
            "period":   None,
            "raw_name": None
        }