import logging
from typing import Optional

from deepgram import DeepgramClient, PrerecordedOptions

from app.core.config import settings
from app.services.stt_fallback import get_stt_fallback_service

logger = logging.getLogger(__name__)


class STTService:
    """Speech-to-Text service using Deepgram's API with Vosk fallback."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize the STT service.

        Args:
            api_key: Deepgram API key. If not provided, uses DEEPGRAM_API_KEY from settings.
        """
        self.api_key = api_key or settings.DEEPGRAM_API_KEY
        self._client: Optional[DeepgramClient] = None
        self._fallback = get_stt_fallback_service()
        self._use_fallback = not self.api_key

    @property
    def client(self) -> DeepgramClient:
        """Lazy initialization of Deepgram client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "Deepgram API key not configured. "
                    "Set DEEPGRAM_API_KEY environment variable."
                )
            self._client = DeepgramClient(self.api_key)
        return self._client

    def _is_credit_error(self, error: Exception) -> bool:
        """Check if the error is related to insufficient credits."""
        error_str = str(error).lower()
        credit_indicators = [
            "insufficient",
            "credit",
            "balance",
            "quota",
            "limit exceeded",
            "payment required",
            "402",
        ]
        return any(indicator in error_str for indicator in credit_indicators)

    async def transcribe(
        self,
        audio_bytes: bytes,
        mimetype: str = "audio/webm",
        language: str = "en",
    ) -> str:
        """
        Convert audio bytes to text using Deepgram's pre-recorded transcription API.
        Falls back to Vosk if Deepgram is unavailable or fails.

        Args:
            audio_bytes: Raw audio data bytes.
            mimetype: Audio MIME type (e.g., 'audio/webm', 'audio/wav', 'audio/mp3').
            language: Language code for transcription (default: 'en' for English).

        Returns:
            Transcribed text from the audio.
        """
        # Use fallback if no API key configured
        if self._use_fallback:
            logger.info("Using fallback STT (Vosk) - Deepgram not configured")
            return await self._fallback.transcribe(
                audio_bytes, mimetype=mimetype, language=language
            )

        try:
            # Configure transcription options
            options = PrerecordedOptions(
                model="nova-2",  # Latest and most accurate model
                language=language,
                smart_format=True,  # Apply punctuation and formatting
                punctuate=True,
                diarize=False,  # Single speaker for interview
            )

            # Create payload with audio bytes
            payload = {"buffer": audio_bytes, "mimetype": mimetype}

            # Call Deepgram API
            response = await self.client.listen.asyncrest.v("1").transcribe_file(
                payload, options
            )

            # Extract transcript from response
            transcript = ""
            if (
                response.results
                and response.results.channels
                and len(response.results.channels) > 0
            ):
                channel = response.results.channels[0]
                if channel.alternatives and len(channel.alternatives) > 0:
                    transcript = channel.alternatives[0].transcript or ""

            logger.debug(f"Transcription completed: {transcript[:100]}...")
            return transcript

        except Exception as e:
            logger.warning(f"Deepgram transcription failed: {e}")

            # Check if this is a credit/billing error
            if self._is_credit_error(e):
                logger.warning("Deepgram credit error detected, switching to fallback")
                self._use_fallback = True

            # Fall back to Vosk
            logger.info("Using fallback STT (Vosk)")
            return await self._fallback.transcribe(
                audio_bytes, mimetype=mimetype, language=language
            )
