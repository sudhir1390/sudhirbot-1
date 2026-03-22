\# My AI Bots



Personal collection of Sudhir Telegram AI bots 



\# My AI Bots



Personal collection of Telegram AI bots powered by Claude AI.



\## Bots



| Bot | What it does | Status |

|-----|-------------|--------|

| youtube-bot | Summarize and quiz YouTube videos | Live |



\## YouTube Bot



A Telegram bot that lets you send any YouTube link and ask questions about it — summarize chapters, get key takeaways, quiz yourself, and see exactly how much each session cost in INR.



\### Features

\- YouTube Q\&A — send any link, ask anything

\- Chapter support — ask about specific chapters

\- Per-chapter quiz — 3-question MCQ quiz on any chapter

\- Multi-turn memory — follow-up questions stay in context

\- Prompt caching — transcript cached for 10 min, follow-ups cost 90% less

\- INR billing — /bye ends session and shows exact cost in rupees

\- 2-hour limit — videos over 120 min are rejected upfront

\- Scalable tools — add /pdf, /news or any tool with one file + two lines



\### Tech Stack



| Component | Tool | Cost |

|-----------|------|------|

| Messaging | Telegram Bot API | Free |

| Hosting | Render.com free tier | Free |

| AI | Claude Haiku (Anthropic) | \~₹10-20/month |

| Transcripts | yt-dlp + YouTubeTranscriptApi | Free |

| Keep-alive | UptimeRobot | Free |

| Code | GitHub (private repo) | Free |



\### Architecture

```

You + friends (Telegram)

&#x20;       ↕

Telegram Bot API (free)

&#x20;       ↕

Render.com free tier — hosts everything

&#x20; ├── gateway/

&#x20; │   ├── telegram.py     — receives all messages, sends replies

&#x20; │   ├── router.py       — reads message, picks the right tool

&#x20; │   ├── session.py      — one session per user, per-tool pockets

&#x20; │   └── billing.py      — tracks tokens, formats INR bill on /bye

&#x20; ├── shared/

&#x20; │   ├── claude.py       — single Claude client, caching + usage tracking

&#x20; │   └── utils.py        — trim\_to\_budget, estimate\_tokens

&#x20; └── tools/

&#x20;     ├── base.py         — BaseTool class, every tool inherits this

&#x20;     └── youtube/

&#x20;         ├── tool.py     — YouTube logic, clean handle() method

&#x20;         └── helpers.py  — yt-dlp, transcript, chapters, quiz formatting

&#x20;       ↕

Claude API (paid \~₹10-20/mo)

YouTube (yt-dlp + transcript, free)

GitHub (auto-deploy on git push, free)

```



\### How it works — Message Flow

```

1\. User sends message on Telegram

2\. Telegram forwards it to Render server via webhook POST

3\. Gateway extracts user\_id and message text

4\. Router checks — is it a command (/youtube, /help, /bye)?

&#x20;  - /youtube  → switches active tool to YouTube

&#x20;  - /bye      → calculates bill, clears session, sends INR summary

&#x20;  - /help     → lists all available tools

&#x20;  - message   → sends to whichever tool is currently active

5\. YouTube tool handles the message:

&#x20;  - YouTube link  → fetches transcript + chapters via yt-dlp

&#x20;  - Question      → sends transcript (cached) + question to Claude

&#x20;  - quiz me       → generates 3 MCQ questions via Claude

&#x20;  - answer: B     → checks answer, shows next question or final score

6\. Reply sent back to user via Telegram

7\. Token usage tracked silently for billing

```



\### Session lifecycle

```

User messages bot for first time

&#x20;       ↓

Bot greets with welcome + /help menu

&#x20;       ↓

User picks /youtube → sends a link

&#x20;       ↓

Bot loads transcript, shows chapters

&#x20;       ↓

User asks questions / takes quiz

&#x20;       ↓

User says /bye

&#x20;       ↓

Bot shows bill in INR → session cleared

&#x20;       ↓

Session also auto-clears at midnight (IST)

```



\### Cost breakdown



| Item | Monthly cost |

|------|-------------|

| Render hosting | ₹0 |

