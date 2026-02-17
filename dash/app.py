from dotenv import load_dotenv
import os
import subprocess
import logging
import signal
import sys
import atexit
from pathlib import Path
from flask import Flask, render_template, jsonify

from modules.system import SystemModule
from modules.websites import WebsitesModule
from modules.docker import DockerModule
from modules.uptime import UptimeTracker


commands = {
    "restart-containers": ["docker", "restart", "$(docker ps -q)"],
    "restart-networking": ["systemctl", "restart", "networking"],
    "reboot": ["systemctl", "reboot"],
    "shutdown": ["systemctl", "poweroff"],
}

logging.basicConfig(level=logging.INFO)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

load_dotenv()

app = Flask(__name__)

# Parse URLs, filtering out empty strings
raw_urls = os.getenv("DASH_URLS", "")
app.config["DASH_URLS"] = [url.strip() for url in raw_urls.split(",") if url.strip()]

# Initialize uptime tracker
uptime_tracker = UptimeTracker(
    storage_path=str(Path(__file__).parent / "uptime_data.json"),
    retention_days=30,
)

system_module = SystemModule(app, "/api/system")
websites_module = WebsitesModule(app, "/api/websites", uptime_tracker=uptime_tracker)
docker_module = DockerModule(app, "/api/docker", uptime_tracker=uptime_tracker)


def cleanup_background_threads():
    """Clean up background polling threads on shutdown."""
    logging.info("Shutting down background threads...")
    try:
        system_module.stop_polling()
        logging.info("System module stopped")
    except Exception as e:
        logging.error(f"Error stopping system module: {e}")

    try:
        websites_module.stop_polling()
        logging.info("Websites module stopped")
    except Exception as e:
        logging.error(f"Error stopping websites module: {e}")

    try:
        docker_module.stop_polling()
        logging.info("Docker module stopped")
    except Exception as e:
        logging.error(f"Error stopping docker module: {e}")

    logging.info("Cleanup complete")


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logging.info(f"Received signal {sig}, initiating graceful shutdown...")
    cleanup_background_threads()
    sys.exit(0)


# Register cleanup handlers
atexit.register(cleanup_background_threads)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


@app.route("/api/<cmd>", methods=["POST"])
def run(cmd):
    try:
        if cmd not in commands:
            logging.warning(f"Unknown API command requested: {cmd}")
            return jsonify({"status": "error", "message": "Command not found"}), 404

        full_command = " ".join(commands[cmd])
        logging.info(f"Executing API command: {cmd}")
        logging.debug(f"Full command: {full_command}")
        result = subprocess.run(
            full_command, capture_output=True, text=True, shell=True
        )

        if result.returncode == 0:
            logging.info(f"Command '{cmd}' completed successfully")
            logging.debug(f"Output: {result.stdout}")
            return jsonify({"status": "ok"})
        else:
            logging.error(f"Command '{cmd}' failed: {result.stderr}")
            return jsonify({"status": "error", "message": result.stderr}), 500

    except Exception as e:
        logging.error(f"Exception executing command '{cmd}': {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/")
def index():
    logging.debug("Dashboard page requested")
    return render_template("index.html", urls=websites_module.urls)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
