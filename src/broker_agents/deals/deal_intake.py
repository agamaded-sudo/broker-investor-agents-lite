"""Filesystem-based preflight checks for new broker deal tickers."""

from dataclasses import asdict, dataclass
from pathlib import Path
import re

import yaml

VALID_TICKER = re.compile(r"^[A-Z0-9.-]+$")


@dataclass(frozen=True)
class DealIntakeStatus:
    """Readiness and file requirements for one prospective broker deal."""

    ticker: str
    normalized_ticker: str
    market: str
    company_name: str
    intake_status: str
    manual_input_path: Path
    manual_input_exists: bool
    expected_output_dir: Path
    expected_deal_package_dir: Path
    sec_fixture_path: Path
    sec_fixture_exists: bool
    market_fixture_path: Path
    market_fixture_exists: bool
    historical_valuation_fixture_path: Path
    historical_valuation_fixture_exists: bool
    growth_peg_fixture_path: Path
    growth_peg_fixture_exists: bool
    portfolio_context_path: Path
    portfolio_context_exists: bool
    can_run_deal: bool
    missing_requirements: list[str]
    optional_missing_sources: list[str]
    backoffice_next_actions: list[str]
    warnings: list[str]
    safety_flags: list[str]

    def to_dict(self) -> dict:
        """Serialize the intake status to JSON-compatible values."""
        data = asdict(self)
        for key in (
            "manual_input_path",
            "expected_output_dir",
            "expected_deal_package_dir",
            "sec_fixture_path",
            "market_fixture_path",
            "historical_valuation_fixture_path",
            "growth_peg_fixture_path",
            "portfolio_context_path",
        ):
            data[key] = str(data[key])
        return data


def _load_identity(path: Path) -> tuple[str | None, str | None]:
    """Read optional company and market metadata from a manual pack."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("Manual input pack must contain a top-level mapping.")
    identity = data.get("company_identity", {})
    metadata = data.get("metadata", {})
    return (
        identity.get("market") or metadata.get("market"),
        identity.get("company_name") or metadata.get("company_name"),
    )


def build_deal_intake_status(
    ticker: str,
    examples_root: Path,
    outputs_root: Path,
    fixtures_root: Path,
    portfolio_context_path: Path | None = None,
    market: str | None = None,
    company_name: str | None = None,
) -> DealIntakeStatus:
    """Check whether a ticker can enter the offline broker deal workflow."""
    raw_ticker = str(ticker or "").strip()
    normalized = raw_ticker.upper()
    valid_ticker = bool(normalized and VALID_TICKER.fullmatch(normalized))
    path_ticker = normalized if valid_ticker else "UNKNOWN"
    lower = path_ticker.lower()
    examples_root = Path(examples_root)
    outputs_root = Path(outputs_root)
    fixtures_root = Path(fixtures_root)
    context_path = (
        Path(portfolio_context_path)
        if portfolio_context_path is not None
        else examples_root / "portfolio_context.yaml"
    )

    manual_path = examples_root / f"{lower}_input.yaml"
    output_dir = outputs_root / path_ticker
    deal_dir = output_dir / "deal_package"
    fixture_paths = {
        "SEC company facts fixture": (
            fixtures_root / f"sec_company_facts_{lower}.json"
        ),
        "Market data fixture": fixtures_root / f"market_data_{lower}.json",
        "Historical valuation fixture": (
            fixtures_root / f"historical_valuation_{lower}.json"
        ),
        "Growth & PEG fixture": fixtures_root / f"growth_peg_{lower}.json",
    }
    fixture_exists = {
        label: path.is_file() for label, path in fixture_paths.items()
    }
    safety_flags = [
        "intake_only",
        "no_recommendation",
        "no_investor_decision",
        "no_ranking",
        "no_consensus",
        "no_allocation",
        "no_trade_signal",
        "no_auto_promotion",
    ]
    missing_requirements: list[str] = []
    optional_missing = [
        f"{label}: {path}"
        for label, path in fixture_paths.items()
        if not fixture_exists[label]
    ]
    warnings: list[str] = []
    detected_market: str | None = None
    detected_company: str | None = None

    if not valid_ticker:
        status = "Insufficient for Deal Workflow"
        can_run = False
        missing_requirements.append("A valid ticker symbol is required.")
        warnings.append("Ticker is empty or contains unsupported characters.")
    elif not manual_path.is_file():
        status = "Manual Pack Required"
        can_run = False
        missing_requirements.append(f"Manual Backoffice input pack: {manual_path}")
    else:
        try:
            detected_market, detected_company = _load_identity(manual_path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            status = "Data Unavailable"
            can_run = False
            missing_requirements.append(
                f"Readable manual Backoffice input pack: {manual_path}"
            )
            warnings.append(f"Could not read manual input pack: {exc}")
        else:
            can_run = True
            if all(fixture_exists.values()):
                status = "Ready for Deal Workflow"
            else:
                status = "Ready with Missing Optional Sources"
                warnings.append(
                    "The deal can run, but enrichment will omit missing fixtures."
                )

    actions: list[str] = []
    if not valid_ticker:
        actions.append("Provide a valid ticker symbol and company identity.")
    elif not manual_path.is_file():
        actions.extend(
            [
                "Create manual Backoffice input pack from template.",
                "Collect official financials.",
                "Collect market data.",
                "Collect historical valuation.",
                "Collect growth and PEG data.",
            ]
        )
    elif not can_run:
        actions.append("Repair or replace the unreadable manual Backoffice input pack.")
    elif optional_missing:
        actions.extend(
            [
                "Add or generate fixture data for missing enrichment sources.",
                "Run enrichment after fixtures are available.",
                f"Run broker-agents run-deal for {normalized}.",
            ]
        )
    else:
        actions.extend(
            [
                f"Run broker-agents run-deal for {normalized}.",
                "Review Broker Deal Package.",
                "Review Investor Response Letters.",
            ]
        )
    if not context_path.is_file():
        actions.append(
            "Add portfolio context if Bogle-specific portfolio fit analysis is needed."
        )

    return DealIntakeStatus(
        ticker=raw_ticker,
        normalized_ticker=normalized,
        market=str(market or detected_market or "Not provided"),
        company_name=str(company_name or detected_company or "Not provided"),
        intake_status=status,
        manual_input_path=manual_path,
        manual_input_exists=manual_path.is_file(),
        expected_output_dir=output_dir,
        expected_deal_package_dir=deal_dir,
        sec_fixture_path=fixture_paths["SEC company facts fixture"],
        sec_fixture_exists=fixture_exists["SEC company facts fixture"],
        market_fixture_path=fixture_paths["Market data fixture"],
        market_fixture_exists=fixture_exists["Market data fixture"],
        historical_valuation_fixture_path=fixture_paths[
            "Historical valuation fixture"
        ],
        historical_valuation_fixture_exists=fixture_exists[
            "Historical valuation fixture"
        ],
        growth_peg_fixture_path=fixture_paths["Growth & PEG fixture"],
        growth_peg_fixture_exists=fixture_exists["Growth & PEG fixture"],
        portfolio_context_path=context_path,
        portfolio_context_exists=context_path.is_file(),
        can_run_deal=can_run,
        missing_requirements=missing_requirements,
        optional_missing_sources=optional_missing,
        backoffice_next_actions=actions,
        warnings=warnings,
        safety_flags=safety_flags,
    )
