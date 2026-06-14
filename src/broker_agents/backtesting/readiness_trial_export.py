"""Convert readiness-only records into research trial backtest inputs."""

import csv
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path

from broker_agents.archive.historical_readiness_ledger import (
    COVERAGE_QUALITY_FIELDS,
    RECORD_TYPE,
)
from broker_agents.deals.readiness_metadata_enrichment import (
    CORE_METADATA_FIELDS,
    ENRICHMENT_FIELDS,
    enrich_historical_readiness_record,
    metadata_status_counts,
    missing_metadata_field_counts,
)

TRIAL_BACKTEST_LABEL = "readiness_only_trial"
SAFETY_NOTICE = (
    "This historical readiness trial ledger contains readiness-only research "
    "artifacts. It is not a recommendation ledger, ranking ledger, allocation "
    "ledger, rebalancing ledger, trade signal ledger, or execution instruction "
    "ledger."
)
FORBIDDEN_COLUMNS = {
    "action",
    "buy",
    "sell",
    "hold",
    "rank",
    "recommendation_score",
    "allocation",
    "rebalance",
    "execution_instruction",
}
TRIAL_LEDGER_FIELDS = (
    "ticker",
    "signal_date",
    "as_of_date",
    "generated_at",
    "run_id",
    "archive_record_id",
    "status",
    "trial_signal_source",
    "record_type",
    "source_run_id",
    "source_run_folder",
    "source_candidate_file",
    "source_assembly_file",
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
    *COVERAGE_QUALITY_FIELDS,
    "unsupported_dates_excluded_count",
    *CORE_METADATA_FIELDS,
    "metadata_enrichment_status",
    "missing_metadata_fields",
    "metadata_source_paths",
    "trial_backtest_label",
    "trial_backtest_allowed",
    "safety_notice",
)


@dataclass(frozen=True)
class ReadinessTrialLedgerRecord:
    """One readiness-only row formatted for the research backtester."""

    ticker: str
    signal_date: str
    as_of_date: str
    generated_at: str
    run_id: str
    archive_record_id: str
    status: str
    trial_signal_source: str
    record_type: str
    source_run_id: str
    source_run_folder: str
    source_candidate_file: str
    source_assembly_file: str
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
    coverage_quality_label: str
    coverage_quality_severity: str
    date_coverage_status: str
    has_delayed_price_anchor: bool
    has_limited_financials: bool
    warning_count: int
    coverage_guardrail_status: str
    unsupported_dates_excluded_count: int
    readiness_label: object
    readiness_status: object
    readiness_score: object
    source_verification_status: object
    verified_source_count: object
    partial_source_count: object
    missing_source_count: object
    placeholder_heavy_source_count: object
    promotion_blocking_count: object
    promotion_blocking_bucket: object
    buffett_interest_level: object
    munger_interest_level: object
    fisher_interest_level: object
    lynch_interest_level: object
    bogle_interest_level: object
    buffett_decision: object
    munger_decision: object
    fisher_decision: object
    lynch_decision: object
    bogle_decision: object
    metadata_enrichment_status: str
    missing_metadata_fields: str
    metadata_source_paths: str
    trial_backtest_label: str
    trial_backtest_allowed: bool
    safety_notice: str

    def to_dict(self) -> dict:
        """Serialize one trial ledger row."""
        return asdict(self)


@dataclass(frozen=True)
class ReadinessTrialExportResult:
    """Artifacts and counts produced by one export."""

    source_ledger: Path
    output_ledger: Path
    metadata_file: Path
    total_input_records: int
    total_exported_records: int
    skipped_records: int
    metadata_enrichment_status_counts: dict[str, int]
    missing_metadata_field_counts: dict[str, int]
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReadinessTrialValidationResult:
    """Safety validation counts for one exported trial ledger."""

    rows: int
    readiness_only_rows: int
    not_trade_signal_rows: int
    not_recommendation_rows: int
    invalid_rows: int
    status: str
    warnings: list[str] = field(default_factory=list)


def _as_bool(value: object) -> bool:
    """Normalize JSON and CSV boolean values."""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _as_int(value: object) -> int:
    """Normalize integer counts from CSV or JSON records."""
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0


