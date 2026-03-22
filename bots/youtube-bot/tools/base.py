from gateway import session as session_store

class BaseTool:
    command:     str = ""
    name:        str = ""
    description: str = ""

    async def handle(self, message: str, session: dict) -> str:
        raise NotImplementedError

    def get_state(self, session: dict) -> dict:
        return session_store.tool_state(session, self.command)