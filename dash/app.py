from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
import os
import psutil
import subprocess
import logging


commands = {
    "restart-containers": ["sh", "-c", "docker restart $(docker ps -q)"],
    "restart-networking": ["systemctl", "restart", "networking"],
    "update-dash": ["git", "pull"],
    "restart-dash": ["systemctl", "restart", "server-dash"],
    "reboot": ["systemctl", "reboot"],
    "shutdown": ["shutdown", "-h", "now"],
}

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

load_dotenv()

urls = os.getenv("DASH_URLS", "")
if urls:
    urls = urls.split(",")

logging.info(f"URLs: {urls}")


@app.route("/api/stats")
def get_stats():
    try:
        with open("/var/log/power.csv", "r") as file:
            power = float(file.readlines()[-1].strip().split(",")[-1])
    except Exception as e:
        logging.error(e)
        power = "nan"

    return jsonify(
        {
            "cpu": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory()._asdict(),
            "disk": psutil.disk_usage("/")._asdict(),
            "power": power,
        }
    )


@app.route("/api/<cmd>", methods=["POST"])
def update_dash(cmd):
    try:
        logging.info(f"Running command: {commands[cmd]}")
        result = subprocess.run(commands[cmd], capture_output=True, text=True)

        if result.returncode == 0:
            logging.info("ok: " + result.stdout)
            return jsonify({"status": "ok"})
        else:
            logging.error(result.stderr)
            return jsonify({"status": "error", "message": result.stderr}), 500
    except Exception as e:
        logging.error(e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/")
def index():
    return render_template("index.html", urls=urls)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
