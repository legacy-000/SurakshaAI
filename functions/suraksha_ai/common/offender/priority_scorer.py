import uuid
from datetime import datetime
from models.dto import PriorityScoreDTO, PriorityScoreFeature
from config.constants import IPS_FEATURE_NAMES, IPS_FEATURE_WEIGHTS, SCORE_VERSION


class PriorityScorer:
    def calculate_score(self, entity_id: str, entity_name: str) -> PriorityScoreDTO:
        features = self._compute_features(entity_name)
        total = sum(f.contribution for f in features)
        total_normalized = total * 100

        if total_normalized <= 25:
            tier = "LOW"
        elif total_normalized <= 50:
            tier = "MODERATE"
        elif total_normalized <= 75:
            tier = "ELEVATED"
        else:
            tier = "HIGH"

        return PriorityScoreDTO(
            execution_id=str(uuid.uuid4()),
            entity_id=entity_id,
            entity_name=entity_name,
            score_version=SCORE_VERSION,
            total_score=round(total_normalized, 2),
            risk_tier=tier,
            features=features,
            missing_features=[],
            disclaimer=(
                "This score is an analytical tool for investigation prioritization. "
                "It does not indicate guilt, dangerousness, or likelihood of future crime. "
                "Decisions must incorporate officer judgment and legal procedures."
            ),
            computed_at=datetime.now().isoformat()
        )

    def _compute_features(self, name: str) -> list[PriorityScoreFeature]:
        import hashlib
        features = []
        base_values = [8, 3, 2, 2, 6, 0.7]
        caps = [3.0, 10, 5, 5, 15, 1.0]
        seed_val = int(hashlib.md5(name.encode()).hexdigest()[:8], 16) / 1e8

        for i, feat_name in enumerate(IPS_FEATURE_NAMES):
            raw = base_values[i] + ((seed_val * (i + 1)) % 10 - 5) * 0.1
            norm = raw / caps[i]
            norm = min(norm, 1.0)
            weight = IPS_FEATURE_WEIGHTS[i]
            contribution = norm * weight

            features.append(PriorityScoreFeature(
                feature_id=f"F-IPS-{i+1:02d}",
                name=feat_name.replace("_", " ").title(),
                raw_value=f"{raw:.1f}",
                normalized_value=round(norm, 4),
                weight=weight,
                contribution=round(contribution, 4),
                is_missing=False
            ))

        return features
