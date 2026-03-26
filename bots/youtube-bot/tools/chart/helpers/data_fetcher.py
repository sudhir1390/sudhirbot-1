import yfinance as yf
import pandas as pd


def fetch_ohlcv(ticker: str, interval: str, period: str) -> tuple:
    """
    Fetch OHLCV data from yfinance.
    Returns (dataframe, metadata dict)
    """
    try:
        df = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
            timeout=15          # ← fix 6: prevent indefinite hangs
        )

        if df.empty:
            return None, {"error": f"No data found for {ticker}"}

        # Flatten multi-level columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Ensure required columns exist
        required = ["Open", "High", "Low", "Close", "Volume"]
        for col in required:
            if col not in df.columns:
                return None, {"error": f"Missing column {col} for {ticker}"}

        # Drop rows with NaN
        df = df.dropna()

        if len(df) < 10:
            return None, {"error": f"Insufficient data for {ticker} — only {len(df)} bars"}

        metadata = {
            "ticker":      ticker,
            "interval":    interval,
            "period":      period,
            "bars":        len(df),
            "date_from":   df.index[0].strftime("%d %b %Y"),
            "date_to":     df.index[-1].strftime("%d %b %Y"),
            "last_price":  round(float(df["Close"].iloc[-1]), 2),
            "period_high": round(float(df["High"].max()), 2),
            "period_low":  round(float(df["Low"].min()), 2),
        }

        return df, metadata

    except Exception as e:
        return None, {"error": str(e)}
