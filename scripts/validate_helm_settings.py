from __future__ import annotations

import argparse
import importlib
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, cast

import yaml

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

SETTINGS_ENV_PREFIXES = (
    "API__",
    "APP__",
    "AUTH_RATE_LIMIT__",
    "CACHE__",
    "DATABASE__",
    "EMAIL__",
    "EXAMPLES__",
    "EXTERNAL__",
    "EXTERNAL_EVENT_POLICIES__",
    "EXTERNAL_POLICIES__",
    "HEALTH__",
    "LOGGING__",
    "METRICS__",
    "OPS__",
    "SECURITY__",
    "TELEMETRY__",
    "WEBHOOK__",
    "WORKER__",
)


def load_values(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping.")
    return data


@contextmanager
def patched_environment(env_data: dict[str, str]) -> Iterator[None]:
    managed_keys = {
        key for key in os.environ if key.startswith(SETTINGS_ENV_PREFIXES) or key in env_data
    }
    previous = {key: os.environ.get(key) for key in managed_keys}
    for key in managed_keys:
        os.environ.pop(key, None)
    os.environ.update(env_data)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def load_settings_class() -> Any:
    settings_module = importlib.import_module("app.core.settings.main")
    return settings_module.Settings


def validate_values(path: Path) -> None:
    values = load_values(path)
    env_values = values.get("config", {}) | values.get("secretData", {})

    env_data: dict[str, str] = {}
    for key, value in env_values.items():
        env_data[key] = str(value)

    with patched_environment(env_data):
        settings_class = cast(Any, load_settings_class())
        settings_class(_env_file=None, **env_data)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate Helm values against application settings startup checks."
    )
    parser.add_argument("values_files", nargs="+", type=Path)
    args = parser.parse_args()

    for values_file in args.values_files:
        validate_values(values_file)
        print(f"validated {values_file}")


if __name__ == "__main__":
    main()
