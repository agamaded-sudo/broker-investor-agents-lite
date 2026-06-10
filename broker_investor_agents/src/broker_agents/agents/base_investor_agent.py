"""Base class for deterministic investor agents."""

from pathlib import Path
from typing import Any

import yaml


class BaseInvestorAgent:
    """Common helpers for simple investor report agents."""

    def __init__(self, pack: dict, method_path: Path) -> None:
        self.pack = pack
        self.method_path = Path(method_path)
        self.method = self._load_method_yaml(self.method_path)

    @staticmethod
    def _load_method_yaml(method_path: Path) -> dict:
        """Load an investor method YAML file."""
        try:
            with method_path.open("r", encoding="utf-8") as file:
                method = yaml.safe_load(file) or {}
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Investor method file not found: {method_path}") from exc
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid investor method YAML in {method_path}: {exc}") from exc
        except OSError as exc:
            raise OSError(f"Could not read investor method file {method_path}: {exc}") from exc

        if not isinstance(method, dict):
            raise ValueError(f"Investor method YAML must contain a mapping: {method_path}")

        return method

    def get_company_name(self) -> str:
        """Return the company name from the backoffice pack."""
        company_identity = self.get_section("company_identity", {})
        metadata = self.get_section("metadata", {})
        return str(
            company_identity.get("company_name")
            or metadata.get("company_name")
            or "Unknown company"
        )

    def get_ticker(self) -> str:
        """Return the ticker from the backoffice pack."""
        company_identity = self.get_section("company_identity", {})
        metadata = self.get_section("metadata", {})
        return str(company_identity.get("ticker") or metadata.get("ticker") or "Unknown ticker")

    def get_section(self, name: str, default: Any = None) -> Any:
        """Return a named top-level section from the backoffice pack."""
        if default is None:
            default = {}
        return self.pack.get(name, default)

    def get_data_gaps(self) -> list[str]:
        """Return known data gaps from the backoffice pack."""
        source_section = self.get_section("sources_confidence_data_gaps", {})
        gaps = source_section.get("known_gaps", []) if isinstance(source_section, dict) else []
        return [str(gap) for gap in gaps] if isinstance(gaps, list) else []

    def build_common_header(self) -> str:
        """Build a shared Markdown header for investor reports."""
        method_name = self.method.get("method_name", "Investor Method")
        return (
            f"# {self.get_company_name()} {method_name} Report\n\n"
            f"- Company: {self.get_company_name()}\n"
            f"- Ticker: {self.get_ticker()}\n"
            f"- Method orientation: {self.method.get('orientation', 'not provided')}\n"
        )
