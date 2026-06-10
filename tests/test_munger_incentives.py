"""Tests for Munger incentives and hidden-stupidity scoring."""

from pathlib import Path

import yaml

from broker_agents.agents.munger_agent import MungerAgent
from broker_agents.calculators.decision_candidates import build_decision_candidate
from broker_agents.calculators.munger_incentives import (
    score_munger_incentives_and_stupidity,
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
SCORE_FIELDS = {
    "incentives_score",
    "capital_allocation_score",
    "buyback_discipline_score",
    "balance_sheet_discipline_score",
    "acquisition_discipline_score",
    "hidden_stupidity_risk_score",
    "overall_munger_quality_score",
}


def load_pack(ticker: str) -> dict:
    path = ROOT / "examples" / f"{ticker.lower()}_input.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_scoring_returns_required_fields_for_manual_companies() -> None:
    for ticker in ("MSFT", "AAPL", "NVDA"):
        result = score_munger_incentives_and_stupidity(load_pack(ticker))

        assert SCORE_FIELDS <= result.keys()
        for field in SCORE_FIELDS:
            assert 0 <= result[field] <= 5


def test_company_specific_evidence_gaps_are_present() -> None:
    aapl = " ".join(
        score_munger_incentives_and_stupidity(load_pack("AAPL"))["evidence_gaps"]
    ).lower()
    nvda = " ".join(
        score_munger_incentives_and_stupidity(load_pack("NVDA"))["evidence_gaps"]
    ).lower()

    assert any(term in aapl for term in ("key product", "buyback", "incentive"))
    assert any(
        term in nvda
        for term in ("customer concentration", "cycle-normalized", "valuation")
    )


def test_munger_candidates_remain_company_specific() -> None:
    assert build_decision_candidate(load_pack("MSFT"), "munger")[
        "candidate_decision"
    ] == "Wait / Avoid Overpaying Candidate"
    assert build_decision_candidate(load_pack("AAPL"), "munger")[
        "candidate_decision"
    ] == "Buy Gradually Candidate with Evidence Conditions"
    assert build_decision_candidate(load_pack("NVDA"), "munger")[
        "candidate_decision"
    ] == "Wait / Avoid Overpaying Candidate"


def test_munger_reports_keep_final_decision_and_disable_auto_promotion() -> None:
    method_path = ROOT / "methods" / "munger_method.yaml"
    for ticker in ("MSFT", "AAPL", "NVDA"):
        pack = load_pack(ticker)
        report = MungerAgent(pack, method_path).generate_report()
        eligibility = evaluate_promotion_eligibility(pack, "munger")

        assert "Munger Incentives & Hidden-Stupidity Score" in report
        assert (
            "## Decision\nBuy Gradually / Wait for Better Evidence on AI Capex Returns"
            in report
        )
        assert eligibility["auto_promotion_allowed"] is False


def test_aggregate_reports_include_munger_scoring_and_precise_requests() -> None:
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

    assert "Munger Incentives & Hidden-Stupidity Comparison" in comparison
    assert "Management compensation metrics" in worklist
    assert "Insider ownership" in worklist
    assert "Buyback price discipline" in worklist
    assert "Acquisition history and returns" in worklist
