"""Tests for preliminary owner earnings calculations."""

from pathlib import Path

import yaml

from broker_agents.agents.buffett_agent import BuffettAgent
from broker_agents.calculators.owner_earnings import calculate_owner_earnings_snapshot
from broker_agents.reports.agents_comparison_report import generate_agents_comparison
from broker_agents.reports.backoffice_report import generate_backoffice_report


def _load_example(filename: str) -> dict:
    path = Path(__file__).resolve().parents[1] / "examples" / filename
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_msft_owner_earnings_capex_to_ocf_is_high() -> None:
    snapshot = calculate_owner_earnings_snapshot(_load_example("msft_input.yaml"))

    assert snapshot["capex_to_ocf"] >= 0.35
    assert snapshot["capex_intensity_label"] == "high"


def test_aapl_owner_earnings_capex_to_ocf_is_low_and_strong() -> None:
    snapshot = calculate_owner_earnings_snapshot(_load_example("aapl_input.yaml"))

    assert snapshot["capex_to_ocf"] < 0.15
    assert snapshot["capex_intensity_label"] == "low"
    assert snapshot["owner_earnings_quality_label"] == "strong"


def test_buffett_report_contains_preliminary_owner_earnings_snapshot() -> None:
    pack = _load_example("msft_input.yaml")
    method_path = Path(__file__).resolve().parents[1] / "methods" / "buffett_method.yaml"

    report = BuffettAgent(pack=pack, method_path=method_path).generate_report()

    assert "Preliminary Owner Earnings Snapshot" in report


def test_comparison_report_contains_buffett_owner_earnings_comparison(tmp_path: Path) -> None:
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
        generate_backoffice_report(_load_example("msft_input.yaml")),
        encoding="utf-8",
    )
    (right_dir / "aapl_backoffice_data_pack.md").write_text(
        generate_backoffice_report(_load_example("aapl_input.yaml")),
        encoding="utf-8",
    )

    comparison = generate_agents_comparison("MSFT", "AAPL", left_summary, right_summary)

    assert "Buffett Owner Earnings Comparison" in comparison
