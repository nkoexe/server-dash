import psutil
import logging
import threading
import time


class SystemModule:
    def __init__(self, app, route_prefix="/api/system", poll_interval=2):
        self.app = app
        self.route_prefix = route_prefix
        self.app.add_url_rule(self.route_prefix, "system_stats", self.get_stats)
        self.poll_interval = poll_interval

        # Cached data
        self._cache = {"cpu": 0, "memory": {}, "disk": {}, "power": "nan"}
        self._cache_lock = threading.Lock()

        # Start background polling
        self._polling = True
        self._poll_thread = threading.Thread(target=self._background_poll, daemon=True)
        self._poll_thread.start()
        logging.info("System monitoring started")

    def _background_poll(self):
        """Background thread that continuously polls system stats."""
        while self._polling:
            try:
                new_stats = self._fetch_system_stats()

                with self._cache_lock:
                    self._cache = new_stats

                logging.debug(
                    f"System stats: CPU {new_stats['cpu']}%, Memory {new_stats['memory']['percent']}%, Disk {new_stats['disk']['percent']}%"
                )

            except Exception as e:
                # Log at debug level as this is routine and recoverable
                logging.debug(f"Error fetching system stats (will retry): {e}")

            time.sleep(self.poll_interval)

    def _fetch_system_stats(self):
        """Fetch system statistics synchronously (called by background thread)."""
        power = self.get_power(False)

        return {
            "cpu": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory()._asdict(),
            "disk": psutil.disk_usage("/")._asdict(),
            "power": power,
        }

    def get_stats(self):
        """Return cached system stats (instant response)."""
        with self._cache_lock:
            return self._cache.copy()

    def stop_polling(self):
        """Stop the background polling thread (for cleanup)."""
        self._polling = False
        if self._poll_thread.is_alive():
            self._poll_thread.join(timeout=2)
            logging.info("System monitoring stopped")

    def get_power(self, avg: bool = False):
        """
        Get power consumption in watts.

        Args:
            avg: Whether to return average of last 10 readings (not implemented)

        Returns:
            Power consumption in watts (currently hardcoded)

        TODO: Implement actual power monitoring via /var/log/power.csv
        """
        # Average consumption of my laptop, hardcoded until better configuration
        return 9
