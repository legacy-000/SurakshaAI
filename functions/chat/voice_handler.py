class VoiceHandler:
    def process_voice_input(self, audio_base64: str, lang: str = "en") -> str:
        transcribed = self._stt(audio_base64, lang)
        return transcribed

    def _stt(self, audio_base64: str, lang: str) -> str:
        return f"[Transcribed {lang} audio]"

    def generate_voice_output(self, text: str, lang: str = "en") -> str:
        return f"[TTS audio bytes for: {text[:50]}...]"
