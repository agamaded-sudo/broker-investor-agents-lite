"""Tests for Bogle index overlap and benchmark risk guardrails."""

from pathlib import Path

import yaml
import pytest

from broker_agents.agents.bogle_agent import BogleAgent
from broker_agents.backoffice.portfolio_context import (
    load_portfolio_context,
    merge_portfolio_context_into_pack,
)
from broker_agents.calculators.bogle_benchmark_risk import (
    calculate_bogle_benchmark_risk,
)
from broker_agents.calculators.bogle_index_overlap import (
    calculate_bogle_index_overlap,
)
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
)
from broker_agents.reports.backoffice_missing_evidence_report import (
    generate_backoffice_missing_evidence_report,
)
from broker_agents.reports.multi_company_comparison_report import (
    generate_multi_company_comparison,
)


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = load_portfolio_context(ROOT / "examples" / "portfolio_context.yaml")


def load_pack(ticker: str) -> dict:
    path = ROOT / "examples" / f"{ticker.lower()}_input.yaml"
    pack = yaml.safe_load(path.read_text(encoding="utf-8"))
    return merge_portfolio_context_into_pack(pack, CONTEXT)


def test_manual_portfolio_overlap_and_limited_weight_guardrails() -> None:
    expected_exposure = {"MSFT": 0.035, "AAPL": 0.034, "NVDA": 0.030}
    for ticker, exposure in expected_exposure.items():
        result = calculate_bogle_index_overlap(load_pack(ticker))

        assert result["portfolio_context_provided"] is True
        assert result["estimated_indirect_exposure"] == exposure
        assert result["overlap_label"] == "high index overlap"
        assert result["limited_weight_candidate"] is True
        assert result["index_core_weight"] == pytest.approx(0.85)


def test_benchmark_risk_is_incomplete_for_manual_packs() -> None:
    for ticker in ("MSFT", "AAPL", "NVDA"):
        result = calculate_bogle_benchmark_risk(load_pack(ticker))

        assert result["risk_data_quality"] == "Incomplete"
        assert result["benchmark_risk_label"] == "Benchmark risk not established"
        assert "Beta." in result["missing_benchmark_evidence"]
        assert "Correlation." in result["missing_benchmark_evidence"]


def test_bogle_reports_keep_final_decision_and_disable_auto_promotion() -> None:
    method_path = ROOT / "methods" / "bogle_method.yaml"
    for ticker in ("MSFT", "AAPL", "NVDA"):
        pack = load_pack(ticker)
        report = BogleAgent(pack, method_path).generate_report()
        eligibility = evaluate_promotion_eligibility(pack, "bogle")

        assert "Bogle Index Overlap & Benchmark Risk" in report
        assert "## Decision\nPrefer Broad Index" in report
        assert eligibility["promotion_eligibility"] == "Conditionally Eligible"
        assert eligibility["auto_promotion_allowed"] is False


def test_evidence_worklist_uses_benchmark_requests_not_context_request() -> None:
    worklist = generate_backoffice_missing_evidence_report(
        ["MSFT", "AAPL", "NVDA"],
        ROOT / "data" / "outputs",
        ROOT / "examples",
        CONTEXT,
    )

    assert "| MSFT | John Bogle | Portfolio context |" not in worklist
    assert "| AAPL | John Bogle | Portfolio context |" not in worklist
    assert "| NVDA | John Bogle | Portfolio context |" not in worklist
    assert "Benchmark-relative return" in worklist
    assert "Stock and benchmark volatility" in worklist
    assert "Stock and benchmark max drawdown" in worklist
    assert "| Beta |" in worklist
    assert "| Correlation |" in worklist


def test_multi_company_comparison_contains_bogle_overlap_section() -> None:
    report = generate_multi_company_comparison(
        ["MSFT", "AAPL", "NVDA"],
        ROOT / "data" / "outputs",
        ROOT / "examples",
        CONTEXT,
    )

    assert "Bogle Index Overlap & Benchmark Risk Comparison" in report
    assert "high index overlap" in report
    assert "Benchmark risk not established" in report
