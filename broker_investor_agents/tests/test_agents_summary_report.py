"""Tests for independent agents summary reports."""

from pathlib import Path

from broker_agents.reports.agents_summary_report import generate_agents_summary


def test_generate_agents_summary_includes_independent_investor_names(tmp_path: Path) -> None:
    report_contents = {
        "buffett": ("Warren Buffett", "Wait for Better Price", "Medium"),
        "munger": ("Charlie Munger", "Buy Gradually", "Medium"),
        "fisher": ("Philip Fisher", "Needs More Scuttlebutt", "Medium"),
        "lynch": ("Peter Lynch", "Follow / Watch", "Medium"),
        "bogle": ("John Bogle", "Prefer Broad Index", "Medium"),
    }
    report_paths: dict[str, Path] = {}

    for agent_name, (investor, decision, confidence) in report_contents.items():
        path = tmp_path / f"msft_{agent_name}_report.md"
        path.write_text(
            f"# {investor} Report\n\nDecision: {decision}\nConfidence: {confidence}\n",
            encoding="utf-8",
        )
        report_paths[agent_name] = path

    summary = generate_agents_summary("Microsoft Corporation", "MSFT", report_paths)

    assert "Independent Investor Agents Summary" in summary
    assert "Microsoft Corporation" in summary
    assert "MSFT" in summary
    assert "Warren Buffett" in summary
    assert "Charlie Munger" in summary
    assert "Philip Fisher" in summary
    assert "Peter Lynch" in summary
    assert "John Bogle" in summary
    assert "not a consensus recommendation" in summary
