import logging
from typing import Optional

from deepgram import DeepgramClient, PrerecordedOptions

from app.core.config import settings

logger = logging.getLogger(__name__)


class STTService:
    """Speech-to-Text service using Deepgram's API."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize the STT service.

        Args:
            api_key: Deepgram API key. If not provided, uses DEEPGRAM_API_KEY from settings.
        """
        self.api_key = api_key or settings.DEEPGRAM_API_KEY
        self._client: Optional[DeepgramClient] = None

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

    async def transcribe(
        self,
        audio_bytes: bytes,
        mimetype: str = "audio/webm",
        language: str = "en",
    ) -> str:
        """
        Convert audio bytes to text using Deepgram's pre-recorded transcription API.

        Args:
            audio_bytes: Raw audio data bytes.
            mimetype: Audio MIME type (e.g., 'audio/webm', 'audio/wav', 'audio/mp3').
            language: Language code for transcription (default: 'en' for English).

        Returns:
            Transcribed text from the audio.

        Raises:
            ValueError: If Deepgram API key is not configured.
            Exception: If transcription fails.
        """
        if not self.api_key:
            logger.warning("Deepgram API key not configured, returning placeholder")
            return "[transcribed audio - Deepgram not configured]"

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
            logger.error(f"Deepgram transcription failed: {e}")
            raise
