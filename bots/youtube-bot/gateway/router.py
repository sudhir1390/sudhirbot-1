from tools.base  import BaseTool
from gateway     import billing, session as session_store

class Router:
    def __init__(self):
        self._tools = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.command] = tool

    async def route(self, message: str, user_id: str) -> str:
        text = message.strip()
        cmd  = text.split()[0].lower() if text.startswith("/") else None
        session = session_store.get(user_id)

        if not session:
            session = session_store.create(user_id)
            return (
                "👋 Hello! I'm your personal AI assistant.\n\n"
                + self._help_text()
                + "\n\nPick a tool above to get started!"
            )

        if cmd in ("/bye", "/end"):
            bill = billing.format_bill(session)
            session_store.delete(user_id)
            return (
                "Session ended!\n\n"
                + bill
                + "\n\nSee you next time — type anything to start fresh."
            )

        if cmd == "/help":
            active = session.get("active_tool")
            active_note = f"\n\nCurrently active: {active}" if active else ""
            return self._help_text() + active_note

        if cmd and cmd in self._tools:
            tool = self._tools[cmd]
            session["active_tool"] = cmd
            state = self._tools[cmd].get_state(session)
            if state:
                return f"Switched to *{tool.name}*. Welcome back — your previous session is restored."
            return f"Switched to *{tool.name}*.\n\n{tool.description}"

        if cmd and cmd not in self._tools:
            return f"Unknown command `{cmd}`.\n\n" + self._help_text()

        active = session.get("active_tool")
        if not active:
            return "Pick a tool first:\n\n" + self._help_text()

        return await self._tools[active].handle(text, session)

    def _help_text(self) -> str:
        lines = ["*Available tools:*"]
        for cmd, tool in self._tools.items():
            lines.append(f"{cmd} — {tool.description}")
        lines.append("\n/help — show this menu")
        lines.append("/bye  — end session and see your bill")
        return "\n".join(lines)