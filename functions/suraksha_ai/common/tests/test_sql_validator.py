from sql.sql_validator import SQLValidator
import sys
import os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)
os.environ.setdefault("PYTHONPATH", BASE)


class TestSQLValidator:
    def test_valid_select_passes(self):
        v = SQLValidator()
        result = v.validate("SELECT * FROM CaseMaster")
        assert result["is_valid"] is True

    def test_ddl_rejected(self):
        v = SQLValidator()
        result = v.validate("DROP TABLE CaseMaster")
        assert result["is_valid"] is False
        assert any("SELECT" in e for e in result["errors"])

    def test_dml_rejected(self):
        v = SQLValidator()
        for stmt in ["INSERT INTO CaseMaster VALUES (1)", "UPDATE CaseMaster SET x=1", "DELETE FROM CaseMaster"]:
            result = v.validate(stmt)
            assert result["is_valid"] is False

    def test_empty_input_rejected(self):
        v = SQLValidator()
        result = v.validate("")
        assert result["is_valid"] is False
        assert any("Empty" in e for e in result["errors"])
