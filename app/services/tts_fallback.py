"""Fallback TTS service using pyttsx3 for offline text-to-speech.

This module provides a free, offline alternative to Deepgram TTS using the
pyttsx3 library, which leverages system TTS engines:
- Windows: SAPI5
- macOS: NSSpeechSynthesizer
- Linux: espeak
"""

import asyncio
import base64
import io
import logging
import tempfile
import wave
from concurrent.futures import ThreadPoolExecutor
from typing import Awaitable, Callable, Optional

import pyttsx3

logger = logging.getLogger(__name__)

# Thread pool for running synchronous pyttsx3 in async context
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="tts_fallback")


class TTSFallbackService:
    """Fallback Text-to-Speech service using pyttsx3."""

    # Chunk size for pseudo-streaming (in bytes)
    CHUNK_SIZE = 4096

    def __init__(self, rate: int = 150, volume: float = 1.0) -> None:
        """Initialize the fallback TTS service.

        Args:
            rate: Speech rate (words per minute). Default is 150.
            volume: Volume level from 0.0 to 1.0. Default is 1.0.
        """
        self.rate = rate
        self.volume = volume
        self._engine: Optional[pyttsx3.Engine] = None

    def _get_engine(self) -> pyttsx3.Engine:
        """Get or create the pyttsx3 engine.

        Note: pyttsx3 engine must be created in the same thread it's used.
        """
        engine = pyttsx3.init()
        engine.setProperty("rate", self.rate)
        engine.setProperty("volume", self.volume)
        return engine

    def _synthesize_sync(self, text: str) -> bytes:
        """Synchronously synthesize text to WAV audio bytes.

        Args:
            text: Text to convert to speech.

        Returns:
            WAV audio data as bytes.
        """
        engine = self._get_engine()

        # Create a temporary file for the audio output
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Save speech to file
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()
            engine.stop()

            # Read the generated audio file
            with open(tmp_path, "rb") as f:
                audio_bytes = f.read()

            return audio_bytes
        finally:
            # Clean up temp file
            import os

            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    async def synthesize(self, text: str) -> bytes:
        """Convert text to speech audio bytes.

        Args:
            text: Text to convert to speech.

        Returns:
            WAV audio data as bytes.
        """
        loop = asyncio.get_event_loop()
        audio_bytes = await loop.run_in_executor(_executor, self._synthesize_sync, text)
        logger.debug(f"Fallback TTS synthesis completed: {len(audio_bytes)} bytes")
        return audio_bytes

    async def synthesize_base64(self, text: str) -> str:
        """Convert text to speech and return as base64-encoded string.

        Args:
            text: Text to convert to speech.

        Returns:
            Base64-encoded WAV audio data string.
        """
        audio_bytes = await self.synthesize(text)
        return base64.b64encode(audio_bytes).decode("utf-8")

    def _convert_wav_to_linear16(self, wav_bytes: bytes) -> bytes:
        """Extract raw PCM (linear16) data from WAV bytes.

        Args:
            wav_bytes: WAV file bytes.

        Returns:
            Raw PCM audio data.
        """
        with io.BytesIO(wav_bytes) as wav_buffer:
            with wave.open(wav_buffer, "rb") as wav_file:
                return wav_file.readframes(wav_file.getnframes())

    async def synthesize_streaming(
        self,
        text: str,
        on_audio_chunk: Callable[[bytes, int], Awaitable[None]],
        on_complete: Optional[Callable[[int], Awaitable[None]]] = None,
        encoding: str = "linear16",
    ) -> int:
        """Stream TTS audio chunks via callback.

        This is pseudo-streaming: we generate the full audio first,
        then deliver it in chunks. This provides API compatibility
        with Deepgram's streaming TTS.

        Args:
            text: Text to convert to speech.
            on_audio_chunk: Async callback for each audio chunk (bytes, index).
            on_complete: Optional callback when streaming ends.
            encoding: Audio encoding (only 'linear16' supported for fallback).

        Returns:
            Total number of audio chunks sent.
        """
        # Generate full audio
        wav_bytes = await self.synthesize(text)

        # Extract raw PCM data if linear16 requested
        if encoding == "linear16":
            audio_data = self._convert_wav_to_linear16(wav_bytes)
        else:
            # For other encodings, return WAV as-is
            audio_data = wav_bytes

        # Stream in chunks
        chunk_index = 0
        offset = 0

        while offset < len(audio_data):
            chunk = audio_data[offset : offset + self.CHUNK_SIZE]
            await on_audio_chunk(chunk, chunk_index)
            chunk_index += 1
            offset += self.CHUNK_SIZE

        # Call completion callback
        if on_complete:
            await on_complete(chunk_index)

        logger.debug(f"Fallback TTS streaming completed: {chunk_index} chunks")
        return chunk_index

    async def synthesize_streaming_base64(
        self,
        text: str,
        on_audio_chunk: Callable[[str, int], Awaitable[None]],
        on_complete: Optional[Callable[[int], Awaitable[None]]] = None,
        encoding: str = "linear16",
    ) -> int:
        """Stream TTS audio chunks as base64-encoded strings.

        Args:
            text: Text to convert to speech.
            on_audio_chunk: Async callback for each chunk (base64_str, index).
            on_complete: Optional callback when streaming ends.
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
            encoding=encoding,
        )


# Singleton instance for reuse
_fallback_service: Optional[TTSFallbackService] = None


def get_tts_fallback_service() -> TTSFallbackService:
    """Get the singleton fallback TTS service instance."""
    global _fallback_service
    if _fallback_service is None:
        _fallback_service = TTSFallbackService()
    return _fallback_service