| Telegram Bot API | ₹0 |

| UptimeRobot | ₹0 |

| GitHub | ₹0 |

| Claude API (10 users, daily use) | \~₹10–20 |

| \*\*Total\*\* | \*\*\~₹10–20/month\*\* |



\### Adding a new tool

```python

\# 1. Create tools/pdf/tool.py

class PDFTool(BaseTool):

&#x20;   command     = "/pdf"

&#x20;   name        = "PDF Assistant"

&#x20;   description = "Ask questions about any PDF"



&#x20;   async def handle(self, message, session):

&#x20;       state = self.get\_state(session)

&#x20;       # your logic here



\# 2. Add two lines in main.py

from tools.pdf.tool import PDFTool

router.register(PDFTool())

```



That's it. Session, billing, Telegram, caching — all inherited automatically.



\## Project Structure

```

my-ai-bots/

&#x20; .gitignore

&#x20; README.md

&#x20; bots/

&#x20;   youtube-bot/

&#x20;     main.py              — entry point, registers tools

&#x20;     requirements.txt     — Python dependencies

&#x20;     render.yaml          — Render deployment config

&#x20;     gateway/

&#x20;       \_\_init\_\_.py

&#x20;       telegram.py        — Telegram I/O

&#x20;       router.py          — message routing

&#x20;       session.py         — user session management

&#x20;       billing.py         — token tracking + INR bill

&#x20;     shared/

&#x20;       \_\_init\_\_.py

&#x20;       claude.py          — Claude API client + caching

&#x20;       utils.py           — token utilities

&#x20;     tools/

&#x20;       \_\_init\_\_.py

&#x20;       base.py            — BaseTool base class

&#x20;       youtube/

&#x20;         \_\_init\_\_.py

&#x20;         tool.py          — YouTube tool logic

&#x20;         helpers.py       — YouTube helpers

```



\## Deployment



Hosted on Render.com free tier. Auto-deploys from GitHub on every `git push`.

UptimeRobot pings `/health` every 5 minutes to prevent Render from sleeping.



To deploy updates:

```bash

git add .

git commit -m "describe your change"

git push

```

Render redeploys automatically in \~60 seconds.

\## Bots



| Bot | What it does | Status |

|-----|-------------|--------|

| youtube-bot | Summarize and quiz YouTube videos | Live |



\## YouTube Bot



A Telegram bot that lets you send any YouTube link and ask questions about it — summarize chapters, get key takeaways, quiz yourself, and see exactly how much each session cost in INR.



\### Features

\- YouTube Q\&A — send any link, ask anything

\- Chapter support — ask about specific chapters

\- Per-chapter quiz — 3-question MCQ quiz on any chapter

\- Multi-turn memory — follow-up questions stay in context

\- Prompt caching — transcript cached for 10 min, follow-ups cost 90% less

\- INR billing — /bye ends session and shows exact cost in rupees

\- 2-hour limit — videos over 120 min are rejected upfront

\- Scalable tools — add /pdf, /news or any tool with one file + two lines



\### Tech Stack



| Component | Tool | Cost |

|-----------|------|------|

| Messaging | Telegram Bot API | Free |

| Hosting | Render.com free tier | Free |

| AI | Claude Haiku (Anthropic) | \~₹10-20/month |

| Transcripts | yt-dlp + YouTubeTranscriptApi | Free |

| Keep-alive | UptimeRobot | Free |

| Code | GitHub (private repo) | Free |



\### Architecture

```

You + friends (Telegram)

&#x20;       ↕

Telegram Bot API (free)

&#x20;       ↕

Render.com free tier — hosts everything

&#x20; ├── gateway/

&#x20; │   ├── telegram.py     — receives all messages, sends replies

&#x20; │   ├── router.py       — reads message, picks the right tool

&#x20; │   ├── session.py      — one session per user, per-tool pockets

&#x20; │   └── billing.py      — tracks tokens, formats INR bill on /bye

&#x20; ├── shared/

&#x20; │   ├── claude.py       — single Claude client, caching + usage tracking

&#x20; │   └── utils.py        — trim\_to\_budget, estimate\_tokens

&#x20; └── tools/

&#x20;     ├── base.py         — BaseTool class, every tool inherits this

&#x20;     └── youtube/

&#x20;         ├── tool.py     — YouTube logic, clean handle() method

&#x20;         └── helpers.py  — yt-dlp, transcript, chapters, quiz formatting

&#x20;       ↕

Claude API (paid \~₹10-20/mo)

YouTube (yt-dlp + transcript, free)

GitHub (auto-deploy on git push, free)

```



