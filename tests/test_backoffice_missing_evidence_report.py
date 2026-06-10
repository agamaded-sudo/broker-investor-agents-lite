"""Tests for the Backoffice missing-evidence request report."""

from pathlib import Path

from broker_agents.reports.backoffice_missing_evidence_report import (
    generate_backoffice_missing_evidence_report,
)


def test_backoffice_missing_evidence_report_contains_required_worklist() -> None:
    root = Path(__file__).resolve().parents[1]

    report = generate_backoffice_missing_evidence_report(
        ["MSFT", "AAPL", "NVDA"],
        root / "data" / "outputs",
        root / "examples",
    )

    assert "Backoffice Missing Evidence Request Report" in report
    assert "not a recommendation" in report
    assert "MSFT" in report
    assert "AAPL" in report
    assert "NVDA" in report
    assert "Evidence Request Summary" in report
    assert "High Priority Backoffice Worklist" in report
    assert "User Input Requests" in report
    assert "Suggested Backoffice Execution Order" in report
    assert "portfolio context" in report.lower()
    assert "intrinsic value range" in report.lower()
    assert "scuttlebutt" in report.lower()
    assert "PEG" in report
    assert "inversion risk evidence" in report.lower()
