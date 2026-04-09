from datetime import datetime, timezone


def normalize_values(raw_values):
    """Normalize incoming values into floats and skip invalid entries."""
    clean = []
    for value in raw_values or []:
        try:
            clean.append(float(value))
        except (TypeError, ValueError):
            continue
    return clean


def build_upload_payload(sensor_id, values):
    """Build a normalized upload payload used by the API layer."""
    return {
        "sensor_id": sensor_id or "unknown",
        "values": normalize_values(values),
        "received_at": datetime.now(timezone.utc).isoformat(),
    }
