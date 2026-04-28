from __future__ import annotations

import uuid
from statistics import mean

# Import database CRUD functions from the DB layer
from db.database import (
    get_record,
    insert_record,
    list_records,
    update_record_status,
    update_record_summary,
)

from backend.exceptions import BackendError, RecordNotFoundError, ValidationError
from backend.models import SensorSummary, generate_object_key
from backend.validators import normalize_sensor_payload, validate_sensor_payload
from shared.storage import store_raw_payload


# services.py — Core business logic (the "brain" of the backend)
#
# This is the SERVICE LAYER. It sits between the API routes and the database.
# The API never talks to the database directly — it always goes through here.
#
# Main responsibilities:
#   1. Ingestion  — validate, normalize, store, and persist sensor data
#   2. Retrieval  — fetch records and summaries
#   3. Status     — manage record lifecycle (pending → processing → done/failed)
#   4. Computation — calculate statistical summaries (min, max, avg, count)




# Ingestion — the main pipeline when sensor data arrives


def ingest_sensor_payload(payload: dict) -> dict:
    """
    Full ingestion pipeline. Called by POST /data in the API.
    
    Steps:
      1. Validate the raw payload (reject bad input early)
      2. Normalize it (clean IDs, unify formats)
      3. Generate unique identifiers (UUID for data_id, path for MinIO)
      4. Store raw JSON to MinIO (backup of original data)
      5. Insert record into DynamoDB with status="pending"
      6. Fetch and return the newly created record
    """
    
    # Step 1 – validate (raises ValidationError if payload is bad)
    validate_sensor_payload(payload)

    # Step 2 – normalize (clean up IDs, convert values to float)
    normalized = normalize_sensor_payload(payload)
    sensor_id: str = normalized.sensor_id
    node_id: str = normalized.node_id
    metrics: dict = normalized.metrics

    # Step 3 – generate unique identifiers
    data_id: str = str(uuid.uuid4())                        # unique ID for this record
    object_key: str = generate_object_key(sensor_id, data_id)  # MinIO path: "raw/SENSOR-01/uuid.json"

    # Step 4 – store raw payload to MinIO (object storage backup)
    try:
        store_raw_payload(object_key, payload)
    except Exception as exc:
        raise BackendError(f"Failed to store raw payload: {exc}") from exc

    # Step 5 – persist record in DynamoDB with initial status "pending"
    try:
        insert_record(
            data_id=data_id,
            sensor_id=sensor_id,
            node_id=node_id,
            object_key=object_key,
            metrics=metrics,
        )
    except Exception as exc:
        raise BackendError(f"Failed to insert record: {exc}") from exc

    # Step 6 – fetch the newly created record to confirm it was saved
    try:
        record = get_record(data_id)
    except Exception as exc:
        raise BackendError(f"Failed to retrieve record after insert: {exc}") from exc

    if record is None:
        raise BackendError(
            f"Record {data_id} not found after insert — possible data consistency issue"
        )

    return record



# Listing — return all records from the database


def list_uploads() -> list[dict]:
    """Retrieve all sensor data records. Called by GET /list."""
    try:
        return list_records()
    except Exception as exc:
        raise BackendError(f"Failed to list records: {exc}") from exc



# Summary retrieval — fetch a single record by its data_id


def get_summary_by_id(data_id: str) -> dict:
    """Retrieve one record by data_id. Called by GET /summary?id=<data_id>."""
    try:
        record = get_record(data_id)
    except Exception as exc:
        raise BackendError(f"Failed to retrieve record: {exc}") from exc

    # If no record found, raise 404-style error
    if record is None:
        raise RecordNotFoundError(data_id)

    return record



# Worker helpers — status transitions
#
# These functions manage the record lifecycle. The WORKER calls them
# as it processes jobs:
#   mark_processing()  → pending    → processing
#   mark_completed()   → processing → done (+ attach summary)
#   mark_failed()      → processing → failed (after all retries exhausted)
#
# Each follows the same pattern:
#   1. Check the record exists (guard clause)
#   2. Perform the status update in DynamoDB
#   3. Fetch and return the updated record


