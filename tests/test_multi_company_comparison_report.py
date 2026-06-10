"""Tests for multi-company independent-agent comparisons."""

from pathlib import Path

from broker_agents.reports.multi_company_comparison_report import (
    generate_multi_company_comparison,
)


def test_multi_company_comparison_contains_required_sections() -> None:
    root = Path(__file__).resolve().parents[1]

    report = generate_multi_company_comparison(
        ["MSFT", "AAPL", "NVDA"],
        root / "data" / "outputs",
        root / "examples",
    )

    assert "Multi-Company Independent Investor Agents Comparison" in report
    assert "MSFT" in report
    assert "AAPL" in report
    assert "NVDA" in report
    assert "Business Model Signal Table" in report
    assert "Buffett Owner Earnings Table" in report
    assert "Buffett Valuation Guardrails Table" in report
    assert "Munger Top Inversion Risk Table" in report
    assert "Investor Decisions Table" in report
    assert "not a ranking" in report
