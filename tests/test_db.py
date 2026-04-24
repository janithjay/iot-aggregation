from db import database


def _configure_local_dynamo_for_host_tests():
    database.DYNAMO_ENDPOINT = "http://localhost:8000"
    database.USE_LOCAL = True
    database._table = None


def test_insert_record_stores_data():
    _configure_local_dynamo_for_host_tests()
    data_id = "test-id"
    database.insert_record(data_id, "sensor-1", "NODE_TH", "uploads/test-id.json")
    record = database.get_record(data_id)
    assert record is not None
    assert record["data_id"] == data_id
