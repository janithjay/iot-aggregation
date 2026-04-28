from __future__ import annotations

from dataclasses import dataclass, field


# models.py — Data models for the backend layer
#
# We use Python dataclasses to define structured, immutable data containers.
# frozen=True makes instances read-only after creation, preventing accidental
# modification as data flows through the pipeline.



# --- Model 1: NormalizedPayload ---
# This is the cleaned-up version of raw sensor input after validation.
# The API receives messy user input; this dataclass holds the sanitized form.
@dataclass(frozen=True)
class NormalizedPayload:
    """Normalized sensor payload with node identification and metrics."""
    sensor_id: str                                          # e.g. "DHT22-01" — identifies which sensor hardware
    node_id: str                                            # e.g. "NODE_TH" — identifies which ESP8266 board
    metrics: dict[str, float] = field(default_factory=dict) # new format: {"temperature": 35.2, "humidity": 72.5}
    values: list[float] = field(default_factory=list)       # legacy format: [20.5, 21.0, 22.3]


# --- Model 2: SensorSummary ---
# Holds computed statistics (min, max, avg, count) for legacy value-list payloads.
# The worker computes these stats and stores them in the database.
@dataclass(frozen=True)
class SensorSummary:
    """Summary statistics for a single value list."""
    min_value: float   # smallest reading in the batch
    max_value: float   # largest reading in the batch
    avg_value: float   # arithmetic mean of all readings
    count: int         # how many readings were in the batch

    def to_dict(self) -> dict:
        """Convert summary to dictionary so it can be stored in DynamoDB as a map."""
        return {
            "min": self.min_value,
            "max": self.max_value,
            "avg": self.avg_value,
            "count": self.count,
        }


# --- Model 3: MetricSummary ---
# Holds per-metric statistics for the newer metrics-based payloads.
# Each named metric (temperature, humidity, etc.) gets its own summary.
@dataclass(frozen=True)
class MetricSummary:
    """Summary statistics for individual metrics with time windows."""
    node_id: str        # which node sent this metric
    metric_name: str    # e.g. "temperature", "humidity"
    latest: float       # most recent reading value
    min_value: float
    max_value: float
    avg_value: float
    count: int          # number of readings aggregated
    
    def to_dict(self) -> dict:
        """Convert metric summary to dictionary for JSON serialization."""
        return {
            "node_id": self.node_id,
            "metric": self.metric_name,
            "latest": self.latest,
            "min": self.min_value,
            "max": self.max_value,
            "avg": self.avg_value,
            "count": self.count,
        }


# --- Helper: generate the MinIO storage path for raw sensor data ---
# Format: "raw/<SENSOR_ID>/<DATA_ID>.json"
# Example: "raw/DHT22-01/550e8400-e29b-41d4-a716-446655440000.json"
def generate_object_key(sensor_id: str, data_id: str) -> str:
   
    return f"raw/{sensor_id}/{data_id}.json"
