KSP_SCHEMA_VERSION = "1.0.0"
PROTOTYPE_VERSION = "1.0.0"
SCORE_VERSION = "1.0.0"
FORECAST_MODEL_VERSION = "prophet_v1.0"

ENTITY_TIER_EXACT_RECORD = "exact_record"
ENTITY_TIER_DETERMINISTIC = "deterministic_match"
ENTITY_TIER_PROBABLE = "probable_match"
ENTITY_TIER_UNRESOLVED = "unresolved_possible"

CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"
CONFIDENCE_INSUFFICIENT = "insufficient_data"

EVIDENCE_DATABASE_FACT = "database_fact"
EVIDENCE_COMPUTED_STATISTIC = "computed_statistic"
EVIDENCE_MODEL_HYPOTHESIS = "model_hypothesis"
EVIDENCE_INVESTIGATIVE_SUGGESTION = "investigative_suggestion"

RISK_LOW = "LOW"
RISK_MODERATE = "MODERATE"
RISK_ELEVATED = "ELEVATED"
RISK_HIGH = "HIGH"

ROLE_INVESTIGATOR = "Investigator"
ROLE_ANALYST = "Analyst"
ROLE_SUPERVISOR = "Supervisor"
ROLE_POLICYMAKER = "Policymaker"
ROLE_SYSTEM_ADMIN = "System Administrator"

KARNATAKA_LAT_MIN = 11.5
KARNATAKA_LAT_MAX = 18.5
KARNATAKA_LNG_MIN = 74.0
KARNATAKA_LNG_MAX = 78.5

IPS_FEATURE_NAMES = [
    "case_frequency", "crime_type_diversity", "geographic_spread",
    "recent_activity_frequency", "co_accused_network_size", "arrest_surrender_ratio"
]
IPS_FEATURE_WEIGHTS = [0.25, 0.15, 0.15, 0.20, 0.15, 0.10]
