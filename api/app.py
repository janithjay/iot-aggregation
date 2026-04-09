from flask import Flask, jsonify, request
import json
import uuid

from backend.service import build_upload_payload
from db.database import (
    create_table_if_not_exists,
    get_record,
    insert_record,
    list_records,
)

app = Flask(__name__)
create_table_if_not_exists()


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/data", methods=["POST"])
def receive_data():
    body = request.get_json(silent=True) or {}
    payload = build_upload_payload(body.get("sensor_id"), body.get("values"))

    data_id = str(uuid.uuid4())
    object_key = f"uploads/{data_id}.json"

    # Starter behavior: this stores payload metadata only.
    insert_record(data_id, payload["sensor_id"], object_key)

    return jsonify({"data_id": data_id, "status": "pending", "payload": payload}), 202


@app.route("/summary")
def summary():
    data_id = request.args.get("id")
    if not data_id:
        return jsonify({"error": "id is required"}), 400

    record = get_record(data_id)
    if not record:
        return jsonify({"error": "not found"}), 404

    return jsonify(record)


@app.route("/list")
def list_uploads():
    return jsonify(list_records())


if __name__ == "__main__":
    # Use default port for starter scaffold.
    app.run(host="0.0.0.0", port=5000, debug=True)
