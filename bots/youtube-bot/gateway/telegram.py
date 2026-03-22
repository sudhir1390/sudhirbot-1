import os
import asyncio
import httpx
from fastapi        import FastAPI, Request
from gateway.router import Router
from gateway        import session as session_store

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_API   = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

class TelegramGateway:
    def __init__(self, router: Router):
        self.router = router
        self.app    = FastAPI()
        self._register_routes()

    def _register_routes(self):
        @self.app.post("/webhook")
        async def webhook(request: Request):
            data = await request.json()
            asyncio.create_task(self._handle(data))
            return {"ok": True}

        @self.app.get("/health")
        async def health():
            return {"status": "ok"}

        @self.app.on_event("startup")
        async def startup():
            asyncio.create_task(self._cleanup_loop())

    async def _handle(self, data: dict):
        msg = data.get("message") or data.get("edited_message")
        if not msg:
            return
        text    = msg.get("text", "").strip()
        user_id = str(msg["from"]["id"])
        if not text:
            return
        reply = await self.router.route(text, user_id)
        await self._send(msg["chat"]["id"], reply)

    async def _send(self, chat_id: int, text: str):
        async with httpx.AsyncClient() as http:
            await http.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id":    chat_id,
                    "text":       text[:4096],
                    "parse_mode": "Markdown",
                }
            )

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(300)
            session_store.cleanup_expired()