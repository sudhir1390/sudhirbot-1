# My AI Bots

Personal collection of Telegram AI bots powered by Claude AI. All three bots run as a single deployment on Render.com, each accessible via its own Telegram bot token.

## Bots

| Bot | What it does | Status |
|-----|-------------|--------|
| YouTube Bot | Summarize and quiz YouTube videos | Live |
| PDF Bot | Analyze and ask questions about PDFs | Live |
| TA Bot | Technical analysis charts for Indian stocks, commodities and forex | Live |

---

## YouTube Bot

A Telegram bot that lets you send any YouTube link and ask questions about it — summarize chapters, get key takeaways, quiz yourself, and see exactly how much each session costs in INR.

### Features
- YouTube Q&A — send any link, ask anything
- Chapter support — ask about specific chapters
- Per-chapter quiz — 3-question MCQ quiz on any chapter
- Multi-turn memory — follow-up questions stay in context
- Prompt caching — transcript cached, follow-ups cost 90% less
- INR billing — /bye ends session and shows exact cost in rupees
- 2-hour limit — videos over 120 min are rejected upfront

### YouTube Commands

| Input | What happens |
|-------|-------------|
| YouTube link | Fetches transcript and chapters, confirms to user |
| `list chapters` | Shows all chapters with timestamps |
| `quiz me` | Generates 3 MCQ questions on current chapter or full video |
| `answer: A/B/C/D` | Submits quiz answer, shows next question or final score |
| Any question | Q&A on the video content |
| `/bye` | End session, see INR bill |

---

## PDF Bot

A Telegram bot that lets you send any PDF and ask questions about it — summarize, extract key data, and have a full Q&A conversation, with exact session cost in INR.

### Features
- PDF Q&A — send any PDF, ask anything
- Summarize — type `summarize` for a full document summary
- Multi-turn memory — follow-up questions stay in context
- Prompt caching — PDF cached, follow-ups cost 90% less
- INR billing — /bye ends session and shows exact cost in rupees
- 200 page limit — first 200 pages processed, rest ignored with warning
- 20MB limit — Telegram's hard cap for file uploads
- Scanned PDF detection — warns user if no text can be extracted

### PDF Commands

| Input | What happens |
|-------|-------------|
| Send a PDF file | Auto-switches to /pdf, extracts text, confirms to user |
| `summarize` | Full document summary |
| Any question | Q&A on the PDF content |
| `/bye` | End session, see INR bill |

---

## TA Bot

A Telegram bot for technical analysis of Indian stocks, commodities and forex. Send any asset name with a timeframe and get a dark-theme candlestick chart with EMA, RSI and volume indicators — then ask follow-up questions about the chart.

### Features
- Candlestick charts — dark theme with EMA 20/50/100/200, RSI(14) + RSI MA, Volume
- Natural language requests — type "Reliance daily 1 year" or "Gold weekly 2 years"
- With analysis — append "with analysis" to get a full Claude Vision TA writeup
- Follow-up Q&A — ask questions after any chart; bot has full indicator context
- Rich indicator snapshot — EMA values, RSI zone, volume vs average, swing highs/lows, trend summary stored at render time and available for all follow-ups
- Indian markets focus — NSE/BSE stocks, MCX commodities, forex pairs
- INR billing — /bye ends session and shows exact cost in rupees

### Supported Assets

| Category | Examples |
|----------|---------|
| NSE Indices | Nifty, Bank Nifty, Finnifty, Sensex |
| NSE Large Caps | Reliance, TCS, Infosys, HDFC Bank, ICICI Bank, SBI and 50+ more |
| MCX Commodities | Gold, Silver, Crude Oil, Natural Gas, Copper, Zinc |
| Forex | USDINR, EURINR, GBPINR, EURUSD, GBPUSD |

### Intervals and Periods

| Interval | Default Period |
|----------|---------------|
| 5 min, 15 min | 5 days |
| 30 min, 1 hour | 1 month |
| Daily | 1 year |
| Weekly | 3 years |
| Monthly | 5 years |

