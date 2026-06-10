"""Tests for deterministic valuation-history evidence."""

from pathlib import Path

import yaml

from broker_agents.agents.buffett_agent import BuffettAgent
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
)
from broker_agents.calculators.valuation_history import analyze_valuation_history
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


def test_valuation_history_returns_labels_for_manual_companies() -> None:
    expected = {
        "MSFT": "above historical range",
        "AAPL": "near historical range",
        "NVDA": "near historical range",
    }
    for ticker, label in expected.items():
        result = analyze_valuation_history(load_pack(ticker))

        assert result["valuation_history_label"] == label
        assert result["current_p_fcf"] is not None
        assert result["p_fcf_5y_median"] is not None
        assert result["valuation_history_confidence"] == "medium_placeholder"


def test_buffett_reports_and_aggregate_outputs_include_history_evidence() -> None:
    method_path = ROOT / "methods" / "buffett_method.yaml"
    for ticker in ("MSFT", "AAPL", "NVDA"):
        pack = load_pack(ticker)
        report = BuffettAgent(pack, method_path).generate_report()
        eligibility = evaluate_promotion_eligibility(pack, "buffett")

        assert "Valuation History Evidence" in report
        assert "## Decision\nWait for Better Price / Complete Intrinsic Value Work" in report
        assert eligibility["auto_promotion_allowed"] is False

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

    assert "Buffett Valuation History & Normalized Owner Earnings Comparison" in comparison
    assert "Historical valuation source validation" in worklist
    assert "| Valuation history |" not in worklist
    assert "5Y/10Y median calculation methodology" in worklist
