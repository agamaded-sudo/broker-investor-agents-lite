"""Tests for readiness-only historical signal candidate artifacts."""

import json
from pathlib import Path

from typer.testing import CliRunner

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


def _assembly() -> HistoricalEnrichedInputAssembly:
    return HistoricalEnrichedInputAssembly(
        ticker="COST",
        as_of_date="2023-06-30",
        run_id="trial_run",
        historical_mode=True,
        point_in_time_enforcement="readiness_only",
        assembly_status="partial_historical_input",
        safe_for_historical_signal_generation=False,
        partial_sections=["official_financials", "market_prices"],
        readiness_only_sections=[
            "historical_valuation",
            "growth_peg",
            "market_snapshot",
            "scuttlebutt",
            "management_incentives",
            "index_overlap",
            "investor_outputs",
        ],
        leakage_risk_sections=[
            "official_financials",
            "market_prices",
            "historical_valuation",
            "growth_peg",
            "market_snapshot",
            "scuttlebutt",
            "management_incentives",
            "index_overlap",
            "investor_outputs",
        ],
        warnings=["Full point-in-time enforcement is not yet guaranteed."],
        next_required_steps=["Add point-in-time historical valuation inputs."],
    )


def _invoke_analyze_stock(
    outputs_root: Path,
    *extra_args: str,
):
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
            *extra_args,
        ],
    )


def _latest_run(outputs_root: Path) -> tuple[Path, dict]:
    latest = outputs_root / "COST" / "runs" / "latest_run_manifest.json"
    manifest = json.loads(latest.read_text(encoding="utf-8"))
    return latest.parent / manifest["run_id"], manifest


def test_build_historical_signal_readiness_candidate() -> None:
    candidate = build_historical_signal_readiness_candidate(
        _assembly(),
        input_assembly_file="assembly.json",
    )
    payload = candidate.to_dict()

    assert payload["ticker"] == "COST"
    assert payload["as_of_date"] == "2023-06-30"
    assert payload["run_id"] == "trial_run"
    assert payload["historical_signal_candidate"] is True
    assert payload["signal_generation_status"] == "readiness_only"
    assert payload["safe_for_historical_signal_generation"] is False
    assert payload["not_trade_signal"] is True
    assert payload["not_recommendation"] is True
    assert payload["not_allocation_instruction"] is True
    assert payload["blocking_reasons"]
    assert payload["readiness_only_sections"] == (
        _assembly().readiness_only_sections
    )
    assert (
        "Historical enriched input assembly is not safe for full historical "
        "signal generation."
    ) in payload["blocking_reasons"]
    assert "action" not in payload
    assert "score" not in payload
    serialized = json.dumps(payload).lower()
    for forbidden in ("top ranked", "best stock"):
        assert forbidden not in serialized


def test_historical_run_writes_candidate_and_manifest(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    result = _invoke_analyze_stock(
        outputs_root,
        "--as-of-date",
        "2023-06-30",
        "--financials-provider",
        "historical_csv",
        "--financials-root",
        str(HISTORICAL_FINANCIALS),
    )

    assert result.exit_code == 0, result.output
    run_folder, manifest = _latest_run(outputs_root)
    json_path = run_folder / "historical_signal_readiness_candidate.json"
    markdown_path = run_folder / "historical_signal_readiness_candidate.md"
    assert json_path.is_file()
    assert markdown_path.is_file()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    candidate_manifest = manifest["historical_signal_readiness_candidate"]
    assert payload["historical_signal_candidate"] is True
    assert payload["signal_generation_status"] == "readiness_only"
    assert payload["safe_for_historical_signal_generation"] is False
    assert payload["not_trade_signal"] is True
    assert payload["not_recommendation"] is True
    assert candidate_manifest["enabled"] is True
    assert Path(candidate_manifest["candidate_file"]) == json_path
    assert Path(candidate_manifest["candidate_markdown"]) == markdown_path
    assert candidate_manifest["blocking_reasons_count"] == len(
        payload["blocking_reasons"]
    )
    assert candidate_manifest["leakage_risk_sections_count"] == len(
        payload["leakage_risk_sections"]
    )

    markdown = markdown_path.read_text(encoding="utf-8")
    summary = (run_folder / "run_summary.md").read_text(encoding="utf-8")
    assert "Signal generation status: readiness_only" in markdown
    assert (
        "This historical signal readiness candidate is not a recommendation, "
        "ranking, vote, average score, consensus, allocation instruction, "
        "rebalancing instruction, trade signal, or execution instruction."
    ) in markdown
    for text in (
        "Historical Signal Readiness Candidate",
        "Signal Generation Status: readiness_only",
        "Safe for Historical Signal Generation: No",
        "Historical signal generation remains disabled",
    ):
        assert text in summary


def test_historical_readiness_without_csv_still_creates_candidate(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    result = _invoke_analyze_stock(
        outputs_root,
        "--as-of-date",
        "2023-06-30",
    )

    assert result.exit_code == 0, result.output
    run_folder, manifest = _latest_run(outputs_root)
    payload = json.loads(
        (
            run_folder / "historical_signal_readiness_candidate.json"
        ).read_text(encoding="utf-8")
    )
    assert payload["signal_generation_status"] == "readiness_only"
    assert payload["safe_for_historical_signal_generation"] is False
    assert "official_financials" in payload["readiness_only_sections"]
    assert manifest["historical_signal_readiness_candidate"]["enabled"] is True


def test_current_run_keeps_candidate_disabled(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    result = _invoke_analyze_stock(outputs_root)

    assert result.exit_code == 0, result.output
    run_folder, manifest = _latest_run(outputs_root)
    assert not (
        run_folder / "historical_signal_readiness_candidate.json"
    ).exists()
    candidate = manifest["historical_signal_readiness_candidate"]
    assert candidate["enabled"] is False
    assert candidate["signal_generation_status"] == "not_enabled"


def test_validate_historical_signal_candidate_command(tmp_path: Path) -> None:
    candidate = build_historical_signal_readiness_candidate(
        _assembly(),
        input_assembly_file="assembly.json",
    )
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps(candidate.to_dict()), encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "validate-historical-signal-candidate",
            "--candidate-file",
            str(path),
        ],
    )

    assert result.exit_code == 0, result.output
    for text in (
        "ticker=COST",
        "signal_generation_status=readiness_only",
        "safe_for_historical_signal_generation=false",
        "not_trade_signal=true",
        "not_recommendation=true",
        "status=valid_readiness_candidate",
    ):
        assert text in result.output


def test_task82_docs_demo_and_offline_scope() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for text in (
        "historical signal generation readiness trial",
        "historical_signal_readiness_candidate.json",
        "validate-historical-signal-candidate",
        "not full historical signal generation",
        "not written to the main signal ledger",
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
        / "historical"
        / "historical_signal_readiness.py"
    ).read_text(encoding="utf-8").lower()
    for network_call in (
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "urlopen(",
    ):
        assert network_call not in source
