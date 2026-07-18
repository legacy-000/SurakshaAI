import logging
import struct
from threading import RLock
from typing import Optional

logger = logging.getLogger(__name__)


class VoiceHandler:
    _instance: Optional["VoiceHandler"] = None
    _lock: RLock = RLock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(VoiceHandler, cls).__new__(cls, *args, **kwargs)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        with self._lock:
            if getattr(self, "_initialized", False):
                return
            self._initialized = True

    def speech_to_text(self, audio_data: bytes, language: str) -> str:
        """
        Simulated Zia STT.
        Returns specific Kannada/Hindi/English transcriptions when matching
        specific header bytes (e.g. b'MOCK_KN', b'MOCK_HI', b'MOCK_EN'),
        otherwise returns a language-specific default transcription.
        """
        if not audio_data:
            logger.warning("Empty audio data passed to speech_to_text")
            return ""

        lang = (language or "en").lower().strip()

        # Specific mock header checks
        if audio_data.startswith(b'MOCK_KN'):
            return "ಪ್ರಕರಣಗಳನ್ನು ಹುಡುಕಿ"
        elif audio_data.startswith(b'MOCK_HI'):
            return "मामले खोजें"
        elif audio_data.startswith(b'MOCK_EN'):
            return "Search Cases"

        # Check if the mock strings are embedded anywhere in the header/audio data
        if b'MOCK_KN' in audio_data:
            return "ಪ್ರಕರಣಗಳನ್ನು ಹುಡುಕಿ"
        elif b'MOCK_HI' in audio_data:
            return "मामले खोजें"
        elif b'MOCK_EN' in audio_data:
            return "Search Cases"

        # Fallback to defaults based on language
        if lang == 'kn':
            return "ಕನ್ನಡದಲ್ಲಿ ಡೀಫಾಲ್ಟ್ ಪ್ರತಿಲಿಪಿ"
        elif lang == 'hi':
            return "हिंदी में डिफ़ॉल्ट प्रतिलेखन"
        else:
            return "Default transcription from Zia STT"

    def text_to_speech(self, text: str, language: str) -> bytes:
        """
        Simulated Zia TTS.
        Returns realistic generated voice audio bytes in WAV format based on
        the input text and language.
        """
        if not text:
            logger.warning("Empty text passed to text_to_speech")
            return b""

        lang = (language or "en").lower().strip()

        # We pack a metadata identifier and the text inside the WAV data section.
        # This keeps the output fully mock-testable and compliant with realistic audio bytes.
        text_payload = f"ZiaTTS:{lang}:{text}".encode('utf-8')
        data_len = len(text_payload)

        # WAV Structure elements
        riff_header = b'RIFF'
        file_size = 36 + data_len
        riff_size = struct.pack('<I', file_size)
        wave_header = b'WAVE'

        fmt_header = b'fmt '
        fmt_size = struct.pack('<I', 16)
        audio_format = struct.pack('<H', 1)  # PCM format
        num_channels = struct.pack('<H', 1)  # Mono channel
        sample_rate = struct.pack('<I', 8000)  # 8000 Hz
        byte_rate = struct.pack('<I', 16000)  # sample_rate * num_channels * bits_per_sample/8
        block_align = struct.pack('<H', 2)   # num_channels * bits_per_sample/8
        bits_per_sample = struct.pack('<H', 16)  # 16 bits

        data_header = b'data'
        data_size_bytes = struct.pack('<I', data_len)

        wav_bytes = (
            riff_header +
            riff_size +
            wave_header +
            fmt_header +
            fmt_size +
            audio_format +
            num_channels +
            sample_rate +
            byte_rate +
            block_align +
            bits_per_sample +
            data_header +
            data_size_bytes +
            text_payload)

        logger.info("Generated %d bytes of voice WAV audio for language: %s", len(wav_bytes), lang)
        return wav_bytes
