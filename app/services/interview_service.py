import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import InterviewSession
from app.services.interview_repository import InterviewRepository
from app.services.openrouter_service import OpenRouterService
from app.services.stt_service import STTService
from app.services.tts_service import TTSService

logger = logging.getLogger(__name__)


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
        self.tts = TTSService()
        self.audio_buffer: bytearray | None = None
        # TTS is always enabled since we have fallback (pyttsx3)
        self._tts_enabled = True

    async def send_event(self, type_: str, payload: Dict[str, Any]) -> None:
        await self.ws.send_json({"type": type_, "payload": payload})

    async def _stream_audio(self, text: str, message_type: str) -> None:
        """Stream TTS audio chunks to the client.

        Uses Deepgram's WebSocket streaming TTS for faster time-to-first-audio.
        Sends AUDIO_CHUNK events as audio is generated, followed by AUDIO_END.

        Args:
            text: Text to convert to speech.
            message_type: Type of message (intro, question, feedback, end).
        """
        if not self._tts_enabled:
            return

        try:
            async def on_chunk(chunk_base64: str, index: int) -> None:
                await self.send_event(
                    "AUDIO_CHUNK",
                    {
                        "chunk": chunk_base64,
                        "messageType": message_type,
                        "index": index,
                    },
                )

            async def on_complete(total_chunks: int) -> None:
                await self.send_event(
                    "AUDIO_END",
                    {
                        "messageType": message_type,
                        "totalChunks": total_chunks,
                    },
                )

            await self.tts.synthesize_streaming_base64(
                text=text,
                on_audio_chunk=on_chunk,
                on_complete=on_complete,
            )
        except Exception as e:
            logger.warning(f"TTS streaming failed: {e}")

    async def send_event_with_audio(
        self, type_: str, payload: Dict[str, Any], text_for_audio: Optional[str] = None
    ) -> None:
        """Send a WebSocket event, then stream TTS audio if enabled.

        This method sends the text message immediately for fast UI response,
        then streams audio chunks separately for better perceived performance.

        Args:
            type_: Event type (e.g., 'INTRO', 'QUESTION', 'FEEDBACK').
            payload: Event payload dictionary.
            text_for_audio: Text to convert to audio. If None, no audio is streamed.
        """
        # Send text message immediately (no blocking on TTS)
        await self.ws.send_json({"type": type_, "payload": payload})

        # Stream audio chunks after text is sent
        if text_for_audio and self._tts_enabled:
            # Map event type to message type for audio chunks
            message_type_map = {
                "INTRO": "intro",
                "QUESTION": "question",
                "FEEDBACK": "feedback",
                "END_INTERVIEW": "end",
            }
            message_type = message_type_map.get(type_, type_.lower())
            await self._stream_audio(text_for_audio, message_type)

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
                await self.send_event_with_audio(
                    "QUESTION",
                    {
                        "message": last_question.content,
                        "questionNumber": session_with_messages.current_question_index,
                    },
                    text_for_audio=last_question.content,
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

        await self.send_event_with_audio(
            "INTRO",
            {"message": intro_message},
            text_for_audio=intro_message,
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

        first_question_msg = await self.repo.add_message(
            self.db,
            session=self.session,
            sender="ai",
            role="assistant",
            content=first_question,
            message_type="question",
        )

        # Track current question ID explicitly to avoid race conditions
        self.session.current_question_id = first_question_msg.id
        await self.db.commit()
        await self.db.refresh(self.session)

        await self.send_event_with_audio(
            "QUESTION",
            {
                "message": first_question,
                "questionNumber": self.session.current_question_index,
            },
            text_for_audio=first_question,
        )

    async def _build_history(self) -> List[Dict[str, Any]]:
        """Build OpenRouter chat history from stored messages."""
        session_id: int = int(self.session.id)  # type: ignore[assignment]
        session_with_messages = await self.repo.get_session_with_messages(
            self.db, session_id=session_id
        )
        history: List[Dict[str, Any]] = []

        if session_with_messages:
            # Messages are ordered in the repository, but guard just in case
            ordered = sorted(
                session_with_messages.messages,
                key=lambda m: getattr(m, "created_at", None) or 0,
            )
            for m in ordered[-10:]:
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

    def _build_feedback_prompt_direct(
        self, question: str, answer: str
    ) -> List[Dict[str, Any]]:
        """Build prompt for getting feedback on user's answer.
        
        This method takes the question and answer directly to avoid
        any database staleness or race conditions.
        """
        base_system = {
            "role": "system",
            "content": (
                "You are conducting a mock interview.\n"
                f"Position: {self.session.position}\n"
                f"Level: {self.session.level}\n"
                f"Total questions: {self.session.total_questions}.\n"
                f"Current question number: {self.session.current_question_index}.\n"
                "Provide brief, encouraging feedback ONLY on the candidate's answer below. "
                "Be specific to what they said. Do NOT ask the next question. "
                "Keep feedback concise and constructive (2-3 sentences max)."
            ),
        }

        # Provide an explicit, single-turn with the exact Q&A
        explicit_turn = {
            "role": "user",
            "content": (
                f"Interview question: {question}\n\n"
                f"Candidate's answer: {answer}\n\n"
                "Please provide brief feedback on this specific answer."
            ),
        }

        return [base_system, explicit_turn]

    async def _build_question_prompt(self) -> List[Dict[str, Any]]:
        """Build prompt for getting the next question.
        
        Only includes questions and answers in history (no feedback)
        to prevent the model from outputting feedback instead of a question.
        """
        base_system = {
            "role": "system",
            "content": (
                "You are conducting a mock interview.\n"
                f"Position: {self.session.position}\n"
                f"Level: {self.session.level}\n"
                f"Total questions: {self.session.total_questions}.\n"
                f"Next question number: {self.session.current_question_index + 1}.\n"
                "Now ask the next interview question. "
                "Output ONLY the question text ending with '?'. "
                "No feedback, no commentary, no numbering. Just the question."
            ),
        }

        # Build history excluding feedback to prevent model confusion
        session_id: int = int(self.session.id)  # type: ignore[assignment]
        session_with_messages = await self.repo.get_session_with_messages(
            self.db, session_id=session_id
        )
        history: List[Dict[str, Any]] = []

        if session_with_messages:
            ordered = sorted(
                session_with_messages.messages,
                key=lambda m: getattr(m, "created_at", None) or 0,
            )
            for m in ordered[-10:]:
                # Only include questions and answers, skip intro/system/feedback
                msg_type = getattr(m, "message_type", None)
                if msg_type in ("intro", "system", "feedback"):
                    continue
                history.append({"role": m.role, "content": m.content})

        return [base_system] + history

    def _build_closing_prompt(self) -> List[Dict[str, Any]]:
        """Build prompt for getting closing message when interview is finished.
        
        Does NOT include history to prevent the model from outputting
        another question instead of a closing message.
        """
        base_system = {
            "role": "system",
            "content": (
                "You are an AI interview coach wrapping up a mock interview.\n"
                f"Position: {self.session.position}\n"
                f"Level: {self.session.level}\n"
                f"The candidate has completed all {self.session.total_questions} questions.\n"
                "Your task: Write a brief, professional CLOSING message.\n"
                "DO NOT ask any questions. DO NOT provide feedback on answers.\n"
                "Simply thank the candidate, confirm the interview is complete, "
                "and mention their results will be processed soon.\n"
                "Keep it to 2-3 sentences max."
            ),
        }

        user_request = {
            "role": "user",
            "content": (
                "The interview is now complete. Please provide a closing message "
                "thanking me and confirming the session has ended."
            ),
        }

        return [base_system, user_request]

    async def handle_text_answer(self, text: str) -> None:
        if not text:
            return

        # Expire any cached data to ensure fresh reads
        self.db.expire_all()
        await self.db.refresh(self.session)

        # Get current question content using explicit ID tracking (reliable)
        current_question_content = ""
        current_question_id = getattr(self.session, "current_question_id", None)

        if current_question_id:
            # Primary method: fetch by explicit ID (guaranteed correct)
            current_question_msg = await self.repo.get_message(
                self.db, message_id=current_question_id
            )
            if current_question_msg:
                current_question_content = current_question_msg.content

        # Fallback for existing sessions without current_question_id set
        if not current_question_content:
            session_with_messages = await self.repo.get_session_with_messages(
                self.db, session_id=int(self.session.id)  # type: ignore[arg-type]
            )
            if session_with_messages and session_with_messages.messages:
                # Sort by created_at descending to get the most recent question reliably
                sorted_messages = sorted(
                    session_with_messages.messages,
                    key=lambda m: getattr(m, "created_at", None) or 0,
                    reverse=True,
                )
                for m in sorted_messages:
                    if m.message_type == "question":
                        current_question_content = m.content
                        break

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
            closing_prompt = self._build_closing_prompt()
            closing_message = await self.ai.chat(closing_prompt)

            # Validate closing message doesn't look like a question
            def _looks_like_question(text: str) -> bool:
                if not text:
                    return False
                stripped = text.strip()
                # If it ends with '?' and is short, it's likely a question
                if stripped.endswith("?") and len(stripped) < 200:
                    return True
                # Check for question starters
                lower = stripped.lower()
                question_starters = [
                    "can you",
                    "what is",
                    "what are",
                    "how would",
                    "how do",
                    "describe",
                    "explain",
                    "walk me through",
                ]
                return any(lower.startswith(s) for s in question_starters)

            if _looks_like_question(closing_message):
                # Retry with very explicit prompt
                fallback_prompt: List[Dict[str, Any]] = [
                    {
                        "role": "system",
                        "content": (
                            "Output a brief closing message for a completed interview. "
                            "DO NOT ask any questions. Just say thank you and goodbye."
                        ),
                    },
                    {
                        "role": "user",
                        "content": "Please close the interview session.",
                    },
                ]
                closing_message = await self.ai.chat(fallback_prompt)

            await self.repo.add_message(
                self.db,
                session=self.session,
                sender="ai",
                role="assistant",
                content=closing_message,
                message_type="system",
            )
            await self.send_event_with_audio(
                "END_INTERVIEW",
                {"message": closing_message, "sessionId": self.session.id},
                text_for_audio=closing_message,
            )
            from datetime import datetime

            self.session.status = "ended"
            self.session.ended_at = datetime.utcnow()
            self.db.add(self.session)
            await self.db.commit()

            # Trigger AI evaluation in background
            session_id = int(self.session.id)  # type: ignore[arg-type]
            trigger_evaluation_background(session_id)
        else:
            # First API call: Get feedback on the answer
            # Pass question and answer directly to avoid any DB staleness
            feedback_prompt = self._build_feedback_prompt_direct(
                question=current_question_content,
                answer=text,
            )
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

            await self.send_event_with_audio(
                "FEEDBACK",
                {"message": feedback_message},
                text_for_audio=feedback_message,
            )

            # Second API call: Get next question
            self.session.current_question_index += 1
            await self.db.commit()
            await self.db.refresh(self.session)

            question_prompt = await self._build_question_prompt()
            raw_next_question = await self.ai.chat(question_prompt)
            next_question = self._clean_question_text(raw_next_question)

            # Detect if the output looks like feedback instead of a question
            def _looks_like_feedback(text: str) -> bool:
                if not text:
                    return True
                lower = text.lower()
                # Must end with '?' to be a valid question
                if not text.strip().endswith("?"):
                    return True
                # Common feedback patterns
                feedback_patterns = [
                    "your approach",
                    "your response",
                    "your solution",
                    "your answer",
                    "good start",
                    "well done",
                    "nice job",
                    "great job",
                    "that's correct",
                    "that is correct",
                    "feedback:",
                    "pause briefly",
                    "overall",
                    "keep up",
                ]
                return any(p in lower for p in feedback_patterns)

            # If the model still returns something that looks like feedback
            # or we couldn't extract a question, fall back to a stricter prompt.
            if _looks_like_feedback(next_question):
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
            next_question_msg = await self.repo.add_message(
                self.db,
                session=self.session,
                sender="ai",
                role="assistant",
                content=next_question,
                message_type="question",
            )

            # Track current question ID explicitly to avoid race conditions
            self.session.current_question_id = next_question_msg.id
            await self.db.commit()
            await self.db.refresh(self.session)

            await self.send_event_with_audio(
                "QUESTION",
                {
                    "message": next_question,
                    "questionNumber": self.session.current_question_index,
                },
                text_for_audio=next_question,
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
        should_evaluate = session_status != "ended"

        if should_evaluate:
            self.session.status = "ended"
            self.session.ended_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(self.session)

        await self.send_event_with_audio(
            "END_INTERVIEW",
            {"message": "Interview ended by user.", "sessionId": self.session.id},
            text_for_audio="Interview ended by user.",
        )

        # Trigger AI evaluation in background (only if session was actually ended)
        if should_evaluate:
            session_id = int(self.session.id)  # type: ignore[arg-type]
            trigger_evaluation_background(session_id)

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


async def evaluate_interview(
    db: AsyncSession,
    session_id: int,
    repo: Optional[InterviewRepository] = None,
) -> Tuple[Optional[int], Optional[str]]:
    """Evaluate an interview session using AI.

    This function collects all Q&A pairs from the session and sends them
    to OpenRouter for evaluation. Returns score (0-100) and feedback.

    Should be called as a background task after interview ends.
    """
    if repo is None:
        repo = InterviewRepository()

    ai = OpenRouterService()

    try:
        # Mark as processing
        await repo.update_evaluation(
            db, session_id=session_id, evaluation_status="processing"
        )

        # Fetch session with messages
        session = await repo.get_session_with_messages(db, session_id=session_id)
        if not session:
            logger.error(f"Session {session_id} not found for evaluation")
            return None, None

        # Collect Q&A pairs
        qa_pairs: List[Dict[str, str]] = []
        ordered_messages = sorted(
            session.messages,
            key=lambda m: getattr(m, "created_at", None) or 0,
        )

        current_question: Optional[str] = None
        for msg in ordered_messages:
            if msg.message_type == "question":
                current_question = msg.content
            elif msg.message_type == "answer" and current_question:
                qa_pairs.append({
                    "question": current_question,
                    "answer": msg.content,
                })
                current_question = None

        if not qa_pairs:
            logger.warning(f"No Q&A pairs found for session {session_id}")
            await repo.update_evaluation(
                db,
                session_id=session_id,
                ai_score=0,
                ai_feedback="No questions and answers were recorded in this interview.",
                evaluation_status="completed",
            )
            return 0, "No questions and answers were recorded in this interview."

        # Build evaluation prompt
        qa_text = "\n\n".join(
            f"Question {i + 1}: {qa['question']}\nAnswer: {qa['answer']}"
            for i, qa in enumerate(qa_pairs)
        )

        evaluation_prompt: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "You are an expert interview evaluator. Analyze the candidate's "
                    "interview performance and provide an objective assessment.\n\n"
                    f"Interview Details:\n"
                    f"- Position: {session.position}\n"
                    f"- Level: {session.level}\n"
                    f"- Interview Type: {session.interview_type}\n\n"
                    "Your response MUST be a valid JSON object with exactly these fields:\n"
                    '- "score": an integer from 0 to 100 (0=poor, 100=excellent)\n'
                    '- "feedback": a comprehensive evaluation (2-4 paragraphs) covering:\n'
                    "  * Overall performance assessment\n"
                    "  * Key strengths demonstrated\n"
                    "  * Areas for improvement\n"
                    "  * Specific recommendations\n\n"
                    "Be constructive and specific. Reference actual answers when possible."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Please evaluate this interview:\n\n{qa_text}\n\n"
                    "Respond with a JSON object containing 'score' and 'feedback'."
                ),
            },
        ]

        # Call AI with longer timeout for evaluation
        response = await ai.chat(
            evaluation_prompt,
            response_format={"type": "json_object"},
            timeout=60,
        )

        # Parse response
        score, feedback = _parse_evaluation_response(response)

        # Store results
        await repo.update_evaluation(
            db,
            session_id=session_id,
            ai_score=score,
            ai_feedback=feedback,
            evaluation_status="completed",
        )

        logger.info(f"Evaluation completed for session {session_id}: score={score}")
        return score, feedback

    except Exception as e:
        logger.error(f"Evaluation failed for session {session_id}: {e}")
        await repo.update_evaluation(
            db,
            session_id=session_id,
            ai_feedback=f"Evaluation failed: {str(e)}",
            evaluation_status="failed",
        )
        return None, None


