from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from requests import get
from time import time
import os
import psutil
import subprocess
import logging


commands = {
    "restart-containers": ["docker", "restart", "$(docker ps -q)"],
    "restart-networking": ["systemctl", "restart", "networking"],
    "reboot": ["systemctl", "reboot"],
    "shutdown": ["systemctl", "poweroff"],
}

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

load_dotenv()

# power = "nan"
# last_power_check = 0
# power_check_interval = 5 * 60

urls = os.getenv("DASH_URLS", "")
if urls:
    urls = urls.split(",")

logging.info(f"URLs: {urls}")


def get_power(avg: bool = False):
    # try:
    #     with open("/var/log/power.csv", "r") as file:
    #         if not avg:
    #             pwrstr = file.readlines()[-1].strip().split(",")[-1]
    #             try:
    #                 return float(pwrstr)
    #             except ValueError:
    #                 pass

    #             return "nan"

    #         pwrlist = [line.strip().split(",")[-1] for line in file.readlines()]

    #         take = 10
    #         i = 0
    #         pwrsum = 0
    #         while take > 0:
    #             i += 1
    #             try:
    #                 pwrsum += float(pwrlist[-i])
    #                 take -= 1
    #             except ValueError:
    #                 pass
    #             finally:
    #                 if i == len(pwrlist):
    #                     break

    #         if pwrsum == 0:
    #             return "nan"

    #         return pwrsum / (10 - take)

    # except Exception as e:
    #     logging.error(e)
    #     return "nan"

    # Average consumption of my laptop, hardcode until better configuration
    return 9


@app.route("/api/website", methods=["POST"])
def get_website():
    url = request.json["url"]
    logging.debug(f"Getting website: {url}")

    try:
        response = get(url)
        if response.status_code == 200:
            return jsonify({"status": "up"})
        else:
            logging.error(f"Website down: {url}")
            return jsonify({"status": "down"})
    except Exception as e:
        logging.error(e)
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/stats")
def get_stats():
    # global last_power_check, power
    # if time() - last_power_check > power_check_interval:
    #     last_power_check = time()
    power = get_power(False)

    return jsonify(
        {
            "cpu": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory()._asdict(),
            "disk": psutil.disk_usage("/")._asdict(),
            "power": power,
        }
    )


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
    return render_template("index.html", urls=urls)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
