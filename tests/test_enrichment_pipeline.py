"""Tests for the unified offline Backoffice enrichment pipeline."""

from pathlib import Path
import shutil

import pytest
import yaml

from broker_agents.agents.bogle_agent import BogleAgent
from broker_agents.agents.buffett_agent import BuffettAgent
from broker_agents.agents.fisher_agent import FisherAgent
from broker_agents.agents.lynch_agent import LynchAgent
from broker_agents.agents.munger_agent import MungerAgent
from broker_agents.backoffice.enrichment_pipeline import (
    fixture_paths_for_known_ticker,
    run_backoffice_enrichment_pipeline,
)
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
)
from broker_agents.reports.enrichment_pipeline_summary import (
    generate_enrichment_pipeline_summary,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"

QUALITY_RANK = {
    "weak": 0,
    "placeholder-heavy": 1,
    "calculated-only": 1,
    "mixed": 2,
    "strong": 3,
}


def _all_fixture_paths(ticker: str) -> dict[str, Path]:
    ticker_lower = ticker.lower()
    return {
        "sec_fixture_path": FIXTURES / f"sec_company_facts_{ticker_lower}.json",
        "market_fixture_path": FIXTURES / f"market_data_{ticker_lower}.json",
        "historical_valuation_fixture_path": (
            FIXTURES / f"historical_valuation_{ticker_lower}.json"
        ),
        "growth_peg_fixture_path": FIXTURES / f"growth_peg_{ticker_lower}.json",
    }


def _changes(result) -> dict[str, dict[str, str]]:
    return {item["section"]: item for item in result.section_quality_changes}


def test_pipeline_applies_all_sources_and_writes_enriched_pack(tmp_path: Path) -> None:
    input_path = ROOT / "examples" / "msft_input.yaml"
    original_text = input_path.read_text(encoding="utf-8")
    output_path = tmp_path / "msft_enriched_input.yaml"

    result = run_backoffice_enrichment_pipeline(
        input_path,
        output_path,
        **_all_fixture_paths("MSFT"),
    )
    enriched = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    changes = _changes(result)

    assert output_path.exists()
    assert (
        tmp_path / "msft_enriched_input_source_verification.md"
    ).exists()
    assert result.applied_sources == [
        "official_financials",
        "market_data",
        "historical_valuation",
        "growth_peg",
    ]
    assert result.skipped_sources == []
    assert result.source_log_count_after > result.source_log_count_before
    assert QUALITY_RANK[result.overall_source_quality_after] >= QUALITY_RANK[
        result.overall_source_quality_before
    ]
    assert changes["financial_statements_summary"]["after"] == "strong"
    assert changes["valuation_snapshot"]["after"] == "strong"
    assert changes["historical_valuation"]["after"] == "strong"
    assert changes["growth_peg_analysis"]["after"] == "strong"
    assert enriched["valuation_snapshot"]["current_price"] == 430
    assert enriched["growth_peg_analysis"]["peg_ratio"] == 2.4
    assert input_path.read_text(encoding="utf-8") == original_text


def test_summary_documents_pipeline_quality_changes(tmp_path: Path) -> None:
    result = run_backoffice_enrichment_pipeline(
        ROOT / "examples" / "aapl_input.yaml",
        tmp_path / "aapl_enriched_input.yaml",
        **_all_fixture_paths("AAPL"),
    )
    summary = generate_enrichment_pipeline_summary(result)

    assert "Backoffice Enrichment Pipeline Summary" in summary
    assert "Applied Sources" in summary
    assert "Source Quality Change" in summary
    assert "Section Quality Changes" in summary
    assert "official_financials" in summary
    assert "growth_peg_analysis" in summary


def test_known_ticker_fixture_inference_and_missing_fixture_skip(
    tmp_path: Path,
) -> None:
    inferred = fixture_paths_for_known_ticker("MSFT", FIXTURES)
    assert inferred == _all_fixture_paths("MSFT")

    partial_root = tmp_path / "fixtures"
    partial_root.mkdir()
    shutil.copy(
        FIXTURES / "sec_company_facts_msft.json",
        partial_root / "sec_company_facts_msft.json",
    )
    partial = fixture_paths_for_known_ticker("MSFT", partial_root)
    result = run_backoffice_enrichment_pipeline(
        ROOT / "examples" / "msft_input.yaml",
        tmp_path / "partial_enriched.yaml",
        **partial,
    )

    assert result.applied_sources == ["official_financials"]
    assert result.skipped_sources == [
        "market_data",
        "historical_valuation",
        "growth_peg",
    ]
    assert "Skipped fixture sources" in " ".join(result.warnings)


def test_invalid_explicit_fixture_path_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Market data fixture not found"):
        run_backoffice_enrichment_pipeline(
            ROOT / "examples" / "msft_input.yaml",
            tmp_path / "not_written.yaml",
            market_fixture_path=tmp_path / "missing_market.json",
        )


def test_original_decisions_and_auto_promotion_remain_unchanged() -> None:
    pack = yaml.safe_load(
        (ROOT / "examples" / "msft_input.yaml").read_text(encoding="utf-8")
    )
    specs = {
        "buffett": (
            BuffettAgent,
            "buffett_method.yaml",
            "Wait for Better Price / Complete Intrinsic Value Work",
        ),
        "munger": (
            MungerAgent,
            "munger_method.yaml",
            "Buy Gradually / Wait for Better Evidence on AI Capex Returns",
        ),
        "fisher": (
            FisherAgent,
            "fisher_method.yaml",
            "Needs More Scuttlebutt / Watch Closely",
        ),
        "lynch": (LynchAgent, "lynch_method.yaml", "Follow / Watch"),
        "bogle": (BogleAgent, "bogle_method.yaml", "Prefer Broad Index"),
    }
    for investor, (agent_class, method_name, decision) in specs.items():
        report = agent_class(pack, ROOT / "methods" / method_name).generate_report()
        eligibility = evaluate_promotion_eligibility(pack, investor)

        assert f"## Decision\n{decision}" in report
        assert eligibility["auto_promotion_allowed"] is False
