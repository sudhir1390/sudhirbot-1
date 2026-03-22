import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TZ = "Asia/Kolkata"
_store: dict[str, dict] = {}

def get(user_id: str) -> dict | None:
    s = _store.get(user_id)
    if s and _is_expired(s):
        delete(user_id)
        return None
    return s

def create(user_id: str) -> dict:
    tz = DEFAULT_TZ
    s = {
        "user_id":          user_id,
        "active_tool":      None,
        "started_at":       time.time(),
        "cache_written_at": 0,
        "expires_at":       _midnight(tz),
        "timezone":         tz,
        "usage":            _empty_usage(),
        "tools":            {},
    }
    _store[user_id] = s
    return s

def delete(user_id: str) -> None:
    _store.pop(user_id, None)

def tool_state(session: dict, command: str) -> dict:
    return session["tools"].setdefault(command, {})

def cleanup_expired() -> None:
    expired = [uid for uid, s in list(_store.items()) if _is_expired(s)]
    for uid in expired:
        del _store[uid]

def _is_expired(session: dict) -> bool:
    return time.time() >= session.get("expires_at", float("inf"))

def _midnight(tz_name: str) -> float:
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo(DEFAULT_TZ)
    now      = datetime.now(tz)
    midnight = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0)
    return midnight.timestamp()

def _empty_usage() -> dict:
    return {
        "input_tokens": 0, "output_tokens": 0,
        "cache_write_tokens": 0, "cache_read_tokens": 0,
        "api_calls": 0
    }