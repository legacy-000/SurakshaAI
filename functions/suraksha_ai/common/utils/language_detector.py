import re
from common.models.dto import DetectedLanguageDTO


class LanguageDetector:
    KANNADA_UNICODE_RANGE = range(0x0C80, 0x0CFF + 1)

    def detect(self, text: str) -> DetectedLanguageDTO:
        for char in text:
            if ord(char) in self.KANNADA_UNICODE_RANGE:
                return DetectedLanguageDTO(language_code="kn", confidence=0.95)
        return DetectedLanguageDTO(language_code="en", confidence=0.98)
