from app.pipelines.scoring import normalize_difficulty, normalize_volume, opportunity_score


def test_normalize_volume_zero_and_none():
    assert normalize_volume(0) == 0.0
    assert normalize_volume(None) == 0.0


def test_normalize_volume_scales_logarithmically():
    low = normalize_volume(100)
    high = normalize_volume(10_000)
    assert 0 < low < high <= 1.0


def test_normalize_volume_caps_at_one():
    assert normalize_volume(1_000_000) == 1.0


def test_normalize_difficulty_none_is_neutral():
    assert normalize_difficulty(None) == 0.5


def test_normalize_difficulty_inverts_and_clamps():
    assert normalize_difficulty(0) == 1.0
    assert normalize_difficulty(100) == 0.0
    assert normalize_difficulty(150) == 0.0  # clamps above range
    assert normalize_difficulty(-10) == 1.0  # clamps below range


def test_opportunity_score_high_volume_low_difficulty_high_relevance_scores_high():
    score = opportunity_score(volume=10_000, difficulty=5, relevance_score=95)
    assert score > 85


def test_opportunity_score_low_volume_high_difficulty_low_relevance_scores_low():
    score = opportunity_score(volume=10, difficulty=95, relevance_score=5)
    assert score < 15


def test_opportunity_score_missing_metrics_still_returns_a_score():
    score = opportunity_score(volume=None, difficulty=None, relevance_score=80)
    assert 0 <= score <= 100


def test_opportunity_score_is_bounded():
    assert 0 <= opportunity_score(volume=1_000_000, difficulty=0, relevance_score=100) <= 100
    assert 0 <= opportunity_score(volume=0, difficulty=100, relevance_score=0) <= 100
