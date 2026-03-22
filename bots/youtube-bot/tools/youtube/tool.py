import re
import json
from tools.base            import BaseTool
from shared                import claude as ai
from shared.utils          import trim_to_budget
from tools.youtube.helpers import (
    extract_video_id, fetch_video_info, get_transcript,
    segment_transcript, fmt_duration, fmt_chapters,
    resolve_chapter, fmt_question, fmt_quiz_result,
    MAX_VIDEO_MINUTES
)

class YouTubeTool(BaseTool):
    command     = "/youtube"
    name        = "YouTube Assistant"
    description = "Summarize, analyze and quiz yourself on any YouTube video (max 2 hours)"

    async def handle(self, message: str, session: dict) -> str:
        state = self.get_state(session)
        tlow  = message.lower()

        if state.get("quiz"):
            return self._handle_quiz(message, state)

        video_id = extract_video_id(message)
        if video_id:
            return await self._load_video(video_id, state)

        if not state.get("full_text"):
            return "Send me a YouTube link to get started! (max 2 hours)"

        if re.search(r"\b(list|show).*(chapter|section)", tlow):
            return fmt_chapters(state.get("chapters", []))

        if re.search(r"\bquiz\b", tlow):
            return await self._start_quiz(message, state, session)

        ch_idx = resolve_chapter(message, state.get("chapters", []))
        if ch_idx is not None and state.get("segmented"):
            return await self._chapter_question(message, ch_idx, state, session)

        if state.get("active_ch") is not None and state.get("segmented"):
            return await self._chapter_question(
                message, state["active_ch"], state, session)

        answer = ai.ask(
            state["full_text"],
            state.setdefault("history", []),
            message, session,
            context_label=state.get("title", "")
        )
        state["history"] += [
            {"role": "user",      "content": message},
            {"role": "assistant", "content": answer}
        ]
        return answer

    async def _load_video(self, video_id: str, state: dict) -> str:
        info = fetch_video_info(video_id)
        if info["duration_seconds"] > MAX_VIDEO_MINUTES * 60:
            return (
                f"This video is {fmt_duration(info['duration_seconds'])} long. "
                "Max 2 hours."
            )
        raw = get_transcript(video_id)
        if not raw:
            return "Couldn't fetch transcript — the video may not have captions."
        chapters  = info["chapters"]
        full_text = trim_to_budget(" ".join(s["text"] for s in raw))
        state.clear()
        state.update({
            "video_id":  video_id,
            "title":     info["title"],
            "duration":  info["duration_seconds"],
            "chapters":  chapters,
            "segmented": segment_transcript(raw, chapters),
            "full_text": full_text,
            "active_ch": None,
            "history":   [],
            "ch_history":{},
            "quiz":      None,
        })
        ch_note = f"\n\n{fmt_chapters(chapters)}" if chapters else "\nNo chapters detected."
        return (
            f"Got it! *{info['title']}* ({fmt_duration(info['duration_seconds'])})"
            f"{ch_note}\n\nAsk me anything!"
        )

    async def _chapter_question(self, message: str, ch_idx: int,
                                 state: dict, session: dict) -> str:
        ch      = state["segmented"][ch_idx]
        state["active_ch"] = ch_idx
        history = state["ch_history"].setdefault(ch_idx, [])
        label   = f"Chapter {ch_idx+1}: {ch['title']}"
        answer  = ai.ask(ch["text"], history, message, session,
                         context_label=label)
        history += [
            {"role": "user",      "content": message},
            {"role": "assistant", "content": answer}
        ]
        return f"*{label}*\n\n{answer}"

    async def _start_quiz(self, message: str, state: dict,
                           session: dict) -> str:
        ch_idx = resolve_chapter(message, state.get("chapters", []))
        if ch_idx is None:
            ch_idx = state.get("active_ch")
        if ch_idx is not None and state.get("segmented"):
            ch         = state["segmented"][ch_idx]
            content    = ch["text"]
            quiz_label = f"Chapter {ch_idx+1}: {ch['title']}"
        else:
            content    = state["full_text"]
            quiz_label = state.get("title", "the video")
        if not content.strip():
            return "Not enough transcript content to build a quiz."
        prompt = (
            f"Generate 3 multiple-choice questions on '{quiz_label}'.\n"
            "JSON array only:\n"
            '[{"question":"...","options":["A)...","B)...","C)...","D)..."],'
            '"answer":"A","explanation":"..."}]'
        )
        try:
            questions = json.loads(ai.ask_json(content, prompt, session))
        except Exception as e:
            return f"Couldn't generate quiz: {e}"
        state["quiz"] = {"questions": questions, "current_q": 0, "score": 0}
        return f"*Quiz: {quiz_label}*\n\n{fmt_question(state['quiz'])}"

    def _handle_quiz(self, message: str, state: dict) -> str:
        quiz = state["quiz"]
        if re.search(r"\b(quit|stop|cancel)\b", message.lower()):
            state["quiz"] = None
            return "Quiz cancelled. Ask me anything else!"
        m = re.search(r"\banswer[:\s]+([abcd])\b", message.lower())
        if not m:
            return "Reply *answer: A/B/C/D* (or *quit* to cancel)."
        chosen  = m.group(1).upper()
        q       = quiz["questions"][quiz["current_q"]]
        correct = q["answer"].upper()
        quiz["score"] += chosen == correct
        feedback = (
            f"{'Correct!' if chosen == correct else f'Not quite. Answer: *{correct}*'}"
            f"\n\n{q['explanation']}"
        )
        quiz["current_q"] += 1
        if quiz["current_q"] >= len(quiz["questions"]):
            result        = fmt_quiz_result(quiz)
            state["quiz"] = None
            return f"{feedback}\n\n{result}"
        return f"{feedback}\n\n{fmt_question(quiz)}"