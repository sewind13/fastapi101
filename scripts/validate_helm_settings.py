from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.core.config import Settings  # noqa: E402


def load_values(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping.")
    return data


def validate_values(path: Path) -> None:
    values = load_values(path)
    env_values = values.get("config", {}) | values.get("secretData", {})

    env_data: dict[str, str] = {}
    for key, value in env_values.items():
        env_data[key] = str(value)

    Settings(_env_file=None, **env_data)


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
