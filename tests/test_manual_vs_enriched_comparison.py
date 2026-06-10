"""Tests for manual versus enriched evidence comparison reports."""

from pathlib import Path

from broker_agents.backoffice.enrichment_pipeline import (
    fixture_paths_for_known_ticker,
    run_backoffice_enrichment_pipeline,
)
from broker_agents.reports.manual_vs_enriched_comparison import (
    generate_manual_vs_enriched_comparison,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def _make_enriched_pack(ticker: str, outputs_root: Path) -> None:
    ticker_upper = ticker.upper()
    ticker_lower = ticker.lower()
    run_backoffice_enrichment_pipeline(
        ROOT / "examples" / f"{ticker_lower}_input.yaml",
        outputs_root / ticker_upper / f"{ticker_lower}_enriched_input.yaml",
        **fixture_paths_for_known_ticker(ticker_upper, FIXTURES),
    )


def test_manual_vs_enriched_comparison_contains_required_sections(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    for ticker in ("MSFT", "AAPL", "NVDA"):
        _make_enriched_pack(ticker, outputs_root)

    report = generate_manual_vs_enriched_comparison(
        ["MSFT", "AAPL", "NVDA"],
        outputs_root,
    )

    assert "Manual vs Enriched Pipeline Comparison" in report
    assert "Source Quality Change" in report
    assert "Investor Final Decision Stability" in report
    assert "Candidate Decision Changes" in report
    assert "Evidence Improvements" in report
    assert "Remaining Gaps After Enrichment" in report
    assert "Safety Check" in report
    assert "Final decisions unchanged: Yes" in report
    assert "Auto-promotion disabled: Yes" in report
    assert "No ranking" in report
    assert "No consensus" in report
    assert "official financials" in report.lower()


def test_candidate_table_does_not_override_final_decision_table(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    _make_enriched_pack("MSFT", outputs_root)
    manual_dir = outputs_root / "MSFT"
    enriched_dir = manual_dir / "enriched"
    enriched_dir.mkdir(parents=True)
    summary_template = """# Summary

| Investor | Decision | Confidence | Report File |
| --- | --- | --- | --- |
| Warren Buffett | Final Decision | Medium | report.md |

## Decision Candidate Snapshot

| Investor | Decision Candidate | Candidate Confidence | Main Blocker |
| --- | --- | --- | --- |
| Warren Buffett | {candidate} | Medium | blocker |
"""
    (manual_dir / "msft_agents_summary.md").write_text(
        summary_template.format(candidate="Manual Candidate"),
        encoding="utf-8",
    )
    (enriched_dir / "msft_agents_summary.md").write_text(
        summary_template.format(candidate="Enriched Candidate"),
        encoding="utf-8",
    )

    report = generate_manual_vs_enriched_comparison(["MSFT"], outputs_root)

    assert "Final Decision -> Final Decision" in report
    assert "Final decisions unchanged: Yes" in report
