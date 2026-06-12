"""Structured append-only ledger for completed analyze-stock runs."""

import csv
from dataclasses import dataclass
import json
from pathlib import Path

INVESTORS = ("buffett", "munger", "fisher", "lynch", "bogle")
LEDGER_FIELDS = (
    "archive_record_id",
    "ticker",
    "company_name",
    "run_id",
    "run_folder",
    "run_manifest_path",
    "input_mode",
    "intake_file",
    "run_label",
    "batch_run_id",
    "batch_folder",
    "generated_at",
    "as_of_date",
    "historical_mode",
    "point_in_time_enforcement",
    "status",
    "broker_deal_package_path",
    "enriched_input_path",
    "source_verification_path",
    "investor_response_letters_dir",
    "investor_follow_up_memos_dir",
    "backoffice_work_orders_path",
    "intake_snapshot_path",
    "readiness_label",
    "source_verification_status",
    "total_investor_responses",
    "total_work_orders",
    "promotion_blocking_categories",
    "buffett_final_decision",
    "munger_final_decision",
    "fisher_final_decision",
    "lynch_final_decision",
    "bogle_final_decision",
    "buffett_interest_level",
    "munger_interest_level",
    "fisher_interest_level",
    "lynch_interest_level",
    "bogle_interest_level",
    "auto_promotion_disabled",
    "human_review_required",
    "no_recommendation",
    "no_ranking",
    "no_consensus",
    "no_trade_signal",
)


@dataclass(frozen=True)
class SignalArchiveResult:
    """Files updated by one signal archive append."""

    record: dict
    jsonl_path: Path
    csv_path: Path
    snapshot_path: Path
    total_archived_records: int


