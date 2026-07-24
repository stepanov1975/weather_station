import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from weather_display.services.json_cache import JsonCache


def test_json_cache_stores_and_reloads_payload(tmp_path: Path) -> None:
    cache_path = tmp_path / "forecast.json"
    payload = {"data": {"title": "Hadera"}}

    cache = JsonCache(cache_path)
    cache.store(payload)

    reloaded = JsonCache(cache_path)

    assert reloaded.payload == payload
    assert reloaded.timestamp == cache.timestamp
    assert reloaded.is_valid(max_age_seconds=60)


def test_json_cache_rejects_stale_payload(tmp_path: Path) -> None:
    cache_path = tmp_path / "forecast.json"
    cache_path.write_text(
        json.dumps({"timestamp": time.time() - 120, "payload": {"data": {}}}),
        encoding="utf-8",
    )

    cache = JsonCache(cache_path)

    assert cache.payload == {"data": {}}
    assert not cache.is_valid(max_age_seconds=60)


def test_json_cache_ignores_unreadable_json(tmp_path: Path) -> None:
    cache_path = tmp_path / "forecast.json"
    cache_path.write_text("{not json", encoding="utf-8")

    cache = JsonCache(cache_path)

    assert cache.payload is None
    assert cache.timestamp is None
    assert not cache.is_valid(max_age_seconds=60)


def test_json_cache_ignores_invalid_cache_shape(tmp_path: Path) -> None:
    cache_path = tmp_path / "forecast.json"
    cache_path.write_text(
        json.dumps({"timestamp": "not-a-number", "payload": ["not", "a", "dict"]}),
        encoding="utf-8",
    )

    cache = JsonCache(cache_path)

    assert cache.payload is None
    assert cache.timestamp is None
    assert not cache.is_valid(max_age_seconds=60)


def test_json_cache_ignores_non_object_json(tmp_path: Path) -> None:
    cache_path = tmp_path / "forecast.json"
    cache_path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

    cache = JsonCache(cache_path)

    assert cache.payload is None
    assert cache.timestamp is None
    assert not cache.is_valid(max_age_seconds=60)


def test_json_cache_keeps_previous_file_when_atomic_replace_fails(tmp_path: Path) -> None:
    cache_path = tmp_path / "forecast.json"
    cache = JsonCache(cache_path)
    cache.store({"data": {"title": "old"}})

    with (
        patch("weather_display.services.json_cache.os.replace", side_effect=OSError("replace failed")),
        pytest.raises(OSError, match="replace failed"),
    ):
        cache.store({"data": {"title": "new"}})

    assert JsonCache(cache_path).payload == {"data": {"title": "old"}}