def _load_records(path: Path) -> list[dict]:
    """Load readiness records from CSV or JSONL."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Historical readiness ledger not found: {path}")
    if path.suffix.lower() == ".jsonl":
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _valid_source_record(record: dict) -> tuple[bool, str | None]:
    """Verify the source record retains every readiness-only invariant."""
    checks = (
        record.get("record_type") == RECORD_TYPE,
        record.get("signal_generation_status") == "readiness_only",
        not _as_bool(record.get("safe_for_historical_signal_generation")),
        _as_bool(record.get("not_trade_signal")),
        _as_bool(record.get("not_recommendation")),
        _as_bool(record.get("not_allocation_instruction")),
        bool(str(record.get("ticker") or "").strip()),
        bool(str(record.get("as_of_date") or "").strip()),
        bool(str(record.get("run_id") or "").strip()),
    )
    if all(checks):
        if record.get("coverage_guardrail_status") == "unsupported_excluded":
            return False, (
                f"Skipped unsupported coverage record for "
                f"{record.get('ticker') or 'unknown ticker'}."
            )
        return True, None
    return False, (
        f"Skipped invalid readiness record for "
        f"{record.get('ticker') or 'unknown ticker'}."
    )


def _trial_record(
    record: dict,
    *,
    unsupported_dates_excluded_count: int,
) -> ReadinessTrialLedgerRecord:
    """Map one validated readiness record into trial-backtest format."""
    ticker = str(record["ticker"]).upper()
    as_of_date = str(record["as_of_date"])
    run_id = str(record["run_id"])
    return ReadinessTrialLedgerRecord(
        ticker=ticker,
        signal_date=as_of_date,
        as_of_date=as_of_date,
        generated_at=f"{as_of_date}T00:00:00+00:00",
        run_id=run_id,
        archive_record_id=f"{ticker}-{run_id}-readiness-trial",
        status="completed",
        trial_signal_source="historical_readiness_ledger",
        record_type=RECORD_TYPE,
        source_run_id=run_id,
        source_run_folder=str(record.get("run_folder") or ""),
        source_candidate_file=str(record.get("candidate_file") or ""),
        source_assembly_file=str(record.get("assembly_file") or ""),
        signal_generation_status="readiness_only",
        safe_for_historical_signal_generation=False,
        not_trade_signal=True,
        not_recommendation=True,
        not_allocation_instruction=True,
        assembly_status=str(record.get("assembly_status") or ""),
        partial_sections_count=_as_int(record.get("partial_sections_count")),
        readiness_only_sections_count=_as_int(
            record.get("readiness_only_sections_count")
        ),
        leakage_risk_sections_count=_as_int(
            record.get("leakage_risk_sections_count")
        ),
        blocking_reasons_count=_as_int(record.get("blocking_reasons_count")),
        warnings_count=_as_int(record.get("warnings_count")),
        coverage_quality_label=str(
            record.get("coverage_quality_label") or "not_available"
        ),
        coverage_quality_severity=str(
            record.get("coverage_quality_severity") or "not_available"
        ),
        date_coverage_status=str(
            record.get("date_coverage_status") or "not_available"
        ),
        has_delayed_price_anchor=_as_bool(
            record.get("has_delayed_price_anchor")
        ),
        has_limited_financials=_as_bool(
            record.get("has_limited_financials")
        ),
        warning_count=_as_int(record.get("warning_count")),
        coverage_guardrail_status=str(
            record.get("coverage_guardrail_status") or "not_available"
        ),
        unsupported_dates_excluded_count=unsupported_dates_excluded_count,
        **{
            field: record.get(field, "Missing")
            for field in CORE_METADATA_FIELDS
        },
        metadata_enrichment_status=str(
            record.get("metadata_enrichment_status") or "not_available"
        ),
        missing_metadata_fields=str(
            record.get("missing_metadata_fields") or ""
        ),
        metadata_source_paths=str(
            record.get("metadata_source_paths") or ""
        ),
        trial_backtest_label=TRIAL_BACKTEST_LABEL,
        trial_backtest_allowed=True,
        safety_notice=SAFETY_NOTICE,
    )


def export_readiness_ledger_to_trial_ledger(
    *,
    source_ledger: Path,
    output_ledger: Path,
    metadata_file: Path | None = None,
    generated_at: datetime | None = None,
    unsupported_dates_excluded_count: int = 0,
) -> ReadinessTrialExportResult:
    """Export validated readiness records into a separate trial CSV."""
    source_ledger = Path(source_ledger)
    output_ledger = Path(output_ledger)
    metadata_file = (
        Path(metadata_file)
        if metadata_file
        else output_ledger.with_name(
            f"{output_ledger.stem}_metadata.json"
        )
    )
    records = _load_records(source_ledger)
    exported = []
    warnings = []
    for record in records:
        valid, warning = _valid_source_record(record)
        if valid:
            exported.append(
                _trial_record(
                    enrich_historical_readiness_record(record),
                    unsupported_dates_excluded_count=(
                        unsupported_dates_excluded_count
                    ),
                )
            )
        elif warning:
            warnings.append(warning)
    exported_dicts = [record.to_dict() for record in exported]
    status_counts = metadata_status_counts(exported_dicts)
    missing_counts = missing_metadata_field_counts(exported_dicts)

    output_ledger.parent.mkdir(parents=True, exist_ok=True)
    with output_ledger.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRIAL_LEDGER_FIELDS)
        writer.writeheader()
        for record in exported:
            writer.writerow(record.to_dict())

    timestamp = generated_at or datetime.now(timezone.utc)
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "source_ledger": str(source_ledger),
        "output_ledger": str(output_ledger),
        "total_input_records": len(records),
        "total_exported_records": len(exported),
        "skipped_records": len(records) - len(exported),
        "generated_at": timestamp.isoformat(),
        "safety_notice": SAFETY_NOTICE,
        "metadata_enrichment_enabled": True,
        "metadata_fields_added": list(ENRICHMENT_FIELDS),
        "metadata_enrichment_status_counts": status_counts,
        "missing_metadata_field_counts": missing_counts,
        "unsupported_dates_excluded_count": (
            unsupported_dates_excluded_count
        ),
        "warnings": warnings,
    }
    metadata_file.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )
    return ReadinessTrialExportResult(
        source_ledger=source_ledger,
        output_ledger=output_ledger,
        metadata_file=metadata_file,
        total_input_records=len(records),
        total_exported_records=len(exported),
        skipped_records=len(records) - len(exported),
        metadata_enrichment_status_counts=status_counts,
        missing_metadata_field_counts=missing_counts,
        warnings=warnings,
    )


def validate_readiness_trial_ledger(
    ledger_path: Path,
) -> ReadinessTrialValidationResult:
    """Validate exported trial rows and reject actionable columns."""
    ledger_path = Path(ledger_path)
    with ledger_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or ())
        rows = list(reader)
    forbidden = sorted(fields & FORBIDDEN_COLUMNS)
    warnings = (
        [f"Forbidden columns present: {', '.join(forbidden)}."]
        if forbidden
        else []
    )
    readiness_only_rows = 0
    not_trade_signal_rows = 0
    not_recommendation_rows = 0
    invalid_rows = 0
    for row in rows:
        readiness = (
            row.get("record_type") == RECORD_TYPE
            and row.get("signal_generation_status") == "readiness_only"
            and not _as_bool(
                row.get("safe_for_historical_signal_generation")
            )
            and _as_bool(row.get("not_allocation_instruction"))
            and _as_bool(row.get("trial_backtest_allowed"))
            and row.get("signal_date") == row.get("as_of_date")
        )
        not_trade = _as_bool(row.get("not_trade_signal"))
        not_recommendation = _as_bool(row.get("not_recommendation"))
        readiness_only_rows += int(readiness)
        not_trade_signal_rows += int(not_trade)
        not_recommendation_rows += int(not_recommendation)
        if not (readiness and not_trade and not_recommendation) or forbidden:
            invalid_rows += 1
    return ReadinessTrialValidationResult(
        rows=len(rows),
        readiness_only_rows=readiness_only_rows,
        not_trade_signal_rows=not_trade_signal_rows,
        not_recommendation_rows=not_recommendation_rows,
        invalid_rows=invalid_rows,
        status="valid" if invalid_rows == 0 else "invalid",
        warnings=warnings,
    )
