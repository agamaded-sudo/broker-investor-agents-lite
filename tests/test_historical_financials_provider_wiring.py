"""Tests for analyze-stock historical financials provider wiring."""

import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.cli import app

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
HISTORICAL_FINANCIALS = FIXTURES / "historical_financials"
PORTFOLIO_CONTEXT = EXAMPLES / "portfolio_context.yaml"
EXPECTED_DECISIONS = {
    "Buffett": "Wait for Better Price / Complete Intrinsic Value Work",
    "Munger": (
        "Buy Gradually / Wait for Better Evidence on Incentives and "
        "Long-Term Durability"
    ),
    "Fisher": "Needs More Scuttlebutt / Watch Closely",
    "Lynch": "Follow / Watch",
    "Bogle": "Prefer Broad Index",
}


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


def _latest_manifest(outputs_root: Path) -> tuple[Path, dict]:
    latest = outputs_root / "COST" / "runs" / "latest_run_manifest.json"
    manifest = json.loads(latest.read_text(encoding="utf-8"))
    return outputs_root / "COST" / "runs" / manifest["run_id"], manifest


def test_default_and_historical_readiness_modes_keep_snapshot_disabled(
    tmp_path: Path,
) -> None:
    current_outputs = tmp_path / "current"
    current = _invoke_analyze_stock(current_outputs)
    historical_outputs = tmp_path / "historical"
    historical = _invoke_analyze_stock(
        historical_outputs,
        "--as-of-date",
        "2023-06-30",
    )

    assert current.exit_code == 0, current.output
    _, current_manifest = _latest_manifest(current_outputs)
    assert current_manifest["official_financials_as_of_snapshot"]["enabled"] is False
    assert current_manifest["official_financials_as_of_contract"] is None

    assert historical.exit_code == 0, historical.output
    _, historical_manifest = _latest_manifest(historical_outputs)
    snapshot = historical_manifest["official_financials_as_of_snapshot"]
    contract = historical_manifest["official_financials_as_of_contract"]
    assert snapshot["enabled"] is False
    assert snapshot["status"] == "not_enabled"
    assert contract["supports_as_of_date"] is False
    assert contract["enforcement_level"] == "readiness_only"
    assert contract["leakage_risk"] == "high"


def test_historical_csv_mode_writes_filtered_snapshot_and_metadata(
    tmp_path: Path,
) -> None:
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
    run_folder, manifest = _latest_manifest(outputs_root)
    snapshot_path = run_folder / "official_financials_as_of_snapshot.csv"
    metadata_path = (
        run_folder / "official_financials_as_of_snapshot_metadata.json"
    )
    summary_path = run_folder / "run_summary.md"
    assert snapshot_path.is_file()
    assert metadata_path.is_file()

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    snapshot = manifest["official_financials_as_of_snapshot"]
    for payload in (metadata, snapshot):
        assert payload["enabled"] is True
        assert payload["provider"] == "historical_financials_csv"
        assert payload["rows_before_filter"] == 6
        assert payload["rows_after_filter"] == 4
        assert payload["future_rows_excluded_count"] == 2
        assert payload["rows_missing_availability_date_count"] == 0
        assert payload["max_filing_date_after_filter"] == "2023-05-01"
        assert payload["max_accepted_date_after_filter"] == "2023-05-01"
        assert payload["status"] == "as_of_filter_applied"
        assert payload["warnings"] == []
    assert Path(snapshot["snapshot_file"]) == snapshot_path
    assert Path(snapshot["metadata_file"]) == metadata_path

    contract = manifest["official_financials_as_of_contract"]
    assert contract["supports_as_of_date"] is True
    assert contract["enforcement_level"] == "partial"
    assert contract["leakage_risk"] == "medium"
    assert contract["status"] == "supported_if_required_date_fields_present"
    assert contract["missing_date_fields"] == []

    with snapshot_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 4
    for row in rows:
        filing_date = row["filing_date"]
        accepted_date = row["accepted_date"]
        assert filing_date or accepted_date
        assert (
            filing_date and filing_date <= "2023-06-30"
        ) or (
            accepted_date and accepted_date <= "2023-06-30"
        )

    summary = summary_path.read_text(encoding="utf-8")
    for text in (
        "Official Financials As-Of Snapshot",
        "Historical financials CSV rows are filtered by filing_date or accepted_date.",
        "Rows Before Filter: 6",
        "Rows After Filter: 4",
        "Future Rows Excluded: 2",
        "Rows Missing Availability Date: 0",
        "This official financials as-of snapshot is not a recommendation, ranking, vote, average score, consensus, allocation instruction, rebalancing instruction, or trade signal.",
    ):
        assert text in summary

    package = json.loads(
        (
            outputs_root
            / "COST"
            / "deal_package"
            / "cost_broker_deal_package.json"
        ).read_text(encoding="utf-8")
    )
    decisions = {
        response["investor"]: response.get("broker_facing_final_decision")
        or response["final_decision"]
        for response in package["investor_responses"]
    }
    assert decisions == EXPECTED_DECISIONS
    assert "no_auto_promotion" in package["workflow_result"]["safety_flags"]


def test_historical_csv_mode_requires_financials_root(tmp_path: Path) -> None:
    result = _invoke_analyze_stock(
        tmp_path / "outputs",
        "--as-of-date",
        "2023-06-30",
        "--financials-provider",
        "historical_csv",
    )

    assert result.exit_code != 0
    assert "--financials-root is required" in result.output
    assert "Traceback" not in result.output


def test_task80_documentation_and_demo_runner_remain() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for text in (
        "Historical Financials Provider Wiring",
        "official_financials_as_of_snapshot.csv",
        "--financials-provider historical_csv",
        "--financials-root tests/fixtures/historical_financials",
        "does not alter investor decisions",
        "No live API",
    ):
        assert text.lower() in readme.lower()

    demo = (ROOT / "scripts" / "run_first_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "python -m ruff check ." in demo
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in demo
    assert "python -m broker_agents.cli" in demo
