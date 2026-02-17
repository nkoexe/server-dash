import json
import os
import logging
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, Optional, Union
from pathlib import Path


class UptimeTracker:
    """
    Tracks uptime for services (websites, docker containers) efficiently.

    Uses a rolling window approach storing aggregated hourly data for the last 30 days.
    This prevents unbounded growth while maintaining accurate uptime statistics.
    """

    def __init__(
        self,
        storage_path: Union[str, Path] = "uptime_data.json",
        retention_days: int = 30,
    ):
        """
        Initialize the uptime tracker.

        Args:
            storage_path: Path to the JSON file for persistent storage (str or Path)
            retention_days: Number of days to retain historical data
        """
        self.storage_path = str(storage_path)
        self.retention_days = retention_days
        self.lock = Lock()  # Thread-safe file operations
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """Load uptime data from storage file with error handling."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    # Validate structure
                    if not isinstance(data, dict):
                        logging.warning(
                            "Invalid uptime data structure, initializing fresh"
                        )
                        return self._init_data_structure()
                    logging.debug(f"Loaded uptime data from {self.storage_path}")
                    return data
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error loading uptime data: {e}, initializing fresh")

        logging.info(f"Initializing new uptime tracker at {self.storage_path}")
        return self._init_data_structure()

    def _init_data_structure(self) -> Dict:
        """Initialize empty data structure."""
        return {
            "websites": {},
            "docker": {},
            "last_cleanup": datetime.now().isoformat(),
        }

    def _save_data(self):
        """Save uptime data to storage file with error handling."""
        try:
            with open(self.storage_path, "w") as f:
                json.dump(self.data, f, indent=2)
            logging.debug("Uptime data saved")
        except IOError as e:
            logging.warning(
                f"Failed to save uptime data (will retry on next update): {e}"
            )

    def _cleanup_old_data(self):
        """Remove data older than retention_days to prevent unbounded growth."""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        cutoff_str = cutoff.isoformat()

        for category in ["websites", "docker"]:
            for service_id in list(self.data[category].keys()):
                service_data = self.data[category][service_id]
                # Remove old entries
                service_data["checks"] = [
                    check
                    for check in service_data.get("checks", [])
                    if check["timestamp"] > cutoff_str
                ]

                # Remove service if no recent data
                if not service_data["checks"]:
                    del self.data[category][service_id]

        self.data["last_cleanup"] = datetime.now().isoformat()

    def _should_cleanup(self) -> bool:
        """Check if cleanup should run (once per day)."""
        last_cleanup = datetime.fromisoformat(
            self.data.get("last_cleanup", "2000-01-01")
        )
        return (datetime.now() - last_cleanup).days >= 1

    def record_check(
        self,
        category: str,
        service_id: str,
        is_up: bool,
        metadata: Optional[Dict] = None,
    ):
        """
        Record a status check for a service.

        Uses aggregation strategy: stores at most one entry per hour to save space.

        Args:
            category: "websites" or "docker"
            service_id: Unique identifier for the service (URL or container name)
            is_up: Whether the service is currently up
            metadata: Optional additional data (e.g., response time, error message)
        """
        with self.lock:
            if category not in self.data:
                self.data[category] = {}

            if service_id not in self.data[category]:
                self.data[category][service_id] = {
                    "checks": [],
                    "first_seen": datetime.now().isoformat(),
                }

            service_data = self.data[category][service_id]
            now = datetime.now()
            current_hour = now.replace(minute=0, second=0, microsecond=0)

            checks = service_data["checks"]

            # Check if we already have an entry for this hour
            if (
                checks
                and datetime.fromisoformat(checks[-1]["timestamp"]).replace(
                    minute=0, second=0, microsecond=0
                )
                == current_hour
            ):
                # Update existing hourly entry (aggregate)
                last_check = checks[-1]
                last_check["up_count"] = last_check.get("up_count", 0) + (
                    1 if is_up else 0
                )
                last_check["total_count"] = last_check.get("total_count", 0) + 1
                last_check["last_status"] = is_up
                last_check["timestamp"] = now.isoformat()
                if metadata:
                    last_check["metadata"] = metadata
            else:
                # Create new hourly entry
                checks.append(
                    {
                        "timestamp": now.isoformat(),
                        "up_count": 1 if is_up else 0,
                        "total_count": 1,
                        "last_status": is_up,
                        "metadata": metadata or {},
                    }
                )

            # Periodic cleanup
            if self._should_cleanup():
                self._cleanup_old_data()

            self._save_data()

    def get_uptime_percentage(
        self, category: str, service_id: str, days: Optional[int] = None
    ) -> Optional[float]:
        """
        Calculate uptime percentage for a service.

        Args:
            category: "websites" or "docker"
            service_id: Unique identifier for the service
            days: Number of days to calculate uptime for (default: all available)

        Returns:
            Uptime percentage (0-100) or None if no data available

        Note: Internal method, assumes caller holds the lock
        """
        if category not in self.data or service_id not in self.data[category]:
            return None

        service_data = self.data[category][service_id]
        checks = service_data.get("checks", [])

        if not checks:
            return None

        # Filter by days if specified (cache cutoff to avoid recalculating)
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            cutoff_iso = cutoff.isoformat()
            checks = [check for check in checks if check["timestamp"] > cutoff_iso]

        if not checks:
            return None

        # Calculate uptime from aggregated data
        total_up = sum(check.get("up_count", 0) for check in checks)
        total_checks = sum(check.get("total_count", 0) for check in checks)

        if total_checks == 0:
            return None

        return (total_up / total_checks) * 100

    def _get_service_stats_internal(
        self, category: str, service_id: str
    ) -> Optional[Dict]:
        """
        Internal method to get service stats. Assumes caller holds the lock.
        """
        if category not in self.data or service_id not in self.data[category]:
            return None

        service_data = self.data[category][service_id]
        checks = service_data.get("checks", [])

        if not checks:
            return {
                "first_seen": service_data.get("first_seen"),
                "current_status": None,
                "uptime_24h": None,
                "uptime_7d": None,
                "uptime_30d": None,
                "uptime_all": None,
            }

        # Calculate all stats in one optimized pass
        now = datetime.now()
        cutoff_24h = (now - timedelta(days=1)).isoformat()
        cutoff_7d = (now - timedelta(days=7)).isoformat()
        cutoff_30d = (now - timedelta(days=30)).isoformat()

        total_up_24h = total_checks_24h = 0
        total_up_7d = total_checks_7d = 0
        total_up_30d = total_checks_30d = 0
        total_up_all = total_checks_all = 0

        for check in checks:
            timestamp = check["timestamp"]
            up_count = check.get("up_count", 0)
            check_count = check.get("total_count", 0)

            # All time
            total_up_all += up_count
            total_checks_all += check_count

            # 30 days
            if timestamp > cutoff_30d:
                total_up_30d += up_count
                total_checks_30d += check_count

                # 7 days
                if timestamp > cutoff_7d:
                    total_up_7d += up_count
                    total_checks_7d += check_count

                    # 24 hours
                    if timestamp > cutoff_24h:
                        total_up_24h += up_count
                        total_checks_24h += check_count

        current_status = checks[-1].get("last_status", False)

        return {
            "first_seen": service_data.get("first_seen"),
            "current_status": current_status,
            "last_check": checks[-1].get("timestamp"),
            "uptime_24h": (
                (total_up_24h / total_checks_24h * 100)
                if total_checks_24h > 0
                else None
            ),
            "uptime_7d": (
                (total_up_7d / total_checks_7d * 100) if total_checks_7d > 0 else None
            ),
            "uptime_30d": (
                (total_up_30d / total_checks_30d * 100)
                if total_checks_30d > 0
                else None
            ),
            "uptime_all": (
                (total_up_all / total_checks_all * 100)
                if total_checks_all > 0
                else None
            ),
            "total_checks": total_checks_all,
        }

    def get_service_stats(self, category: str, service_id: str) -> Optional[Dict]:
        """
        Get comprehensive statistics for a service.

        Returns:
            Dictionary with uptime percentages, first seen date, current status, etc.
        """
        with self.lock:
            return self._get_service_stats_internal(category, service_id)

    def get_all_stats(self, category: str) -> Dict[str, Dict]:
        """
        Get statistics for all services in a category.

        Args:
            category: "websites" or "docker"

        Returns:
            Dictionary mapping service_id to stats
        """
        with self.lock:
            if category not in self.data:
                return {}

            return {
                service_id: self._get_service_stats_internal(category, service_id)
                for service_id in self.data[category].keys()
            }
