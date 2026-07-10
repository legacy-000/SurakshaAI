from common.models.dto import FinancialAnalysisResultDTO


class FinancialStub:
    def get_status(self) -> FinancialAnalysisResultDTO:
        return FinancialAnalysisResultDTO(
            data_available=False,
            schema_source="KSP FIR Schema",
            missing_datasets=[
                "FinancialAccount",
                "FinancialTransaction",
                "PersonAccountAssociation",
                "CaseTransactionAssociation"
            ],
            message=(
                "Financial transaction data is not available in the provided KSP FIR schema. "
                "The financial analysis module is ready to process data when an extension dataset is integrated."
            ),
            synthetic_demo_available=True,
            synthetic_data_label="DEMONSTRATION DATA ONLY - NOT REAL KSP RECORDS"
        )
