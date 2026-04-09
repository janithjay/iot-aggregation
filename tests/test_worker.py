from worker.worker import compute_summary


def test_compute_summary_basic():
    summary = compute_summary([10, 20, 30])
    assert summary["min"] == 10
    assert summary["max"] == 30
    assert summary["avg"] == 20