### TA Bot Commands

| Input | What happens |
|-------|-------------|
| `Reliance daily 1 year` | Fetches data, renders chart, sends as photo |
| `Gold weekly 2 years with analysis` | Chart + full Claude Vision TA writeup |
| `Nifty 15 min last week` | Intraday chart for the past week |
| `list chapters` / any question | Follow-up Q&A using stored indicator snapshot |
| `/bye` | End session, see INR bill |

---

## Tech Stack

| Component | Tool | Cost |
|-----------|------|------|
| Messaging | Telegram Bot API | Free |
| Hosting | Render.com free tier | Free |
| AI — NLP parsing | Claude Haiku 4.5 | Low |
| AI — Chart analysis + Follow-ups | Claude Sonnet 4.6 | Medium |
| AI — YouTube/PDF Q&A | Claude Haiku 4.5 | Low |
| Transcripts | Supadata API | Free tier |
| PDF extraction | PyMuPDF | Free |
| Chart data | yfinance | Free |
| Chart rendering | Matplotlib + mplfinance + ta | Free |
| Keep-alive | UptimeRobot | Free |
| Code | GitHub (private repo) | Free |

---

## Cost Breakdown

Costs depend on which tools users interact with. Haiku 4.5 is used for YouTube/PDF Q&A and NLP parsing. Sonnet 4.6 is used for chart analysis (Vision) and chart follow-up Q&A.

| Scenario | Approx monthly cost |
|----------|-------------------|
| Light use — YouTube/PDF only (10 users) | ₹10–20 |
| Moderate use — includes chart Q&A, no analysis | ₹30–60 |
| Heavy use — chart with analysis daily | ₹100–200 |
| **Typical mixed use (10 users)** | **~₹40–80** |

Prompt caching cuts repeat Q&A costs by ~90%. Vision calls (chart with analysis) are the most expensive operation at ~₹1–2 per call.

---

## Architecture

All three bots are deployed as a **single service** on Render.com. Each bot has its own Telegram Bot token but shares the same gateway, session store, billing, and Claude client.

```
Users (Telegram)
      ↕
Telegram Bot API (free)
      ↕
Render.com — single deployment, hosts all 3 bots
  ├── gateway/
  │   ├── telegram.py     — receives messages + PDF uploads, sends replies/photos
  │   ├── router.py       — reads message, picks the right tool
  │   ├── session.py      — one session per user, per-tool state pockets
  │   └── billing.py      — tracks tokens, formats INR bill on /bye
  ├── shared/
  │   ├── claude.py       — single Claude client, shared across all tools
  │   └── utils.py        — trim_to_budget, estimate_tokens
  └── tools/
      ├── base.py         — BaseTool base class, every tool inherits this
      ├── youtube/
      │   ├── tool.py     — YouTube Q&A, chapter support, quiz flow
      │   └── helpers.py  — Supadata transcript fetch, chapter parsing, quiz formatting
      ├── pdf/
      │   ├── tool.py     — PDF Q&A, summarize
      │   └── helpers.py  — PyMuPDF extraction, page/token warnings
      └── chart/
          ├── tool.py     — orchestrates chart flow, stores indicator snapshot
          ├── helpers/
          │   ├── nlp_parser.py       — regex fast-path + Claude fallback for intent parsing
          │   ├── symbol_resolver.py  — resolves name/symbol to yfinance ticker
          │   ├── symbol_map.py       — lookup table for 80+ Indian assets
          │   ├── data_fetcher.py     — yfinance OHLCV download
          │   ├── chart_engine.py     — Matplotlib chart render + indicator snapshot
          │   ├── analysis_engine.py  — Claude Vision TA analysis
          │   └── followup_handler.py — follow-up Q&A with indicator context
          └── prompts/
              └── analysis_prompt.py  — prompt templates for analysis + follow-ups
        ↕
Claude API (Haiku 4.5 + Sonnet 4.6)
Supadata API (YouTube transcripts)
yfinance (market data)
GitHub (auto-deploy on git push)
```

---

## Message Flow

