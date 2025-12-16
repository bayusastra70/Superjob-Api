class STTService:
    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Convert raw audio bytes to text.

        This is a stub implementation; plug in your preferred STT provider
        (e.g. Whisper, Deepgram, etc.) by replacing the body of this method.
        """
        # TODO: Implement real STT provider call.
        # For now, return a placeholder so the flow keeps working.
        return "[transcribed audio]"


