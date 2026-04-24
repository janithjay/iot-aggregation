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
    assert parsed["is_metrics_job"] is False


def test_parse_job_message_node_metrics_payload():
    """Test parsing of node-based metrics job payload."""
    payload = {
        "data_id": "xyz-123",
        "node_id": "NODE_TH",
        "object_key": "raw/sensor-1/xyz-123.json",
        "metrics": {"temperature": 22.5, "humidity": 45.2},
        "retry_count": 0
    }
    parsed = parse_job_message(json.dumps(payload).encode("utf-8"))
    assert parsed["data_id"] == "xyz-123"
    assert parsed["node_id"] == "NODE_TH"
    assert parsed["object_key"] == "raw/sensor-1/xyz-123.json"
    assert parsed["metrics"] == {"temperature": 22.5, "humidity": 45.2}
    assert parsed["is_metrics_job"] is True


def test_parse_job_message_invalid_payload_raises():
    with pytest.raises(ValidationError, match="valid data_id"):
        parse_job_message(json.dumps({"values": [1]}).encode("utf-8"))


@patch("worker.worker.mark_completed")
@patch("worker.worker.compute_summary")
@patch("worker.worker.mark_processing")
def test_process_job_success(mock_mark_processing, mock_compute_summary, mock_mark_completed):
    mock_compute_summary.return_value = {"min": 1.0, "max": 2.0, "avg": 1.5, "count": 2}
    mock_mark_completed.return_value = {"data_id": "abc", "status": "done"}

    result = process_job({"data_id": "abc", "values": [1.0, 2.0], "is_metrics_job": False})

    mock_mark_processing.assert_called_once_with("abc")
    mock_compute_summary.assert_called_once_with([1.0, 2.0])
    mock_mark_completed.assert_called_once()
    assert result["status"] == "done"


@patch("worker.worker.mark_completed")
@patch("worker.worker.compute_metrics_summary")
@patch("worker.worker.mark_processing")
def test_process_job_node_metrics_success(mock_mark_processing, mock_compute_metrics, mock_mark_completed):
    """Test node-based metrics job processing."""
    mock_compute_metrics.return_value = {
        "temperature": {
            "node_id": "NODE_TH",
            "latest": 22.5,
            "min": 22.5,
            "max": 22.5,
            "avg": 22.5,
            "count": 1
        },
        "humidity": {
            "node_id": "NODE_TH",
            "latest": 45.2,
            "min": 45.2,
            "max": 45.2,
            "avg": 45.2,
            "count": 1
        }
    }
    mock_mark_completed.return_value = {"data_id": "xyz-123", "status": "done", "node_id": "NODE_TH"}
    
    job_payload = {
        "data_id": "xyz-123",
        "node_id": "NODE_TH",
        "object_key": "raw/sensor-1/xyz-123.json",
        "metrics": {"temperature": 22.5, "humidity": 45.2},
        "is_metrics_job": True,
    }
    
    result = process_job(job_payload)
    
    mock_mark_processing.assert_called_once_with("xyz-123")
    mock_compute_metrics.assert_called_once()
    mock_mark_completed.assert_called_once()
    assert result["status"] == "done"


@patch("worker.worker.fetch_raw_payload")
@patch("worker.worker.mark_completed")
@patch("worker.worker.compute_metrics_summary")
@patch("worker.worker.mark_processing")
def test_process_job_fetches_from_minio(
    mock_mark_processing, mock_compute_metrics, mock_mark_completed, mock_fetch
):
    """Test that worker fetches from MinIO when object_key is available."""
    mock_fetch.return_value = {
        "node_id": "NODE_PA",
        "metrics": {"pressure": 1013.25, "ethanol": 25.5}
    }
    mock_compute_metrics.return_value = {
        "pressure": {"node_id": "NODE_PA", "latest": 1013.25, "min": 1013.25, "max": 1013.25, "avg": 1013.25, "count": 1},
        "ethanol": {"node_id": "NODE_PA", "latest": 25.5, "min": 25.5, "max": 25.5, "avg": 25.5, "count": 1}
    }
    mock_mark_completed.return_value = {"data_id": "pa-123", "status": "done"}
    
    job_payload = {
        "data_id": "pa-123",
        "node_id": "NODE_PA",
        "object_key": "raw/sensor-pa/pa-123.json",
        "metrics": {},  # Empty initially, will fetch from MinIO
        "is_metrics_job": True,
    }
    
    result = process_job(job_payload)
    
    mock_fetch.assert_called_once_with("raw/sensor-pa/pa-123.json")
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
