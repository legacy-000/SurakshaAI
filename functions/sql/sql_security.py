from models.dto import SQLValidationResultDTO, SecuredSQLDTO


class SQLSecurityEnforcer:
    def enforce(self, validation: SQLValidationResultDTO, user_scope: dict = None) -> SecuredSQLDTO:
        sql = validation.validated_sql

        if ";" in sql and sql.count(";") > 1:
            sql = sql.split(";")[0] + ";"

        sql = sql.replace("-- ", "")

        if "LIMIT" not in sql.upper():
            sql = sql.rstrip(";") + " LIMIT 1000;"

        return SecuredSQLDTO(sql_text=sql, max_rows=1000, timeout_seconds=30)
