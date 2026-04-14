from backend.exceptions import ValidationError
from backend.models import NormalizedPayload


def validate_sensor_payload(payload: dict) -> None:
    if not isinstance(payload, dict):
        raise ValidationError("Payload must be a dictionary")

    # --- sensor_id checks ---
    if "sensor_id" not in payload:
        raise ValidationError("sensor_id is required")

    sensor_id = payload["sensor_id"]
    if not isinstance(sensor_id, str):
        raise ValidationError("sensor_id must be a string")

    if not sensor_id.strip():
        raise ValidationError("sensor_id must not be empty or whitespace")

    # --- values checks ---
    if "values" not in payload:
        raise ValidationError("values is required")

    values = payload["values"]
    if not isinstance(values, list):
        raise ValidationError("values must be a list")

    if len(values) == 0:
        raise ValidationError("values must not be empty")

    for idx, v in enumerate(values):
        if not isinstance(v, (int, float)):
            raise ValidationError(
                f"All values must be numeric; got {type(v).__name__} at index {idx}"
            )


def normalize_sensor_payload(payload: dict) -> NormalizedPayload:
    return NormalizedPayload(
        sensor_id=payload["sensor_id"].strip().upper(),
        values=[float(v) for v in payload["values"]],
    )
