import json
import re
import anthropic
import os
from shared.claude import MODEL_TEXT

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_KEY"])

NLP_SYSTEM = """You are a financial markets assistant. Extract structured intent from a user's natural language message about charts.

Return ONLY a valid JSON object with these exact fields, no other text:
{
  "type": "new_chart",
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "interval": "1d",
  "period": "1y",
  "raw_name": "Reliance"
}

Type rules:
- Use "new_chart_analysis" if message contains "with analysis"
- Use "new_chart" if a stock, commodity or forex name is mentioned
- Use "followup" if no asset is mentioned

Exchange rules:
- NSE for Indian stocks by default
- BSE if user says BSE
- MCX for Gold, Silver, Crude Oil, Natural Gas, Copper
- FOREX for currency pairs like USDINR, EURINR

Interval mapping:
- 5 min = 5m
- 15 min = 15m
- 30 min = 30m
- hourly = 1h
- daily = 1d
- weekly = 1wk
- monthly = 1mo
- default = 1d

Period mapping:
- 1 week = 5d
- 1 month = 1mo
- 3 months = 3mo
- 6 months = 6mo
- 1 year = 1y
- 2 years = 2y
- 3 years = 3y
- 5 years = 5y

Period defaults by interval:
- 5m, 15m = 5d
- 30m, 1h = 1mo
- 1d = 1y
- 1wk = 3y
- 1mo = 5y

Return null for any field you cannot determine.
Return ONLY the JSON object. No markdown. No explanation. No extra text."""

NLP_USER = "Message: {message}"


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