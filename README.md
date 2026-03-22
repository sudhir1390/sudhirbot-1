# My AI Bots

Personal collection of Telegram AI bots powered by Claude AI.

## Bots

| Bot | What it does | Status |
|-----|-------------|--------|
| youtube-bot | Summarize and quiz YouTube videos | Live |
| pdf-bot | Analyze and ask questions about PDFs | Live |

---

## YouTube Bot

A Telegram bot that lets you send any YouTube link and ask questions about it — summarize chapters, get key takeaways, quiz yourself, and see exactly how much each session cost in INR.

### Features
- YouTube Q&A — send any link, ask anything
- Chapter support — ask about specific chapters
- Per-chapter quiz — 3-question MCQ quiz on any chapter
- Multi-turn memory — follow-up questions stay in context
- Prompt caching — transcript cached, follow-ups cost 90% less
- INR billing — /bye ends session and shows exact cost in rupees
- 2-hour limit — videos over 120 min are rejected upfront

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
| Send a PDF file | Auto-switches to /pdf, extracts text, confirms |
| `summarize` | Full document summary |
| Any question | Q&A on the PDF content |
| `/bye` | End session, see INR bill |

---

## Tech Stack

| Component | Tool | Cost |
|-----------|------|------|
| Messaging | Telegram Bot API | Free |
| Hosting | Render.com free tier | Free |
| AI | Claude Haiku (Anthropic) | ~₹10-20/month |
| Transcripts | yt-dlp + YouTubeTranscriptApi | Free |
| PDF extraction | PyMuPDF | Free |
| Keep-alive | UptimeRobot | Free |
| Code | GitHub (private repo) | Free |

---

## Architecture

```
You + friends (Telegram)
        ↕
Telegram Bot API (free)
        ↕
Render.com free tier — hosts everything
  ├── gateway/
  │   ├── telegram.py     — receives messages + PDF uploads, sends replies
  │   ├── router.py       — reads message, picks the right tool
  │   ├── session.py      — one session per user, per-tool pockets
  │   └── billing.py      — tracks tokens, formats INR bill on /bye
  ├── shared/
  │   ├── claude.py       — single Claude client, caching + usage tracking
  │   └── utils.py        — trim_to_budget, estimate_tokens
  └── tools/
      ├── base.py         — BaseTool base class, every tool inherits this
      ├── youtube/
      │   ├── tool.py     — YouTube logic, clean handle() method
      │   └── helpers.py  — yt-dlp, transcript, chapters, quiz formatting
      └── pdf/
          ├── tool.py     — PDF logic, Q&A + summarize
          └── helpers.py  — PyMuPDF extraction, page/token warnings
        ↕
Claude API (paid ~₹10-20/mo)
YouTube (yt-dlp + transcript, free)
GitHub (auto-deploy on git push, free)
```

---

## How it works — Message Flow

```
1. User sends message or PDF file on Telegram
2. Telegram forwards it to Render server via webhook POST
3. Gateway checks — is it a PDF file or a text message?
   - PDF file   → auto-switch to /pdf, extract text, confirm to user
   - Text       → extract user_id and message text
4. Router checks — is it a command (/youtube, /pdf, /help, /bye)?
   - /youtube   → switches active tool to YouTube
   - /pdf       → switches active tool to PDF
   - /bye       → calculates bill, clears session, sends INR summary
   - /help      → lists all available tools
   - message    → sends to whichever tool is currently active
5. Tool handles the message:
   YouTube:
     - YouTube link  → fetches transcript + chapters via yt-dlp
     - Question      → sends transcript (cached) + question to Claude
     - quiz me       → generates 3 MCQ questions via Claude
     - answer: B     → checks answer, shows next question or final score
   PDF:
     - PDF file      → extracts text (max 200 pages), stores in session
     - summarize     → sends full doc to Claude for summary
     - Question      → sends PDF text (cached) + question to Claude
6. Reply sent back to user via Telegram
7. Token usage tracked silently for billing
```

---

## Session lifecycle

```
User messages bot (or sends PDF) for first time
        ↓
Session auto-created
        ↓
User picks /youtube or sends a PDF (auto-switches to /pdf)
        ↓
Bot loads content, confirms to user
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

## Cost breakdown

| Item | Monthly cost |
|------|-------------|
| Render hosting | ₹0 |
| Telegram Bot API | ₹0 |
| UptimeRobot | ₹0 |
| GitHub | ₹0 |
| Claude API (10 users, daily use) | ~₹10–20 |
| **Total** | **~₹10–20/month** |

---

## Project Structure

```
my-ai-bots/
  .gitignore
  README.md
  bots/
    youtube-bot/
      main.py              — entry point, registers tools
      requirements.txt     — Python dependencies
      render.yaml          — Render deployment config
      gateway/
        __init__.py
        telegram.py        — Telegram I/O, handles text + PDF uploads
        router.py          — message routing
        session.py         — user session management
        billing.py         — token tracking + INR bill
      shared/
        __init__.py
        claude.py          — Claude API client + caching
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
          tool.py          — PDF tool logic (Q&A, summarize)
          helpers.py       — PyMuPDF extraction, page/token warnings
```

---

## Adding a new tool

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

That's it. Session, billing, Telegram, caching — all inherited automatically.

---

## Deployment

Hosted on Render.com free tier. Auto-deploys from GitHub on every `git push`.

UptimeRobot pings `/health` every 5 minutes to prevent Render from sleeping.

To deploy updates:
```bash
git add .
git commit -m "describe your change"
git push
```

Render redeploys automatically in ~60 seconds.
