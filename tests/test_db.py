from db.database import insert_record, get_record


def test_insert_record_stores_data():
    data_id = "test-id"
    insert_record(data_id, "sensor-1", "uploads/test-id.json")
    record = get_record(data_id)
    assert record is not None
    assert record["data_id"] == data_id
