"""Tests for generated report quality review."""

from pathlib import Path

from broker_agents.reports.report_quality_review import review_generated_reports


def test_review_generated_reports_contains_expected_sections(tmp_path: Path) -> None:
    reports_dir = tmp_path / "data" / "outputs" / "MSFT"
    reports_dir.mkdir(parents=True)
    report_paths: dict[str, Path] = {
        "backoffice": reports_dir / "msft_backoffice_data_pack.md",
        "buffett": reports_dir / "msft_buffett_report.md",
        "munger": reports_dir / "msft_munger_report.md",
        "fisher": reports_dir / "msft_fisher_report.md",
        "lynch": reports_dir / "msft_lynch_report.md",
        "bogle": reports_dir / "msft_bogle_report.md",
        "agents_summary": reports_dir / "msft_agents_summary.md",
    }
    report_paths["backoffice"].write_text(
        "# Microsoft Corporation Backoffice Data Pack\n\n"
        "This report does not include an investment recommendation.\n\n"
        "## Financial Highlights\n\n## Sources and Data Gaps\n\n### Sources\n\n### Data Gaps\n",
        encoding="utf-8",
    )
    decisions = {
        "buffett": ("Warren Buffett", "Wait for Better Price / Complete Intrinsic Value Work"),
        "munger": ("Charlie Munger", "Buy Gradually / Wait for Better Evidence on AI Capex Returns"),
        "fisher": ("Philip Fisher", "Needs More Scuttlebutt / Watch Closely"),
        "lynch": ("Peter Lynch", "Follow / Watch"),
        "bogle": ("John Bogle", "Prefer Broad Index"),
    }
    for agent, (investor, decision) in decisions.items():
        report_paths[agent].write_text(
            f"# {investor} Report\n\n"
            "## Investor Identity\n\n"
            f"{investor}\n\n"
            "## Company Under Review\n\n"
            "Microsoft Corporation (MSFT)\n\n"
            "## Core Question\n\n"
            "Question.\n\n"
            "## Completed Investor Analysis\n\n"
            "- Done.\n\n"
            "## Missing Backoffice Data\n\n"
            "- Missing.\n\n"
            "## Pending Investor Analysis\n\n"
            "- Pending.\n\n"
            "## Decision\n\n"
            f"{decision}\n\n"
            "## Confidence Level\n\n"
            "Medium\n\n"
            f"## Final {investor.split()[-1]} Statement\n\n"
            "Final statement.\n",
            encoding="utf-8",
        )
    report_paths["agents_summary"].write_text(
        "This is not a consensus recommendation. Each investor agent is independent.",
        encoding="utf-8",
    )

    review = review_generated_reports(report_paths)

    assert "MSFT Reports Quality Review" in review
    assert "Warren Buffett" in review
    assert "Charlie Munger" in review
    assert "Philip Fisher" in review
    assert "Peter Lynch" in review
    assert "John Bogle" in review
    assert "Investor Independence Review" in review
    assert "Recommended Improvements for v0.2" in review


def test_review_generated_reports_reads_aapl_output_directory(tmp_path: Path) -> None:
    reports_dir = tmp_path / "data" / "outputs" / "AAPL"
    reports_dir.mkdir(parents=True)
    report_paths = {
        "backoffice": reports_dir / "aapl_backoffice_data_pack.md",
        "buffett": reports_dir / "aapl_buffett_report.md",
        "munger": reports_dir / "aapl_munger_report.md",
        "fisher": reports_dir / "aapl_fisher_report.md",
        "lynch": reports_dir / "aapl_lynch_report.md",
        "bogle": reports_dir / "aapl_bogle_report.md",
        "agents_summary": reports_dir / "aapl_agents_summary.md",
    }
    for path in report_paths.values():
        path.write_text(
            "# Placeholder\n\n## Decision\n\nNot found\n\n## Confidence Level\n\nMedium\n",
            encoding="utf-8",
        )

    review = review_generated_reports(report_paths)

    assert "AAPL Reports Quality Review" in review
    assert "data" in review
    assert "outputs" in review
