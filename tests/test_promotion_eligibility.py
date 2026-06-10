"""Tests for cautious candidate promotion eligibility."""

from pathlib import Path

import yaml

from broker_agents.agents.bogle_agent import BogleAgent
from broker_agents.agents.buffett_agent import BuffettAgent
from broker_agents.agents.fisher_agent import FisherAgent
from broker_agents.agents.lynch_agent import LynchAgent
from broker_agents.agents.munger_agent import MungerAgent
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
)
from broker_agents.reports.decision_candidate_audit_report import (
    generate_decision_candidate_audit,
)
from broker_agents.reports.multi_company_comparison_report import (
    generate_multi_company_comparison,
)


ROOT = Path(__file__).resolve().parents[1]
TICKERS = ("MSFT", "AAPL", "NVDA")
INVESTORS = ("buffett", "munger", "fisher", "lynch", "bogle")


def _load(ticker: str) -> dict:
    path = ROOT / "examples" / f"{ticker.lower()}_input.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_buffett_promotion_eligibility_differs_by_company() -> None:
    assert evaluate_promotion_eligibility(_load("AAPL"), "buffett")[
        "promotion_eligibility"
    ] == "Needs More Evidence"
    assert evaluate_promotion_eligibility(_load("MSFT"), "buffett")[
        "promotion_eligibility"
    ] == "Needs More Evidence"
    assert evaluate_promotion_eligibility(_load("NVDA"), "buffett")[
        "promotion_eligibility"
    ] == "Needs More Evidence"


def test_aapl_lynch_is_conditionally_eligible() -> None:
    result = evaluate_promotion_eligibility(_load("AAPL"), "lynch")

    assert result["promotion_eligibility"] == "Conditionally Eligible"


def test_fisher_and_bogle_need_more_evidence_for_all_companies() -> None:
    for ticker in TICKERS:
        fisher = evaluate_promotion_eligibility(_load(ticker), "fisher")
        bogle = evaluate_promotion_eligibility(_load(ticker), "bogle")
        assert fisher["promotion_eligibility"] == "Needs More Evidence"
        assert bogle["promotion_eligibility"] == "Needs More Evidence"
        assert "Portfolio context" in " ".join(bogle["required_evidence"])


def test_auto_promotion_is_disabled_for_every_record() -> None:
    for ticker in TICKERS:
        for investor in INVESTORS:
            result = evaluate_promotion_eligibility(_load(ticker), investor)
            assert result["auto_promotion_allowed"] is False


def test_all_investor_reports_contain_promotion_eligibility() -> None:
    pack = _load("MSFT")
    specs = [
        (BuffettAgent, "buffett_method.yaml"),
        (MungerAgent, "munger_method.yaml"),
        (FisherAgent, "fisher_method.yaml"),
        (LynchAgent, "lynch_method.yaml"),
        (BogleAgent, "bogle_method.yaml"),
    ]
    for agent_class, method_name in specs:
        report = agent_class(
            pack=pack,
            method_path=ROOT / "methods" / method_name,
        ).generate_report()
        assert "## Promotion Eligibility" in report
        assert "Auto-Promotion Allowed: No" in report


def test_audit_and_multi_company_reports_include_eligibility_sections() -> None:
    audit = generate_decision_candidate_audit(
        list(TICKERS),
        ROOT / "data" / "outputs",
        ROOT / "examples",
    )
    comparison = generate_multi_company_comparison(
        list(TICKERS),
        ROOT / "data" / "outputs",
        ROOT / "examples",
    )

    assert "Promotion Eligibility Review" in audit
    assert "Promotion Eligibility Comparison" in comparison
