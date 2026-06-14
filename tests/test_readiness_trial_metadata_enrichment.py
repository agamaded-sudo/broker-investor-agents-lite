"""Tests for structured readiness trial metadata enrichment."""

import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.backtesting.readiness_trial_export import (
    TRIAL_LEDGER_FIELDS,
    export_readiness_ledger_to_trial_ledger,
)
from broker_agents.cli import app
from broker_agents.deals.readiness_metadata_enrichment import (
    CORE_METADATA_FIELDS,
    bucket_promotion_blockers,
    build_readiness_metadata,
    load_readiness_metadata_for_run,
)

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_PRICES = ROOT / "tests" / "fixtures" / "historical_price_history"
INVESTORS = ("buffett", "munger", "fisher", "lynch", "bogle")


def _package_payload() -> dict:
    return {
        "investor_responses": [
            {
                "investor": investor.title(),
                "interest_level": f"{investor.title()} Research Interest",
                "final_decision": f"{investor.title()} Existing Decision",
            }
            for investor in INVESTORS
        ],
        "source_verification_matrix": {
            "overall_status": "partially verified",
            "verified_categories_count": 4,
            "partial_categories_count": 1,
            "missing_or_placeholder_categories_count": 2,
            "categories": [
                {"status": "verified"},
                {"status": "verified"},
                {"status": "verified"},
                {"status": "verified"},
                {"status": "partial"},
                {"status": "missing"},
                {"status": "placeholder_heavy"},
            ],
        },
    }


def _manifest(package_markdown: Path) -> dict:
    return {
        "readiness_label": "Investor Review Possible with Evidence Gaps",
        "source_verification_status": (
            "partially verified (placeholder-heavy)"
        ),
        "promotion_blocking_categories": [
            "scuttlebutt",
            "management_incentives",
            "index_overlap",
        ],
        "historical_enriched_input_assembly": {
            "assembly_status": "partial_historical_input"
        },
        "broker_deal_package_path": str(package_markdown),
    }


def _source_record(run_folder: Path) -> dict:
    return {
        "record_type": "historical_signal_readiness_candidate",
        "ticker": "COST",
        "as_of_date": "2023-06-30",
        "run_id": "metadata-trial",
        "run_folder": str(run_folder),
        "candidate_file": str(run_folder / "candidate.json"),
        "assembly_file": str(run_folder / "assembly.json"),
        "signal_generation_status": "readiness_only",
        "safe_for_historical_signal_generation": "False",
        "not_trade_signal": "True",
        "not_recommendation": "True",
        "not_allocation_instruction": "True",
        "assembly_status": "partial_historical_input",
        "partial_sections_count": "2",
        "readiness_only_sections_count": "8",
        "leakage_risk_sections_count": "10",
        "blocking_reasons_count": "10",
        "warnings_count": "3",
        "created_at": "2026-06-14T00:00:00+00:00",
        "source": "analyze_stock_historical_mode",
    }


def _write_structured_run(tmp_path: Path) -> Path:
    run_folder = tmp_path / "outputs" / "COST" / "runs" / "metadata-trial"
    package_markdown = (
        tmp_path / "outputs" / "COST" / "deal_package" / "package.md"
    )
    run_folder.mkdir(parents=True)
    package_markdown.parent.mkdir(parents=True)
    package_markdown.with_suffix(".json").write_text(
        json.dumps(_package_payload()),
        encoding="utf-8",
    )
    (run_folder / "run_manifest.json").write_text(
        json.dumps(_manifest(package_markdown)),
        encoding="utf-8",
    )
    return run_folder


def _write_source(path: Path, record: dict) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=record.keys())
        writer.writeheader()
        writer.writerow(record)


def test_metadata_helper_extracts_only_structured_local_values(
    tmp_path: Path,
) -> None:
    run_folder = _write_structured_run(tmp_path)

    metadata = load_readiness_metadata_for_run(run_folder=run_folder)

    assert metadata["readiness_label"].startswith("Investor Review")
    assert metadata["readiness_status"] == "partial_historical_input"
    assert metadata["readiness_score"] == "Missing"
    assert metadata["source_verification_status"].startswith(
        "partially verified"
    )
    assert metadata["verified_source_count"] == 4
    assert metadata["partial_source_count"] == 1
    assert metadata["missing_source_count"] == 1
    assert metadata["placeholder_heavy_source_count"] == 1
    assert metadata["promotion_blocking_count"] == 3
    assert metadata["promotion_blocking_bucket"] == "moderate_blockers"
    assert metadata["buffett_interest_level"] == (
        "Buffett Research Interest"
    )
    assert metadata["buffett_decision"] == "Buffett Existing Decision"
    assert metadata["metadata_enrichment_status"] == "partial"
    assert "readiness_score" in metadata["missing_metadata_fields"]
    assert "run_manifest.json" in metadata["metadata_source_paths"]
    assert "package.json" in metadata["metadata_source_paths"]


