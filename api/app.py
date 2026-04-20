from flask import Flask, jsonify, request
import sys

# Ensure project root modules (backend/, db/, shared/) are importable in container.
sys.path.insert(0, "/app")

from backend.exceptions import BackendError, RecordNotFoundError, ValidationError
from backend.services import get_summary_by_id, ingest_sensor_payload, list_uploads as service_list_uploads
from db.database import create_table_if_not_exists

app = Flask(__name__)
create_table_if_not_exists()


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/data", methods=["POST"])
def receive_data():
    body = request.get_json(silent=True) or {}
    try:
        record = ingest_sensor_payload(body)
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400
    except BackendError as exc:
        return jsonify({"error": str(exc)}), 500

    return (
        jsonify({"data_id": record["data_id"], "status": record.get("status", "pending")}),
        202,
    )


@app.route("/summary")
def summary():
    data_id = request.args.get("id")
    if not data_id:
        return jsonify({"error": "id is required"}), 400

    try:
        record = get_summary_by_id(data_id)
    except RecordNotFoundError:
        return jsonify({"error": "not found"}), 404
    except BackendError as exc:
        return jsonify({"error": str(exc)}), 500

    return jsonify(record)


@app.route("/list")
def list_uploads():
    try:
        return jsonify(service_list_uploads())
    except BackendError as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    # Use default port for starter scaffold.
    app.run(host="0.0.0.0", port=5000, debug=True)
