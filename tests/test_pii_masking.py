from functions.security.pii_masker import PIIMasker

def test_accused_name_masked():
    masker = PIIMasker()
    result = masker.mask_accused_name("Ravi Kumar")
    assert "***" in result
    assert result != "Ravi Kumar"

def test_pii_masking_in_rows():
    masker = PIIMasker()
    rows = [["Ravi Kumar", 101], ["Suresh P", 102]]
    columns = ["name", "id"]
    masked = masker.mask_pii_in_results(rows, columns, ["name"])
    assert masked[0][0] != "Ravi Kumar"
    assert "***" in masked[0][0]
