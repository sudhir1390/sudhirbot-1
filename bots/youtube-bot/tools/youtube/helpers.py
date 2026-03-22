import re
import json
import glob
import os
import subprocess
import tempfile

MAX_VIDEO_MINUTES = 120


def _write_cookies_file() -> str | None:
    """Write cookies from environment variable to a temp file."""
    cookies = os.environ.get("YOUTUBE_COOKIES")
    if not cookies:
        return None
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                      delete=False, encoding="utf-8")
    tmp.write(cookies)
    tmp.close()
    return tmp.name


def extract_video_id(url: str) -> str | None:
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None


def fetch_video_info(video_id: str) -> dict:
    cookies_file = _write_cookies_file()
    try:
        cmd = ["yt-dlp", "--dump-json", "--no-download",
               "--js-runtimes", "node",
               f"https://www.youtube.com/watch?v={video_id}"]
        if cookies_file:
            cmd += ["--cookies", cookies_file]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        info = json.loads(result.stdout)
        return {
            "duration_seconds": int(info.get("duration") or 0),
            "title":            info.get("title", "Unknown"),
            "chapters":         [
                {"title": ch["title"], "start_time": int(ch["start_time"])}
                for ch in (info.get("chapters") or [])
            ]
        }
    except Exception as e:
        print("fetch_video_info error:", e)
        return {"duration_seconds": 0, "title": "Unknown", "chapters": []}
    finally:
        if cookies_file and os.path.exists(cookies_file):
            os.unlink(cookies_file)


def get_transcript(video_id: str) -> list[dict] | None:
    cookies_file = _write_cookies_file()
    try:
        cmd = ["yt-dlp",
               "--write-auto-sub",
               "--write-sub",
               "--sub-lang", "en,hi,en-IN",
               "--skip-download",
               "--sub-format", "json3",
               "--js-runtimes", "node",
               "--remote-components", "ejs:github",
               "-o", f"/tmp/%(id)s.%(ext)s",
               f"https://www.youtube.com/watch?v={video_id}"]
        if cookies_file:
            cmd += ["--cookies", cookies_file]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60
        )
        print("yt-dlp stdout:", result.stdout[:500])
        print("yt-dlp stderr:", result.stderr[:500])

        files = glob.glob(f"/tmp/{video_id}*.json3")
        print("transcript files found:", files)

        if not files:
            return None

        with open(files[0], "r", encoding="utf-8") as f:
            data = json.load(f)

        segments = []
        for event in data.get("events", []):
            if "segs" not in event:
                continue
            text = "".join(s.get("utf8", "") for s in event["segs"]).strip()
            if text:
                segments.append({
                    "text":     text,
                    "start":    event.get("tStartMs", 0) / 1000,
                    "duration": event.get("dDurationMs", 0) / 1000,
                })

        print("segments found:", len(segments))
        return segments if segments else None

    except Exception as e:
        print("transcript error:", e)
        return None
    finally:
        if cookies_file and os.path.exists(cookies_file):
            os.unlink(cookies_file)


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