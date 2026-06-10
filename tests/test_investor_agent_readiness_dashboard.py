"""Tests for the investor-agent readiness dashboard."""

from pathlib import Path

from broker_agents.reports.investor_agent_readiness_dashboard import (
    generate_investor_agent_readiness_dashboard,
)


def test_readiness_dashboard_contains_required_content() -> None:
    root = Path(__file__).resolve().parents[1]
    report = generate_investor_agent_readiness_dashboard(
        ["MSFT", "AAPL", "NVDA"],
        root / "data" / "outputs",
        root / "examples",
    )

    assert "Investor Agent Readiness Dashboard" in report
    assert "not a recommendation" in report
    for investor in ("Buffett", "Munger", "Fisher", "Lynch", "Bogle"):
        assert investor in report
    assert "Agent Readiness Summary" in report
    assert "Evidence Bottlenecks" in report
    assert "Recommended Development Sequence" in report
    assert "Not Yet Ready For" in report
    assert "Auto-promotion; it remains disabled" in report
    assert "| Fisher |" in report
    assert "Needs Evidence" in report
    assert "Bogle benchmark risk" in report
