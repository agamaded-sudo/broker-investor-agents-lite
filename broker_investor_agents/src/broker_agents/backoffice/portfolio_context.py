"""Loading and merging of optional investor portfolio context."""

from copy import deepcopy
from pathlib import Path

import yaml


def load_portfolio_context(path: Path | None) -> dict:
    """Load a portfolio context mapping from YAML."""
    if path is None:
        return {}
    with Path(path).open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Portfolio context YAML must contain a mapping: {path}")
    context = data.get("portfolio_context", data)
    if not isinstance(context, dict):
        raise ValueError(f"portfolio_context must be a mapping: {path}")
    return context


def merge_portfolio_context_into_pack(pack: dict, portfolio_context: dict) -> dict:
    """Return a pack with optional portfolio context merged into it."""
    if not portfolio_context:
        return pack
    merged = deepcopy(pack)
    merged["portfolio_context_form"] = deepcopy(portfolio_context)
    return merged
