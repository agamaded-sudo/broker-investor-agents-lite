"""Tests for the governed Human Review Queue."""

import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.backoffice.enrichment_pipeline import (
    fixture_paths_for_known_ticker,
    run_backoffice_enrichment_pipeline,
)
from broker_agents.calculators.decision_candidates import CURRENT_DECISIONS
from broker_agents.cli import app
from broker_agents.reports.human_review_queue_report import (
    generate_human_review_queue_report,
)
from broker_agents.review.human_review_queue import generate_human_review_queue

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def _enrich_known_tickers(outputs_root: Path) -> None:
    """Create temporary enriched packs for all queue tests."""
    for ticker in ("MSFT", "AAPL", "NVDA"):
        lower = ticker.lower()
        run_backoffice_enrichment_pipeline(
            ROOT / "examples" / f"{lower}_input.yaml",
            outputs_root / ticker / f"{lower}_enriched_input.yaml",
            **fixture_paths_for_known_ticker(ticker, FIXTURES),
        )


def test_human_review_queue_items_are_deterministic_and_safe(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    _enrich_known_tickers(outputs_root)

    items = generate_human_review_queue(
        ["MSFT", "AAPL", "NVDA"],
        outputs_root,
        ROOT / "examples",
    )

    assert len(items) == 15
    expected_investors = {"Buffett", "Munger", "Fisher", "Lynch", "Bogle"}
    for ticker in ("MSFT", "AAPL", "NVDA"):
        ticker_items = [item for item in items if item.ticker == ticker]
        assert {item.investor for item in ticker_items} == expected_investors
    assert {item.review_id for item in items} >= {
        "HRQ-MSFT-BUFFETT-001",
        "HRQ-AAPL-MUNGER-001",
        "HRQ-NVDA-BOGLE-001",
    }
    assert all(item.status == "Open" for item in items)
    assert all(item.blocks_promotion for item in items)
    assert all(
        {
            "not_a_recommendation",
            "no_auto_promotion",
            "human_review_required",
            "final_decision_unchanged",
        }.issubset(item.safety_flags)
        for item in items
    )
    for item in items:
        key = item.investor.lower()
        assert item.final_decision == CURRENT_DECISIONS[key]

    fisher = next(item for item in items if item.investor == "Fisher")
    munger = next(item for item in items if item.investor == "Munger")
    buffett = next(item for item in items if item.investor == "Buffett")
    bogle = next(item for item in items if item.investor == "Bogle")
    assert "scuttlebutt" in " ".join(fisher.related_gap).lower()
    assert any(
        term in " ".join(munger.related_gap).lower()
        for term in ("incentives", "ownership")
    )
    assert any(
        term in " ".join(buffett.related_gap).lower()
        for term in ("owner earnings", "capex")
    )
    assert any(
        term in (bogle.review_question + " " + " ".join(bogle.related_gap)).lower()
        for term in ("index overlap", "benchmark", "portfolio fit")
    )


def test_human_review_queue_report_contains_governance_sections(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    _enrich_known_tickers(outputs_root)
    items = generate_human_review_queue(
        ["MSFT", "AAPL", "NVDA"],
        outputs_root,
        ROOT / "examples",
    )

    report = generate_human_review_queue_report(items)

    assert "Human Review Queue" in report
    assert "Queue Summary" in report
    assert "Review Items" in report
    assert "Promotion Safety Gate" in report
    assert "Suggested Review Order" in report
    assert "Safety Check" in report
    assert "Auto-promotion disabled" in report
    assert "not a recommendation, ranking, vote, average score, consensus" in report
    assert "allocation instruction" in report
    assert "trade signal" in report


def test_human_review_queue_cli_writes_markdown_and_json(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    _enrich_known_tickers(outputs_root)
    markdown_path = tmp_path / "human_review_queue.md"
    json_path = tmp_path / "human_review_queue.json"

    result = CliRunner().invoke(
        app,
        [
            "human-review-queue",
            "--tickers",
            "MSFT,AAPL,NVDA",
            "--outputs-root",
            str(outputs_root),
            "--examples-root",
            str(ROOT / "examples"),
            "--output",
            str(markdown_path),
            "--json-output",
            str(json_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert markdown_path.exists()
    assert json_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert len(payload) == 15
    assert payload[0]["status"] == "Open"
    assert payload[0]["blocks_promotion"] is True
    assert payload[0]["safety_flags"]
