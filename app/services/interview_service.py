from typing import Any, Dict, List

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import InterviewSession
from app.services.interview_repository import InterviewRepository
from app.services.openrouter_service import OpenRouterService
from app.services.stt_service import STTService


class InterviewRuntime:
    def __init__(
        self,
        *,
        websocket: WebSocket,
        db: AsyncSession,
        session: InterviewSession,
        repo: InterviewRepository,
    ) -> None:
        self.ws = websocket
        self.db = db
        self.session = session
        self.repo = repo
        self.ai = OpenRouterService()
        self.stt = STTService()
        self.audio_buffer: bytearray | None = None

    async def send_event(self, type_: str, payload: Dict[str, Any]) -> None:
        await self.ws.send_json({"type": type_, "payload": payload})

    async def start_interview(self) -> None:
        """Send AI intro and first question as separate messages.

        This method is **idempotent** for a given session:
        - If the session already has messages, it will NOT regenerate the
          introduction or first question.
        - On reconnect, it will only re-send the latest question so the
          frontend can resume cleanly without duplicated intro text.
        """
        # If this session already has messages, assume the interview has been
        # started earlier and avoid duplicating intro/question.
        session_with_messages = await self.repo.get_session_with_messages(
            self.db, session_id=int(self.session.id)  # type: ignore[arg-type]
        )

        if session_with_messages and session_with_messages.messages:
            # Find the most recent question to re-send on reconnect
            last_question = None
            for m in reversed(session_with_messages.messages):
                if m.message_type == "question":
                    last_question = m
                    break

            if last_question is not None:
                await self.send_event(
                    "QUESTION",
                    {
                        "message": last_question.content,
                        "questionNumber": session_with_messages.current_question_index,
                    },
                )

            # In either case (whether we found a question or not), do not
            # generate a new intro/question for an already-started session.
            return

        # --- Fresh interview start path (no existing messages) ---

        # First API call: Get introduction only
        intro_prompt = (
            "You are an AI interviewer. Conduct a structured mock interview.\n"
            f"Position: {self.session.position}\n"
            f"Level: {self.session.level}\n"
            f"Total questions: {self.session.total_questions}.\n"
            "Briefly introduce yourself and the interview format. "
            "Do NOT ask any questions yet. Keep it concise and welcoming."
        )

        intro_messages: List[Dict[str, Any]] = [
            {"role": "system", "content": intro_prompt},
        ]

        intro_message = await self.ai.chat(intro_messages)

        # Persist and send introduction
        await self.repo.add_message(
            self.db,
            session=self.session,
            sender="ai",
            role="assistant",
            content=intro_message,
            message_type="intro",
        )

        await self.send_event(
            "INTRO",
            {"message": intro_message},
        )

        # Second API call: Get first question only
        question_prompt = (
            "You are an AI interviewer conducting a mock interview.\n"
            f"Position: {self.session.position}\n"
            f"Level: {self.session.level}\n"
            f"Total questions: {self.session.total_questions}.\n"
            "Now ask the first interview question. "
            "Only ask the question, no introduction or other text. "
            "Keep the question concise and relevant to the position and level."
        )

        question_messages: List[Dict[str, Any]] = [
            {"role": "system", "content": question_prompt},
        ]

        first_question = await self.ai.chat(question_messages)

        # Set question index and persist first question
        self.session.current_question_index = 1
        await self.db.commit()
        await self.db.refresh(self.session)

        await self.repo.add_message(
            self.db,
            session=self.session,
            sender="ai",
            role="assistant",
            content=first_question,
            message_type="question",
        )

        await self.send_event(
            "QUESTION",
            {
                "message": first_question,
                "questionNumber": self.session.current_question_index,
            },
        )

    async def _build_history(self) -> List[Dict[str, Any]]:
        """Build OpenRouter chat history from stored messages."""
        session_id: int = int(self.session.id)  # type: ignore[assignment]
        session_with_messages = await self.repo.get_session_with_messages(
            self.db, session_id=session_id
        )
        history: List[Dict[str, Any]] = []

        if session_with_messages:
            for m in session_with_messages.messages[-10:]:
                # Skip intro/system-style messages so the model doesn't keep
                # echoing the introduction or meta instructions in later turns.
                if getattr(m, "message_type", None) in ("intro", "system"):
                    continue
                history.append({"role": m.role, "content": m.content})

        return history

    def _clean_question_text(self, text: str) -> str:
        """Best-effort extraction of a proper question from model output.

        - Prefer the first line/sentence that ends with '?'
        - Strip out obvious feedback/guide lines (e.g. '**Feedback:**', 'Pause briefly...')
        """
        if not text:
            return ""

        stripped = text.strip()
        if not stripped:
            return ""

        lines = [ln.strip() for ln in stripped.splitlines() if ln.strip()]

        # First, try to find a line that clearly looks like a question
        for ln in lines:
            if "?" in ln:
                idx = ln.rfind("?")
                candidate = ln[: idx + 1].strip()
                if candidate:
                    return candidate

        # Fallback: remove known feedback/meta patterns
        filtered_lines: List[str] = []
        for ln in lines:
            lower = ln.lower()
            if "feedback:" in lower:
                continue
            if "pause briefly" in lower:
                continue
            if "proceed to ask" in lower:
                continue
            if "when you’re ready" in lower or "when you're ready" in lower:
                continue
            filtered_lines.append(ln)

        return "\n".join(filtered_lines).strip()

    async def _build_feedback_prompt(self) -> List[Dict[str, Any]]:
        """Build prompt for getting feedback on user's answer."""
        base_system = {
            "role": "system",
            "content": (
                "You are conducting a mock interview.\n"
                f"Position: {self.session.position}\n"
                f"Level: {self.session.level}\n"
                f"Total questions: {self.session.total_questions}.\n"
                f"Current question number: {self.session.current_question_index}.\n"
                "The candidate has just answered a question. "
                "Provide brief, encouraging feedback on their answer. "
                "Do NOT ask the next question yet. Keep feedback concise and constructive."
            ),
        }

        history = await self._build_history()
        return [base_system] + history

    async def _build_question_prompt(self) -> List[Dict[str, Any]]:
        """Build prompt for getting the next question."""
        base_system = {
            "role": "system",
            "content": (
                "You are conducting a mock interview.\n"
                f"Position: {self.session.position}\n"
                f"Level: {self.session.level}\n"
                f"Total questions: {self.session.total_questions}.\n"
                f"Next question number: {self.session.current_question_index + 1}.\n"
                "Now ask the next interview question. "
                "Only ask the question, no feedback or other text. "
                "Keep the question concise and relevant to the position and level."
            ),
        }

        history = await self._build_history()
        return [base_system] + history

    async def _build_closing_prompt(self) -> List[Dict[str, Any]]:
        """Build prompt for getting closing message when interview is finished."""
        base_system = {
            "role": "system",
            "content": (
                "You are conducting a mock interview.\n"
                f"Position: {self.session.position}\n"
                f"Level: {self.session.level}\n"
                f"Total questions: {self.session.total_questions}.\n"
                "All interview questions have been asked and answered. "
                "Provide a clear, professional closing message thanking the candidate "
                "and indicating that the interview is finished."
            ),
        }

        history = await self._build_history()
        return [base_system] + history

    async def handle_text_answer(self, text: str) -> None:
        if not text:
            return

        # Persist user answer
        await self.repo.add_message(
            self.db,
            session=self.session,
            sender="user",
            role="user",
            content=text,
            message_type="answer",
        )

        current_idx = int(self.session.current_question_index)  # type: ignore[assignment]
        total_q = int(self.session.total_questions)  # type: ignore[assignment]
        is_last = current_idx >= total_q

        if is_last:
            # Final closing - no feedback needed, just closing message
            closing_prompt = await self._build_closing_prompt()
            closing_message = await self.ai.chat(closing_prompt)

            await self.repo.add_message(
                self.db,
                session=self.session,
                sender="ai",
                role="assistant",
                content=closing_message,
                message_type="system",
            )
            await self.send_event(
                "END_INTERVIEW",
                {"message": closing_message, "sessionId": self.session.id},
            )
            from datetime import datetime

            self.session.status = "ended"
            self.session.ended_at = datetime.utcnow()
            self.db.add(self.session)
            await self.db.commit()
        else:
            # First API call: Get feedback on the answer
            feedback_prompt = await self._build_feedback_prompt()
            feedback_message = await self.ai.chat(feedback_prompt)

            # Persist and send feedback
            await self.repo.add_message(
                self.db,
                session=self.session,
                sender="ai",
                role="assistant",
                content=feedback_message,
                message_type="feedback",
            )

            await self.send_event(
                "FEEDBACK",
                {"message": feedback_message},
            )

            # Second API call: Get next question
            self.session.current_question_index += 1
            await self.db.commit()
            await self.db.refresh(self.session)

            question_prompt = await self._build_question_prompt()
            raw_next_question = await self.ai.chat(question_prompt)
            next_question = self._clean_question_text(raw_next_question)

            # If the model still returns something that looks like feedback
            # or we couldn't extract a question, fall back to a stricter prompt.
            if (
                not next_question
                or "feedback:" in next_question.lower()
                or "pause briefly" in next_question.lower()
            ):
                strict_prompt = (
                    "You are an AI interviewer conducting a mock interview.\n"
                    f"Position: {self.session.position}\n"
                    f"Level: {self.session.level}\n"
                    f"Total questions: {self.session.total_questions}.\n"
                    f"Next question number: {self.session.current_question_index}.\n"
                    "Output ONLY the next interview question as a single sentence that ends with '?'. "
                    "Do NOT include feedback, introductions, markdown formatting, quotes, or meta instructions. "
                    "Just the question text itself."
                )
                strict_messages: List[Dict[str, Any]] = [
                    {"role": "system", "content": strict_prompt}
                ]
                strict_raw = await self.ai.chat(strict_messages)
                cleaned_strict = self._clean_question_text(strict_raw)
                next_question = cleaned_strict or strict_raw.strip()

            # Persist and send next question
            await self.repo.add_message(
                self.db,
                session=self.session,
                sender="ai",
                role="assistant",
                content=next_question,
                message_type="question",
            )

            await self.send_event(
                "QUESTION",
                {
                    "message": next_question,
                    "questionNumber": self.session.current_question_index,
                },
            )

    async def handle_audio_chunk(self, chunk: Any, is_first: bool) -> None:
        if chunk is None:
            return
        if is_first or self.audio_buffer is None:
            self.audio_buffer = bytearray()

        # Assuming frontend sends base64 string for simplicity
        if isinstance(chunk, str):
            import base64

            self.audio_buffer.extend(base64.b64decode(chunk))
        elif isinstance(chunk, (bytes, bytearray)):
            self.audio_buffer.extend(chunk)

    async def handle_audio_end(self) -> None:
        if not self.audio_buffer:
            return
        transcript = await self.stt.transcribe(bytes(self.audio_buffer))
        self.audio_buffer = None

        await self.send_event("TRANSCRIPT_FINAL", {"text": transcript})
        await self.handle_text_answer(transcript)

    async def handle_control_update(self, payload: Dict[str, Any]) -> None:
        # For now, controls are not persisted; hook for future analytics/state.
        _ = payload

    async def handle_hangup(self) -> None:
        from datetime import datetime

        session_status = str(self.session.status)  # type: ignore[assignment]
        if session_status != "ended":
            self.session.status = "ended"
            self.session.ended_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(self.session)

        await self.send_event(
            "END_INTERVIEW",
            {"message": "Interview ended by user.", "sessionId": self.session.id},
        )
        await self.ws.close()

    async def handle_disconnect(self) -> None:
        # Optionally track disconnects; keep session open for history.
        return

    async def send_error(self, message: str) -> None:
        try:
            await self.send_event("ERROR", {"message": message})
        except Exception:
            # Best-effort error reporting
            pass


