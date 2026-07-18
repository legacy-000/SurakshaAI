from voice.voice_handler import VoiceHandler
from i18n.translation_manager import TranslationManager
import sys
import os
import struct
import threading
from typing import Set

# Ensure common directory is in PYTHONPATH for testing imports
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE not in sys.path:
    sys.path.insert(0, BASE)
os.environ.setdefault("PYTHONPATH", BASE)


class TestTranslationManager:
    def test_singleton_and_thread_safety(self):
        """Verify that TranslationManager is a thread-safe singleton."""
        instances: Set[TranslationManager] = set()
        lock = threading.Lock()

        def get_instance():
            inst = TranslationManager()
            with lock:
                instances.add(inst)

        threads = [threading.Thread(target=get_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(instances) == 1
        # Check that we can get the same instance in the main thread
        manager = TranslationManager()
        assert next(iter(instances)) is manager

    def test_translation_english(self):
        """Verify English translation returns expected values or fallback."""
        manager = TranslationManager()

        # Exact matching keys
        assert manager.translate("Search Cases", "en") == "Search Cases"
        assert manager.translate("dashboard", "en") == "Dashboard"
        assert manager.translate("new alert generated", "en") == "New alert generated"

        # Fallback check for missing English keys
        assert manager.translate("Random Nonexistent Phrase", "en") == "Random Nonexistent Phrase"

    def test_translation_kannada(self):
        """Verify Kannada translations match UI, notification, and response terms."""
        manager = TranslationManager()

        # UI labels
        assert manager.translate("Search Cases", "kn") == "ಪ್ರಕರಣಗಳನ್ನು ಹುಡುಕಿ"
        assert manager.translate("dashboard", "kn") == "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್"
        assert manager.translate("settings", "kn") == "ಸಂಯೋಜನೆಗಳು"

        # Notifications
        assert manager.translate("new alert generated", "kn") == "ಹೊಸ ಎಚ್ಚರಿಕೆ ಬಂದಿದೆ"

        # AI responses
        assert manager.translate("how can I help you today?", "kn") == "ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?"

        # System errors
        assert manager.translate("database connection failed", "kn") == "ಡೇಟಾಬೇಸ್ ಸಂಪರ್ಕ ವಿಫಲವಾಗಿದೆ"

    def test_translation_hindi(self):
        """Verify Hindi translations match UI, notification, and response terms."""
        manager = TranslationManager()

        # UI labels
        assert manager.translate("Search Cases", "hi") == "मामले खोजें"
        assert manager.translate("dashboard", "hi") == "डैशबोर्ड"
        assert manager.translate("settings", "hi") == "सेटिंग्स"

        # Notifications
        assert manager.translate("new alert generated", "hi") == "नया अलर्ट उत्पन्न हुआ"

        # AI responses
        assert manager.translate("how can I help you today?", "hi") == "आज मैं आपकी क्या सहायता कर सकता हूँ?"

        # System errors
        assert manager.translate("database connection failed", "hi") == "डेटाबेस कनेक्शन विफल रहा"

    def test_translation_normalization_and_casing(self):
        """Verify translation works with variations in casing and whitespace."""
        manager = TranslationManager()

        # Uppercase / lower / mixed casing
        assert manager.translate("SEARCH CASES", "kn") == "ಪ್ರಕರಣಗಳನ್ನು ಹುಡುಕಿ"
        assert manager.translate("  search cases  ", "kn") == "ಪ್ರಕರಣಗಳನ್ನು ಹುಡುಕಿ"
        assert manager.translate("Search Cases", "kn") == "ಪ್ರಕರಣಗಳನ್ನು ಹುಡುಕಿ"

        # Hindi checks
        assert manager.translate("database connection failed", "hi") == "डेटाबेस कनेक्शन विफल रहा"
        assert manager.translate("Database Connection Failed", "hi") == "डेटाबेस कनेक्शन विफल रहा"
        assert manager.translate("  database connection failed  ", "hi") == "डेटाबेस कनेक्शन विफल रहा"

    def test_translation_fallbacks(self):
        """Verify that translation falls back to original text when unsupported."""
        manager = TranslationManager()

        # Unsupported language
        assert manager.translate("Dashboard", "fr") == "Dashboard"

        # Non-existent translation string
        assert manager.translate("Hello police officer", "kn") == "Hello police officer"
        assert manager.translate("Hello police officer", "hi") == "Hello police officer"

    def test_translation_empty_inputs(self):
        """Verify translation handles empty inputs gracefully."""
        manager = TranslationManager()
        assert manager.translate("", "kn") == ""
        assert manager.translate(None, "kn") == ""


class TestVoiceHandler:
    def test_singleton_and_thread_safety(self):
        """Verify that VoiceHandler is a thread-safe singleton."""
        instances: Set[VoiceHandler] = set()
        lock = threading.Lock()

        def get_instance():
            inst = VoiceHandler()
            with lock:
                instances.add(inst)

        threads = [threading.Thread(target=get_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(instances) == 1
        handler = VoiceHandler()
        assert next(iter(instances)) is handler

    def test_speech_to_text_mock_headers(self):
        """Verify STT returns expected transcriptions for mock audio header signatures."""
        handler = VoiceHandler()

        # Kannada mock header
        kn_audio = b"MOCK_KN_arbitrary_audio_bytes"
        assert handler.speech_to_text(kn_audio, "kn") == "ಪ್ರಕರಣಗಳನ್ನು ಹುಡುಕಿ"
        # Language parameter shouldn't override the mock header signature
        assert handler.speech_to_text(kn_audio, "en") == "ಪ್ರಕರಣಗಳನ್ನು ಹುಡುಕಿ"

        # Hindi mock header
        hi_audio = b"MOCK_HI_audio_payload"
        assert handler.speech_to_text(hi_audio, "hi") == "मामले खोजें"
        assert handler.speech_to_text(hi_audio, "en") == "मामले खोजें"

        # English mock header
        en_audio = b"MOCK_EN_audio_payload"
        assert handler.speech_to_text(en_audio, "en") == "Search Cases"

    def test_speech_to_text_defaults(self):
        """Verify STT returns default transcriptions when header bytes do not match."""
        handler = VoiceHandler()
        generic_audio = b"SOME_REAL_PCM_AUDIO_BYTES_WITHOUT_SIGNATURES"

        assert handler.speech_to_text(generic_audio, "kn") == "ಕನ್ನಡದಲ್ಲಿ ಡೀಫಾಲ್ಟ್ ಪ್ರತಿಲಿಪಿ"
        assert handler.speech_to_text(generic_audio, "hi") == "हिंदी में डिफ़ॉल्ट प्रतिलेखन"
        assert handler.speech_to_text(generic_audio, "en") == "Default transcription from Zia STT"
        assert handler.speech_to_text(generic_audio, "unsupported") == "Default transcription from Zia STT"

    def test_speech_to_text_empty(self):
        """Verify STT handles empty audio data gracefully."""
        handler = VoiceHandler()
        assert handler.speech_to_text(b"", "en") == ""
        assert handler.speech_to_text(None, "en") == ""

    def test_text_to_speech_output_format(self):
        """Verify TTS returns realistic generated audio bytes in WAV format."""
        handler = VoiceHandler()

        test_text = "Search Cases"
        audio_bytes = handler.text_to_speech(test_text, "en")

        # Verify valid WAV container structure
        assert len(audio_bytes) > 44
        assert audio_bytes[0:4] == b"RIFF"
        assert audio_bytes[8:12] == b"WAVE"
        assert audio_bytes[12:16] == b"fmt "
        assert audio_bytes[36:40] == b"data"

        # Read fmt chunk sizes & format (PCM mono 8000Hz 16bit)
        fmt_size = struct.unpack('<I', audio_bytes[16:20])[0]
        assert fmt_size == 16
        audio_format = struct.unpack('<H', audio_bytes[20:22])[0]
        assert audio_format == 1
        num_channels = struct.unpack('<H', audio_bytes[22:24])[0]
        assert num_channels == 1
        sample_rate = struct.unpack('<I', audio_bytes[24:28])[0]
        assert sample_rate == 8000

        # Read text metadata payload from the wav data chunk
        data_len = struct.unpack('<I', audio_bytes[40:44])[0]
        payload = audio_bytes[44: 44 + data_len].decode('utf-8')
        assert payload == f"ZiaTTS:en:{test_text}"

    def test_text_to_speech_languages(self):
        """Verify TTS works for Kannada, Hindi and English generating customized payloads."""
        handler = VoiceHandler()

        # Kannada check
        kn_text = "ಪ್ರಕರಣಗಳನ್ನು ಹುಡುಕಿ"
        kn_audio = handler.text_to_speech(kn_text, "kn")
        data_len_kn = struct.unpack('<I', kn_audio[40:44])[0]
        payload_kn = kn_audio[44: 44 + data_len_kn].decode('utf-8')
        assert payload_kn == f"ZiaTTS:kn:{kn_text}"

        # Hindi check
        hi_text = "मामले खोजें"
        hi_audio = handler.text_to_speech(hi_text, "hi")
        data_len_hi = struct.unpack('<I', hi_audio[40:44])[0]
        payload_hi = hi_audio[44: 44 + data_len_hi].decode('utf-8')
        assert payload_hi == f"ZiaTTS:hi:{hi_text}"

    def test_text_to_speech_empty(self):
        """Verify TTS handles empty inputs gracefully."""
        handler = VoiceHandler()
        assert handler.text_to_speech("", "en") == b""
        assert handler.text_to_speech(None, "en") == b""
