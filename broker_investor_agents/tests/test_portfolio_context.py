"""Tests for optional Bogle portfolio context."""

from pathlib import Path

import yaml

from broker_agents.agents.bogle_agent import BogleAgent
from broker_agents.backoffice.portfolio_context import (
    load_portfolio_context,
    merge_portfolio_context_into_pack,
)
from broker_agents.calculators.decision_candidates import build_decision_candidate
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
)
from broker_agents.reports.backoffice_missing_evidence_report import (
    generate_backoffice_missing_evidence_report,
)
from broker_agents.reports.decision_candidate_audit_report import (
    generate_decision_candidate_audit,
)


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_PATH = ROOT / "examples" / "portfolio_context.yaml"


def _load_pack(ticker: str = "MSFT") -> dict:
    path = ROOT / "examples" / f"{ticker.lower()}_input.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _merged_pack(ticker: str = "MSFT") -> dict:
    return merge_portfolio_context_into_pack(
        _load_pack(ticker),
        load_portfolio_context(CONTEXT_PATH),
    )


def test_portfolio_context_example_loads() -> None:
    context = load_portfolio_context(CONTEXT_PATH)

    assert context["provided"] is True
    assert context["investor_profile"]["portfolio_name"] == "Manual Test Portfolio"


def test_merge_sets_portfolio_context_form_provided() -> None:
    merged = _merged_pack()

    assert merged["portfolio_context_form"]["provided"] is True


def test_bogle_report_uses_supplied_portfolio_context() -> None:
    report = BogleAgent(
        pack=_merged_pack(),
        method_path=ROOT / "methods" / "bogle_method.yaml",
    ).generate_report()

    assert "Portfolio Context Analysis" in report
    assert "Portfolio context provided: Yes" in report
    assert "Index core weight: 85.0%" in report
    assert "Individual Stock Acceptable at Limited Weight Candidate" in report
    assert "## Decision\nPrefer Broad Index" in report


def test_bogle_candidate_and_eligibility_clear_missing_context_blocker() -> None:
    pack = _merged_pack()
    candidate = build_decision_candidate(pack, "bogle")
    eligibility = evaluate_promotion_eligibility(pack, "bogle")
    combined = " ".join(
        candidate["decision_blockers"] + eligibility["blocking_conditions"]
    ).lower()

    assert candidate["candidate_decision"] == (
        "Individual Stock Acceptable at Limited Weight Candidate"
    )
    assert eligibility["promotion_eligibility"] == "Conditionally Eligible"
    assert eligibility["auto_promotion_allowed"] is False
    assert "portfolio context is missing" not in combined


def test_audit_and_missing_evidence_use_supplied_context() -> None:
    context = load_portfolio_context(CONTEXT_PATH)
    audit = generate_decision_candidate_audit(
        ["MSFT", "AAPL", "NVDA"],
        ROOT / "data" / "outputs",
        ROOT / "examples",
        context,
    )
    worklist = generate_backoffice_missing_evidence_report(
        ["MSFT", "AAPL", "NVDA"],
        ROOT / "data" / "outputs",
        ROOT / "examples",
        context,
    )

    assert "Individual Stock Acceptable at Limited Weight Candidate" in audit
    assert "Portfolio context is missing" not in audit
    assert "| MSFT | John Bogle | Portfolio context |" not in worklist
    assert "| AAPL | John Bogle | Portfolio context |" not in worklist
    assert "| NVDA | John Bogle | Portfolio context |" not in worklist
    assert "Proposed position size" in worklist
