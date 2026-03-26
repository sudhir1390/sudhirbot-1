import os
import asyncio
import httpx
from fastapi        import FastAPI, Request
from gateway.router import Router
from gateway        import session as session_store

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_API   = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

MAX_PDF_BYTES  = 20 * 1024 * 1024  # 20MB Telegram bot limit

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
        @self.app.head("/health")
        async def health():
            return {"status": "ok"}

        @self.app.on_event("startup")
        async def startup():
            asyncio.create_task(self._cleanup_loop())

    async def _handle(self, data: dict):
        msg = data.get("message") or data.get("edited_message")
        if not msg:
            return

        user_id = str(msg["from"]["id"])
        chat_id = msg["chat"]["id"]

        # ── PDF upload ──────────────────────────────────────────
        doc = msg.get("document")
        if doc and doc.get("mime_type") == "application/pdf":
            await self._handle_pdf(doc, user_id, chat_id)
            return

        # ── Text message ────────────────────────────────────────
        text = msg.get("text", "").strip()
        if not text:
            return

        reply = await self.router.route(text, user_id)

        # ── Route reply type ────────────────────────────────────
        if isinstance(reply, dict) and reply.get("type") == "photo":
            await self._send_photo(
                chat_id,
                reply["image"],
                reply.get("caption", "")
            )
            if reply.get("analysis"):
                await self._send(chat_id, reply["analysis"])
        else:
            await self._send(chat_id, reply)

    async def _handle_pdf(self, doc: dict, user_id: str, chat_id: int):
        if doc.get("file_size", 0) > MAX_PDF_BYTES:
            await self._send(chat_id, "❌ PDF too large. Please send a file under 20MB.")
            return

        session = session_store.get(user_id)
        if not session:
            session = session_store.create(user_id)
        session["active_tool"] = "/pdf"

        await self._send(chat_id, "⏳ Processing your PDF...")

        try:
            file_info = await self._get_file(doc["file_id"])
            pdf_bytes = await self._download_file(file_info["file_path"])

            pdf_tool = self.router._tools.get("/pdf")
            if not pdf_tool:
                await self._send(chat_id, "❌ PDF tool is not enabled.")
                return

            reply = pdf_tool.load_pdf(
                pdf_bytes,
                doc.get("file_name", "document.pdf"),
                session
            )
            await self._send(chat_id, reply)

        except Exception as e:
            print("PDF handling error:", e)
            await self._send(chat_id, "❌ Failed to process PDF. Please try again.")

    async def _get_file(self, file_id: str) -> dict:
        async with httpx.AsyncClient() as http:
            r = await http.get(
                f"{TELEGRAM_API}/getFile",
                params={"file_id": file_id}
            )
            r.raise_for_status()
            return r.json()["result"]

    async def _download_file(self, file_path: str) -> bytes:
        url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
        async with httpx.AsyncClient(timeout=30) as http:
            r = await http.get(url)
            r.raise_for_status()
            return r.content

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

    async def _send_photo(self, chat_id: int, image_bytes: bytes, caption: str = ""):
        async with httpx.AsyncClient(timeout=60) as http:
            await http.post(
                f"{TELEGRAM_API}/sendPhoto",
                data={
                    "chat_id":    chat_id,
                    "caption":    caption[:1024],
                    "parse_mode": "Markdown",
                },
                files={
                    "photo": ("chart.png", image_bytes, "image/png")
                }
            )

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(300)
            session_store.cleanup_expired()