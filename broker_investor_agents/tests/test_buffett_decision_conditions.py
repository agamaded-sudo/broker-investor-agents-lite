"""Tests for Buffett decision upgrade and downgrade conditions."""

from pathlib import Path

import yaml

from broker_agents.agents.buffett_agent import BuffettAgent
from broker_agents.calculators.buffett_decision_conditions import (
    build_buffett_decision_conditions,
)
from broker_agents.reports.agents_comparison_report import generate_agents_comparison
from broker_agents.reports.backoffice_report import generate_backoffice_report


def _load_example(filename: str) -> dict:
    path = Path(__file__).resolve().parents[1] / "examples" / filename
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_msft_upgrade_conditions_mention_capex_returns_or_split() -> None:
    conditions = build_buffett_decision_conditions(_load_example("msft_input.yaml"))
    upgrade_text = " ".join(conditions["upgrade_conditions"]).lower()

    assert "capex produces attractive returns" in upgrade_text or "maintenance vs growth capex" in upgrade_text


def test_aapl_watch_items_mention_cash_conversion_or_buybacks() -> None:
    conditions = build_buffett_decision_conditions(_load_example("aapl_input.yaml"))
    watch_text = " ".join(conditions["watch_items"]).lower()

    assert "cash conversion" in watch_text or "buybacks" in watch_text


def test_buffett_report_contains_decision_upgrade_downgrade_conditions() -> None:
    pack = _load_example("msft_input.yaml")
    method_path = Path(__file__).resolve().parents[1] / "methods" / "buffett_method.yaml"

    report = BuffettAgent(pack=pack, method_path=method_path).generate_report()

    assert "Decision Upgrade / Downgrade Conditions" in report


def test_comparison_contains_buffett_upgrade_downgrade_conditions(tmp_path: Path) -> None:
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
    for directory, ticker, pack_file in [
        (left_dir, "msft", "msft_input.yaml"),
        (right_dir, "aapl", "aapl_input.yaml"),
    ]:
        pack = _load_example(pack_file)
        (directory / f"{ticker}_backoffice_data_pack.md").write_text(
            generate_backoffice_report(pack),
            encoding="utf-8",
        )
        method_path = Path(__file__).resolve().parents[1] / "methods" / "buffett_method.yaml"
        (directory / f"{ticker}_buffett_report.md").write_text(
            BuffettAgent(pack=pack, method_path=method_path).generate_report(),
            encoding="utf-8",
        )

    comparison = generate_agents_comparison("MSFT", "AAPL", left_summary, right_summary)

    assert "Buffett Upgrade/Downgrade Conditions Comparison" in comparison
