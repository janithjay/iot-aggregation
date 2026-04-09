from datetime import datetime, timezone

# In-memory starter store for local development before DynamoDB is wired.
_STORE = {}


def create_table_if_not_exists():
    # No-op for starter scaffold.
    return True


def insert_record(data_id, sensor_id, object_key):
    _STORE[data_id] = {
        "data_id": data_id,
        "sensor_id": sensor_id,
        "object_key": object_key,
        "status": "pending",
        "summary": {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def update_record_status(data_id, status):
    if data_id in _STORE:
        _STORE[data_id]["status"] = status


def update_record_summary(data_id, summary):
    if data_id in _STORE:
        _STORE[data_id]["summary"] = summary
        _STORE[data_id]["status"] = "done"


def get_record(data_id):
    return _STORE.get(data_id)


def list_records():
    return list(_STORE.values())
