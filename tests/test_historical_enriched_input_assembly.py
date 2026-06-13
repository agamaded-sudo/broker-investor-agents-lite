"""Tests for run-local historical enriched input readiness assembly."""

import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.historical.historical_enriched_input import (
    build_historical_enriched_input_assembly,
)
from broker_agents.historical.price_windows import (
    build_analysis_price_window,
)
from broker_agents.historical.snapshot_contract import (
    build_historical_snapshot_contract,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
HISTORICAL_FINANCIALS = FIXTURES / "historical_financials"
PORTFOLIO_CONTEXT = EXAMPLES / "portfolio_context.yaml"


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
    manifest_path = (
        outputs_root / "COST" / "runs" / "latest_run_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return manifest_path.parent / manifest["run_id"], manifest


def test_build_historical_enriched_input_assembly() -> None:
    contract = build_historical_snapshot_contract(
        "2023-06-30",
        price_provider="fixture",
        ticker="COST",
        fixtures_root=FIXTURES,
    )
    price_window = {
        "analysis_window": build_analysis_price_window(
            "2023-06-30"
        ).to_dict()
    }
    financials_snapshot = {
        "enabled": True,
        "provider": "historical_financials_csv",
        "snapshot_file": "snapshot.csv",
        "rows_before_filter": 5,
        "rows_after_filter": 3,
        "future_rows_excluded_count": 1,
        "rows_missing_availability_date_count": 1,
        "status": "as_of_filter_applied",
        "warnings": ["One row lacked an availability date."],
    }

    assembly = build_historical_enriched_input_assembly(
        ticker="COST",
        as_of_date="2023-06-30",
        run_id="test_run",
        point_in_time_enforcement="readiness_only",
        historical_snapshot_contract=contract.to_dict(),
        historical_price_window=price_window,
        official_financials_snapshot=financials_snapshot,
    )
    payload = assembly.to_dict()

    assert payload["ticker"] == "COST"
    assert payload["as_of_date"] == "2023-06-30"
    assert payload["historical_mode"] is True
    assert payload["point_in_time_enforcement"] == "readiness_only"
    assert payload["assembly_status"] == "partial_historical_input"
    assert payload["safe_for_historical_signal_generation"] is False
    assert payload["section_statuses"]
    assert payload["warnings"]
    assert set(payload["partial_sections"]) == {
        "market_prices",
        "official_financials",
    }

    by_section = {
        item["section_name"]: item for item in payload["section_statuses"]
    }
    assert by_section["market_prices"]["provider"] == "csv"
    assert (
        by_section["market_prices"]["enforcement_level"]
        == "analysis_window_enforced"
    )
    assert by_section["official_financials"]["provider"] == (
        "historical_financials_csv"
    )
    assert by_section["official_financials"]["enforcement_level"] == "partial"
    assert by_section["official_financials"]["rows_after_filter"] == 3
    for section in (
        "historical_valuation",
        "growth_peg",
        "market_snapshot",
        "scuttlebutt",
        "management_incentives",
        "index_overlap",
        "investor_outputs",
    ):
        assert section in payload["readiness_only_sections"]


def test_historical_run_writes_assembly_files_and_manifest(tmp_path: Path) -> None:
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
    json_path = run_folder / "historical_enriched_input_assembly.json"
    markdown_path = run_folder / "historical_enriched_input_assembly.md"
    assert json_path.is_file()
    assert markdown_path.is_file()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assembly_manifest = manifest["historical_enriched_input_assembly"]
    assert payload["safe_for_historical_signal_generation"] is False
    assert payload["assembly_status"] == "partial_historical_input"
    assert set(payload["partial_sections"]) == {
        "market_prices",
        "official_financials",
    }
    assert assembly_manifest["enabled"] is True
    assert Path(assembly_manifest["assembly_file"]) == json_path
    assert Path(assembly_manifest["assembly_markdown"]) == markdown_path
    assert (
        assembly_manifest["safe_for_historical_signal_generation"] is False
    )

    markdown = markdown_path.read_text(encoding="utf-8")
    summary = (run_folder / "run_summary.md").read_text(encoding="utf-8")
    for text in (
        "Historical Enriched Input Assembly",
        "Safe for historical signal generation: No",
        (
            "This historical enriched input assembly is not a recommendation, "
            "ranking, vote, average score, consensus, allocation instruction, "
            "rebalancing instruction, or trade signal."
        ),
    ):
        assert text in markdown
    for text in (
        "Historical Enriched Input Assembly",
        "Safe for Historical Signal Generation: No",
        (
            "Historical signal generation remains disabled until sufficient "
            "point-in-time inputs are available."
        ),
    ):
        assert text in summary


def test_historical_readiness_run_marks_financials_readiness_only(
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
            run_folder / "historical_enriched_input_assembly.json"
        ).read_text(encoding="utf-8")
    )
    assert payload["assembly_status"] == "readiness_only"
    assert "official_financials" in payload["readiness_only_sections"]
    assert "market_prices" in payload["partial_sections"]
    assert manifest["historical_enriched_input_assembly"]["enabled"] is True


def test_current_run_does_not_write_historical_assembly(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    result = _invoke_analyze_stock(outputs_root)

    assert result.exit_code == 0, result.output
    run_folder, manifest = _latest_run(outputs_root)
    assert not (
        run_folder / "historical_enriched_input_assembly.json"
    ).exists()
    assembly = manifest["historical_enriched_input_assembly"]
    assert assembly["enabled"] is False
    assert assembly["assembly_status"] == "not_enabled"


def test_task81_documentation_and_demo_runner_remain() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for text in (
        "Historical Enriched Input Assembly",
        "historical_enriched_input_assembly.json",
        "safe_for_historical_signal_generation",
        "does not generate signals",
        "No live API",
    ):
        assert text.lower() in readme.lower()

    demo = (ROOT / "scripts" / "run_first_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "python -m ruff check ." in demo
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in demo
    assert "python -m broker_agents.cli" in demo
