from backend.exceptions import ValidationError
from backend.models import NormalizedPayload


# validators.py — Input validation and normalization
#
# Two-stage process:
#   1. validate_sensor_payload() → checks the raw dict, raises ValidationError
#   2. normalize_sensor_payload() → cleans and converts to NormalizedPayload
#
# We support TWO payload formats for backward compatibility:
#   New:    { "metrics": {"temperature": 35.2, "humidity": 72.5} }
#   Legacy: { "values": [20.5, 21.0, 22.3] }



def validate_sensor_payload(payload: dict) -> None:
    """
    Stage 1: Validate the raw sensor payload.
    Raises ValidationError if anything is wrong — does NOT modify the data.
    """

    # The payload itself must be a dictionary (not a list, string, etc.)
    if not isinstance(payload, dict):
        raise ValidationError("Payload must be a dictionary")

    # --- node_id checks ---
    # node_id identifies which ESP8266 board sent the data
    if "node_id" not in payload:
        raise ValidationError("node_id is required")

    node_id = payload["node_id"]
    if not isinstance(node_id, str):
        raise ValidationError("node_id must be a string")

    if not node_id.strip():
        raise ValidationError("node_id must not be empty or whitespace")

    # --- sensor_id checks ---
    # sensor_id identifies which sensor hardware (e.g. DHT22, MQ3)
    if "sensor_id" not in payload:
        raise ValidationError("sensor_id is required")

    sensor_id = payload["sensor_id"]
    if not isinstance(sensor_id, str):
        raise ValidationError("sensor_id must be a string")

    if not sensor_id.strip():
        raise ValidationError("sensor_id must not be empty or whitespace")

    # --- metrics checks (new structure) ---
    # metrics is a dict like {"temperature": 35.2, "humidity": 72.5}
    # Each key must be a string, each value must be a number
    if "metrics" in payload:
        metrics = payload["metrics"]
        if not isinstance(metrics, dict):
            raise ValidationError("metrics must be a dictionary")
        for key, val in metrics.items():
            if not isinstance(key, str):
                raise ValidationError("Metric names must be strings")
            if not isinstance(val, (int, float)):
                raise ValidationError(f"Metric '{key}' must be numeric, got {type(val).__name__}")

    # --- values checks (legacy format, kept for backward compatibility) ---
    # values is a simple list of numbers like [20.5, 21.0, 22.3]
    if "values" in payload:
        values = payload["values"]
        if not isinstance(values, list):
            raise ValidationError("values must be a list")

        if len(values) == 0:
            raise ValidationError("values must not be empty")

        # Every element in the list must be a number (int or float)
        for idx, v in enumerate(values):
            if not isinstance(v, (int, float)):
                raise ValidationError(
                    f"All values must be numeric; got {type(v).__name__} at index {idx}"
                )

    # At least one data source must be present — can't have an empty payload
    if "metrics" not in payload and "values" not in payload:
        raise ValidationError("Either metrics (dict) or values (list) must be provided")


def normalize_sensor_payload(payload: dict) -> NormalizedPayload:
    """
    Stage 2: Clean and convert validated payload into a NormalizedPayload.
    - Strips whitespace and uppercases IDs for consistency
    - Converts all values to float
    - Handles both new (metrics) and legacy (values) formats
    """

    # Standardize IDs: "  node_th  " → "NODE_TH"
    node_id = payload["node_id"].strip().upper()
    sensor_id = payload["sensor_id"].strip().upper()
    
    # Handle new metrics format: extract values list from metrics dict
    if "metrics" in payload and payload["metrics"]:
        metrics = {k: float(v) for k, v in payload["metrics"].items()}
        values = list(metrics.values())  # also keep as a flat list for backward compat
    else:
        # Fall back to legacy values format
        values = [float(v) for v in payload.get("values", [])]
        metrics = {}
    
    # Return an immutable NormalizedPayload dataclass
    return NormalizedPayload(
        sensor_id=sensor_id,
        node_id=node_id,
        metrics=metrics,
        values=values,
    )