def _load_json(path: Path) -> dict:
    """Load a required structured artifact."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}.")
    return data


def _investor_response_map(package_payload: dict) -> dict[str, dict]:
    """Index investor responses by normalized investor name."""
    responses = package_payload.get("investor_responses", [])
    return {
        str(response.get("investor", "")).strip().lower(): response
        for response in responses
        if isinstance(response, dict)
    }


def build_signal_record(
    *,
    run_manifest_path: Path,
    broker_package_json_path: Path,
    batch_run_id: str | None = None,
    batch_folder: Path | None = None,
) -> dict:
    """Build one ledger record from canonical structured run artifacts."""
    run_manifest_path = Path(run_manifest_path)
    manifest = _load_json(run_manifest_path)
    package_payload = _load_json(Path(broker_package_json_path))
    responses = _investor_response_map(package_payload)
    ticker = str(manifest["ticker"]).upper()
    record = {
        "archive_record_id": f"{ticker}-{manifest['run_id']}",
        "ticker": ticker,
        "company_name": manifest.get("company_name"),
        "run_id": manifest["run_id"],
        "run_folder": str(run_manifest_path.parent),
        "run_manifest_path": str(run_manifest_path),
        "input_mode": manifest.get("input_mode"),
        "intake_file": manifest.get("intake_file"),
        "run_label": manifest.get("run_label"),
        "batch_run_id": batch_run_id,
        "batch_folder": str(batch_folder) if batch_folder else None,
        "generated_at": manifest.get("generated_at"),
        "as_of_date": manifest.get("as_of_date"),
        "historical_mode": manifest.get("historical_mode", False),
        "point_in_time_enforcement": manifest.get(
            "point_in_time_enforcement",
            "readiness_only",
        ),
        "status": manifest.get("status", "completed"),
        "broker_deal_package_path": manifest.get(
            "broker_deal_package_path"
        ),
        "enriched_input_path": manifest.get("enriched_input_path"),
        "source_verification_path": manifest.get(
            "source_verification_path"
        ),
        "investor_response_letters_dir": manifest.get(
            "investor_response_letters_dir"
        ),
        "investor_follow_up_memos_dir": manifest.get(
            "investor_follow_up_memos_dir"
        ),
        "backoffice_work_orders_path": manifest.get(
            "backoffice_work_orders_path"
        ),
        "intake_snapshot_path": manifest.get("intake_snapshot_path"),
        "readiness_label": manifest.get("readiness_label"),
        "source_verification_status": manifest.get(
            "source_verification_status"
        ),
        "total_investor_responses": manifest.get(
            "total_investor_responses",
            0,
        ),
        "total_work_orders": manifest.get("total_work_orders", 0),
        "promotion_blocking_categories": manifest.get(
            "promotion_blocking_categories",
            [],
        ),
        "auto_promotion_disabled": True,
        "human_review_required": True,
        "no_recommendation": True,
        "no_ranking": True,
        "no_consensus": True,
        "no_trade_signal": True,
    }
    for investor in INVESTORS:
        response = responses.get(investor, {})
        record[f"{investor}_final_decision"] = response.get(
            "broker_facing_final_decision"
        ) or response.get("final_decision")
        record[f"{investor}_interest_level"] = response.get("interest_level")
    return record


def _csv_row(record: dict) -> dict:
    """Flatten list values for the tabular ledger."""
    row = {field: record.get(field) for field in LEDGER_FIELDS}
    row["promotion_blocking_categories"] = ";".join(
        record.get("promotion_blocking_categories", [])
    )
    return row


def _record_count(jsonl_path: Path) -> int:
    """Count non-empty append-only records."""
    if not jsonl_path.exists():
        return 0
    return sum(
        1
        for line in jsonl_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def _ensure_csv_schema(csv_path: Path) -> None:
    """Upgrade an existing ledger CSV header while preserving prior rows."""
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        existing_fields = tuple(reader.fieldnames or ())
        rows = list(reader)
    if existing_fields == LEDGER_FIELDS:
        return
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {field: row.get(field) for field in LEDGER_FIELDS}
            )


def append_signal_record(
    *,
    outputs_root: Path,
    record: dict,
) -> SignalArchiveResult:
    """Append one record and refresh CSV and latest snapshot files."""
    archive_dir = Path(outputs_root) / "signal_archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = archive_dir / "signal_ledger.jsonl"
    csv_path = archive_dir / "signal_ledger.csv"
    snapshot_path = archive_dir / "latest_signal_ledger_snapshot.json"

    with jsonl_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, separators=(",", ":")) + "\n")
    _ensure_csv_schema(csv_path)
    write_header = not csv_path.exists() or csv_path.stat().st_size == 0
    with csv_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(_csv_row(record))

    total_records = _record_count(jsonl_path)
    previous_snapshot = {}
    if snapshot_path.exists():
        previous_snapshot = _load_json(snapshot_path)
    snapshot = {
        "total_archived_records": total_records,
        "latest_run_id": record["run_id"],
        "latest_batch_run_id": (
            record.get("batch_run_id")
            or previous_snapshot.get("latest_batch_run_id")
        ),
        "latest_ticker": record["ticker"],
        "generated_at": record.get("generated_at"),
    }
    snapshot_path.write_text(
        json.dumps(snapshot, indent=2),
        encoding="utf-8",
    )
    return SignalArchiveResult(
        record=record,
        jsonl_path=jsonl_path,
        csv_path=csv_path,
        snapshot_path=snapshot_path,
        total_archived_records=total_records,
    )


def archive_completed_run(
    *,
    outputs_root: Path,
    run_manifest_path: Path,
    broker_deal_package_path: Path,
    batch_run_id: str | None = None,
    batch_folder: Path | None = None,
) -> SignalArchiveResult:
    """Build and append a ledger record for one completed run."""
    package_json_path = Path(broker_deal_package_path).with_suffix(".json")
    record = build_signal_record(
        run_manifest_path=run_manifest_path,
        broker_package_json_path=package_json_path,
        batch_run_id=batch_run_id,
        batch_folder=batch_folder,
    )
    return append_signal_record(
        outputs_root=outputs_root,
        record=record,
    )
