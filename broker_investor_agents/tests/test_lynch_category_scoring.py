"""Tests for deterministic Lynch category scoring."""

from pathlib import Path

import yaml

from broker_agents.agents.lynch_agent import LynchAgent
from broker_agents.calculators.decision_candidates import build_decision_candidate
from broker_agents.calculators.lynch_category_scoring import score_lynch_category
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
)
from broker_agents.reports.multi_company_comparison_report import (
    generate_multi_company_comparison,
)


ROOT = Path(__file__).resolve().parents[1]


def load_pack(ticker: str) -> dict:
    path = ROOT / "examples" / f"{ticker.lower()}_input.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_company_business_models_and_categories_are_distinct() -> None:
    msft = score_lynch_category(load_pack("MSFT"))
    aapl = score_lynch_category(load_pack("AAPL"))
    nvda = score_lynch_category(load_pack("NVDA"))

    assert msft["business_model_type"] == "software_cloud"
    assert aapl["business_model_type"] == "consumer_ecosystem"
    assert nvda["business_model_type"] == "semiconductor"
    assert any(
        category in f"{msft['primary_category']} {msft['secondary_category']}"
        for category in ("Hybrid", "Stalwart", "Fast Grower")
    )
    assert any(
        category in f"{aapl['primary_category']} {aapl['secondary_category']}"
        for category in ("Hybrid", "Stalwart")
    )
    assert any(
        category in f"{nvda['primary_category']} {nvda['secondary_category']}"
        for category in ("Hybrid", "Fast Grower", "Cyclical")
    )


def test_lynch_candidates_remain_differentiated() -> None:
    assert build_decision_candidate(load_pack("MSFT"), "lynch")[
        "candidate_decision"
    ] == "Follow / Watch Candidate"
    assert build_decision_candidate(load_pack("AAPL"), "lynch")[
        "candidate_decision"
    ] == "Buy Gradually Candidate"
    assert build_decision_candidate(load_pack("NVDA"), "lynch")[
        "candidate_decision"
    ] == "Follow / Watch Candidate"


def test_lynch_reports_include_scoring_without_changing_final_decision() -> None:
    method_path = ROOT / "methods" / "lynch_method.yaml"
    for ticker in ("MSFT", "AAPL", "NVDA"):
        report = LynchAgent(load_pack(ticker), method_path).generate_report()
        eligibility = evaluate_promotion_eligibility(load_pack(ticker), "lynch")

        assert "Lynch Category Scoring" in report
        assert "## Decision\nFollow / Watch" in report
        assert eligibility["auto_promotion_allowed"] is False


def test_multi_company_comparison_contains_lynch_category_scoring() -> None:
    report = generate_multi_company_comparison(
        ["MSFT", "AAPL", "NVDA"],
        ROOT / "data" / "outputs",
        ROOT / "examples",
    )

    assert "Lynch Category Scoring Comparison" in report
    assert "software_cloud" in report
    assert "consumer_ecosystem" in report
    assert "semiconductor" in report
