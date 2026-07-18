from functions.offender.priority_scorer import PriorityScorer


def test_score_reproducibility():
    scorer = PriorityScorer()
    score1 = scorer.calculate_score("ent_test_1", "Ravi Kumar")
    score2 = scorer.calculate_score("ent_test_1", "Ravi Kumar")
    assert score1.total_score == score2.total_score
