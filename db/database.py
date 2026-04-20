from __future__ import annotations

import os
from datetime import datetime, timezone

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = Exception

TABLE_NAME = os.getenv("DYNAMO_TABLE", "iot_data")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DYNAMO_ENDPOINT = os.getenv("DYNAMO_ENDPOINT", "http://dynamodb-local:8000")
USE_LOCAL = os.getenv("USE_LOCAL", "true").lower() == "true"

_IN_MEMORY_STORE: dict[str, dict] = {}
_table = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _using_in_memory() -> bool:
    return boto3 is None


def _build_boto_kwargs() -> dict:
    kwargs = {"region_name": AWS_REGION}
    if USE_LOCAL and DYNAMO_ENDPOINT:
        kwargs["endpoint_url"] = DYNAMO_ENDPOINT
        kwargs["aws_access_key_id"] = os.getenv("AWS_ACCESS_KEY_ID", "fake")
        kwargs["aws_secret_access_key"] = os.getenv("AWS_SECRET_ACCESS_KEY", "fake")
    return kwargs


def _get_table():
    global _table
    if _using_in_memory():
        return None
    if _table is None:
        dynamodb = boto3.resource("dynamodb", **_build_boto_kwargs())
        _table = dynamodb.Table(TABLE_NAME)
    return _table


def create_table_if_not_exists() -> bool:
    if _using_in_memory():
        return True

    client = boto3.client("dynamodb", **_build_boto_kwargs())
    try:
        client.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{"AttributeName": "data_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "data_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
    except Exception as exc:
        if isinstance(exc, ClientError):
            code = exc.response.get("Error", {}).get("Code")
            if code == "ResourceInUseException":
                return True
        raise
    return True


def insert_record(data_id: str, sensor_id: str, object_key: str):
    item = {
        "data_id": data_id,
        "sensor_id": sensor_id,
        "object_key": object_key,
        "status": "pending",
        "summary": {},
        "timestamp": _now_iso(),
    }
    if _using_in_memory():
        _IN_MEMORY_STORE[data_id] = item
        return

    _get_table().put_item(Item=item)


def update_record_status(data_id: str, status: str):
    if _using_in_memory():
        if data_id in _IN_MEMORY_STORE:
            _IN_MEMORY_STORE[data_id]["status"] = status
        return

    _get_table().update_item(
        Key={"data_id": data_id},
        UpdateExpression="SET #s = :s",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": status},
    )


def update_record_summary(data_id: str, summary: dict):
    if _using_in_memory():
        if data_id in _IN_MEMORY_STORE:
            _IN_MEMORY_STORE[data_id]["summary"] = summary
            _IN_MEMORY_STORE[data_id]["status"] = "done"
        return

    _get_table().update_item(
        Key={"data_id": data_id},
        UpdateExpression="SET summary = :sum, #s = :done",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":sum": summary, ":done": "done"},
    )


def get_record(data_id: str):
    if _using_in_memory():
        return _IN_MEMORY_STORE.get(data_id)

    response = _get_table().get_item(Key={"data_id": data_id})
    return response.get("Item")


def list_records():
    if _using_in_memory():
        return list(_IN_MEMORY_STORE.values())

    response = _get_table().scan()
    return response.get("Items", [])