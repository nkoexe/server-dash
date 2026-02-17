import subprocess
import logging
import threading
import time


class DockerModule:
    def __init__(
        self, app, route_prefix="/api/docker", uptime_tracker=None, poll_interval=10
    ):
        self.app = app
        self.route_prefix = route_prefix
        self.app.add_url_rule(self.route_prefix, "docker_status", self.get_status)
        self.app.add_url_rule(
            f"{self.route_prefix}/uptime", "docker_uptime", self.get_uptime
        )
        self.uptime_tracker = uptime_tracker
        self.poll_interval = poll_interval

        # Cached data
        self._cache = {"error": "Docker status not yet available"}
        self._cache_lock = threading.Lock()

        # Start background polling
        self._polling = True
        self._poll_thread = threading.Thread(target=self._background_poll, daemon=True)
        self._poll_thread.start()
        logging.info("Docker module started")

    def _background_poll(self):
        """Background thread that continuously polls Docker status."""
        while self._polling:
            try:
                new_status = self._fetch_docker_status()

                with self._cache_lock:
                    self._cache = new_status

            except Exception as e:
                logging.error(f"Error in Docker background poll: {e}")
                with self._cache_lock:
                    self._cache = {"error": f"Background polling error: {str(e)}"}

            time.sleep(self.poll_interval)

    def _fetch_docker_status(self):
        """Fetch Docker status synchronously (called by background thread)."""
        try:
            logging.debug("Fetching Docker container status")
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
                logging.warning(f"Docker command failed: {result.stderr}")
                return {"error": "Failed to get Docker status"}

            containers = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("|")
                if len(parts) == 4:
                    container_id, name, status, state = parts
                    is_running = state == "running"

                    containers.append(
                        {
                            "id": container_id,
                            "name": name,
                            "status": status,
                            "state": state,
                        }
                    )

                    # Record uptime check for each container
                    if self.uptime_tracker:
                        self.uptime_tracker.record_check(
                            category="docker",
                            service_id=name,
                            is_up=is_running,
                            metadata={"container_id": container_id, "status": status},
                        )

            logging.debug(
                f"Docker: {len([c for c in containers if c['state'] == 'running'])}/{len(containers)} containers running"
            )

            return {
                "total": len(containers),
                "running": len([c for c in containers if c["state"] == "running"]),
                "containers": containers,
            }

        except subprocess.TimeoutExpired:
            logging.warning("Docker command timed out")
            return {"error": "Docker command timed out"}
        except FileNotFoundError:
            logging.warning("Docker is not installed or not in PATH")
            return {"error": "Docker not found"}
        except Exception as e:
            logging.error(f"Unexpected error getting Docker status: {e}")
            return {"error": str(e)}

    def get_status(self):
        """Return cached Docker status (instant response)."""
        with self._cache_lock:
            return self._cache.copy()

    def stop_polling(self):
        """Stop the background polling thread (for cleanup)."""
        self._polling = False
        if self._poll_thread.is_alive():
            self._poll_thread.join(timeout=2)
            logging.info("Docker polling stopped")

    def get_uptime(self):
        """Get uptime statistics for all monitored Docker containers."""
        if not self.uptime_tracker:
            return {"error": "Uptime tracking not enabled"}

        return self.uptime_tracker.get_all_stats("docker")
