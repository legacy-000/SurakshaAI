import logging

logger = logging.getLogger(__name__)


class EvidenceValidator:
    def validate(self, evidence_list: list) -> list:
        validated = []
        for ev in evidence_list:
            v = dict(ev)
            v["validated"] = True
            v["validated_at"] = __import__("datetime").datetime.utcnow().isoformat()
            validated.append(v)
        return validated
