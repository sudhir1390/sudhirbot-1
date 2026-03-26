from tools.base                            import BaseTool
from tools.chart.helpers.nlp_parser        import parse_intent
from tools.chart.helpers.symbol_resolver   import resolve
from tools.chart.helpers.data_fetcher      import fetch_ohlcv
from tools.chart.helpers.chart_engine      import generate_chart
from tools.chart.helpers.analysis_engine   import analyse_chart
from tools.chart.helpers.followup_handler  import answer_followup


class ChartTool(BaseTool):
    command     = "/chart"
    name        = "Chart Assistant"
    description = (
        "TA charts for Indian stocks, commodities & forex.\n"
        "Examples:\n"
        "  Reliance daily 1 year\n"
        "  Nifty 15 min last week\n"
        "  Gold weekly 2 years with analysis\n"
        "  USDINR daily 6 months"
    )

    async def handle(self, message: str, session: dict):
        state    = self.get_state(session)
        intent   = parse_intent(message)
        msg_type = intent.get("type", "followup")

        # ── Follow-up question ────────────────────────────────
        if msg_type == "followup":
            if not state.get("last_symbol"):
                return (
                    "📊 Send me a chart request to get started!\n\n"
                    "*Examples:*\n"
                    "• `Reliance daily 1 year`\n"
                    "• `Nifty 15 min last week`\n"
                    "• `Gold weekly 2 years with analysis`\n"
                    "• `USDINR daily 6 months`"
                )
            answer = answer_followup(message, state, session)
            state.setdefault("chat_history", []).extend([
                {"role": "user",      "content": message},
                {"role": "assistant", "content": answer},
            ])
            return answer

        # ── New chart request ─────────────────────────────────
        symbol        = intent.get("symbol")
        exchange      = intent.get("exchange", "NSE")
        interval      = intent.get("interval", "1d")
        period        = intent.get("period",   "1y")
        raw_name      = intent.get("raw_name")
        with_analysis = (msg_type == "new_chart_analysis")

        if not symbol:
            return "❌ Couldn't identify a symbol. Try: `Reliance daily 1 year`"

        # Resolve to yfinance ticker
        ticker, symbol, exchange = resolve(symbol, exchange, raw_name)

        # Fetch OHLCV data
        df, metadata = fetch_ohlcv(ticker, interval, period)
        if df is None:
            return f"❌ {metadata.get('error', 'Could not fetch data')} for *{symbol}*"

        # Generate chart image
        try:
            image_bytes = generate_chart(df, symbol, exchange, interval, metadata)
        except Exception as e:
            print(f"Chart engine error: {e}")
            return f"❌ Could not generate chart: {e}"

        # Store state for follow-ups
        state.update({
            "last_symbol":   symbol,
            "last_exchange": exchange,
            "last_interval": interval,
            "last_period":   period,
            "metadata":      metadata,
            "last_analysis": None,
            "chat_history":  [],
        })

        caption = (
            f"*{exchange}:{symbol}*  |  {_interval_label(interval)}  |  "
            f"{metadata['date_from']} - {metadata['date_to']}\n"
            f"Last: *{metadata['last_price']}*  "
            f"H: {metadata['period_high']}  "
            f"L: {metadata['period_low']}"
        )

        # Chart only
        if not with_analysis:
            return {
                "type":     "photo",
                "image":    image_bytes,
                "caption":  caption,
                "analysis": None,
            }

        # Chart + analysis
        analysis             = analyse_chart(
            image_bytes, symbol, exchange, interval, metadata, session
        )
        state["last_analysis"] = analysis

        return {
            "type":     "photo",
            "image":    image_bytes,
            "caption":  caption,
            "analysis": analysis,
        }


def _interval_label(interval: str) -> str:
    mapping = {
        "5m":  "5 Min",  "15m": "15 Min", "30m": "30 Min",
        "1h":  "1 Hour", "1d":  "Daily",  "1wk": "Weekly",
        "1mo": "Monthly"
    }
    return mapping.get(interval, interval)