def _parse_evaluation_response(response: str) -> Tuple[int, str]:
    """Parse AI evaluation response and extract score and feedback."""
    try:
        # Try direct JSON parse
        data = json.loads(response)
        score = int(data.get("score", 0))
        feedback = str(data.get("feedback", ""))
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
            score = int(data.get("score", 0))
            feedback = str(data.get("feedback", ""))
        else:
            # Fallback: try to extract score and feedback manually
            score_match = re.search(r'"score"\s*:\s*(\d+)', response)
            score = int(score_match.group(1)) if score_match else 50

            feedback_match = re.search(
                r'"feedback"\s*:\s*"(.*?)"(?:,|\})', response, re.DOTALL
            )
            feedback = feedback_match.group(1) if feedback_match else response

    # Clamp score to valid range
    score = max(0, min(100, score))

    return score, feedback


async def _run_evaluation_with_new_session(session_id: int) -> None:
    """Run evaluation with its own database session.

    This is needed because the WebSocket's db session may close
    before the evaluation completes.
    """
    from app.db.session import SessionLocal

    async with SessionLocal() as db:
        try:
            await evaluate_interview(db, session_id)
        except Exception as e:
            logger.error(f"Background evaluation error for session {session_id}: {e}")


def trigger_evaluation_background(session_id: int) -> None:
    """Trigger interview evaluation as a background task.

    This creates a fire-and-forget task that won't block the main flow.
    Creates its own database session to avoid session lifecycle issues.
    """
    asyncio.create_task(
        _run_evaluation_with_new_session(session_id),
        name=f"evaluate_interview_{session_id}",
    )


