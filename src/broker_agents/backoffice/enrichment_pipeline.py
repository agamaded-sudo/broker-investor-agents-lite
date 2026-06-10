"""Unified offline Backoffice enrichment pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from broker_agents.backoffice.growth_peg_mapper import merge_growth_peg_into_pack
from broker_agents.backoffice.historical_valuation_mapper import (
    merge_historical_valuation_into_pack,
)
from broker_agents.backoffice.market_data_mapper import merge_market_data_into_pack
from broker_agents.backoffice.official_financials_mapper import (
    merge_official_financials_into_pack,
)
from broker_agents.backoffice.source_tracker import collect_source_log
from broker_agents.backoffice.source_verification import verify_sources
from broker_agents.fetchers.growth_peg_fetcher import (
    GrowthPegFetcher,
    load_growth_peg_fixture,
)
from broker_agents.fetchers.historical_valuation_fetcher import (
    HistoricalValuationFetcher,
    load_historical_valuation_fixture,
)
from broker_agents.fetchers.market_data_fetcher import (
    MarketDataFetcher,
    load_market_data_fixture,
)
from broker_agents.fetchers.sec_financials_fetcher import (
    load_sec_fixture,
    map_fixture_to_financials,
)
from broker_agents.reports.source_verification_report import (
    generate_source_verification_report_for_pack,
)

SOURCE_NAMES = (
    "official_financials",
    "market_data",
    "historical_valuation",
    "growth_peg",
)


def fixture_paths_for_known_ticker(
    ticker: str,
    fixtures_root: Path,
) -> dict[str, Path | None]:
    """Infer known fixture names, returning None for fixtures not present."""
    ticker_lower = ticker.strip().lower()
    candidates = {
        "sec_fixture_path": Path(fixtures_root)
        / f"sec_company_facts_{ticker_lower}.json",
        "market_fixture_path": Path(fixtures_root)
        / f"market_data_{ticker_lower}.json",
        "historical_valuation_fixture_path": Path(fixtures_root)
        / f"historical_valuation_{ticker_lower}.json",
        "growth_peg_fixture_path": Path(fixtures_root)
        / f"growth_peg_{ticker_lower}.json",
    }
    return {
        name: path if path.is_file() else None for name, path in candidates.items()
    }


@dataclass(frozen=True)
class EnrichmentPipelineResult:
    """Summary of one completed Backoffice enrichment run."""

    ticker: str
    input_path: Path
    output_path: Path
    applied_sources: list[str]
    skipped_sources: list[str]
    source_log_count_before: int
    source_log_count_after: int
    overall_source_quality_before: str
    overall_source_quality_after: str
    section_quality_changes: list[dict[str, str]]
    warnings: list[str]


def _load_pack(path: Path) -> dict:
    """Load a YAML Backoffice pack with clear local errors."""
    if not path.exists():
        raise FileNotFoundError(f"Backoffice input pack not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in Backoffice input pack {path}: {exc}") from exc
    except OSError as exc:
        raise OSError(f"Could not read Backoffice input pack {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Backoffice input pack must contain a YAML mapping: {path}")
    return data


def _require_fixture(path: Path, source_name: str) -> Path:
    """Validate an explicitly supplied fixture path."""
    if not path.exists():
        raise FileNotFoundError(f"{source_name} fixture not found: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"{source_name} fixture is not a file: {path}")
    return path


def _quality_map(verification: dict) -> dict[str, str]:
    """Return section quality labels indexed by section name."""
    return {
        item["section_name"]: item["section_quality_label"]
        for item in verification["source_quality_by_section"]
    }


def run_backoffice_enrichment_pipeline(
    input_path: Path,
    output_path: Path,
    sec_fixture_path: Path | None = None,
    market_fixture_path: Path | None = None,
    historical_valuation_fixture_path: Path | None = None,
    growth_peg_fixture_path: Path | None = None,
) -> EnrichmentPipelineResult:
    """Apply available offline fixtures in a deterministic enrichment sequence."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    pack = _load_pack(input_path)
    before = verify_sources(pack)
    source_count_before = len(collect_source_log(pack))
    applied: list[str] = []
    skipped: list[str] = []
    warnings: list[str] = []

    if sec_fixture_path is None:
        skipped.append("official_financials")
    else:
        path = _require_fixture(Path(sec_fixture_path), "Official financials")
        financials = map_fixture_to_financials(load_sec_fixture(path))
        pack = merge_official_financials_into_pack(pack, financials)
        applied.append("official_financials")

    if market_fixture_path is None:
        skipped.append("market_data")
    else:
        path = _require_fixture(Path(market_fixture_path), "Market data")
        snapshot = MarketDataFetcher().map_fixture_to_market_data(
            load_market_data_fixture(path)
        )
        pack = merge_market_data_into_pack(pack, snapshot)
        applied.append("market_data")

    if historical_valuation_fixture_path is None:
        skipped.append("historical_valuation")
    else:
        path = _require_fixture(
            Path(historical_valuation_fixture_path),
            "Historical valuation",
        )
        snapshot = HistoricalValuationFetcher().map_fixture_to_historical_valuation(
            load_historical_valuation_fixture(path)
        )
        pack = merge_historical_valuation_into_pack(pack, snapshot)
        applied.append("historical_valuation")

    if growth_peg_fixture_path is None:
        skipped.append("growth_peg")
    else:
        path = _require_fixture(Path(growth_peg_fixture_path), "Growth and PEG")
        snapshot = GrowthPegFetcher().map_fixture_to_growth_peg(
            load_growth_peg_fixture(path)
        )
        pack = merge_growth_peg_into_pack(pack, snapshot)
        applied.append("growth_peg")

    after = verify_sources(pack)
    before_quality = _quality_map(before)
    after_quality = _quality_map(after)
    section_names = list(dict.fromkeys([*before_quality, *after_quality]))
    changes = [
        {
            "section": section,
            "before": before_quality.get(section, "not assessed"),
            "after": after_quality.get(section, "not assessed"),
        }
        for section in section_names
    ]
    if not applied:
        warnings.append("No enrichment fixtures were applied.")
    if skipped:
        warnings.append(
            "Skipped fixture sources: " + ", ".join(skipped) + "."
        )

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            yaml.safe_dump(pack, sort_keys=False, allow_unicode=False),
            encoding="utf-8",
        )
        verification_output = output_path.with_name(
            f"{output_path.stem}_source_verification.md"
        )
        verification_output.write_text(
            generate_source_verification_report_for_pack(pack),
            encoding="utf-8",
        )
    except OSError as exc:
        raise OSError(
            f"Could not write enriched Backoffice outputs for {output_path}: {exc}"
        ) from exc

    identity = pack.get("company_identity", {})
    metadata = pack.get("metadata", {})
    ticker = str(identity.get("ticker") or metadata.get("ticker") or "UNKNOWN").upper()
    return EnrichmentPipelineResult(
        ticker=ticker,
        input_path=input_path,
        output_path=output_path,
        applied_sources=applied,
        skipped_sources=skipped,
        source_log_count_before=source_count_before,
        source_log_count_after=len(collect_source_log(pack)),
        overall_source_quality_before=before["overall_source_quality"],
        overall_source_quality_after=after["overall_source_quality"],
        section_quality_changes=changes,
        warnings=warnings,
    )
