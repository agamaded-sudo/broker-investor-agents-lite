"""Project file path helpers."""

from pathlib import Path


def project_root() -> Path:
    """Return the root directory for the broker_investor_agents project."""
    return Path(__file__).resolve().parents[3]


def config_dir() -> Path:
    """Return the configuration directory path."""
    return project_root() / "config"


def schemas_dir() -> Path:
    """Return the schemas directory path."""
    return project_root() / "schemas"


def methods_dir() -> Path:
    """Return the investment methods directory path."""
    return project_root() / "methods"


def examples_dir() -> Path:
    """Return the examples directory path."""
    return project_root() / "examples"


def data_dir() -> Path:
    """Return the data directory path."""
    return project_root() / "data"


def data_outputs_dir() -> Path:
    """Return the data outputs directory path."""
    return data_dir() / "outputs"


def config_path(filename: str) -> Path:
    """Return a path inside the configuration directory."""
    return config_dir() / filename


def schema_path(filename: str) -> Path:
    """Return a path inside the schemas directory."""
    return schemas_dir() / filename


def method_path(filename: str) -> Path:
    """Return a path inside the methods directory."""
    return methods_dir() / filename


def example_path(filename: str) -> Path:
    """Return a path inside the examples directory."""
    return examples_dir() / filename


def data_output_path(filename: str) -> Path:
    """Return a path inside the data outputs directory."""
    return data_outputs_dir() / filename


def output_dir_for_ticker(ticker: str) -> Path:
    """Return the data output directory for a ticker."""
    return data_outputs_dir() / ticker.upper()
