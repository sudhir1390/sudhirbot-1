import io
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle
import pandas as pd
import pandas_ta as ta
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
    20:  "#26c6da",   # cyan
    50:  "#ff9800",   # orange
    100: "#ef5350",   # red
    200: "#7b1fa2",   # purple
}
RSI_COLOR    = "#7c4dff"
RSI_MA_COLOR = "#ffd600"


def generate_chart(df: pd.DataFrame, symbol: str, exchange: str,
                   interval: str, metadata: dict) -> bytes:
    """
    Generate dark-theme candlestick chart with EMA 20/50/100/200,
    Volume, and RSI panels. Returns PNG as bytes.
    """
    # -- Calculate indicators --
    for period in [20, 50, 100, 200]:
        df[f"EMA{period}"] = ta.ema(df["Close"], length=period)

    df["RSI"]    = ta.rsi(df["Close"], length=14)
    df["RSI_MA"] = df["RSI"].rolling(14).mean()

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
            ax_price.plot(x, df[col].values,
                          color=color, linewidth=1.2,
                          label=f"EMA {period}", zorder=4)

    ax_price.legend(
        loc="upper left", fontsize=7.5,
        facecolor="#1e2230", edgecolor=GRID,
        labelcolor=TEXT, framealpha=0.9
    )

    ax_price.set_xlim(-1, len(df))
    ax_price.set_ylim(df["Low"].min() * 0.97, df["High"].max() * 1.02)

    # Price label
    last_close = df["Close"].iloc[-1]
    ax_price.annotate(
        f"{last_close:.2f}",
        xy=(1.002, last_close),
        xycoords=("axes fraction", "data"),
        fontsize=8, color="white",
        bbox=dict(boxstyle="round,pad=0.3", fc=DOWN, ec="none")
    )

    # Title
    ax_price.set_title(
        f"{exchange}:{symbol}  |  {_interval_label(interval)}  |  "
        f"{metadata['date_from']} - {metadata['date_to']}  |  "
        f"EMA 20/50/100/200",
        color=TEXT, fontsize=9, loc="left", pad=6
    )

    # -- Volume --
    for i, (_, row) in enumerate(df.iterrows()):
        color = UP if row["Close"] >= row["Open"] else DOWN
        ax_vol.bar(i, row["Volume"], color=color, alpha=0.6,
                   width=0.8, zorder=3)

    ax_vol.set_ylabel("Vol", color=TEXT, fontsize=8,
                      rotation=0, labelpad=30)
    ax_vol.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda v, _: f"{v/1e6:.0f}M"
                          if v >= 1e6 else f"{v/1e3:.0f}K")
    )

    # -- RSI --
    ax_rsi.plot(x, df["RSI"].values,
                color=RSI_COLOR, linewidth=1.2, label="RSI")
    ax_rsi.plot(x, df["RSI_MA"].values,
                color=RSI_MA_COLOR, linewidth=1.0, label="RSI MA")

    ax_rsi.axhline(60, color=TEXT, linewidth=0.6,
                   linestyle="--", alpha=0.6)
    ax_rsi.axhline(40, color=TEXT, linewidth=0.6,
                   linestyle="--", alpha=0.6)
    ax_rsi.axhline(50, color=GRID, linewidth=0.5, alpha=0.5)

    ax_rsi.fill_between(x, 60, df["RSI"].values,
                        where=(df["RSI"].values > 60),
                        color=UP, alpha=0.1)
    ax_rsi.fill_between(x, 40, df["RSI"].values,
                        where=(df["RSI"].values < 40),
                        color=DOWN, alpha=0.1)

    ax_rsi.set_ylim(20, 85)
    ax_rsi.set_ylabel("RSI", color=TEXT, fontsize=8,
                      rotation=0, labelpad=30)

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
    plt.savefig(buf, dpi=150, bbox_inches="tight",
                facecolor=BG, edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _interval_label(interval: str) -> str:
    mapping = {
        "5m":  "5 Min",  "15m": "15 Min", "30m": "30 Min",
        "1h":  "1 Hour", "1d":  "Daily",  "1wk": "Weekly",
        "1mo": "Monthly"
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
