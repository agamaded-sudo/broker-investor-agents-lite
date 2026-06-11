"""Tests for the analyze-stock signal archive and run result ledger."""

import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.cli import app

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
PORTFOLIO_CONTEXT = EXAMPLES / "portfolio_context.yaml"
EXPECTED_COST_DECISIONS = {
    "buffett_final_decision": (
        "Wait for Better Price / Complete Intrinsic Value Work"
    ),
    "munger_final_decision": (
        "Buy Gradually / Wait for Better Evidence on Incentives and "
        "Long-Term Durability"
    ),
    "fisher_final_decision": "Needs More Scuttlebutt / Watch Closely",
    "lynch_final_decision": "Follow / Watch",
    "bogle_final_decision": "Prefer Broad Index",
}


def _ledger_records(outputs_root: Path) -> list[dict]:
    """Load every JSONL ledger record from an output root."""
    ledger_path = outputs_root / "signal_archive" / "signal_ledger.jsonl"
    assert ledger_path.exists()
    return [
        json.loads(line)
        for line in ledger_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _ticker_args(outputs_root: Path) -> list[str]:
    """Build shared offline paths for ticker-mode commands."""
    return [
        "--examples-root",
        str(EXAMPLES),
        "--outputs-root",
        str(outputs_root),
        "--fixtures-root",
        str(FIXTURES),
        "--portfolio-context",
        str(PORTFOLIO_CONTEXT),
    ]


def test_analyze_stock_appends_cost_signal_record(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    result = CliRunner().invoke(
        app,
        [
            "analyze-stock",
            "--ticker",
            "COST",
            *_ticker_args(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Signal Archive Record" in result.output
    assert "archived" in result.output
    assert "Signal Ledger" in result.output

    archive_dir = outputs_root / "signal_archive"
    csv_path = archive_dir / "signal_ledger.csv"
    snapshot_path = archive_dir / "latest_signal_ledger_snapshot.json"
    assert csv_path.exists()
    assert snapshot_path.exists()
    records = _ledger_records(outputs_root)
    assert len(records) == 1
    record = records[0]
    assert record["ticker"] == "COST"
    assert record["run_id"]
    assert record["run_manifest_path"]
    assert record["readiness_label"]
    assert record["source_verification_status"]
    assert record["total_investor_responses"] == 5
    assert record["total_work_orders"] > 0
    assert record["batch_run_id"] is None
    for field, expected in EXPECTED_COST_DECISIONS.items():
        assert record[field] == expected
    for investor in ("buffett", "munger", "fisher", "lynch", "bogle"):
        assert record[f"{investor}_interest_level"]
    for field in (
        "auto_promotion_disabled",
        "human_review_required",
        "no_recommendation",
        "no_ranking",
        "no_consensus",
        "no_trade_signal",
    ):
        assert record[field] is True

    with csv_path.open(encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert len(csv_rows) == 1
    assert csv_rows[0]["ticker"] == "COST"
    assert csv_rows[0]["run_id"] == record["run_id"]
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert snapshot["total_archived_records"] == 1
    assert snapshot["latest_run_id"] == record["run_id"]
    assert snapshot["latest_ticker"] == "COST"

    forbidden_output_fields = {
        "recommendation",
        "ranking_result",
        "vote",
        "average_score",
        "consensus_result",
        "allocation_instruction",
        "rebalancing_instruction",
        "trade_instruction",
    }
    assert forbidden_output_fields.isdisjoint(record)


def test_analyze_batch_archives_each_completed_ticker(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    result = CliRunner().invoke(
        app,
        [
            "analyze-batch",
            "--tickers",
            "MSFT,AAPL,NVDA,COST",
            *_ticker_args(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Signal Archive Records: 4" in result.output
    assert "Signal Ledger" in result.output
    records = _ledger_records(outputs_root)
    assert [record["ticker"] for record in records] == [
        "MSFT",
        "AAPL",
        "NVDA",
        "COST",
    ]
    batch_ids = {record["batch_run_id"] for record in records}
    batch_folders = {record["batch_folder"] for record in records}
    assert len(batch_ids) == 1
    assert None not in batch_ids
    assert len(batch_folders) == 1
    assert None not in batch_folders
    for record in records:
        assert Path(record["run_folder"]).is_dir()
        assert Path(record["broker_deal_package_path"]).is_file()
        assert record["status"] == "completed"
        assert record["auto_promotion_disabled"] is True
        assert record["human_review_required"] is True
        assert record["no_recommendation"] is True
        assert record["no_ranking"] is True
        assert record["no_consensus"] is True
        assert record["no_trade_signal"] is True

    snapshot = json.loads(
        (
            outputs_root
            / "signal_archive"
            / "latest_signal_ledger_snapshot.json"
        ).read_text(encoding="utf-8")
    )
    assert snapshot["total_archived_records"] == 4
    assert snapshot["latest_batch_run_id"] in batch_ids
    assert snapshot["latest_ticker"] == "COST"


def test_signal_archive_documentation_and_demo_runner_remain() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Signal Archive / Run Result Ledger" in readme
    assert "data/outputs/signal_archive/signal_ledger.jsonl" in readme
    assert "data/outputs/signal_archive/signal_ledger.csv" in readme

    demo_script = (ROOT / "scripts" / "run_first_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "python -m ruff check ." in demo_script
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in demo_script
    assert "python -m broker_agents.cli deal-intakes" in demo_script
    assert "python -m broker_agents.cli run-deals" in demo_script
