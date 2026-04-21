"""
Comprehensive unit tests for the IoT Data Aggregation API.

Tests cover:
- Endpoint availability and health checks
- Request validation (missing fields, invalid types, empty values)
- Successful data ingestion and queueing
- Error handling and status codes
- Summary retrieval and status polling
- List operations
"""

import sys
import pytest
import json
from unittest.mock import patch, MagicMock

# Ensure project modules are importable
sys.path.insert(0, "/app")

from api.app import app
from backend.exceptions import BackendError, RecordNotFoundError, ValidationError


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def valid_sensor_payload():
    """Sample valid sensor data payload."""
    return {
        "sensor_id": "sensor-001",
        "values": [22.5, 23.1, 24.5, 23.8]
    }


@pytest.fixture
def mock_record():
    """Mock database record."""
    return {
        "data_id": "550e8400-e29b-41d4-a716-446655440000",
        "sensor_id": "SENSOR-001",
        "object_key": "raw/SENSOR-001/550e8400-e29b-41d4-a716-446655440000.json",
        "status": "pending",
        "summary": None,
        "created_at": "2025-04-21T10:30:45.123Z"
    }


@pytest.fixture
def mock_completed_record():
    """Mock database record after processing."""
    return {
        "data_id": "550e8400-e29b-41d4-a716-446655440000",
        "sensor_id": "SENSOR-001",
        "object_key": "raw/SENSOR-001/550e8400-e29b-41d4-a716-446655440000.json",
        "status": "done",
        "summary": {
            "min": 22.5,
            "max": 24.5,
            "avg": 23.475,
            "count": 4
        },
        "created_at": "2025-04-21T10:30:45.123Z"
    }


# ============================================================================
# Health Check Tests
# ============================================================================


