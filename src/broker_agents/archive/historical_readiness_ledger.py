"""Separate append-only ledger for historical readiness candidates."""

import csv
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from broker_agents.historical.historical_signal_readiness import (
    HistoricalSignalReadinessCandidate,
)

RECORD_TYPE = "historical_signal_readiness_candidate"
LEDGER_FIELDS = (
    "record_type",
    "ticker",
    "as_of_date",
    "run_id",
    "run_folder",
    "candidate_file",
    "assembly_file",
    "signal_generation_status",
    "safe_for_historical_signal_generation",
    "not_trade_signal",
    "not_recommendation",
    "not_allocation_instruction",
    "assembly_status",
    "partial_sections_count",
    "readiness_only_sections_count",
    "leakage_risk_sections_count",
    "blocking_reasons_count",
    "warnings_count",
    "created_at",
    "source",
)
SAFETY_NOTICE = (
    "This historical readiness ledger contains readiness-only research "
    "artifacts. It is not a recommendation ledger, ranking ledger, allocation "
    "ledger, rebalancing ledger, trade signal ledger, or execution instruction "
    "ledger."
)


@dataclass(frozen=True)
class HistoricalReadinessLedgerRecord:
    """Stable readiness-only ledger record."""

    record_type: str
    ticker: str
    as_of_date: str
    run_id: str
    run_folder: str
    candidate_file: str
    assembly_file: str
    signal_generation_status: str
    safe_for_historical_signal_generation: bool
    not_trade_signal: bool
    not_recommendation: bool
    not_allocation_instruction: bool
    assembly_status: str
    partial_sections_count: int
    readiness_only_sections_count: int
    leakage_risk_sections_count: int
    blocking_reasons_count: int
    warnings_count: int
    created_at: str
    source: str

    def to_dict(self) -> dict:
        """Serialize the ledger record."""
        return asdict(self)


@dataclass(frozen=True)
class HistoricalReadinessArchiveResult:
    """Paths and counts updated by one readiness-ledger append."""

    record: HistoricalReadinessLedgerRecord
    jsonl_path: Path
    csv_path: Path
    snapshot_path: Path
    total_records: int


def build_historical_readiness_ledger_record(
    *,
    candidate: HistoricalSignalReadinessCandidate,
    run_folder: Path,
    candidate_file: Path,
    assembly_file: Path,
    created_at: str,
) -> HistoricalReadinessLedgerRecord:
    """Build and enforce a readiness-only record."""
    if candidate.signal_generation_status != "readiness_only":
        raise ValueError("Historical readiness records must be readiness_only.")
    if candidate.safe_for_historical_signal_generation:
        raise ValueError("Historical readiness records cannot be signal-safe.")
    if not (
        candidate.not_trade_signal
        and candidate.not_recommendation
        and candidate.not_allocation_instruction
    ):
        raise ValueError(
            "Historical readiness records must preserve all safety invariants."
        )
    return HistoricalReadinessLedgerRecord(
        record_type=RECORD_TYPE,
        ticker=candidate.ticker,
        as_of_date=candidate.as_of_date,
        run_id=candidate.run_id,
        run_folder=str(run_folder),
        candidate_file=str(candidate_file),
        assembly_file=str(assembly_file),
        signal_generation_status="readiness_only",
        safe_for_historical_signal_generation=False,
        not_trade_signal=True,
        not_recommendation=True,
        not_allocation_instruction=True,
        assembly_status=candidate.assembly_status,
        partial_sections_count=len(candidate.partial_sections),
        readiness_only_sections_count=len(
            candidate.readiness_only_sections
        ),
        leakage_risk_sections_count=len(candidate.leakage_risk_sections),
        blocking_reasons_count=len(candidate.blocking_reasons),
        warnings_count=len(candidate.warnings),
        created_at=created_at,
        source="analyze_stock_historical_mode",
    )


def _record_count(path: Path) -> int:
    """Count non-empty JSONL records."""
    if not path.exists():
        return 0
    return sum(
        bool(line.strip())
        for line in path.read_text(encoding="utf-8").splitlines()
    )


def append_historical_readiness_candidate(
    *,
    outputs_root: Path,
    candidate: HistoricalSignalReadinessCandidate,
    run_folder: Path,
    candidate_file: Path,
    assembly_file: Path,
    created_at: str,
) -> HistoricalReadinessArchiveResult:
    """Append one candidate to the separate readiness research ledger."""
    record = build_historical_readiness_ledger_record(
        candidate=candidate,
        run_folder=run_folder,
        candidate_file=candidate_file,
        assembly_file=assembly_file,
        created_at=created_at,
    )
    ledger_dir = Path(outputs_root) / "historical_readiness_ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = ledger_dir / "historical_signal_readiness_ledger.jsonl"
    csv_path = ledger_dir / "historical_signal_readiness_ledger.csv"
    snapshot_path = (
        ledger_dir / "latest_historical_signal_readiness_ledger_snapshot.json"
    )

    with jsonl_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record.to_dict(), separators=(",", ":")) + "\n")
    write_header = not csv_path.exists() or csv_path.stat().st_size == 0
    with csv_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(record.to_dict())

    total_records = _record_count(jsonl_path)
    snapshot = {
        "total_records": total_records,
        "latest_record": record.to_dict(),
        "ledger_jsonl": str(jsonl_path),
        "ledger_csv": str(csv_path),
        "generated_at": created_at,
        "safety_notice": SAFETY_NOTICE,
    }
    snapshot_path.write_text(
        json.dumps(snapshot, indent=2),
        encoding="utf-8",
    )
    return HistoricalReadinessArchiveResult(
        record=record,
        jsonl_path=jsonl_path,
        csv_path=csv_path,
        snapshot_path=snapshot_path,
        total_records=total_records,
    )
