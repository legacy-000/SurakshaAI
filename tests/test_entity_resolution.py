from functions.network.entity_resolver import EntityResolver
from models.dto import EntityResolutionRequestDTO

def test_exact_match():
    resolver = EntityResolver()
    req = EntityResolutionRequestDTO(accused_name="Ravi Kumar")
    result = resolver.resolve(req)
    assert len(result.candidates) > 0
    assert result.candidates[0].match_type == "exact_record"

def test_partial_match():
    resolver = EntityResolver()
    req = EntityResolutionRequestDTO(accused_name="Ravi")
    result = resolver.resolve(req)
    assert len(result.candidates) > 0
