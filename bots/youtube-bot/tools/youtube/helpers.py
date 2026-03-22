import re
import json
import os
import subprocess

MAX_VIDEO_MINUTES = 120


def extract_video_id(url: str) -> str | None:
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None


def fetch_video_info(video_id: str) -> dict:
    try:
        cmd = ["yt-dlp", "--dump-json", "--no-download",
               "--js-runtimes", "node",
               f"https://www.youtube.com/watch?v={video_id}"]
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


def get_transcript(video_id: str) -> list[dict] | None:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        username = os.environ.get("WEBSHARE_USERNAME")
        password = os.environ.get("WEBSHARE_PASSWORD")

        if username and password:
            proxy_url = f"http://{username}:{password}@p.webshare.io:80"
            proxies   = {"http": proxy_url, "https": proxy_url}
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=["en", "hi", "en-IN"],
                proxies=proxies
            )
        else:
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=["en", "hi", "en-IN"]
            )

        print(f"transcript fetched: {len(transcript)} segments")
        return transcript

    except Exception as e:
        print("transcript error:", e)
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