\### How it works — Message Flow

```

1\. User sends message on Telegram

2\. Telegram forwards it to Render server via webhook POST

3\. Gateway extracts user\_id and message text

4\. Router checks — is it a command (/youtube, /help, /bye)?

&#x20;  - /youtube  → switches active tool to YouTube

&#x20;  - /bye      → calculates bill, clears session, sends INR summary

&#x20;  - /help     → lists all available tools

&#x20;  - message   → sends to whichever tool is currently active

5\. YouTube tool handles the message:

&#x20;  - YouTube link  → fetches transcript + chapters via yt-dlp

&#x20;  - Question      → sends transcript (cached) + question to Claude

&#x20;  - quiz me       → generates 3 MCQ questions via Claude

&#x20;  - answer: B     → checks answer, shows next question or final score

6\. Reply sent back to user via Telegram

7\. Token usage tracked silently for billing

```



\### Session lifecycle

```

User messages bot for first time

&#x20;       ↓

Bot greets with welcome + /help menu

&#x20;       ↓

User picks /youtube → sends a link

&#x20;       ↓

Bot loads transcript, shows chapters

&#x20;       ↓

User asks questions / takes quiz

&#x20;       ↓

User says /bye

&#x20;       ↓

Bot shows bill in INR → session cleared

&#x20;       ↓

Session also auto-clears at midnight (IST)

```



\### Cost breakdown



| Item | Monthly cost |

|------|-------------|

| Render hosting | ₹0 |

| Telegram Bot API | ₹0 |

| UptimeRobot | ₹0 |

| GitHub | ₹0 |

| Claude API (10 users, daily use) | \~₹10–20 |

| \*\*Total\*\* | \*\*\~₹10–20/month\*\* |



\### Adding a new tool

```python

\# 1. Create tools/pdf/tool.py

class PDFTool(BaseTool):

&#x20;   command     = "/pdf"

&#x20;   name        = "PDF Assistant"

&#x20;   description = "Ask questions about any PDF"



&#x20;   async def handle(self, message, session):

&#x20;       state = self.get\_state(session)

&#x20;       # your logic here



\# 2. Add two lines in main.py

from tools.pdf.tool import PDFTool

router.register(PDFTool())

```



That's it. Session, billing, Telegram, caching — all inherited automatically.



\## Project Structure

```

my-ai-bots/

&#x20; .gitignore

&#x20; README.md

&#x20; bots/

&#x20;   youtube-bot/

&#x20;     main.py              — entry point, registers tools

&#x20;     requirements.txt     — Python dependencies

&#x20;     render.yaml          — Render deployment config

&#x20;     gateway/

&#x20;       \_\_init\_\_.py

&#x20;       telegram.py        — Telegram I/O

&#x20;       router.py          — message routing

&#x20;       session.py         — user session management

&#x20;       billing.py         — token tracking + INR bill

&#x20;     shared/

&#x20;       \_\_init\_\_.py

&#x20;       claude.py          — Claude API client + caching

&#x20;       utils.py           — token utilities

&#x20;     tools/

&#x20;       \_\_init\_\_.py

&#x20;       base.py            — BaseTool base class

&#x20;       youtube/

&#x20;         \_\_init\_\_.py

&#x20;         tool.py          — YouTube tool logic

&#x20;         helpers.py       — YouTube helpers

```



\## Deployment



Hosted on Render.com free tier. Auto-deploys from GitHub on every `git push`.

UptimeRobot pings `/health` every 5 minutes to prevent Render from sleeping.



To deploy updates:

```bash

git add .

git commit -m "describe your change"

git push

```

Render redeploys automatically in \~60 seconds.

