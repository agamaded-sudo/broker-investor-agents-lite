"""Tests for the decision candidate audit report."""

from pathlib import Path

from broker_agents.reports.decision_candidate_audit_report import (
    generate_decision_candidate_audit,
)


def test_decision_candidate_audit_contains_required_content() -> None:
    root = Path(__file__).resolve().parents[1]

    audit = generate_decision_candidate_audit(
        ["MSFT", "AAPL", "NVDA"],
        root / "data" / "outputs",
        root / "examples",
    )

    assert "Decision Candidate Audit Report" in audit
    assert "MSFT" in audit
    assert "AAPL" in audit
    assert "NVDA" in audit
    assert "Candidate vs Final Decision Table" in audit
    assert "Candidate Support Check" in audit
    assert "Upgrade Readiness Review" in audit
    assert "does not create a recommendation" in audit
    assert "| AAPL | Warren Buffett |" in audit
    assert "Buy Gradually Candidate" in audit
    assert "portfolio context" in audit.lower()
    assert "Index overlap and current portfolio exposure" in audit
