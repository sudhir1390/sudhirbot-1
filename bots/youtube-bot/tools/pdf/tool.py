from tools.base            import BaseTool
from shared                import claude as ai
from tools.pdf.helpers     import extract_text, fmt_load_message


class PDFTool(BaseTool):
    command     = "/pdf"
    name        = "PDF Assistant"
    description = "Summarize, analyze and ask questions about any PDF (max 200 pages)"

    async def handle(self, message: str, session: dict) -> str:
        state = self.get_state(session)

        if not state.get("full_text"):
            return "Send me a PDF file to get started!"

        if message.lower().strip() in ("summarize", "summary", "/summarize"):
            return await self._summarize(state, session)

        return await self._qa(message, state, session)

    async def _summarize(self, state: dict, session: dict) -> str:
        answer = ai.ask(
            state["full_text"],
            [],                         # fresh history — summary is always full-doc
            "Give a concise summary of this document: key topics, main points, and conclusions.",
            session,
            context_label=state.get("filename", "PDF")
        )
        return answer

    async def _qa(self, message: str, state: dict, session: dict) -> str:
        answer = ai.ask(
            state["full_text"],
            state.setdefault("history", []),
            message,
            session,
            context_label=state.get("filename", "PDF")
        )
        state["history"] += [
            {"role": "user",      "content": message},
            {"role": "assistant", "content": answer},
        ]
        return answer

    def load_pdf(self, pdf_bytes: bytes, filename: str, session: dict) -> str:
        """
        Called by TelegramGateway when a PDF document is received.
        Extracts text, stores state, returns confirmation message with warnings.
        """
        text, total_pages, extracted, page_warning, token_warning = extract_text(pdf_bytes)

        if not text.strip():
            return (
                "❌ Couldn't extract any text from this PDF. "
                "It may be a scanned image — only text-based PDFs are supported."
            )

        state = self.get_state(session)
        state.clear()
        state.update({
            "filename":  filename,
            "full_text": text,
            "pages":     total_pages,
            "history":   [],
        })

        return fmt_load_message(filename, total_pages, extracted, page_warning, token_warning)
