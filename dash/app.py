from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
import os
import psutil
import subprocess


commands = {
    "restart-containers": ["docker-compose", "restart"],
    "update-containers": ["docker-compose", "pull"],
    "update-app": ["git", "pull"],
    "restart-networking": ["systemctl", "restart", "networking"],
    "reboot": ["reboot"],
}


app = Flask(__name__)

load_dotenv()

urls = os.getenv("DASH_URLS", "")
if urls:
    urls = urls.split(",")


@app.route("/api/stats")
def get_stats():
    try:
        with open("/var/log/power.log", "r") as file:
            power = float(file.readlines()[-1].strip().split(",")[-1])
    except Exception:
        power = "nan"

    return jsonify(
        {
            "cpu": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory()._asdict(),
            "disk": psutil.disk_usage("/")._asdict(),
            "power": power,
        }
    )


@app.route("/api/restart-containers", methods=["POST"])
def restart_containers():
    try:
        result = subprocess.run(
            ["docker-compose", "restart"], capture_output=True, text=True
        )

        if result.returncode == 0:
            return jsonify({"status": "ok"})
        else:
            return jsonify({"status": "error", "message": result.stderr}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/restart-networking", methods=["POST"])
def restart_network():
    try:
        result = subprocess.run(
            ["systemctl", "restart", "networking"], capture_output=True, text=True
        )

        if result.returncode == 0:
            return jsonify({"status": "ok"})
        else:
            return jsonify({"status": "error", "message": result.stderr}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/reboot", methods=["POST"])
def reboot():
    try:
        result = subprocess.run(["reboot"], capture_output=True, text=True)

        if result.returncode == 0:
            return jsonify({"status": "ok"})
        else:
            return jsonify({"status": "error", "message": result.stderr}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/")
def index():
    return render_template("index.html", urls=urls)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