def mark_processing(data_id: str) -> dict:
    """Mark a record as 'processing' — worker has started working on it."""
    _ensure_record_exists(data_id)

    try:
        update_record_status(data_id, "processing")
    except Exception as exc:
        raise BackendError(f"Failed to mark record as processing: {exc}") from exc

    # Fetch the updated record to return it
    try:
        record = get_record(data_id)
    except Exception as exc:
        raise BackendError(
            f"Failed to retrieve record after marking processing: {exc}"
        ) from exc

    if record is None:
        raise BackendError(
            f"Record {data_id} not found after marking processing"
        )

    return record


def mark_completed(data_id: str, summary: dict) -> dict:
    """Mark a record as 'done' and attach the computed summary statistics."""
    _ensure_record_exists(data_id)

    # update_record_summary sets both the summary AND the status to "done"
    try:
        update_record_summary(data_id, summary)
    except Exception as exc:
        raise BackendError(f"Failed to mark record as completed: {exc}") from exc

    try:
        record = get_record(data_id)
    except Exception as exc:
        raise BackendError(
            f"Failed to retrieve record after marking completed: {exc}"
        ) from exc

    if record is None:
        raise BackendError(
            f"Record {data_id} not found after marking completed"
        )

    return record


def mark_failed(data_id: str) -> dict:
    """Mark a record as 'failed' — all retry attempts have been exhausted."""
    _ensure_record_exists(data_id)

    try:
        update_record_status(data_id, "failed")
    except Exception as exc:
        raise BackendError(f"Failed to mark record as failed: {exc}") from exc

    try:
        record = get_record(data_id)
    except Exception as exc:
        raise BackendError(
            f"Failed to retrieve record after marking failed: {exc}"
        ) from exc

    if record is None:
        raise BackendError(
            f"Record {data_id} not found after marking failed"
        )

    return record



# Computation — statistical summary functions


def compute_summary(values: list[float]) -> dict:
    """
    Compute min, max, avg, count for a list of numeric values.
    Used for legacy value-list payloads.
    
    Example: [20.5, 21.0, 22.3] → {"min": 20.5, "max": 22.3, "avg": 21.2667, "count": 3}
    """
    if not isinstance(values, list) or len(values) == 0:
        raise ValidationError("compute_summary requires a non-empty list of values")

    summary = SensorSummary(
        min_value=min(values),
        max_value=max(values),
        avg_value=round(mean(values), 4),  # round to 4 decimal places
        count=len(values),
    )
    return summary.to_dict()


def compute_metrics_summary(metrics: dict[str, float], node_id: str) -> dict:
    """
    Compute per-metric summaries from a metrics dictionary.
    Used for the newer metrics-based payloads.
    
    Example input:  {"temperature": 35.2, "humidity": 72.5}, node_id="NODE_TH"
    Example output: {
        "temperature": {"node_id": "NODE_TH", "latest": 35.2, "count": 1},
        "humidity":    {"node_id": "NODE_TH", "latest": 72.5, "count": 1}
    }
    
    For single-reading payloads, we store the latest value and count=1.
    """
    if not isinstance(metrics, dict) or len(metrics) == 0:
        return {}
    
    summary = {}
    for metric_name, value in metrics.items():
        if isinstance(value, (int, float)):
            summary[metric_name] = {
                "node_id": node_id,
                "latest": float(value),
                "count": 1,
            }
    
    return summary



# Internal helpers


def _ensure_record_exists(data_id: str) -> dict:
    """
    Guard clause: check that a record exists before performing updates.
    Raises RecordNotFoundError (→ HTTP 404) if the record doesn't exist.
    """
    try:
        record = get_record(data_id)
    except Exception as exc:
        raise BackendError(f"Failed to look up record: {exc}") from exc

    if record is None:
        raise RecordNotFoundError(data_id)

    return record

