from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class NormalizedPayload:
   
    sensor_id: str
    values: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class SensorSummary:
    

    min_value: float
    max_value: float
    avg_value: float
    count: int

    def to_dict(self) -> dict:
        
        return {
            "min": self.min_value,
            "max": self.max_value,
            "avg": self.avg_value,
            "count": self.count,
        }


def generate_object_key(sensor_id: str, data_id: str) -> str:

    return f"raw/{sensor_id}/{data_id}.json"
