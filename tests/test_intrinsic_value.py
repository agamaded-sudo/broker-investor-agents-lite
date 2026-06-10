"""Tests for the preliminary Buffett intrinsic value range."""

from pathlib import Path

import yaml

from broker_agents.agents.buffett_agent import BuffettAgent
from broker_agents.calculators.intrinsic_value import (
    calculate_buffett_intrinsic_value_range,
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


def load_pack(ticker: str) -> dict:
    path = ROOT / "examples" / f"{ticker.lower()}_input.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_intrinsic_value_range_exists_for_all_manual_companies() -> None:
    for ticker in ("MSFT", "AAPL", "NVDA"):
        result = calculate_buffett_intrinsic_value_range(load_pack(ticker))

        assert result["intrinsic_value_low"] is not None
        assert result["intrinsic_value_mid"] is not None
        assert result["intrinsic_value_high"] is not None
        assert result["intrinsic_value_low"] < result["intrinsic_value_mid"]
        assert result["intrinsic_value_mid"] < result["intrinsic_value_high"]
        assert result["margin_of_safety_low"] is not None
        assert result["margin_of_safety_mid"] is not None
        assert result["margin_of_safety_high"] is not None


def test_buffett_reports_include_range_and_keep_final_decision() -> None:
    method_path = ROOT / "methods" / "buffett_method.yaml"
    for ticker in ("MSFT", "AAPL", "NVDA"):
        report = BuffettAgent(load_pack(ticker), method_path).generate_report()
        eligibility = evaluate_promotion_eligibility(load_pack(ticker), "buffett")

        assert "Preliminary Intrinsic Value Range" in report
        assert "## Decision\nWait for Better Price / Complete Intrinsic Value Work" in report
        assert eligibility["auto_promotion_allowed"] is False


def test_aggregate_reports_include_range_and_replace_missing_request() -> None:
    comparison = generate_multi_company_comparison(
        ["MSFT", "AAPL", "NVDA"],
        ROOT / "data" / "outputs",
        ROOT / "examples",
    )
    worklist = generate_backoffice_missing_evidence_report(
        ["MSFT", "AAPL", "NVDA"],
        ROOT / "data" / "outputs",
        ROOT / "examples",
    )

    assert "Buffett Intrinsic Value Range Comparison" in comparison
    assert "| Intrinsic value range |" not in worklist
    assert "Preliminary intrinsic value source verification" in worklist
    assert "Margin of safety validation" in worklist
    assert "Historical valuation source validation" in worklist
    assert "Provider methodology validation" in worklist
    assert "5Y/10Y median calculation methodology" in worklist
    assert "Normalized owner earnings history" in worklist