```
1. User sends message or PDF file on Telegram
2. Telegram forwards it to Render server via webhook POST
3. Gateway checks — is it a PDF file or a text message?
   - PDF file   → auto-switch to /pdf, extract text, confirm to user
   - Text       → extract user_id and message text
4. Router checks — is it a command (/youtube, /pdf, /chart, /help, /bye)?
   - /youtube   → switches active tool to YouTube
   - /pdf       → switches active tool to PDF
   - /chart     → switches active tool to TA Bot
   - /bye       → calculates bill, clears session, sends INR summary
   - /help      → lists all available tools
   - message    → sends to whichever tool is currently active
5. Tool handles the message:
   YouTube:
     - YouTube link  → fetches transcript + chapters via Supadata
     - Question      → sends transcript (cached) + question to Claude Haiku
     - quiz me       → generates 3 MCQ questions via Claude Haiku
     - answer: B     → checks answer, shows next question or final score
   PDF:
     - PDF file      → extracts text (max 200 pages), stores in session
     - summarize     → sends full doc to Claude Haiku for summary
     - Question      → sends PDF text (cached) + question to Claude Haiku
   TA Bot:
     - Chart request → NLP parser extracts symbol/interval/period
                     → yfinance fetches OHLCV data
                     → Matplotlib renders dark-theme chart
                     → indicator snapshot computed and stored in session
                     → chart sent as photo
     - with analysis → above + Claude Sonnet Vision analyses chart image
     - Follow-up     → Claude Sonnet answers using stored indicator snapshot
6. Reply sent back to user via Telegram
7. Token usage tracked silently for billing
```

---

## Session Lifecycle

```
User messages bot (or sends PDF) for first time
        ↓
Session auto-created
        ↓
User picks /youtube, /pdf, /chart — or sends a PDF (auto-switches to /pdf)
        ↓
Bot loads content / confirms tool is ready
        ↓
User asks questions
        ↓
User says /bye
        ↓
Bot shows bill in INR → session cleared
        ↓
Session also auto-clears at midnight (IST)
```

---

## Project Structure

```
sudhirbot/
  .gitignore
  .gitattributes
  README.md
  bots/
    youtube-bot/
      main.py              — entry point, registers all 3 tools
      requirements.txt     — Python dependencies
      render.yaml          — Render deployment config
      .python-version      — pins Python 3.11.0
      gateway/
        __init__.py
        telegram.py        — Telegram I/O, handles text + PDF uploads
        router.py          — message routing
        session.py         — user session management
        billing.py         — token tracking + INR bill
      shared/
        __init__.py
        claude.py          — single Anthropic client + caching
        utils.py           — token utilities
      tools/
        __init__.py
        base.py            — BaseTool base class
        youtube/
          __init__.py
          tool.py          — YouTube tool logic
          helpers.py       — YouTube helpers
        pdf/
          __init__.py
          tool.py          — PDF tool logic
          helpers.py       — PyMuPDF extraction
        chart/
          __init__.py
          tool.py          — TA Bot orchestration
          helpers/
            __init__.py
            nlp_parser.py
            symbol_resolver.py
            symbol_map.py
            data_fetcher.py
            chart_engine.py
            analysis_engine.py
            followup_handler.py
          prompts/
            __init__.py
            analysis_prompt.py
```

---

## Adding a New Tool

```python
# 1. Create tools/mytool/tool.py
class MyTool(BaseTool):
    command     = "/mytool"
    name        = "My Tool"
    description = "Does something useful"

    async def handle(self, message, session):
        state = self.get_state(session)
        # your logic here

# 2. Add two lines in main.py
from tools.mytool.tool import MyTool
router.register(MyTool())
```

Session, billing, Telegram, and caching are all inherited automatically.

---

## Deployment

All 3 bots are hosted on Render.com free tier as a single service. Auto-deploys from GitHub on every `git push`.

UptimeRobot pings `/health` every 5 minutes to prevent Render from sleeping.

```bash
git add .
git commit -m "describe your change"
git push
```

Render redeploys automatically in ~60 seconds.