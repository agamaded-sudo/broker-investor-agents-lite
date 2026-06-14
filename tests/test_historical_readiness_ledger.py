"""Tests for the separate historical readiness candidate ledger."""

import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.archive.historical_readiness_ledger import (
    LEDGER_FIELDS,
    append_historical_readiness_candidate,
)
from broker_agents.cli import app
from broker_agents.historical.historical_enriched_input import (
    HistoricalEnrichedInputAssembly,
)
from broker_agents.historical.historical_signal_readiness import (
    build_historical_signal_readiness_candidate,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
HISTORICAL_FINANCIALS = FIXTURES / "historical_financials"
PORTFOLIO_CONTEXT = EXAMPLES / "portfolio_context.yaml"


def _candidate():
    assembly = HistoricalEnrichedInputAssembly(
        ticker="COST",
        as_of_date="2023-06-30",
        run_id="trial_run",
        historical_mode=True,
        point_in_time_enforcement="readiness_only",
        assembly_status="partial_historical_input",
        safe_for_historical_signal_generation=False,
        partial_sections=["official_financials", "market_prices"],
        readiness_only_sections=["historical_valuation", "investor_outputs"],
        leakage_risk_sections=[
            "official_financials",
            "market_prices",
            "historical_valuation",
            "investor_outputs",
        ],
        warnings=["Point-in-time coverage remains incomplete."],
        next_required_steps=["Add historical valuation inputs."],
    )
    return build_historical_signal_readiness_candidate(
        assembly,
        input_assembly_file="assembly.json",
    )


def _invoke_historical(outputs_root: Path):
    return CliRunner().invoke(
        app,
        [
            "analyze-stock",
            "--ticker",
            "COST",
            "--examples-root",
            str(EXAMPLES),
            "--outputs-root",
            str(outputs_root),
            "--fixtures-root",
            str(FIXTURES),
            "--portfolio-context",
            str(PORTFOLIO_CONTEXT),
            "--as-of-date",
            "2023-06-30",
            "--financials-provider",
            "historical_csv",
            "--financials-root",
            str(HISTORICAL_FINANCIALS),
        ],
    )


def test_append_historical_readiness_candidate_writes_separate_ledgers(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    result = append_historical_readiness_candidate(
        outputs_root=outputs_root,
        candidate=_candidate(),
        run_folder=outputs_root / "COST" / "runs" / "trial_run",
        candidate_file=Path("candidate.json"),
        assembly_file=Path("assembly.json"),
        created_at="2026-06-13T00:00:00+00:00",
    )

    assert result.jsonl_path.is_file()
    assert result.csv_path.is_file()
    assert result.snapshot_path.is_file()
    record = json.loads(
        result.jsonl_path.read_text(encoding="utf-8").strip()
    )
    assert record["record_type"] == "historical_signal_readiness_candidate"
    assert record["signal_generation_status"] == "readiness_only"
    assert record["safe_for_historical_signal_generation"] is False
    assert record["not_trade_signal"] is True
    assert record["not_recommendation"] is True
    assert record["not_allocation_instruction"] is True
    assert set(record) == set(LEDGER_FIELDS)
    serialized = json.dumps(record).lower()
    for forbidden in (
        '"action"',
        '"score"',
        "top ranked",
        "best stock",
        "execution instruction",
    ):
        assert forbidden not in serialized

    with result.csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert tuple(reader.fieldnames or ()) == LEDGER_FIELDS
    assert len(rows) == 1
    assert rows[0]["ticker"] == "COST"
    assert rows[0]["metadata_enrichment_status"] == "not_available"
    assert rows[0]["coverage_quality_label"] == "not_available"
    assert rows[0]["coverage_guardrail_status"] == "not_available"

    snapshot = json.loads(
        result.snapshot_path.read_text(encoding="utf-8")
    )
    assert snapshot["total_records"] == 1
    assert snapshot["latest_record"] == record
    assert "readiness-only research artifacts" in snapshot["safety_notice"]


def test_historical_analyze_stock_archives_readiness_separately(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    result = _invoke_historical(outputs_root)

    assert result.exit_code == 0, result.output
    assert "Historical Readiness Ledger Record" in result.output
    assert "Historical Readiness Ledger" in result.output
    readiness_dir = outputs_root / "historical_readiness_ledger"
    readiness_jsonl = (
        readiness_dir / "historical_signal_readiness_ledger.jsonl"
    )
    main_jsonl = outputs_root / "signal_archive" / "signal_ledger.jsonl"
    assert readiness_jsonl.is_file()
    assert main_jsonl.is_file()
    assert readiness_jsonl != main_jsonl

    readiness_records = [
        json.loads(line)
        for line in readiness_jsonl.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    main_records = [
        json.loads(line)
        for line in main_jsonl.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(readiness_records) == 1
    assert len(main_records) == 1
    assert readiness_records[0]["record_type"] == (
        "historical_signal_readiness_candidate"
    )
    assert readiness_records[0]["metadata_enrichment_status"] == "partial"
    assert readiness_records[0]["readiness_label"]
    assert readiness_records[0]["source_verification_status"]
    assert readiness_records[0]["buffett_interest_level"]
    assert readiness_records[0]["coverage_quality_label"]
    assert readiness_records[0]["coverage_quality_severity"]
    assert readiness_records[0]["coverage_guardrail_status"]
    assert isinstance(
        readiness_records[0]["has_delayed_price_anchor"],
        bool,
    )
    assert isinstance(readiness_records[0]["has_limited_financials"], bool)
    assert "record_type" not in main_records[0]

    latest_manifest = json.loads(
        (
            outputs_root / "COST" / "runs" / "latest_run_manifest.json"
        ).read_text(encoding="utf-8")
    )
    receipt = latest_manifest["historical_readiness_ledger_record"]
    assert receipt["archived"] is True
    assert Path(receipt["ledger_jsonl"]) == readiness_jsonl
    assert Path(receipt["ledger_csv"]).is_file()
    assert Path(receipt["latest_snapshot"]).is_file()
    assert receipt["signal_generation_status"] == "readiness_only"
    assert receipt["not_trade_signal"] is True
    assert receipt["not_recommendation"] is True
    assert receipt["not_allocation_instruction"] is True


def test_current_analyze_stock_does_not_create_readiness_ledger(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    result = CliRunner().invoke(
        app,
        [
            "analyze-stock",
            "--ticker",
            "COST",
            "--examples-root",
            str(EXAMPLES),
            "--outputs-root",
            str(outputs_root),
            "--fixtures-root",
            str(FIXTURES),
            "--portfolio-context",
            str(PORTFOLIO_CONTEXT),
        ],
    )

    assert result.exit_code == 0, result.output
    assert not (outputs_root / "historical_readiness_ledger").exists()
    manifest = json.loads(
        (
            outputs_root / "COST" / "runs" / "latest_run_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["historical_readiness_ledger_record"]["archived"] is False


def test_show_historical_readiness_ledger_command(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    historical = _invoke_historical(outputs_root)
    assert historical.exit_code == 0, historical.output

    result = CliRunner().invoke(
        app,
        [
            "show-historical-readiness-ledger",
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    for text in (
        "total_records=1",
        "latest_ticker=COST",
        "latest_as_of_date=2023-06-30",
        "latest_signal_generation_status=readiness_only",
        "latest_not_trade_signal=true",
        "latest_not_recommendation=true",
        "ledger_jsonl=",
        "ledger_csv=",
    ):
        assert text in result.output


def test_task83_documentation_demo_and_offline_scope() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for text in (
        "historical readiness candidate ledger",
        "historical_signal_readiness_ledger.jsonl",
        "historical_signal_readiness_ledger.csv",
        "latest_historical_signal_readiness_ledger_snapshot.json",
        "separate from",
        "must not be confused with the main signal ledger",
    ):
        assert text in readme

    demo = (ROOT / "scripts" / "run_first_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "python -m ruff check ." in demo
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in demo
    assert "python -m broker_agents.cli" in demo

    source = (
        ROOT
        / "src"
        / "broker_agents"
        / "archive"
        / "historical_readiness_ledger.py"
    ).read_text(encoding="utf-8").lower()
    for network_call in (
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "urlopen(",
    ):
        assert network_call not in source
