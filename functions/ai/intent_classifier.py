from models.dto import NormalizedQueryDTO, IntentResultDTO


class IntentClassifier:
    def classify(self, query: NormalizedQueryDTO) -> IntentResultDTO:
        text = query.normalized_text.lower()
        if any(w in text for w in ["network", "link", "connect", "association", "co-accused"]):
            return IntentResultDTO(intent_type="NETWORK_QUERY", confidence=0.85)
        if any(w in text for w in ["trend", "month", "year", "time", "pattern", "change"]):
            return IntentResultDTO(intent_type="TREND_QUERY", confidence=0.85)
        if any(w in text for w in ["hotspot", "map", "location", "area", "cluster"]):
            return IntentResultDTO(intent_type="HOTSPOT_QUERY", confidence=0.85)
        if any(w in text for w in ["forecast", "predict", "future", "next month"]):
            return IntentResultDTO(intent_type="FORECAST_QUERY", confidence=0.85)
        if any(w in text for w in ["profile", "offender", "accused", "priority", "score"]):
            return IntentResultDTO(intent_type="OFFENDER_QUERY", confidence=0.85)
        if any(w in text for w in ["similar", "like", "comparable", "modus"]):
            return IntentResultDTO(intent_type="SIMILARITY_QUERY", confidence=0.85)
        return IntentResultDTO(intent_type="DATA_QUERY", confidence=0.95)
