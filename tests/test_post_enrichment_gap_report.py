"""Tests for the post-enrichment evidence gap report."""

from pathlib import Path

from broker_agents.backoffice.enrichment_pipeline import (
    fixture_paths_for_known_ticker,
    run_backoffice_enrichment_pipeline,
)
from broker_agents.reports.post_enrichment_gap_report import (
    generate_post_enrichment_gap_report,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def _enrich_known_tickers(outputs_root: Path) -> None:
    """Create deterministic enriched packs for the report test."""
    for ticker in ("MSFT", "AAPL", "NVDA"):
        lower = ticker.lower()
        run_backoffice_enrichment_pipeline(
            ROOT / "examples" / f"{lower}_input.yaml",
            outputs_root / ticker / f"{lower}_enriched_input.yaml",
            **fixture_paths_for_known_ticker(ticker, FIXTURES),
        )


def test_post_enrichment_gap_report_contains_required_analysis(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    _enrich_known_tickers(outputs_root)

    report = generate_post_enrichment_gap_report(
        ["MSFT", "AAPL", "NVDA"],
        outputs_root,
        ROOT / "examples",
    )

    assert "Post-Enrichment Evidence Gap Report" in report
    assert "What Improved After Enrichment" in report
    assert "Remaining Evidence Gaps by Investor" in report
    assert "Promotion Blockers After Enrichment" in report
    assert "Fetcher Roadmap From Remaining Gaps" in report
    assert "Human Review Queue Candidates" in report
    assert "Safety Check" in report
    for investor in ("Buffett", "Munger", "Fisher", "Lynch", "Bogle"):
        assert investor in report
    assert "customer scuttlebutt" in report
    assert "management incentives" in report
    assert "insider ownership" in report
    assert "Benchmark Risk & Index Holdings Fetcher" in report
    assert "maintenance vs growth capex" in report
    assert "Auto-promotion disabled" in report
    assert "not a recommendation, ranking, vote, average score, or consensus" in report
    assert "| Rank |" not in report
    assert "combined recommendation" not in report.lower()
