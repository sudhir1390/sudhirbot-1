import json
import anthropic
import os
from tools.chart.prompts.nlp_prompt import NLP_SYSTEM, NLP_USER

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_KEY"])

def parse_intent(message: str) -> dict:
    """
    Parse user message into structured chart intent.
    Returns dict with: type, symbol, exchange, interval, period, raw_name
    """
    try:
        response = client.messages.create(
            model="claude-haiku-latest",
            max_tokens=300,
            system=NLP_SYSTEM,
            messages=[{
                "role": "user",
                "content": NLP_USER.format(message=message)
            }]
        )
        raw = response.content[0].text.strip()
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
