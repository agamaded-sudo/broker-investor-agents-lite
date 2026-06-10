"""JSON storage helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    """Load JSON data from a file."""
    file_path = Path(path)
    try:
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"JSON file not found: {file_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {file_path}: {exc}") from exc
    except OSError as exc:
        raise OSError(f"Could not read JSON file {file_path}: {exc}") from exc


def save_json(path: str | Path, data: Any) -> None:
    """Save JSON data to a file, creating parent directories as needed."""
    file_path = Path(path)
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
            file.write("\n")
    except TypeError as exc:
        raise TypeError(f"Data is not JSON serializable for {file_path}: {exc}") from exc
    except OSError as exc:
        raise OSError(f"Could not write JSON file {file_path}: {exc}") from exc
