"""
app.py
------
Flask backend. It connects three things:
  frontend (HTML/JS)  <->  this API  <->  schedulers.py + SQLite database

Run from the backend/ folder:   python app.py
Then open:                      http://127.0.0.1:5000
"""

import os

from flask import Flask, jsonify, request

from dsa.schedulers import validate_processes, run_algorithm, compare_all, to_int
from db import database

# Serve the frontend folder from Flask, so no CORS setup is needed.
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

database.init_db()   # make sure tables exist when the server starts

SAMPLE_PROCESSES = [
    {"pid": "P1", "arrival": 0, "burst": 5, "priority": 2},
    {"pid": "P2", "arrival": 1, "burst": 3, "priority": 1},
    {"pid": "P3", "arrival": 2, "burst": 8, "priority": 4},
    {"pid": "P4", "arrival": 3, "burst": 6, "priority": 3},
]


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
@app.errorhandler(ValueError)
def handle_value_error(error):
    """Any ValueError (bad input, duplicate PID...) becomes a 400 JSON message."""
    return jsonify({"error": str(error)}), 400


def clean_process(data):
    """Validate one process dict (uses the same checks as the schedulers)."""
    return validate_processes([{
        "pid": data.get("pid", ""),
        "arrival": data.get("arrival"),
        "burst": data.get("burst"),
        "priority": data.get("priority", 0),
    }])[0]


def read_quantum():
    """Read the time quantum from the JSON body (default 2)."""
    data = request.get_json(silent=True) or {}
    return to_int(data.get("quantum", 2), "Time quantum")


# ---------------------------------------------------------------
# Frontend page
# ---------------------------------------------------------------
@app.route("/")
def home():
    return app.send_static_file("index.html")


# ---------------------------------------------------------------
# Process routes
# ---------------------------------------------------------------
@app.route("/api/processes", methods=["GET"])
def list_processes():
    return jsonify(database.get_processes())


@app.route("/api/processes", methods=["POST"])
def create_process():
    p = clean_process(request.get_json(silent=True) or {})
    database.add_process(p["pid"], p["arrival"], p["burst"], p["priority"])
    return jsonify(p), 201


@app.route("/api/processes/<pid>", methods=["PUT"])
def edit_process(pid):
    data = request.get_json(silent=True) or {}
    data["pid"] = pid                      # PID comes from the URL
    p = clean_process(data)
    if not database.update_process(pid, p["arrival"], p["burst"], p["priority"]):
        return jsonify({"error": "Process not found"}), 404
    return jsonify(p)


@app.route("/api/processes/<pid>", methods=["DELETE"])
def remove_process(pid):
    if not database.delete_process(pid):
        return jsonify({"error": "Process not found"}), 404
    return jsonify({"deleted": pid})


@app.route("/api/processes", methods=["DELETE"])
def remove_all_processes():
    database.clear_processes()
    return jsonify({"deleted": "all"})


@app.route("/api/processes/sample", methods=["POST"])
def load_sample():
    """Replace the process list with 4 demo processes."""
    database.clear_processes()
    for p in SAMPLE_PROCESSES:
        database.add_process(p["pid"], p["arrival"], p["burst"], p["priority"])
    return jsonify(database.get_processes())


# ---------------------------------------------------------------
# Simulation routes
# ---------------------------------------------------------------
@app.route("/api/simulate", methods=["POST"])
def simulate():
    """Run ONE algorithm on the saved processes and store the run."""
    data = request.get_json(silent=True) or {}
    algorithm = str(data.get("algorithm", "")).upper()
    quantum = read_quantum()

    result = run_algorithm(algorithm, database.get_processes(), quantum)
    used_quantum = quantum if algorithm == "RR" else None
    result["run_id"] = database.save_run(result, used_quantum)
    return jsonify(result)


@app.route("/api/compare", methods=["POST"])
def compare():
    """Run ALL algorithms on the saved processes and store each run."""
    quantum = read_quantum()
    comparison = compare_all(database.get_processes(), quantum)
    for result in comparison["results"]:
        used_quantum = quantum if result["algorithm"] == "RR" else None
        result["run_id"] = database.save_run(result, used_quantum)
    return jsonify(comparison)


# ---------------------------------------------------------------
# History routes
# ---------------------------------------------------------------
@app.route("/api/runs", methods=["GET"])
def list_runs():
    return jsonify(database.get_runs())


@app.route("/api/runs/<int:run_id>", methods=["GET"])
def show_run(run_id):
    run = database.get_run(run_id)
    if run is None:
        return jsonify({"error": "Run not found"}), 404
    return jsonify(run)


@app.route("/api/runs", methods=["DELETE"])
def remove_runs():
    database.clear_runs()
    return jsonify({"deleted": "all"})


if __name__ == "__main__":
    app.run(debug=True)
