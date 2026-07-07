class ZiaSTTClient:
    def transcribe(self, audio_bytes: bytes, lang: str = "en") -> str:
        return "[Transcribed audio text]"


class ZiaTTSClient:
    def synthesize(self, text: str, lang: str = "en") -> bytes:
        return b"[TTS audio data]"


class ZiaTranslationClient:
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if source_lang == "en" and target_lang == "kn":
            return f"[Kannada translation of: {text[:50]}...]"
        if source_lang == "kn" and target_lang == "en":
            return f"[English translation of: {text[:50]}...]"
        return text
