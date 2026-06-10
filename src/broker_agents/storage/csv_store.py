"""CSV storage helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load a CSV file into a pandas DataFrame."""
    file_path = Path(path)
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"CSV file not found: {file_path}") from exc
    except pd.errors.ParserError as exc:
        raise ValueError(f"Invalid CSV in {file_path}: {exc}") from exc
    except OSError as exc:
        raise OSError(f"Could not read CSV file {file_path}: {exc}") from exc


def save_csv(path: str | Path, rows: list[dict[str, Any]] | pd.DataFrame) -> None:
    """Save rows or a pandas DataFrame to CSV, creating parent directories as needed."""
    file_path = Path(path)
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        data_frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
        data_frame.to_csv(file_path, index=False, encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Could not write CSV file {file_path}: {exc}") from exc