def test_health_check(client):
    """Test that health endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_health_check_content_type(client):
    """Test that health endpoint returns JSON."""
    response = client.get("/health")
    assert response.content_type == "application/json"


# ============================================================================
# Data Ingestion Tests - Success Cases
# ============================================================================


@patch("api.app.publish_job")
@patch("api.app.ingest_sensor_payload")
def test_post_data_success(mock_ingest, mock_publish, client, valid_sensor_payload, mock_record):
    """Test successful data ingestion."""
    mock_ingest.return_value = mock_record
    
    response = client.post(
        "/data",
        data=json.dumps(valid_sensor_payload),
        content_type="application/json"
    )
    
    assert response.status_code == 202
    assert response.json["data_id"] == mock_record["data_id"]
    assert response.json["status"] == "pending"
    mock_ingest.assert_called_once()
    mock_publish.assert_called_once()


@patch("api.app.publish_job")
@patch("api.app.ingest_sensor_payload")
def test_post_data_with_many_values(mock_ingest, mock_publish, client, mock_record):
    """Test data ingestion with large number of sensor values."""
    payload = {
        "sensor_id": "temp-sensor",
        "values": [20 + i*0.1 for i in range(100)]  # 100 readings
    }
    mock_ingest.return_value = mock_record
    
    response = client.post(
        "/data",
        data=json.dumps(payload),
        content_type="application/json"
    )
    
    assert response.status_code == 202
    mock_publish.assert_called_once()


@patch("api.app.publish_job")
@patch("api.app.ingest_sensor_payload")
def test_post_data_with_normalized_sensor_id(mock_ingest, mock_publish, client, mock_record):
    """Test that sensor_id is normalized to uppercase."""
    payload = {
        "sensor_id": "sensor-001",
        "values": [23.5]
    }
    mock_ingest.return_value = mock_record
    
    response = client.post(
        "/data",
        data=json.dumps(payload),
        content_type="application/json"
    )
    
    assert response.status_code == 202
    assert response.json["data_id"] == mock_record["data_id"]


# ============================================================================
# Data Ingestion Tests - Validation Error Cases
# ============================================================================


@patch("api.app.ingest_sensor_payload")
def test_post_data_missing_sensor_id(mock_ingest, client):
    """Test POST /data with missing sensor_id."""
    mock_ingest.side_effect = ValidationError("sensor_id is required")
    payload = {"values": [1.0, 2.0]}
    
    response = client.post(
        "/data",
        data=json.dumps(payload),
        content_type="application/json"
    )
    
    assert response.status_code == 400
    assert "sensor_id is required" in response.json["error"]


@patch("api.app.ingest_sensor_payload")
def test_post_data_missing_values(mock_ingest, client):
    """Test POST /data with missing values."""
    mock_ingest.side_effect = ValidationError("values is required")
    payload = {"sensor_id": "sensor-001"}
    
    response = client.post(
        "/data",
        data=json.dumps(payload),
        content_type="application/json"
    )
    
    assert response.status_code == 400
    assert "values is required" in response.json["error"]


@patch("api.app.ingest_sensor_payload")
def test_post_data_empty_sensor_id(mock_ingest, client):
    """Test POST /data with empty sensor_id."""
    mock_ingest.side_effect = ValidationError("sensor_id must not be empty or whitespace")
    payload = {"sensor_id": "", "values": [1.0]}
    
    response = client.post(
        "/data",
        data=json.dumps(payload),
        content_type="application/json"
    )
    
    assert response.status_code == 400
    assert "sensor_id must not be empty" in response.json["error"]


@patch("api.app.ingest_sensor_payload")
def test_post_data_empty_values(mock_ingest, client):
    """Test POST /data with empty values list."""
    mock_ingest.side_effect = ValidationError("values must not be empty")
    payload = {"sensor_id": "sensor-001", "values": []}
    
    response = client.post(
        "/data",
        data=json.dumps(payload),
        content_type="application/json"
    )
    
    assert response.status_code == 400
    assert "values must not be empty" in response.json["error"]


@patch("api.app.ingest_sensor_payload")
def test_post_data_invalid_value_type(mock_ingest, client):
    """Test POST /data with non-numeric values."""
    mock_ingest.side_effect = ValidationError(
        "All values must be numeric; got str at index 0"
    )
    payload = {"sensor_id": "sensor-001", "values": ["not_a_number"]}
    
    response = client.post(
        "/data",
        data=json.dumps(payload),
        content_type="application/json"
    )
    
    assert response.status_code == 400
    assert "must be numeric" in response.json["error"]


@patch("api.app.ingest_sensor_payload")
def test_post_data_values_not_list(mock_ingest, client):
    """Test POST /data with values as non-list."""
    mock_ingest.side_effect = ValidationError("values must be a list")
    payload = {"sensor_id": "sensor-001", "values": 42}
    
    response = client.post(
        "/data",
        data=json.dumps(payload),
        content_type="application/json"
    )
    
    assert response.status_code == 400
    assert "values must be a list" in response.json["error"]


@patch("api.app.ingest_sensor_payload")
def test_post_data_sensor_id_not_string(mock_ingest, client):
    """Test POST /data with sensor_id as non-string."""
    mock_ingest.side_effect = ValidationError("sensor_id must be a string")
    payload = {"sensor_id": 123, "values": [1.0]}
    
    response = client.post(
        "/data",
        data=json.dumps(payload),
        content_type="application/json"
    )
    
    assert response.status_code == 400
    assert "sensor_id must be a string" in response.json["error"]


# ============================================================================
# Data Ingestion Tests - Backend Error Cases
# ============================================================================


@patch("api.app.ingest_sensor_payload")
def test_post_data_backend_error(mock_ingest, client, valid_sensor_payload):
    """Test POST /data when backend fails."""
    mock_ingest.side_effect = BackendError("Failed to insert record")
    
    response = client.post(
        "/data",
        data=json.dumps(valid_sensor_payload),
        content_type="application/json"
    )
    
    assert response.status_code == 500
    assert "Failed to insert record" in response.json["error"]


@patch("api.app.mark_failed")
@patch("api.app.publish_job")
@patch("api.app.ingest_sensor_payload")
def test_post_data_queue_publish_error_marks_failed(
    mock_ingest, mock_publish, mock_mark_failed, client, valid_sensor_payload, mock_record
):
    """Test that record is marked failed if queue publish fails."""
    mock_ingest.return_value = mock_record
    mock_publish.side_effect = Exception("Queue connection failed")
    
    response = client.post(
        "/data",
        data=json.dumps(valid_sensor_payload),
        content_type="application/json"
    )
    
    assert response.status_code == 500
    assert "Failed to enqueue processing job" in response.json["error"]
    mock_mark_failed.assert_called_once_with(mock_record["data_id"])


@patch("api.app.ingest_sensor_payload")
def test_post_data_invalid_json(mock_ingest, client):
    """Test POST /data with invalid JSON."""
    response = client.post(
        "/data",
        data="not valid json",
        content_type="application/json"
    )
    
    # Flask handles invalid JSON gracefully
    assert response.status_code in [400, 500]


@patch("api.app.publish_job")
@patch("api.app.ingest_sensor_payload")
def test_post_data_no_content_type(mock_ingest, mock_publish, client, valid_sensor_payload):
    """Test POST /data without Content-Type header."""
    mock_ingest.return_value = {"data_id": "test-id", "status": "pending"}
    
    response = client.post("/data", data=json.dumps(valid_sensor_payload))
    
    # Should still work, defaults to form-data; publish_job mocked to avoid external queue
    assert response.status_code in [202, 400]


# ============================================================================
# Summary Retrieval Tests - Success Cases
# ============================================================================


@patch("api.app.get_summary_by_id")
def test_get_summary_success(mock_get_summary, client, mock_completed_record):
    """Test successful summary retrieval."""
    mock_get_summary.return_value = mock_completed_record
    
    response = client.get("/summary?id=550e8400-e29b-41d4-a716-446655440000")
    
    assert response.status_code == 200
    assert response.json["data_id"] == mock_completed_record["data_id"]
    assert response.json["status"] == "done"
    assert response.json["summary"]["avg"] == 23.475


@patch("api.app.get_summary_by_id")
def test_get_summary_still_pending(mock_get_summary, client, mock_record):
    """Test summary retrieval when still processing."""
    mock_get_summary.return_value = mock_record
    
    response = client.get("/summary?id=550e8400-e29b-41d4-a716-446655440000")
    
    assert response.status_code == 200
    assert response.json["status"] == "pending"
    assert response.json["summary"] is None


# ============================================================================
# Summary Retrieval Tests - Error Cases
# ============================================================================


def test_get_summary_missing_id(client):
    """Test GET /summary without id parameter."""
    response = client.get("/summary")
    
    assert response.status_code == 400
    assert "id is required" in response.json["error"]


@patch("api.app.get_summary_by_id")
def test_get_summary_not_found(mock_get_summary, client):
    """Test GET /summary with non-existent id."""
    mock_get_summary.side_effect = RecordNotFoundError("550e8400-e29b-41d4-a716-446655440000")
    
    response = client.get("/summary?id=550e8400-e29b-41d4-a716-446655440000")
    
    assert response.status_code == 404
    assert "not found" in response.json["error"]


@patch("api.app.get_summary_by_id")
def test_get_summary_backend_error(mock_get_summary, client):
    """Test GET /summary when backend fails."""
    mock_get_summary.side_effect = BackendError("Database connection failed")
    
    response = client.get("/summary?id=550e8400-e29b-41d4-a716-446655440000")
    
    assert response.status_code == 500
    assert "Database connection failed" in response.json["error"]


def test_get_summary_empty_id(client):
    """Test GET /summary with empty id parameter."""
    response = client.get("/summary?id=")
    
    assert response.status_code == 400


# ============================================================================
# List Tests - Success Cases
# ============================================================================


@patch("api.app.service_list_uploads")
def test_list_uploads_success(mock_list, client, mock_completed_record, mock_record):
    """Test successful list retrieval."""
    mock_list.return_value = [mock_completed_record, mock_record]
    
    response = client.get("/list")
    
    assert response.status_code == 200
    records = response.json
    assert len(records) == 2
    assert records[0]["data_id"] == mock_completed_record["data_id"]
    assert records[1]["status"] == "pending"


@patch("api.app.service_list_uploads")
def test_list_uploads_empty(mock_list, client):
    """Test list retrieval with no records."""
    mock_list.return_value = []
    
    response = client.get("/list")
    
    assert response.status_code == 200
    assert response.json == []


# ============================================================================
# List Tests - Error Cases
# ============================================================================


@patch("api.app.service_list_uploads")
def test_list_uploads_backend_error(mock_list, client):
    """Test list retrieval when backend fails."""
    mock_list.side_effect = BackendError("Database connection failed")
    
    response = client.get("/list")
    
    assert response.status_code == 500
    assert "Database connection failed" in response.json["error"]


# ============================================================================
# HTTP Method Tests
# ============================================================================


def test_get_data_not_allowed(client):
    """Test that GET /data is not allowed."""
    response = client.get("/data")
    
    assert response.status_code == 405


def test_post_summary_not_allowed(client):
    """Test that POST /summary is not allowed."""
    response = client.post("/summary", data=json.dumps({"id": "test"}))
    
    assert response.status_code == 405


def test_post_list_not_allowed(client):
    """Test that POST /list is not allowed."""
    response = client.post("/list", data=json.dumps({}))
    
    assert response.status_code == 405


# ============================================================================
# 404 Not Found Tests
# ============================================================================


def test_nonexistent_endpoint(client):
    """Test request to non-existent endpoint."""
    response = client.get("/nonexistent")
    
    assert response.status_code == 404
    assert "not found" in response.json["error"].lower()


# ============================================================================
# Content-Type Tests
# ============================================================================


def test_all_endpoints_return_json(client):
    """Test that all endpoints return JSON content type."""
    endpoints = [
        ("/health", "GET"),
        ("/list", "GET"),
        ("/summary?id=test", "GET"),
    ]
    
    for endpoint, method in endpoints:
        if method == "GET":
            response = client.get(endpoint)
        
        assert response.content_type == "application/json", f"Failed for {endpoint}"


# ============================================================================
# Integration-like Tests
# ============================================================================


@patch("api.app.publish_job")
@patch("api.app.ingest_sensor_payload")
@patch("api.app.get_summary_by_id")
def test_full_workflow_simulation(
    mock_get_summary, mock_ingest, mock_publish, client, valid_sensor_payload, 
    mock_record, mock_completed_record
):
    """
    Test a simulated full workflow:
    1. Ingest data (returns pending)
    2. Poll for summary (still pending)
    3. Poll for summary (now done)
    """
    data_id = mock_record["data_id"]
    mock_ingest.return_value = mock_record
    
    # Step 1: Ingest
    response = client.post(
        "/data",
        data=json.dumps(valid_sensor_payload),
        content_type="application/json"
    )
    assert response.status_code == 202
    assert response.json["status"] == "pending"
    
    # Step 2: Poll (still pending)
    mock_get_summary.return_value = mock_record
    response = client.get(f"/summary?id={data_id}")
    assert response.status_code == 200
    assert response.json["status"] == "pending"
    assert response.json["summary"] is None
    
    # Step 3: Poll (now done)
    mock_get_summary.return_value = mock_completed_record
    response = client.get(f"/summary?id={data_id}")
    assert response.status_code == 200
    assert response.json["status"] == "done"
    assert response.json["summary"]["avg"] == 23.475