def test_missing_metadata_remains_explicit_and_blocker_buckets_are_safe(
    tmp_path: Path,
) -> None:
    metadata = build_readiness_metadata()
    loaded = load_readiness_metadata_for_run(
        run_folder=tmp_path / "absent"
    )

    assert metadata["metadata_enrichment_status"] == "missing"
    assert loaded["metadata_enrichment_status"] == "missing"
    assert metadata["readiness_label"] == "Missing"
    assert metadata["buffett_interest_level"] == "Missing"
    assert bucket_promotion_blockers(None) == "missing"
    assert bucket_promotion_blockers(0) == "no_blockers"
    assert bucket_promotion_blockers(2) == "low_blockers"
    assert bucket_promotion_blockers(3) == "moderate_blockers"
    assert bucket_promotion_blockers(8) == "high_blockers"


def test_export_and_backtest_preserve_enriched_metadata(
    tmp_path: Path,
) -> None:
    run_folder = _write_structured_run(tmp_path)
    source = tmp_path / "readiness.csv"
    trial = tmp_path / "trial.csv"
    metadata_path = tmp_path / "trial_metadata.json"
    _write_source(source, _source_record(run_folder))

    export = export_readiness_ledger_to_trial_ledger(
        source_ledger=source,
        output_ledger=trial,
        metadata_file=metadata_path,
    )

    assert export.metadata_enrichment_status_counts == {"partial": 1}
    with trial.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert tuple(reader.fieldnames or ()) == TRIAL_LEDGER_FIELDS
    for field in (
        *CORE_METADATA_FIELDS,
        "metadata_enrichment_status",
        "missing_metadata_fields",
        "metadata_source_paths",
    ):
        assert field in rows[0]
    assert rows[0]["readiness_label"].startswith("Investor Review")
    assert rows[0]["source_verification_status"].startswith(
        "partially verified"
    )
    assert rows[0]["promotion_blocking_bucket"] == "moderate_blockers"
    assert rows[0]["buffett_interest_level"] == (
        "Buffett Research Interest"
    )
    export_metadata = json.loads(
        metadata_path.read_text(encoding="utf-8")
    )
    assert export_metadata["metadata_enrichment_enabled"] is True
    assert set(CORE_METADATA_FIELDS).issubset(
        export_metadata["metadata_fields_added"]
    )
    assert export_metadata["metadata_enrichment_status_counts"] == {
        "partial": 1
    }
    assert export_metadata["missing_metadata_field_counts"] == {
        "readiness_score": 1
    }

    outputs_root = tmp_path / "backtest_outputs"
    result = CliRunner().invoke(
        app,
        [
            "backtest-signals",
            "--ledger",
            str(trial),
            "--price-provider",
            "csv",
            "--price-fixtures",
            str(HISTORICAL_PRICES),
            "--outputs-root",
            str(outputs_root),
            "--lookback-years",
            "5",
            "--dedupe-mode",
            "latest_per_ticker_per_day",
            "--walk-forward",
            "--walk-forward-frequency",
            "yearly",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Metadata Enrichment" in result.output
    assert "detected" in result.output
    assert "Missing Metadata Fields" in result.output
    manifest = json.loads(
        (
            outputs_root / "backtests" / "latest_backtest_manifest.json"
        ).read_text(encoding="utf-8")
    )
    with Path(manifest["results_path"]).open(
        encoding="utf-8",
        newline="",
    ) as handle:
        result_row = next(csv.DictReader(handle))
    assert result_row["readiness_label"].startswith("Investor Review")
    assert result_row["promotion_blocking_bucket"] == "moderate_blockers"
    assert result_row["buffett_interest_level"] == (
        "Buffett Research Interest"
    )
    metrics = json.loads(
        Path(manifest["metrics_summary_path"]).read_text(encoding="utf-8")
    )
    assert metrics["metadata_enrichment_status_counts"] == {"partial": 1}
    assert metrics["missing_metadata_fields"] == []
    assert metrics["grouped_metrics"]["readiness_label"][0][
        "group_name"
    ].startswith("Investor Review")
    assert metrics["grouped_metrics"]["promotion_blocking_bucket"][0][
        "group_name"
    ] == "moderate_blockers"
    diagnostic = json.loads(
        Path(
            manifest["readiness_trial_diagnostic_report_json_path"]
        ).read_text(encoding="utf-8")
    )
    concentration = diagnostic["concentration_diagnostics"]
    assert concentration["metadata_enrichment_status_counts"] == {
        "partial": 1
    }
    assert all(concentration["grouped_metadata_availability"].values())
    markdown = Path(
        manifest["readiness_trial_diagnostic_report_path"]
    ).read_text(encoding="utf-8")
    assert "Metadata enrichment status counts" in markdown
    assert "Grouped metadata availability" in markdown
    assert "Rows with available metadata can now be grouped separately." in (
        markdown
    )


def test_enrichment_module_has_no_network_calls() -> None:
    source = (
        ROOT
        / "src"
        / "broker_agents"
        / "deals"
        / "readiness_metadata_enrichment.py"
    ).read_text(encoding="utf-8").lower()
    for network_call in (
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "urlopen(",
    ):
        assert network_call not in source
