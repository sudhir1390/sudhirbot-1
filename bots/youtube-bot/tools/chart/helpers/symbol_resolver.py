from tools.chart.helpers.symbol_map import SYMBOL_MAP

# Special yfinance tickers that don't follow .NS / .BO pattern
YFINANCE_MAP = {
    # NSE Indices
    "NIFTY":       "^NSEI",
    "BANKNIFTY":   "^NSEBANK",
    "SENSEX":      "^BSESN",
    "NIFTYIT":     "^CNXIT",
    "NIFTYPHARMA": "^CNXPHARMA",
    "NIFTYAUTO":   "^CNXAUTO",
    "NIFTYFMCG":   "^CNXFMCG",
    "FINNIFTY":    "^NSEMDCP50",
    "MIDCPNIFTY":  "^NSEMDCP50",

    # MCX Commodities -> international futures (USD)
    "GOLD":        "GC=F",
    "SILVER":      "SI=F",
    "CRUDEOIL":    "CL=F",
    "NATURALGAS":  "NG=F",
    "COPPER":      "HG=F",
    "ZINC":        "ZNC=F",
    "ALUMINIUM":   "ALI=F",
    "NICKEL":      "LNI=F",
    "LEAD":        "LLD=F",

    # Forex
    "USDINR":      "USDINR=X",
    "EURINR":      "EURINR=X",
    "GBPINR":      "GBPINR=X",
    "JPYINR":      "JPYINR=X",
    "EURUSD":      "EURUSD=X",
    "GBPUSD":      "GBPUSD=X",
    "USDJPY":      "USDJPY=X",
}


def resolve(symbol: str, exchange: str, raw_name: str = None) -> tuple:
    """
    Returns (yfinance_ticker, clean_symbol, exchange)
    """
    # Try raw_name lookup first (catches multi-word names like "hdfc bank")
    if raw_name:
        lookup = raw_name.lower().strip()
        if lookup in SYMBOL_MAP:
            symbol, exchange = SYMBOL_MAP[lookup]

    # Try symbol lookup
    if symbol:
        lookup = symbol.lower().strip()
        if lookup in SYMBOL_MAP:
            symbol, exchange = SYMBOL_MAP[lookup]

    # Build yfinance ticker
    ticker = _build_ticker(symbol, exchange)
    return ticker, symbol, exchange


def _build_ticker(symbol: str, exchange: str) -> str:
    # Check special map first
    if symbol in YFINANCE_MAP:
        return YFINANCE_MAP[symbol]

    # NSE stocks -> append .NS
    if exchange == "NSE":
        return f"{symbol}.NS"

    # BSE stocks -> append .BO
    if exchange == "BSE":
        return f"{symbol}.BO"

    # Fallback
    return symbol
