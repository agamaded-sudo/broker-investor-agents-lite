"""Tests for independent investor agent comparison reports."""

from pathlib import Path

from broker_agents.reports.agents_comparison_report import generate_agents_comparison


def test_generate_agents_comparison_contains_expected_terms(tmp_path: Path) -> None:
    left_dir = tmp_path / "MSFT"
    right_dir = tmp_path / "AAPL"
    left_dir.mkdir()
    right_dir.mkdir()
    left_summary = left_dir / "msft_agents_summary.md"
    right_summary = right_dir / "aapl_agents_summary.md"
    summary_table = """| Investor | Decision | Confidence | Report File |
| --- | --- | --- | --- |
| Warren Buffett | Wait for Better Price / Complete Intrinsic Value Work | Medium | report.md |
| Charlie Munger | Buy Gradually / Wait for Better Evidence on AI Capex Returns | Medium | report.md |
| Philip Fisher | Needs More Scuttlebutt / Watch Closely | Medium | report.md |
| Peter Lynch | Follow / Watch | Medium | report.md |
| John Bogle | Prefer Broad Index | Medium | report.md |
"""
    left_summary.write_text(summary_table, encoding="utf-8")
    right_summary.write_text(summary_table, encoding="utf-8")
    (left_dir / "msft_backoffice_data_pack.md").write_text(
        "- Primary growth engine: Cloud and AI infrastructure\n"
        "- Dominant revenue stream: Enterprise software, cloud, and productivity ecosystem\n"
        "- Major capex issue: AI and data center infrastructure capex\n"
        "- Fisher angle: Needs customer/developer scuttlebutt\n"
        "- Lynch angle: Cloud + AI + productivity ecosystem story\n"
        "- Bogle angle: Large index constituent\n",
        encoding="utf-8",
    )
    (right_dir / "aapl_backoffice_data_pack.md").write_text(
        "- Primary growth engine: iPhone ecosystem and services monetization\n"
        "- Dominant revenue stream: iPhone-led hardware ecosystem with services expansion\n"
        "- Major capex issue: Lower direct capex intensity than cloud infrastructure businesses\n"
        "- Fisher angle: Needs installed base and services adoption evidence\n"
        "- Lynch angle: Ecosystem + services monetization story\n"
        "- Bogle angle: Large index constituent\n",
        encoding="utf-8",
    )
    for directory, ticker, rationale in [
        (left_dir, "msft", "MSFT rationale."),
        (right_dir, "aapl", "AAPL rationale."),
    ]:
        for agent in ["buffett", "munger", "fisher", "lynch", "bogle"]:
            (directory / f"{ticker}_{agent}_report.md").write_text(
                f"## Decision Rationale\n\n{rationale}\n",
                encoding="utf-8",
            )

    comparison = generate_agents_comparison("MSFT", "AAPL", left_summary, right_summary)

    assert "Independent Investor Agents Comparison" in comparison
    assert "MSFT" in comparison
    assert "AAPL" in comparison
    assert "Warren Buffett" in comparison
    assert "John Bogle" in comparison
    assert "not a recommendation" in comparison
    assert "Company-Specific Signal Comparison" in comparison
    assert "Rationale Differences" in comparison
    assert "Recommended Improvements" in comparison
