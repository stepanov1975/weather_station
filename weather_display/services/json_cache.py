"""Small JSON cache used by weather services for offline resilience."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class JsonCache:
    """Persist one JSON-serializable payload with a timestamp."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.payload: dict[str, Any] | None = None
        self.timestamp: float | None = None
        self.load()

    def is_valid(self, max_age_seconds: int) -> bool:
        return (
            self.payload is not None
            and self.timestamp is not None
            and (time.time() - self.timestamp) < max_age_seconds
        )

    def store(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.timestamp = time.time()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        cache_data = {"timestamp": self.timestamp, "payload": payload}
        self.path.write_text(json.dumps(cache_data), encoding="utf-8")

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            cache_data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Ignoring unreadable cache file %s: %s", self.path, exc)
            return

        if not isinstance(cache_data, dict):
            logger.warning("Ignoring invalid cache file %s: expected JSON object", self.path)
            return

        payload = cache_data.get("payload")
        timestamp = cache_data.get("timestamp")
        if isinstance(payload, dict) and isinstance(timestamp, (int, float)):
            self.payload = payload
            self.timestamp = float(timestamp)
