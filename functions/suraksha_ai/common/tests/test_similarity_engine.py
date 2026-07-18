from investigation.similarity_engine import SimilarityEngine, cosine_similarity
import sys
import os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)
os.environ.setdefault("PYTHONPATH", BASE)


class TestCosineSimilarity:
    def test_identical_vectors(self):
        assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0

    def test_orthogonal_vectors(self):
        assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0

    def test_empty_vectors(self):
        assert cosine_similarity([], []) == 0.0

    def test_mismatched_length(self):
        assert cosine_similarity([1.0], [1.0, 0.0]) == 0.0


class TestSimilarityEngine:
    def test_find_similar_returns_correct_count(self):
        sim = SimilarityEngine()
        results = sim.find_similar(101, top_k=3)
        assert len(results) == 3

    def test_find_similar_all_scores_in_range(self):
        sim = SimilarityEngine()
        results = sim.find_similar(101, top_k=5)
        for r in results:
            assert 0.0 <= r.similarity_score <= 1.0
            assert r.case_master_id > 0
            assert r.crime_no is not None

    def test_find_similar_has_per_feature_scores(self):
        sim = SimilarityEngine()
        results = sim.find_similar(101, top_k=1)
        for r in results:
            assert "crime_type" in r.per_feature_scores
            assert "time_proximity" in r.per_feature_scores
            assert "location" in r.per_feature_scores
            assert "text_embedding" in r.per_feature_scores

    def test_find_similar_deterministic_across_instances(self):
        r1 = SimilarityEngine().find_similar(101, top_k=3)
        r2 = SimilarityEngine().find_similar(101, top_k=3)
        for a, b in zip(r1, r2):
            assert a.similarity_score == b.similarity_score

    def test_db_query_uses_case_master_schema(self):
        class MockDB:
            is_connected = True

            def __init__(self):
                self.sql = ""

            def execute_non_query(self, sql):
                self.sql = sql
                return {
                    "columns": ["CrimeNo", "CrimeMinorHeadID", "BriefFacts"],
                    "rows": [["CN001", 10, "Theft at market"]],
                }

        db = MockDB()
        SimilarityEngine(db=db).find_similar(101, top_k=1)
        assert "FROM CaseMaster" in db.sql
        assert "FirMaster" not in db.sql
        assert "BriefFacts" in db.sql
