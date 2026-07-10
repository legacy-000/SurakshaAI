from common.models.dto import QueryExecutionResultDTO
from common.config.constants import CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, CONFIDENCE_LOW, CONFIDENCE_INSUFFICIENT


class ConfidenceClassifier:
    def classify(self, execution: QueryExecutionResultDTO) -> str:
        if not execution or execution.execution_status == "error":
            return CONFIDENCE_LOW
        if execution.row_count == 0:
            return CONFIDENCE_HIGH
        if execution.row_count > 1000:
            return CONFIDENCE_MEDIUM
        return CONFIDENCE_HIGH
