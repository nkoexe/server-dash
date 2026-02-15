from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
import os
import subprocess
import logging

from modules.system import SystemModule
from modules.websites import WebsitesModule
from modules.docker import DockerModule


commands = {
    "restart-containers": ["docker", "restart", "$(docker ps -q)"],
    "restart-networking": ["systemctl", "restart", "networking"],
    "reboot": ["systemctl", "reboot"],
    "shutdown": ["systemctl", "poweroff"],
}

logging.basicConfig(level=logging.DEBUG)
load_dotenv()

app = Flask(__name__)

app.config["DASH_URLS"] = os.getenv("DASH_URLS", "").split(",")


system_module = SystemModule(app, "/api/system")
websites_module = WebsitesModule(app, "/api/websites")
docker_module = DockerModule(app, "/api/docker")


@app.route("/api/<cmd>", methods=["POST"])
def run(cmd):
    try:
        if cmd not in commands:
            return jsonify({"status": "error", "message": "Command not found"}), 404

        full_command = " ".join(commands[cmd])
        logging.info(f"Running command: {full_command}")
        result = subprocess.run(
            full_command, capture_output=True, text=True, shell=True
        )

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
    return render_template("index.html", urls=websites_module.urls)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
