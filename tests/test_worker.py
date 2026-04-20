from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from backend.exceptions import ValidationError
from worker.worker import handle_job_failure, on_message, parse_job_message, process_job


def test_parse_job_message_valid_payload():
    payload = {"data_id": "abc", "values": [1, 2.5], "retry_count": 1}
    parsed = parse_job_message(json.dumps(payload).encode("utf-8"))
    assert parsed["data_id"] == "abc"
    assert parsed["values"] == [1.0, 2.5]
    assert parsed["retry_count"] == 1


def test_parse_job_message_invalid_payload_raises():
    with pytest.raises(ValidationError, match="valid data_id"):
        parse_job_message(json.dumps({"values": [1]}).encode("utf-8"))


@patch("worker.worker.mark_completed")
@patch("worker.worker.compute_summary")
@patch("worker.worker.mark_processing")
def test_process_job_success(mock_mark_processing, mock_compute_summary, mock_mark_completed):
    mock_compute_summary.return_value = {"min": 1.0, "max": 2.0, "avg": 1.5, "count": 2}
    mock_mark_completed.return_value = {"data_id": "abc", "status": "done"}

    result = process_job({"data_id": "abc", "values": [1.0, 2.0]})

    mock_mark_processing.assert_called_once_with("abc")
    mock_compute_summary.assert_called_once_with([1.0, 2.0])
    mock_mark_completed.assert_called_once()
    assert result["status"] == "done"


@patch("worker.worker.publish_job")
def test_handle_job_failure_requeues_before_max_retry(mock_publish_job):
    result = handle_job_failure({"data_id": "abc", "values": [1], "retry_count": 0}, RuntimeError("boom"))
    assert result == "retried"
    mock_publish_job.assert_called_once()


@patch("worker.worker.mark_failed")
@patch("worker.worker.publish_job")
def test_handle_job_failure_marks_failed_after_retries(mock_publish_job, mock_mark_failed):
    result = handle_job_failure({"data_id": "abc", "values": [1], "retry_count": 99}, RuntimeError("boom"))
    assert result == "failed"
    mock_publish_job.assert_not_called()
    mock_mark_failed.assert_called_once_with("abc")


@patch("worker.worker.process_job")
@patch("worker.worker.parse_job_message")
def test_on_message_acknowledges_after_processing(mock_parse, mock_process):
    channel = MagicMock()
    method = MagicMock()
    method.delivery_tag = "tag-1"
    mock_parse.return_value = {"data_id": "abc", "values": [1]}

    on_message(channel, method, None, b"{}")

    mock_process.assert_called_once()
    channel.basic_ack.assert_called_once_with(delivery_tag="tag-1")
