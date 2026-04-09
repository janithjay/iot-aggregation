from backend.service import normalize_values


def test_normalize_values_filters_invalid():
    assert normalize_values([1, "2", "x", None]) == [1.0, 2.0]
