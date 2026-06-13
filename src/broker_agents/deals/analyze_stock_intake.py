"""Structured YAML/JSON intake configuration for analyze-stock."""

from dataclasses import asdict, dataclass, field, replace
import json
from pathlib import Path

import yaml

from broker_agents.historical.as_of_context import build_as_of_context

DEFAULT_INVESTORS = ["Buffett", "Munger", "Fisher", "Lynch", "Bogle"]


@dataclass(frozen=True)
class AnalyzeStockIntake:
    """Validated configuration for one unified stock analysis run."""

    ticker: str
    company_name: str | None = None
    market: str | None = None
    exchange: str | None = None
    sector: str | None = None
    purpose: str = "broker_review"
    investor_set: list[str] = field(
        default_factory=lambda: list(DEFAULT_INVESTORS)
    )
    evidence_mode: str = "fixtures"
    output_mode: str = "full_bundle"
    run_label: str | None = None
    as_of_date: str | None = None
    financials_provider: str = "sec_fixture"
    financials_root: Path | None = None
    examples_root: Path = Path("examples")
    outputs_root: Path = Path("data/outputs")
    fixtures_root: Path = Path("tests/fixtures")
    portfolio_context: Path | None = Path("examples/portfolio_context.yaml")

    def to_snapshot(
        self,
        *,
        input_mode: str,
        intake_file: Path | None = None,
    ) -> dict:
        """Return the compact trace stored with generated deal outputs."""
        snapshot = {
            "ticker": self.ticker,
            "company_name": self.company_name,
            "market": self.market,
            "exchange": self.exchange,
            "sector": self.sector,
            "purpose": self.purpose,
            "evidence_mode": self.evidence_mode,
            "output_mode": self.output_mode,
            "investor_set": list(self.investor_set),
            "run_label": self.run_label,
            "as_of_date": self.as_of_date,
            "financials_provider": self.financials_provider,
            "financials_root": (
                str(self.financials_root) if self.financials_root else None
            ),
            "input_mode": input_mode,
            "intake_file": str(intake_file) if intake_file else None,
        }
        return snapshot

    def to_dict(self) -> dict:
        """Serialize the full intake configuration."""
        data = asdict(self)
        for key in (
            "examples_root",
            "outputs_root",
            "fixtures_root",
            "financials_root",
            "portfolio_context",
        ):
            value = data[key]
            data[key] = str(value) if value is not None else None
        return data


def _load_mapping(path: Path) -> dict:
    """Load a YAML or JSON intake file into a mapping."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Analyze-stock intake file not found: {path}")
    try:
        if path.suffix.lower() == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"Invalid analyze-stock intake file {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(
            f"Analyze-stock intake file must contain a mapping: {path}"
        )
    return data


def load_analyze_stock_intake(path: Path) -> AnalyzeStockIntake:
    """Load and validate a structured analyze-stock intake file."""
    data = _load_mapping(path)
    ticker = str(data.get("ticker") or "").strip().upper()
    if not ticker:
        raise ValueError("Analyze-stock intake requires a non-empty ticker.")

    investor_set = data.get("investor_set", DEFAULT_INVESTORS)
    if not isinstance(investor_set, list) or not all(
        isinstance(item, str) and item.strip() for item in investor_set
    ):
        raise ValueError("Analyze-stock investor_set must be a list of names.")

    portfolio_value = data.get(
        "portfolio_context",
        "examples/portfolio_context.yaml",
    )
    as_of_context = build_as_of_context(data.get("as_of_date"))
    return AnalyzeStockIntake(
        ticker=ticker,
        company_name=(
            str(data["company_name"]).strip()
            if data.get("company_name")
            else None
        ),
        market=str(data["market"]).strip() if data.get("market") else None,
        exchange=(
            str(data["exchange"]).strip() if data.get("exchange") else None
        ),
        sector=str(data["sector"]).strip() if data.get("sector") else None,
        purpose=str(data.get("purpose") or "broker_review"),
        investor_set=[str(item).strip() for item in investor_set],
        evidence_mode=str(data.get("evidence_mode") or "fixtures"),
        output_mode=str(data.get("output_mode") or "full_bundle"),
        run_label=(
            str(data["run_label"]).strip() if data.get("run_label") else None
        ),
        as_of_date=(
            as_of_context.as_of_date.isoformat()
            if as_of_context.as_of_date
            else None
        ),
        financials_provider=str(
            data.get("financials_provider") or "sec_fixture"
        ).strip().lower(),
        financials_root=(
            Path(data["financials_root"])
            if data.get("financials_root")
            else None
        ),
        examples_root=Path(data.get("examples_root") or "examples"),
        outputs_root=Path(data.get("outputs_root") or "data/outputs"),
        fixtures_root=Path(data.get("fixtures_root") or "tests/fixtures"),
        portfolio_context=(
            Path(portfolio_value) if portfolio_value not in {None, ""} else None
        ),
    )


def build_ticker_analyze_stock_intake(
    ticker: str,
    examples_root: Path,
    outputs_root: Path,
    fixtures_root: Path,
    portfolio_context: Path | None,
    as_of_date: str | None = None,
    financials_provider: str = "sec_fixture",
    financials_root: Path | None = None,
) -> AnalyzeStockIntake:
    """Create the equivalent structured intake for legacy ticker mode."""
    normalized = str(ticker or "").strip().upper()
    if not normalized:
        raise ValueError("Analyze-stock requires a non-empty ticker.")
    as_of_context = build_as_of_context(as_of_date)
    return AnalyzeStockIntake(
        ticker=normalized,
        as_of_date=(
            as_of_context.as_of_date.isoformat()
            if as_of_context.as_of_date
            else None
        ),
        financials_provider=str(
            financials_provider or "sec_fixture"
        ).strip().lower(),
        financials_root=(
            Path(financials_root) if financials_root is not None else None
        ),
        examples_root=Path(examples_root),
        outputs_root=Path(outputs_root),
        fixtures_root=Path(fixtures_root),
        portfolio_context=(
            Path(portfolio_context) if portfolio_context is not None else None
        ),
    )


def with_as_of_date(
    intake: AnalyzeStockIntake,
    as_of_date: str | None,
) -> AnalyzeStockIntake:
    """Return an intake with a validated CLI as-of-date override."""
    context = build_as_of_context(as_of_date)
    return replace(
        intake,
        as_of_date=(
            context.as_of_date.isoformat() if context.as_of_date else None
        ),
    )

def with_financials_provider(
    intake: AnalyzeStockIntake,
    provider_name: str,
    financials_root: Path | None,
) -> AnalyzeStockIntake:
    """Return an intake with explicit historical financials configuration."""
    normalized = str(provider_name or "sec_fixture").strip().lower()
    if normalized in {"fixture", "default"}:
        normalized = "sec_fixture"
    if normalized not in {"sec_fixture", "historical_csv"}:
        raise ValueError(
            "financials_provider must be one of: fixture, sec_fixture, "
            "default, historical_csv."
        )
    if normalized == "historical_csv" and financials_root is None:
        raise ValueError(
            "--financials-root is required when --financials-provider "
            "historical_csv is used."
        )
    if normalized == "historical_csv" and not intake.as_of_date:
        raise ValueError(
            "--as-of-date is required when --financials-provider "
            "historical_csv is used."
        )
    return replace(
        intake,
        financials_provider=normalized,
        financials_root=(
            Path(financials_root) if financials_root is not None else None
        ),
    )
