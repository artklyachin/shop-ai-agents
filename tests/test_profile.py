import json
import pytest
from pathlib import Path

from agents_booking.profile import load_profile, save_profile, PROFILE_ALLOWED_KEYS


def test_load_missing_file(tmp_path):
    result = load_profile(tmp_path / "nonexistent.json")
    assert result == {}


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "profile.json"
    data = {"name": "Anna", "brand": "Sony", "max_price": "200"}
    save_profile(data, path)
    loaded = load_profile(path)
    assert loaded == data


def test_save_filters_unknown_keys(tmp_path):
    path = tmp_path / "profile.json"
    data = {"name": "Boris", "unknown_key": "value", "another": 123}
    save_profile(data, path)
    loaded = load_profile(path)
    assert "unknown_key" not in loaded
    assert "another" not in loaded
    assert loaded.get("name") == "Boris"


def test_save_writes_valid_json(tmp_path):
    path = tmp_path / "profile.json"
    save_profile({"name": "Test"}, path)
    raw = path.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    assert isinstance(parsed, dict)


def test_allowed_keys_are_complete():
    assert PROFILE_ALLOWED_KEYS == {"name", "brand", "max_price", "color", "category"}


def test_save_empty_profile(tmp_path):
    path = tmp_path / "profile.json"
    save_profile({}, path)
    assert load_profile(path) == {}
