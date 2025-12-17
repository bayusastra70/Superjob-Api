import asyncio
import base64
import json
import logging
from typing import Awaitable, Callable, Optional

import websockets

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

    async def synthesize_streaming(
        self,
        text: str,
        on_audio_chunk: Callable[[bytes, int], Awaitable[None]],
        on_complete: Optional[Callable[[int], Awaitable[None]]] = None,
        voice: Optional[str] = None,
        encoding: str = "linear16",
    ) -> int:
        """
        Stream TTS audio chunks via callback as they're generated.

        Uses Deepgram's WebSocket TTS endpoint for real-time streaming,
        providing faster time-to-first-audio compared to batch synthesis.

        Args:
            text: Text to convert to speech.
            on_audio_chunk: Async callback called for each audio chunk.
                           Receives (audio_bytes, chunk_index).
            on_complete: Optional async callback called when streaming ends.
                        Receives total chunk count.
            voice: Voice model to use. If not provided, uses instance default.
            encoding: Audio encoding ('linear16' recommended for streaming).

        Returns:
            Total number of audio chunks sent.

        Raises:
            ValueError: If Deepgram API key is not configured.
            Exception: If streaming fails.
        """
        if not self.api_key:
            logger.warning("Deepgram API key not configured, cannot stream audio")
            raise ValueError("Deepgram API key not configured")

        model = voice or self.voice
        ws_url = f"wss://api.deepgram.com/v1/speak?model={model}&encoding={encoding}"

        chunk_index = 0

        try:
            async with websockets.connect(
                ws_url,
                extra_headers={"Authorization": f"Token {self.api_key}"},
            ) as ws:
                # Send text to synthesize
                await ws.send(json.dumps({"type": "Speak", "text": text}))

                # Signal end of input
                await ws.send(json.dumps({"type": "Flush"}))

                # Receive audio chunks
                async for message in ws:
                    if isinstance(message, bytes):
                        # Audio data chunk
                        await on_audio_chunk(message, chunk_index)
                        chunk_index += 1
                    elif isinstance(message, str):
                        # Control message (JSON)
                        data = json.loads(message)
                        msg_type = data.get("type", "")

                        if msg_type == "Flushed":
                            # All audio for current text has been sent
                            logger.debug(f"TTS streaming flushed after {chunk_index} chunks")
                            # Call completion callback NOW, before connection closes
                            if on_complete:
                                await on_complete(chunk_index)
                            break  # Exit the loop after flush
                        elif msg_type == "Warning":
                            logger.warning(f"Deepgram TTS warning: {data}")
                        elif msg_type == "Error":
                            logger.error(f"Deepgram TTS error: {data}")
                            break

                # Send close signal
                await ws.send(json.dumps({"type": "Close"}))

        except websockets.exceptions.ConnectionClosed as e:
            logger.debug(f"TTS WebSocket closed: {e}")
            # If we haven't called on_complete yet (unexpected close), call it now
            if on_complete and chunk_index > 0:
                try:
                    await on_complete(chunk_index)
                except Exception:
                    pass  # Best effort
        except Exception as e:
            logger.error(f"Deepgram TTS streaming failed: {e}")
            raise

        logger.debug(f"TTS streaming completed: {chunk_index} chunks")
        return chunk_index

    async def synthesize_streaming_base64(
        self,
        text: str,
        on_audio_chunk: Callable[[str, int], Awaitable[None]],
        on_complete: Optional[Callable[[int], Awaitable[None]]] = None,
        voice: Optional[str] = None,
        encoding: str = "linear16",
    ) -> int:
        """
        Stream TTS audio chunks as base64-encoded strings.

        Convenience wrapper around synthesize_streaming that encodes
        audio chunks to base64 for easy WebSocket/JSON transmission.

        Args:
            text: Text to convert to speech.
            on_audio_chunk: Async callback for each chunk (base64_str, index).
            on_complete: Optional callback when streaming ends.
            voice: Voice model to use.
            encoding: Audio encoding format.

        Returns:
            Total number of audio chunks sent.
        """
        async def encode_and_forward(audio_bytes: bytes, index: int) -> None:
            base64_chunk = base64.b64encode(audio_bytes).decode("utf-8")
            await on_audio_chunk(base64_chunk, index)

        return await self.synthesize_streaming(
            text=text,
            on_audio_chunk=encode_and_forward,
            on_complete=on_complete,
            voice=voice,
            encoding=encoding,
        )

