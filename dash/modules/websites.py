import logging
import threading
import time

try:
    from requests import get
except ImportError:
    logging.error("requests library not installed. Install with: pip install requests")
    raise


class WebsitesModule:
    def __init__(
        self, app, route_prefix="/api/websites", uptime_tracker=None, poll_interval=30
    ):
        self.app = app
        self.route_prefix = route_prefix
        self.app.add_url_rule(self.route_prefix, "websites", self.get_websites)
        self.app.add_url_rule(
            f"{self.route_prefix}/uptime", "websites_uptime", self.get_uptime
        )

        self.urls = app.config.get("DASH_URLS", [])
        self.uptime_tracker = uptime_tracker
        self.poll_interval = poll_interval

        # Cached data
        self._cache = {}
        self._cache_lock = threading.Lock()

        # Start background polling if URLs configured
        if self.urls:
            self._polling = True
            self._poll_thread = threading.Thread(
                target=self._background_poll, daemon=True
            )
            self._poll_thread.start()
            logging.info(f"Websites module started, monitoring {len(self.urls)} URL(s)")
        else:
            self._polling = False
            self._poll_thread = None
            logging.info("Websites module started with no URLs configured")

    def _background_poll(self):
        """Background thread that continuously polls website status."""
        while self._polling:
            try:
                new_status = self._fetch_website_status()

                with self._cache_lock:
                    self._cache = new_status

            except Exception as e:
                logging.error(f"Error in websites background poll: {e}")
                with self._cache_lock:
                    self._cache = {"error": f"Background polling error: {str(e)}"}

            time.sleep(self.poll_interval)

    def _fetch_website_status(self):
        """Fetch website status synchronously (called by background thread)."""
        if not self.urls:
            return {"error": "No URLs configured"}

        status = {}

        for url in self.urls:
            logging.debug(f"Checking website: {url}")

            try:
                response = get(url, timeout=5)
                is_up = response.status_code == 200
                status[url] = "up" if is_up else "down"

                logging.debug(
                    f"Website {url}: {status[url]} (HTTP {response.status_code})"
                )

                # Record uptime check
                if self.uptime_tracker:
                    self.uptime_tracker.record_check(
                        category="websites",
                        service_id=url,
                        is_up=is_up,
                        metadata={"status_code": response.status_code},
                    )
            except Exception as e:
                logging.warning(f"Website {url} unreachable: {e}")
                status[url] = "down"

                # Record failed check
                if self.uptime_tracker:
                    self.uptime_tracker.record_check(
                        category="websites",
                        service_id=url,
                        is_up=False,
                        metadata={"error": str(e)},
                    )

        return status

    def get_websites(self):
        """Return cached website status (instant response)."""
        if not self.urls:
            return {"error": "No URLs configured"}

        with self._cache_lock:
            # Return cache if available, otherwise return empty dict with note
            if self._cache:
                return self._cache.copy()
            else:
                return {url: "checking" for url in self.urls}

    def stop_polling(self):
        """Stop the background polling thread (for cleanup)."""
        self._polling = False
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=2)
            logging.info("Websites polling stopped")

    def get_uptime(self):
        """Get uptime statistics for all monitored websites."""
        if not self.uptime_tracker:
            return {"error": "Uptime tracking not enabled"}

        return self.uptime_tracker.get_all_stats("websites")
