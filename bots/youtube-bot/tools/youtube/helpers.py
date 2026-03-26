import re
import os

MAX_VIDEO_MINUTES = 120


def extract_video_id(url: str) -> str | None:
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None


def _parse_chapters_from_description(description: str) -> list[dict]:
    """
    Parse chapter timestamps from a YouTube video description.
    Supports formats: 0:00, 00:00, 0:00:00, 00:00:00
    Returns list of {"title", "start_time"} dicts sorted by start_time.
    """
    pattern = re.compile(
        r"(?:^|\n)\s*(?:(\d+):)?(\d{1,2}):(\d{2})\s+(.+)", re.MULTILINE
    )
    chapters = []
    for m in pattern.finditer(description):
        hours   = int(m.group(1)) if m.group(1) else 0
        minutes = int(m.group(2))
        seconds = int(m.group(3))
        title   = m.group(4).strip()
        start   = hours * 3600 + minutes * 60 + seconds
        chapters.append({"title": title, "start_time": start})
    # Must have at least 2 timestamps to be considered real chapters
    return sorted(chapters, key=lambda c: c["start_time"]) if len(chapters) >= 2 else []


def fetch_video_info(video_id: str) -> dict:
    try:
        from supadata import Supadata
        client      = Supadata(api_key=os.environ["SUPADATA_API_KEY"])
        video       = client.metadata(url=f"https://www.youtube.com/watch?v={video_id}")
        description = getattr(video, "description", "") or ""
        # duration lives under video.media for the unified metadata endpoint
        duration = 0
        media = getattr(video, "media", None)
        if media:
            if isinstance(media, dict):
                duration = int(media.get("duration", 0) or 0)
            else:
                duration = int(getattr(media, "duration", 0) or 0)
        chapters = _parse_chapters_from_description(description)
        print(f"fetch_video_info: duration={duration}s, chapters={len(chapters)}")
        return {
            "duration_seconds": duration,
            "title":            getattr(video, "title", None) or "Unknown",
            "chapters":         chapters,
        }
    except Exception as e:
        print("fetch_video_info error:", e)
        return {"duration_seconds": 0, "title": "Unknown", "chapters": []}


def get_transcript(video_id: str) -> list[dict] | None:
    try:
        from supadata import Supadata
        client = Supadata(api_key=os.environ["SUPADATA_API_KEY"])
        result = client.youtube.transcript(video_id=video_id)
        if not result.content:
            print("Supadata returned empty transcript")
            return None
        transcript = [
            {
                "text":     seg.text,
                "start":    seg.offset / 1000.0,
                "duration": seg.duration / 1000.0,
            }
            for seg in result.content
        ]
        print(f"Supadata transcript fetched: {len(transcript)} segments")
        return transcript
    except Exception as e:
        print("Supadata transcript error:", e)
        return None


def segment_transcript(transcript: list[dict], chapters: list[dict]) -> list[dict]:
    if not chapters:
        return []
    result = []
    for i, ch in enumerate(chapters):
        end = chapters[i+1]["start_time"] if i+1 < len(chapters) else float("inf")
        lines = [s["text"] for s in transcript if ch["start_time"] <= s["start"] < end]
        result.append({
            "title":      ch["title"],
            "start_time": ch["start_time"],
            "text":       " ".join(lines).strip()
        })
    return result


def fmt_duration(seconds: int) -> str:
    h, m = divmod(seconds // 60, 60)
    return f"{h}h {m}m" if h else f"{m}m"


def fmt_chapters(chapters: list[dict]) -> str:
    if not chapters:
        return "No chapters in this video."
    lines = ["*Chapters:*"]
    for i, ch in enumerate(chapters, 1):
        m, s = divmod(ch["start_time"], 60)
        lines.append(f"{i}. {ch['title']} ({m}:{s:02d})")
    return "\n".join(lines)


def resolve_chapter(text: str, chapters: list[dict]) -> int | None:
    t = text.lower()
    m = re.search(r"\b(?:chapter|ch\.?)\s*(\d+)\b", t)
    if m:
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(chapters):
            return idx
    words = {
        "one":1,"two":2,"three":3,"four":4,"five":5,
        "six":6,"seven":7,"eight":8,"nine":9,"ten":10
    }
    for w, n in words.items():
        if re.search(rf"\bchapter\s+{w}\b", t):
            idx = n - 1
            if 0 <= idx < len(chapters):
                return idx
    for i, ch in enumerate(chapters):
        if ch["title"].lower() in t:
            return i
    return None


def fmt_question(quiz: dict) -> str:
    q = quiz["questions"][quiz["current_q"]]
    return (
        f"*Question {quiz['current_q']+1}/{len(quiz['questions'])}*\n\n"
        f"{q['question']}\n\n"
        + "\n".join(q["options"])
        + "\n\nReply *answer: A/B/C/D*"
    )


def fmt_quiz_result(quiz: dict) -> str:
    pct   = int(quiz["score"] / len(quiz["questions"]) * 100)
    grade = "Excellent!" if pct >= 80 else "Good effort!" if pct >= 50 else "Keep reviewing!"
    return f"*Quiz done!* {grade} Score: {quiz['score']}/{len(quiz['questions'])} ({pct}%)"