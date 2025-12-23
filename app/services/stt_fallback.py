"""Fallback STT service using faster-whisper for offline speech-to-text.

This module provides a free, offline alternative to Deepgram STT using the
faster-whisper library, which runs OpenAI's Whisper model locally with
CTranslate2 optimization for faster inference.
"""

import asyncio
import io
import logging
import os
import subprocess
import tempfile
import wave
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

logger = logging.getLogger(__name__)

# Thread pool for running synchronous whisper in async context
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="stt_fallback")

# Model configuration
# Available models: tiny, base, small, medium, large-v2, large-v3
# Recommended: "base" for good balance of speed/accuracy, "small" for better accuracy
DEFAULT_WHISPER_MODEL = "medium"


def _convert_audio_to_wav(audio_bytes: bytes, mimetype: str) -> str:
    """Convert audio bytes to WAV format using ffmpeg and return temp file path.

    Args:
        audio_bytes: Raw audio data.
        mimetype: Audio MIME type (e.g., 'audio/webm', 'audio/mp3').

    Returns:
        Path to temporary WAV file (16kHz mono).
    """
    # Determine input format from mimetype
    format_map = {
        "audio/webm": "webm",
        "audio/wav": "wav",
        "audio/wave": "wav",
        "audio/mp3": "mp3",
        "audio/mpeg": "mp3",
        "audio/ogg": "ogg",
        "audio/flac": "flac",
        "audio/x-wav": "wav",
    }

    input_format = format_map.get(mimetype, "webm")

    # Create temp file for input
    with tempfile.NamedTemporaryFile(
        suffix=f".{input_format}", delete=False
    ) as input_file:
        input_file.write(audio_bytes)
        input_path = input_file.name

    output_path = input_path.rsplit(".", 1)[0] + "_converted.wav"

    # If already WAV with correct format, check if conversion needed
    if input_format == "wav":
        try:
            with io.BytesIO(audio_bytes) as buf:
                with wave.open(buf, "rb") as wav:
                    if wav.getframerate() == 16000 and wav.getnchannels() == 1:
                        # Already in correct format, return input path
                        return input_path
        except Exception:
            pass

    # Use ffmpeg for conversion to 16kHz mono WAV
    try:
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-i", input_path,
            "-ar", "16000",  # 16kHz sample rate (Whisper expects this)
            "-ac", "1",  # Mono
            "-f", "wav",
            output_path,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=30,
        )

        if result.returncode != 0:
            logger.warning(f"ffmpeg conversion failed: {result.stderr.decode()}")
            # Fall back to input file
            return input_path

        # Clean up input file
        try:
            os.unlink(input_path)
        except OSError:
            pass

        return output_path

    except FileNotFoundError:
        logger.warning("ffmpeg not found, using original audio file")
        return input_path
    except Exception as e:
        logger.warning(f"Audio conversion error: {e}")
        return input_path


class STTFallbackService:
    """Fallback Speech-to-Text service using faster-whisper."""

    def __init__(self, model_size: str = DEFAULT_WHISPER_MODEL) -> None:
        """Initialize the fallback STT service.

        Args:
            model_size: Whisper model size. Options:
                - "tiny": ~75MB, fastest, lower accuracy
                - "base": ~150MB, good balance (recommended)
                - "small": ~500MB, better accuracy
                - "medium": ~1.5GB, high accuracy
                - "large-v2"/"large-v3": ~3GB, best accuracy
        """
        self._model_size = model_size
        self._model = None
        self._initialized = False

    def _ensure_model(self):
        """Ensure the Whisper model is loaded."""
        if self._initialized:
            return

        try:
            from faster_whisper import WhisperModel

            logger.info(f"Loading Whisper model '{self._model_size}'...")

            # Use CPU with int8 quantization for efficiency
            # On systems with CUDA, you can change to device="cuda"
            self._model = WhisperModel(
                self._model_size,
                device="cpu",
                compute_type="int8",
            )

            self._initialized = True
            logger.info(f"Whisper model '{self._model_size}' loaded successfully")

        except ImportError:
            logger.error(
                "faster-whisper library not installed. Run: pip install faster-whisper"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    def _transcribe_sync(self, audio_bytes: bytes, mimetype: str, language: str) -> str:
        """Synchronously transcribe audio bytes to text.

        Args:
            audio_bytes: Raw audio data.
            mimetype: Audio MIME type.
            language: Language code for transcription.

        Returns:
            Transcribed text.
        """
        self._ensure_model()

        audio_path = None
        try:
            # Convert audio to WAV format
            audio_path = _convert_audio_to_wav(audio_bytes, mimetype)

            # Transcribe with Whisper
            segments, info = self._model.transcribe(
                audio_path,
                language=language if language else None,
                beam_size=5,
                vad_filter=True,  # Voice activity detection to filter silence
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                ),
            )

            # Combine all segments into full transcript
            transcript = " ".join(segment.text.strip() for segment in segments)

            logger.debug(
                f"Whisper transcription completed: {transcript[:100]}... "
                f"(detected language: {info.language}, probability: {info.language_probability:.2f})"
            )

            return transcript.strip()

        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return ""

        finally:
            # Clean up temp file
            if audio_path:
                try:
                    os.unlink(audio_path)
                except OSError:
                    pass

    async def transcribe(
        self,
        audio_bytes: bytes,
        mimetype: str = "audio/webm",
        language: str = "en",
    ) -> str:
        """Convert audio bytes to text.

        Args:
            audio_bytes: Raw audio data bytes.
            mimetype: Audio MIME type (e.g., 'audio/webm', 'audio/wav').
            language: Language code for transcription (e.g., 'en', 'es', 'fr').
                     Whisper supports 99+ languages.

        Returns:
            Transcribed text from the audio.
        """
        loop = asyncio.get_event_loop()
        transcript = await loop.run_in_executor(
            _executor, self._transcribe_sync, audio_bytes, mimetype, language
        )
        return transcript


# Singleton instance for reuse
_fallback_service: Optional[STTFallbackService] = None


def get_stt_fallback_service() -> STTFallbackService:
    """Get the singleton fallback STT service instance."""
    global _fallback_service
    if _fallback_service is None:
        _fallback_service = STTFallbackService()
    return _fallback_service
