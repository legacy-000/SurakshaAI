import logging
from threading import RLock
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TranslationManager:
    _instance: Optional["TranslationManager"] = None
    _lock: RLock = RLock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(TranslationManager, cls).__new__(cls, *args, **kwargs)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        with self._lock:
            if getattr(self, "_initialized", False):
                return

            # Dictionaries for 'en', 'kn' (Kannada), and 'hi' (Hindi)
            self._translations: Dict[str, Dict[str, str]] = {
                "en": {
                    # UI Labels
                    "search cases": "Search Cases",
                    "dashboard": "Dashboard",
                    "settings": "Settings",
                    "profile": "Profile",
                    "help": "Help",
                    "submit": "Submit",
                    "cancel": "Cancel",
                    "alerts": "Alerts",
                    "report": "Report",

                    # Notifications
                    "new alert generated": "New alert generated",
                    "case updated successfully": "Case updated successfully",
                    "report generated": "Report generated",
                    "unauthorized access detected": "Unauthorized access detected",

                    # AI Responses
                    "how can I help you today?": "How can I help you today?",
                    "i found the following cases:": "I found the following cases:",
                    "no cases match your query.": "No cases match your query.",
                    "generating report...": "Generating report...",

                    # System / Error Messages
                    "database connection failed": "Database connection failed",
                    "invalid credentials": "Invalid credentials",
                    "an unexpected error occurred": "An unexpected error occurred",
                    "permission denied": "Permission denied",
                    "session expired": "Session expired"
                },
                "kn": {
                    # UI Labels
                    "search cases": "ಪ್ರಕರಣಗಳನ್ನು ಹುಡುಕಿ",
                    "dashboard": "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
                    "settings": "ಸಂಯೋಜನೆಗಳು",
                    "profile": "ಪ್ರೊಫೈಲ್",
                    "help": "ಸಹಾಯ",
                    "submit": "ಸಲ್ಲಿಸು",
                    "cancel": "ರದ್ದುಮಾಡು",
                    "alerts": "ಎಚ್ಚರಿಕೆಗಳು",
                    "report": "ವರದಿ",

                    # Notifications
                    "new alert generated": "ಹೊಸ ಎಚ್ಚರಿಕೆ ಬಂದಿದೆ",
                    "case updated successfully": "ಪ್ರಕರಣವನ್ನು ಯಶಸ್ವಿಯಾಗಿ ನವೀಕರಿಸಲಾಗಿದೆ",
                    "report generated": "ವರದಿ ಸಿದ್ಧವಾಗಿದೆ",
                    "unauthorized access detected": "ಅನಧಿಕೃತ ಪ್ರವೇಶ ಪತ್ತೆಯಾಗಿದೆ",

                    # AI Responses
                    "how can I help you today?": "ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
                    "i found the following cases:": "ನನಗೆ ಈ ಕೆಳಗಿನ ಪ್ರಕರಣಗಳು ಕಂಡುಬಂದಿವೆ:",
                    "no cases match your query.": "ನಿಮ್ಮ ಪ್ರಶ್ನೆಗೆ ಯಾವುದೇ ಪ್ರಕರಣಗಳು ತಾಳೆಯಾಗುತ್ತಿಲ್ಲ.",
                    "generating report...": "ವರದಿ ಸಿದ್ಧಪಡಿಸಲಾಗುತ್ತಿದೆ...",

                    # System / Error Messages
                    "database connection failed": "ಡೇಟಾಬೇಸ್ ಸಂಪರ್ಕ ವಿಫಲವಾಗಿದೆ",
                    "invalid credentials": "ಅಮಾನ್ಯ ರುಜುವಾತುಗಳು",
                    "an unexpected error occurred": "ಅನಿರೀಕ್ಷಿತ ದೋಷ ಸಂಭವಿಸಿದೆ",
                    "permission denied": "ಅನುಮತಿ ನಿರಾಕರಿಸಲಾಗಿದೆ",
                    "session expired": "ಅಧಿವೇಶನದ ಅವಧಿ ಮುಗಿದಿದೆ"
                },
                "hi": {
                    # UI Labels
                    "search cases": "मामले खोजें",
                    "dashboard": "डैशबोर्ड",
                    "settings": "सेटिंग्स",
                    "profile": "प्रोफ़ाइल",
                    "help": "सहायता",
                    "submit": "जमा करें",
                    "cancel": "रद्द करें",
                    "alerts": "अलर्ट",
                    "report": "रिपोर्ट",

                    # Notifications
                    "new alert generated": "नया अलर्ट उत्पन्न हुआ",
                    "case updated successfully": "मामला सफलतापूर्वक अपडेट किया गया",
                    "report generated": "रिपोर्ट तैयार की गई",
                    "unauthorized access detected": "अनधिकृत पहुंच का पता चला",

                    # AI Responses
                    "how can I help you today?": "आज मैं आपकी क्या सहायता कर सकता हूँ?",
                    "i found the following cases:": "मुझे निम्नलिखित मामले मिले:",
                    "no cases match your query.": "आपके प्रश्न से कोई मामला मेल नहीं खाता।",
                    "generating report...": "रिपोर्ट तैयार की जा रही है...",

                    # System / Error Messages
                    "database connection failed": "डेटाबेस कनेक्शन विफल रहा",
                    "invalid credentials": "अमान्या क्रेडेंशियल",
                    "an unexpected error occurred": "एक अप्रत्याशित त्रुटि हुई",
                    "permission denied": "अनुमति अस्वीकृत",
                    "session expired": "सत्र समाप्त हो गया"
                }
            }

            # Prepopulate casing and space normalization matches
            for lang in list(self._translations.keys()):
                lang_dict = self._translations[lang]
                extended = {}
                for key, val in lang_dict.items():
                    extended[key] = val
                    extended[key.lower()] = val
                    extended[key.capitalize()] = val
                    extended[key.title()] = val

                    # Strip spaces just in case
                    extended[key.strip()] = val
                    extended[key.lower().strip()] = val
                self._translations[lang] = extended

            self._initialized = True

    def translate(self, text: str, target_lang: str) -> str:
        """
        Translate the given text into the target language.
        If target_lang is 'kn', return the Kannada translation.
        If target_lang is 'hi', return the Hindi translation.
        Supports falling back to the original text if target_lang is not
        supported or no translation is available.
        """
        if not text:
            return ""

        lang = (target_lang or "en").lower().strip()

        if lang not in self._translations:
            logger.warning("Unsupported target language: '%s'. Returning original text.", target_lang)
            return text

        lang_dict = self._translations[lang]

        # 1. Exact match lookup
        if text in lang_dict:
            return lang_dict[text]

        # 2. Try normalized (lowercase and stripped) match
        norm_text = text.lower().strip()
        if norm_text in lang_dict:
            return lang_dict[norm_text]

        # 3. Fallback to original text
        logger.debug("Translation not found for key: '%s' (lang: '%s').", text, target_lang)
        return text
