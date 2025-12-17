import base64
import logging
from typing import Optional

from deepgram import DeepgramClient, SpeakOptions

from app.core.config import settings

logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-Speech service using Deepgram's Aura API."""

    # Available Aura voices
    VOICES = {
        "asteria": "aura-asteria-en",  # Female, American accent (default)
        "luna": "aura-luna-en",  # Female, American accent
        "stella": "aura-stella-en",  # Female, American accent
        "athena": "aura-athena-en",  # Female, British accent
        "hera": "aura-hera-en",  # Female, American accent
        "orion": "aura-orion-en",  # Male, American accent
        "arcas": "aura-arcas-en",  # Male, American accent
        "perseus": "aura-perseus-en",  # Male, American accent
        "angus": "aura-angus-en",  # Male, Irish accent
        "orpheus": "aura-orpheus-en",  # Male, American accent
        "helios": "aura-helios-en",  # Male, British accent
        "zeus": "aura-zeus-en",  # Male, American accent
    }

    DEFAULT_VOICE = "aura-2-odysseus-en"

    def __init__(
        self,
        api_key: Optional[str] = None,
        voice: Optional[str] = None,
    ) -> None:
        """Initialize the TTS service.

        Args:
            api_key: Deepgram API key. If not provided, uses DEEPGRAM_API_KEY from settings.
            voice: Voice model to use. Defaults to 'aura-asteria-en'.
        """
        self.api_key = api_key or settings.DEEPGRAM_API_KEY
        self.voice = voice or self.DEFAULT_VOICE
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

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        encoding: str = "mp3",
    ) -> bytes:
        """
        Convert text to speech audio bytes using Deepgram's Aura TTS API.

        Args:
            text: Text to convert to speech.
            voice: Voice model to use. If not provided, uses the instance default.
            encoding: Audio encoding format ('mp3', 'wav', 'flac', 'aac').

        Returns:
            Audio data as bytes.

        Raises:
            ValueError: If Deepgram API key is not configured.
            Exception: If synthesis fails.
        """
        if not self.api_key:
            logger.warning("Deepgram API key not configured, cannot synthesize audio")
            raise ValueError("Deepgram API key not configured")

        try:
            # Configure TTS options
            options = SpeakOptions(
                model=voice or self.voice,
                encoding=encoding,
            )

            # Create payload
            payload = {"text": text}

            # Call Deepgram TTS API - use save method to get bytes directly
            response = await self.client.speak.asyncrest.v("1").stream_memory(
                payload, options
            )

            # Get audio bytes from response
            audio_bytes = response.stream_memory.getvalue()

            logger.debug(f"TTS synthesis completed: {len(audio_bytes)} bytes")
            return audio_bytes

        except Exception as e:
            logger.error(f"Deepgram TTS synthesis failed: {e}")
            raise

    async def synthesize_base64(
        self,
        text: str,
        voice: Optional[str] = None,
        encoding: str = "mp3",
    ) -> str:
        """
        Convert text to speech and return as base64-encoded string.

        This is convenient for sending audio over WebSocket/JSON.

        Args:
            text: Text to convert to speech.
            voice: Voice model to use. If not provided, uses the instance default.
            encoding: Audio encoding format ('mp3', 'wav', 'flac', 'aac').

        Returns:
            Base64-encoded audio data string.
        """
        audio_bytes = await self.synthesize(text, voice=voice, encoding=encoding)
        return base64.b64encode(audio_bytes).decode("utf-8")

    def get_audio_mimetype(self, encoding: str = "mp3") -> str:
        """Get the MIME type for the given audio encoding."""
        mimetypes = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "flac": "audio/flac",
            "aac": "audio/aac",
        }
        return mimetypes.get(encoding, "audio/mpeg")

