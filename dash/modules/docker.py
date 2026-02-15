import subprocess
import logging


class DockerModule:
    def __init__(self, app, route_prefix="/api/docker"):
        self.app = app
        self.route_prefix = route_prefix
        self.app.add_url_rule(self.route_prefix, "docker_status", self.get_status)

    def get_status(self):
        try:
            # Get all containers with their status and uptime
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "-a",
                    "--format",
                    "{{.ID}}|{{.Names}}|{{.Status}}|{{.State}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                logging.error(f"Docker command failed: {result.stderr}")
                return {"error": "Failed to get Docker status"}

            containers = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("|")
                if len(parts) == 4:
                    container_id, name, status, state = parts
                    containers.append(
                        {
                            "id": container_id,
                            "name": name,
                            "status": status,
                            "state": state,
                        }
                    )

            return {
                "total": len(containers),
                "running": len([c for c in containers if c["state"] == "running"]),
                "containers": containers,
            }

        except subprocess.TimeoutExpired:
            logging.error("Docker command timed out")
            return {"error": "Docker command timed out"}
        except FileNotFoundError:
            logging.error("Docker is not installed or not in PATH")
            return {"error": "Docker not found"}
        except Exception as e:
            logging.error(f"Error getting Docker status: {e}")
            return {"error": str(e)}
