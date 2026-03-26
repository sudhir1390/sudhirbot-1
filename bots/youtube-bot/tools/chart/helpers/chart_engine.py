import io
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle
import pandas as pd
import ta as ta_lib
import warnings
warnings.filterwarnings("ignore")

# -- Dark theme colors --
BG         = "#131722"
PANEL_BG   = "#131722"
GRID       = "#1e2230"
TEXT       = "#b2b5be"
UP         = "#26a69a"
DOWN       = "#ef5350"
EMA_COLORS = {
    20:  "#26c6da",
    50:  "#ff9800",
    100: "#ef5350",
    200: "#7b1fa2",
}
RSI_COLOR    = "#7c4dff"
RSI_MA_COLOR = "#ffd600"


def generate_chart(df: pd.DataFrame, symbol: str, exchange: str,
                   interval: str, metadata: dict) -> tuple[bytes, str]:
    """
    Generate dark-theme candlestick chart with EMA 20/50/100/200,
    Volume, and RSI panels.
    Returns (image_bytes as PNG, indicator_text snapshot for follow-up context).
    """
    # -- Calculate indicators --
    df["EMA20"]  = ta_lib.trend.ema_indicator(df["Close"], window=20)
    df["EMA50"]  = ta_lib.trend.ema_indicator(df["Close"], window=50)
    df["EMA100"] = ta_lib.trend.ema_indicator(df["Close"], window=100)
    df["EMA200"] = ta_lib.trend.ema_indicator(df["Close"], window=200)
    df["RSI"]    = ta_lib.momentum.rsi(df["Close"], window=14)
    df["RSI_MA"] = df["RSI"].rolling(14).mean()

    # -- Build indicator text snapshot (fix 7) --
    indicator_text = _build_indicator_text(df, symbol, exchange, interval, metadata)

    # -- Figure setup --
    fig = plt.figure(figsize=(18, 10), facecolor=BG)
    gs  = gridspec.GridSpec(3, 1, figure=fig,
                            height_ratios=[5, 1.5, 1.5],
                            hspace=0.04)

    ax_price = fig.add_subplot(gs[0])
    ax_vol   = fig.add_subplot(gs[1], sharex=ax_price)
    ax_rsi   = fig.add_subplot(gs[2], sharex=ax_price)

    for ax in [ax_price, ax_vol, ax_rsi]:
        ax.set_facecolor(PANEL_BG)
        ax.tick_params(colors=TEXT, labelsize=8)
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position("right")
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID)
        ax.grid(color=GRID, linewidth=0.5, alpha=0.8)

    x = np.arange(len(df))

    # -- Candlesticks --
    width = 0.6
    for i, (_, row) in enumerate(df.iterrows()):
        color = UP if row["Close"] >= row["Open"] else DOWN
        ax_price.add_patch(Rectangle(
            (i - width / 2, min(row["Open"], row["Close"])),
            width, abs(row["Close"] - row["Open"]),
            color=color, zorder=3
        ))
        ax_price.plot([i, i], [row["Low"], row["High"]],
                      color=color, linewidth=0.7, zorder=2)

    # -- EMAs --
    for period, color in EMA_COLORS.items():
        col = f"EMA{period}"
        if col in df.columns:
            last_val = df[col].iloc[-1]
            label = f"EMA {period}  {last_val:,.2f}" if pd.notna(last_val) else f"EMA {period}"
            ax_price.plot(x, df[col].values,
                          color=color, linewidth=1.2,
                          label=label, zorder=4)

    ax_price.legend(
        loc="upper left", fontsize=7.5,
        facecolor="#1e2230", edgecolor=GRID,
        labelcolor=TEXT, framealpha=0.9
    )

    ax_price.set_xlim(-1, len(df))
    ax_price.set_ylim(df["Low"].min() * 0.97, df["High"].max() * 1.02)

    last_close = df["Close"].iloc[-1]
    ax_price.annotate(
        f"{last_close:.2f}",
        xy=(1.002, last_close),
        xycoords=("axes fraction", "data"),
        fontsize=8, color="white",
        bbox=dict(boxstyle="round,pad=0.3", fc=DOWN, ec="none")
    )

    ax_price.set_title(
        f"{exchange}:{symbol}  |  {_interval_label(interval)}  |  "
        f"{metadata['date_from']} - {metadata['date_to']}  |  "
        f"EMA 20/50/100/200",
        color=TEXT, fontsize=9, loc="left", pad=6
    )

    # -- Volume --
    for i, (_, row) in enumerate(df.iterrows()):
        color = UP if row["Close"] >= row["Open"] else DOWN
        ax_vol.bar(i, row["Volume"], color=color, alpha=0.6, width=0.8, zorder=3)

    ax_vol.set_ylabel("Vol", color=TEXT, fontsize=8, rotation=0, labelpad=30)
    ax_vol.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda v, _: f"{v/1e6:.0f}M" if v >= 1e6 else f"{v/1e3:.0f}K")
    )

    # -- RSI --
    ax_rsi.plot(x, df["RSI"].values, color=RSI_COLOR, linewidth=1.2, label="RSI")
    ax_rsi.plot(x, df["RSI_MA"].values, color=RSI_MA_COLOR, linewidth=1.0, label="RSI MA")
    ax_rsi.axhline(60, color=TEXT, linewidth=0.6, linestyle="--", alpha=0.6)
    ax_rsi.axhline(40, color=TEXT, linewidth=0.6, linestyle="--", alpha=0.6)
    ax_rsi.axhline(50, color=GRID, linewidth=0.5, alpha=0.5)
    ax_rsi.fill_between(x, 60, df["RSI"].values,
                        where=(df["RSI"].values > 60), color=UP, alpha=0.1)
    ax_rsi.fill_between(x, 40, df["RSI"].values,
                        where=(df["RSI"].values < 40), color=DOWN, alpha=0.1)
    ax_rsi.set_ylim(20, 85)
    ax_rsi.set_ylabel("RSI", color=TEXT, fontsize=8, rotation=0, labelpad=30)

    last_rsi    = df["RSI"].iloc[-1]
    last_rsi_ma = df["RSI_MA"].iloc[-1]
    ax_rsi.annotate(
        f"RSI {last_rsi:.1f}  MA {last_rsi_ma:.1f}",
        xy=(0.01, 0.88), xycoords="axes fraction",
        fontsize=8, color=TEXT
    )
    ax_rsi.legend(
        loc="upper right", fontsize=7,
        facecolor="#1e2230", edgecolor=GRID,
        labelcolor=TEXT, framealpha=0.9
    )

    # -- X-axis dates --
    tick_positions, tick_labels = _build_xticks(df, interval)
    ax_rsi.set_xticks(tick_positions)
    ax_rsi.set_xticklabels(tick_labels, color=TEXT, fontsize=8)
    plt.setp(ax_price.get_xticklabels(), visible=False)
    plt.setp(ax_vol.get_xticklabels(),   visible=False)

    # -- Save to bytes --
    buf = io.BytesIO()
    plt.savefig(buf, dpi=150, bbox_inches="tight", facecolor=BG, edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.read(), indicator_text


def _build_indicator_text(df: pd.DataFrame, symbol: str, exchange: str,
                           interval: str, metadata: dict) -> str:
    """
    Build a rich plain-text snapshot of all computed indicators.
    Stored in state and injected directly into the follow-up prompt.
    """
    last  = df.iloc[-1]
    close = float(last["Close"])

    # -- EMAs --
    ema20  = _val(df, "EMA20")
    ema50  = _val(df, "EMA50")
    ema100 = _val(df, "EMA100")
    ema200 = _val(df, "EMA200")

    # EMA positioning
    def pos(ema): return "above" if ema and close > ema else "below"
    ema_cross = []
    if ema20 and ema50:
        ema_cross.append(f"EMA20 {'>' if ema20 > ema50 else '<'} EMA50")
    if ema50 and ema200:
        ema_cross.append(f"EMA50 {'>' if ema50 > ema200 else '<'} EMA200")

    # -- RSI --
    rsi    = _val(df, "RSI")
    rsi_ma = _val(df, "RSI_MA")
    if rsi:
        rsi_zone = "overbought" if rsi > 60 else "oversold" if rsi < 40 else "neutral"
        rsi_vs_ma = "above" if (rsi and rsi_ma and rsi > rsi_ma) else "below"

    # -- Volume --
    last_vol   = float(last["Volume"])
    avg_vol_20 = float(df["Volume"].tail(20).mean())
    vol_ratio  = last_vol / avg_vol_20 if avg_vol_20 > 0 else 1.0
    vol_signal = "above average" if vol_ratio > 1.1 else "below average" if vol_ratio < 0.9 else "average"

    # Volume trend — last 5 bars slope
    vol5 = df["Volume"].tail(5).values
    vol_trend = "increasing" if vol5[-1] > vol5[0] else "decreasing"

    # -- Price structure --
    period_high = metadata.get("period_high", float(df["High"].max()))
    period_low  = metadata.get("period_low",  float(df["Low"].min()))
    pct_from_high = round((close - period_high) / period_high * 100, 2)
    pct_from_low  = round((close - period_low)  / period_low  * 100, 2)

    # Recent swing highs/lows — local extremes in last 20 bars
    recent = df.tail(20)
    swing_highs = _swing_points(recent["High"].values, mode="high")
    swing_lows  = _swing_points(recent["Low"].values,  mode="low")

    # -- Trend summary --
    above_count = sum(1 for e in [ema20, ema50, ema100, ema200] if e and close > e)
    if above_count == 4:
        trend = "strongly bullish (price above all EMAs)"
    elif above_count >= 3:
        trend = "bullish (price above most EMAs)"
    elif above_count == 2:
        trend = "mixed / sideways"
    elif above_count == 1:
        trend = "bearish (price below most EMAs)"
    else:
        trend = "strongly bearish (price below all EMAs)"

    # -- Assemble text --
    lines = [
        f"CHART INDICATORS — {exchange}:{symbol} | {interval} | {metadata.get('date_from')} to {metadata.get('date_to')}",
        "",
        f"Price: {close:.2f}  |  Period High: {period_high}  |  Period Low: {period_low}",
        f"Distance from period high: {pct_from_high:.2f}%  |  From period low: +{pct_from_low:.2f}%",
        "",
        "EMAs:",
        f"  EMA 20:  {_fmt(ema20)}  ({pos(ema20)} price)",
        f"  EMA 50:  {_fmt(ema50)}  ({pos(ema50)} price)",
        f"  EMA 100: {_fmt(ema100)}  ({pos(ema100)} price)",
        f"  EMA 200: {_fmt(ema200)}  ({pos(ema200)} price)",
        f"  Crossovers: {', '.join(ema_cross) if ema_cross else 'none computed'}",
        "",
        "RSI (14):",
        f"  RSI: {_fmt(rsi)}  |  RSI MA: {_fmt(rsi_ma)}",
        f"  Zone: {rsi_zone if rsi else 'n/a'}  |  RSI vs MA: {rsi_vs_ma if rsi else 'n/a'}",
        "",
        "Volume:",
        f"  Last bar: {_fmt_vol(last_vol)}  |  20-bar avg: {_fmt_vol(avg_vol_20)}",
        f"  Signal: {vol_signal} ({vol_ratio:.2f}x avg)  |  5-bar trend: {vol_trend}",
        "",
        f"Recent swing highs (last 20 bars): {', '.join(str(round(v,2)) for v in swing_highs) or 'none'}",
        f"Recent swing lows  (last 20 bars): {', '.join(str(round(v,2)) for v in swing_lows)  or 'none'}",
        "",
        f"Trend: {trend}",
    ]
    return "\n".join(lines)


def _val(df: pd.DataFrame, col: str) -> float | None:
    if col not in df.columns:
        return None
    v = df[col].iloc[-1]
    return float(v) if pd.notna(v) else None


def _fmt(v: float | None) -> str:
    return f"{v:,.2f}" if v is not None else "n/a"


def _fmt_vol(v: float) -> str:
    if v >= 1_000_000:
        return f"{v/1_000_000:.2f}M"
    if v >= 1_000:
        return f"{v/1_000:.1f}K"
    return str(int(v))


def _swing_points(values: np.ndarray, mode: str, window: int = 3) -> list[float]:
    """Return local maxima (mode='high') or minima (mode='low') from array."""
    result = []
    for i in range(window, len(values) - window):
        segment = values[i - window: i + window + 1]
        if mode == "high" and values[i] == max(segment):
            result.append(float(values[i]))
        elif mode == "low" and values[i] == min(segment):
            result.append(float(values[i]))
    return result[-3:] if result else []  # last 3 only


def _interval_label(interval: str) -> str:
    mapping = {
        "5m": "5 Min", "15m": "15 Min", "30m": "30 Min",
        "1h": "1 Hour", "1d": "Daily", "1wk": "Weekly", "1mo": "Monthly"
    }
    return mapping.get(interval, interval)


def _build_xticks(df: pd.DataFrame, interval: str):
    positions, labels = [], []
    prev = None
    for i, dt in enumerate(df.index):
        if interval in ("5m", "15m", "30m", "1h"):
            key   = dt.strftime("%d %b")
            label = dt.strftime("%d %b")
        elif interval in ("1d", "1wk"):
            key   = dt.strftime("%b %Y")
            label = dt.strftime("%b %y")
        else:
            key   = dt.strftime("%Y")
            label = dt.strftime("%Y")
        if key != prev:
            positions.append(i)
            labels.append(label)
            prev = key
    return positions, labels
