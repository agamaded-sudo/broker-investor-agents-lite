"""Research-only backtesting skeleton for archived signal records."""

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from statistics import median

from broker_agents.backtesting.backtest_metrics import (
    calculate_backtest_metrics,
    render_backtest_metrics_summary,
)
from broker_agents.backtesting.price_history import (
    forward_return,
    forward_return_observation,
    max_drawdown,
)
from broker_agents.backtesting.walk_forward import (
    generate_walk_forward_outputs,
)
from broker_agents.data_providers.price_provider import (
    PriceHistoryProvider,
    PriceHistoryResult,
    create_price_provider,
)

FORWARD_WINDOWS = (3, 6, 12)
DEDUPE_MODES = {
    "none",
    "latest_per_ticker_per_day",
    "first_per_ticker_per_day",
    "latest_per_ticker",
}
INTEREST_FIELDS = (
    "buffett_interest_level",
    "munger_interest_level",
    "fisher_interest_level",
    "lynch_interest_level",
    "bogle_interest_level",
)
READINESS_TRIAL_FIELDS = (
    "record_type",
    "signal_generation_status",
    "safe_for_historical_signal_generation",
    "not_trade_signal",
    "not_recommendation",
    "not_allocation_instruction",
    "source_run_id",
    "assembly_status",
    "partial_sections_count",
    "readiness_only_sections_count",
    "leakage_risk_sections_count",
    "blocking_reasons_count",
    "trial_backtest_label",
)
READINESS_RECORD_TYPE = "historical_signal_readiness_candidate"
READINESS_TRIAL_SAFETY_NOTICE = (
    "This readiness trial backtest evaluates readiness-only research "
    "artifacts. It is not a recommendation backtest, ranking backtest, "
    "allocation backtest, rebalancing backtest, trade signal backtest, or "
    "execution instruction."
)
RESULT_FIELDS = (
    "ticker",
    "run_id",
    "archive_record_id",
    "generated_at",
    "as_of_date",
    "historical_mode",
    "signal_date",
    "trial_signal_source",
    "readiness_label",
    "source_verification_status",
    "promotion_blocking_categories",
    "promotion_blocking_count",
    "total_work_orders",
    *INTEREST_FIELDS,
    *READINESS_TRIAL_FIELDS,
    "price_column_used",
    "price_start_date",
    "price_end_date_3m",
    "price_end_date_6m",
    "price_end_date_12m",
    "forward_return_3m",
    "forward_return_6m",
    "forward_return_12m",
    "benchmark_return_3m",
    "benchmark_return_6m",
    "benchmark_return_12m",
    "relative_return_3m",
    "relative_return_6m",
    "relative_return_12m",
    "max_drawdown_12m",
    "data_status",
)
SAFE_LABEL = re.compile(r"[^a-z0-9_-]+")


@dataclass(frozen=True)
class BacktestRunResult:
    """Generated artifacts for one research backtest run."""

    backtest_run_id: str
    backtest_folder: Path
    summary_path: Path
    results_path: Path
    metrics_summary_path: Path
    metrics_summary_md_path: Path
    manifest_path: Path
    latest_manifest_path: Path
    evaluated_records: int
    skipped_records: int
    metrics: dict
    backtest_run_type: str = "standard"
    walk_forward_summary_path: Path | None = None
    walk_forward_results_path: Path | None = None
    walk_forward_metrics_path: Path | None = None
    walk_forward_periods_evaluated: int = 0


def _load_ledger(path: Path) -> list[dict]:
    """Load signal archive records from CSV or JSONL."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Signal ledger not found: {path}")
    if path.suffix.lower() == ".jsonl":
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _parse_generated_at(value: str | None) -> datetime | None:
    """Parse the archive timestamp and normalize it to UTC."""
    if not value or not str(value).strip():
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _as_bool(value: object) -> bool:
    """Normalize boolean fields from JSON or CSV ledgers."""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _is_readiness_trial(records: list[dict]) -> bool:
    """Detect a readiness-only trial ledger from explicit record metadata."""
    return any(
        record.get("record_type") == READINESS_RECORD_TYPE
        or record.get("trial_backtest_label") == "readiness_only_trial"
        for record in records
    )


def _valid_readiness_trial_record(record: dict) -> bool:
    """Require every readiness-only safety invariant before evaluation."""
    return (
        record.get("record_type") == READINESS_RECORD_TYPE
        and record.get("signal_generation_status") == "readiness_only"
        and not _as_bool(
            record.get("safe_for_historical_signal_generation")
        )
        and _as_bool(record.get("not_trade_signal"))
        and _as_bool(record.get("not_recommendation"))
        and _as_bool(record.get("not_allocation_instruction"))
    )


def _signal_date(record: dict) -> str:
    """Derive the UTC signal date from an archived timestamp."""
    generated_at = _parse_generated_at(record.get("generated_at"))
    return generated_at.date().isoformat() if generated_at else ""


def _blocking_categories(value: object) -> list[str]:
    """Normalize list or semicolon-delimited blocker categories."""
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [
        item.strip()
        for item in str(value or "").split(";")
        if item.strip()
    ]


def _blocker_group(count: int) -> str:
    """Map a blocker count to a non-ordinal research bucket."""
    if count == 0:
        return "no_blockers"
    if count <= 2:
        return "one_or_two_blockers"
    return "three_or_more_blockers"


def _record_word(count: int) -> str:
    """Return a grammatically correct record count label."""
    return f"{count} record" if count == 1 else f"{count} records"


def _dedupe_records(records: list[dict], mode: str) -> list[dict]:
    """Apply one deterministic archive dedupe policy."""
    if mode not in DEDUPE_MODES:
        allowed = ", ".join(sorted(DEDUPE_MODES))
        raise ValueError(f"dedupe_mode must be one of: {allowed}.")
    if mode == "none":
        return list(records)

    selected: dict[tuple[str, ...], tuple[int, dict]] = {}
    for index, record in enumerate(records):
        ticker = str(record.get("ticker") or "").upper()
        generated_at = _parse_generated_at(record.get("generated_at"))
        if mode == "latest_per_ticker":
            key = (ticker,)
        else:
            signal_date = (
                generated_at.date().isoformat()
                if generated_at
                else f"missing-{index}"
            )
            key = (ticker, signal_date)
        existing = selected.get(key)
        if existing is None:
            selected[key] = (index, record)
            continue
        existing_index, existing_record = existing
        existing_time = _parse_generated_at(existing_record.get("generated_at"))
        if mode == "first_per_ticker_per_day":
            replace = (
                generated_at is not None
                and (existing_time is None or generated_at < existing_time)
            )
        else:
            replace = (
                generated_at is not None
                and (existing_time is None or generated_at > existing_time)
            )
        if replace:
            selected[key] = (index, record)
        else:
            selected[key] = (existing_index, existing_record)
    return [item[1] for item in sorted(selected.values(), key=lambda item: item[0])]


def _safe_id_label(value: str | None) -> str | None:
    """Normalize an optional run label for a folder name."""
    if not value:
        return None
    normalized = SAFE_LABEL.sub("_", value.strip().lower()).strip("_")
    return normalized or None


def _allocate_run_id(
    backtests_root: Path,
    timestamp: datetime,
    run_label: str | None,
) -> str:
    """Allocate a timestamped collision-safe backtest ID."""
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    safe_label = _safe_id_label(run_label)
    if safe_label:
        base = f"{base}_{safe_label}"
    run_id = base
    suffix = 2
    while (backtests_root / run_id).exists():
        run_id = f"{base}_{suffix:02d}"
        suffix += 1
    return run_id


def _number(value: float | None) -> str:
    """Format an optional decimal for CSV output."""
    return "" if value is None else f"{value:.6f}"


def _relative(stock_return: float | None, benchmark_return: float | None) -> float | None:
    """Return stock minus benchmark performance when both exist."""
    if stock_return is None or benchmark_return is None:
        return None
    return stock_return - benchmark_return


def _evaluate_record(
    record: dict,
    provider: PriceHistoryProvider,
    benchmark_result: PriceHistoryResult,
) -> dict:
    """Evaluate one archived record against offline price fixtures."""
    result = {field: record.get(field, "") for field in RESULT_FIELDS}
    result["signal_date"] = _signal_date(record)
    blockers = _blocking_categories(record.get("promotion_blocking_categories"))
    result["promotion_blocking_categories"] = ";".join(blockers)
    result["promotion_blocking_count"] = len(blockers)
    generated_at = _parse_generated_at(record.get("generated_at"))
    if generated_at is None:
        result["data_status"] = "missing_signal_date"
        return result
    start_date = generated_at.date()
    ticker = str(record["ticker"]).upper()
    price_result = provider.get_price_history(ticker)
    if price_result.status != "available":
        result["data_status"] = price_result.status
        return result

    points = price_result.rows
    result["price_column_used"] = price_result.price_column_used or ""
    stock_observations = {
        months: forward_return_observation(points, start_date, months)
        for months in FORWARD_WINDOWS
    }
    stock_returns = {
        months: observation.value
        for months, observation in stock_observations.items()
    }
    first_start = stock_observations[3].start
    result["price_start_date"] = (
        first_start.date.isoformat() if first_start else ""
    )
    benchmark_returns = {
        months: (
            forward_return(benchmark_result.rows, start_date, months)
            if benchmark_result.status == "available"
            else None
        )
        for months in FORWARD_WINDOWS
    }
    for months in FORWARD_WINDOWS:
        end = stock_observations[months].end
        result[f"price_end_date_{months}m"] = (
            end.date.isoformat() if end else ""
        )
        result[f"forward_return_{months}m"] = _number(stock_returns[months])
        result[f"benchmark_return_{months}m"] = _number(
            benchmark_returns[months]
        )
        result[f"relative_return_{months}m"] = _number(
            _relative(stock_returns[months], benchmark_returns[months])
        )
    result["max_drawdown_12m"] = _number(
        max_drawdown(points, start_date, 12)
    )
    if stock_returns[12] is None:
        result["data_status"] = "insufficient_forward_history"
    elif benchmark_result.status != "available":
        result["data_status"] = "complete_without_benchmark"
    else:
        result["data_status"] = f"complete_{price_result.data_type}"
    return result


def _median_return(rows: list[dict], field: str) -> str:
    """Return a display median for non-empty decimal fields."""
    values = [float(row[field]) for row in rows if row.get(field) not in {"", None}]
    return f"{median(values):.4f}" if values else "Missing"


def _group_summary(
    rows: list[dict],
    field: str,
    heading: str,
    minimum_group_size: int,
) -> list[str]:
    """Render count and median-return summaries for one signal category."""
    groups: dict[str, list[dict]] = {}
    for row in rows:
        label = str(row.get(field) or "Missing")
        groups.setdefault(label, []).append(row)
    lines = [
        f"### {heading}",
        "",
        (
            "| Category | Records | Median 3M Return | Median 6M Return | "
            "Median 12M Return | Sample Warning |"
        ),
        "|---|---:|---:|---:|---:|---|",
    ]
    for label in sorted(groups):
        group = groups[label]
        lines.append(
            f"| {label} | {len(group)} | "
            f"{_median_return(group, 'forward_return_3m')} | "
            f"{_median_return(group, 'forward_return_6m')} | "
            f"{_median_return(group, 'forward_return_12m')} | "
            f"{f'Small sample: category has fewer than {minimum_group_size} records.' if len(group) < minimum_group_size else ''} |"
        )
    lines.append("")
    return lines


def _metric_display(value: object) -> str:
    """Format an optional metric for the main Markdown summary."""
    if value is None:
        return "Missing"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _compact_metrics_table(metrics: dict, field: str) -> list[str]:
    """Render one compact grouped metrics table."""
    lines = [
        f"### {field}",
        "",
        (
            "| Group | Sample Size | Median 12M Return | "
            "Median Relative 12M Return | Hit Rate vs Benchmark 12M | "
            "Small Sample Warning |"
        ),
        "|---|---:|---:|---:|---:|---|",
    ]
    for group in metrics["grouped_metrics"][field]:
        lines.append(
            f"| {group['group_name']} | {group['sample_size']} | "
            f"{_metric_display(group['median_forward_return_12m'])} | "
            f"{_metric_display(group['median_relative_return_12m'])} | "
            f"{_metric_display(group['hit_rate_vs_benchmark_12m'])} | "
            f"{_metric_display(group['small_sample_warning'])} |"
        )
    lines.append("")
    return lines


def _render_summary(manifest: dict, rows: list[dict], metrics: dict) -> str:
    """Render a transparent research-only backtest summary."""
    lines = [
        "# Archived Signal Backtest Summary",
        "",
        "## Run Context",
        "",
        f"- Backtest Run ID: {manifest['backtest_run_id']}",
        f"- Ledger Path: {manifest['ledger_path']}",
        (
            "- Historical Trial Ledger: "
            f"{str(manifest['historical_trial_ledger']).lower()}"
        ),
        (
            "- Trial Signal Source: "
            f"{manifest.get('trial_signal_source') or 'Not applicable'}"
        ),
        f"- Lookback Years: {manifest['lookback_years']}",
        f"- Dedupe Mode: {manifest['dedupe_mode']}",
        (
            "- Records Before Dedupe: "
            f"{manifest['total_records_before_dedupe']}"
        ),
        (
            "- Records After Dedupe: "
            f"{manifest['evaluated_records_after_dedupe']}"
        ),
        (
            "- Duplicate Records Removed: "
            f"{manifest['duplicate_records_removed']}"
        ),
        f"- Evaluated Records: {manifest['evaluated_records']}",
        f"- Skipped Records: {manifest['skipped_records']}",
        f"- Tickers Evaluated: {', '.join(manifest['tickers']) or 'None'}",
        "- Forward Windows: 3 months, 6 months, 12 months",
        f"- Benchmark: {manifest['benchmark']}",
        f"- Price Data Type: {manifest['price_data_type']}",
        f"- Minimum Group Size: {manifest['minimum_group_size']}",
        f"- Small Sample Warning: {str(manifest['small_sample_warning']).lower()}",
        *(
            [
                "",
                "## Readiness Trial Backtest Notice",
                "",
                "- Backtest Run Type: readiness_trial",
                "- Readiness Only: Yes",
                "- Not Trade Signal: Yes",
                "- Not Recommendation: Yes",
                "- Not Allocation Instruction: Yes",
                f"- Safety Notice: {manifest['safety_notice']}",
                "",
                (
                    "These results must not be interpreted as investment "
                    "recommendations or trading signals."
                ),
            ]
            if manifest["backtest_run_type"] == "readiness_trial"
            else []
        ),
        "",
        "## Price Data Provider",
        "",
        f"- Provider: {manifest['price_provider']}",
        f"- Provider Name: {manifest['price_provider_name']}",
        f"- Data Type: {manifest['price_data_type']}",
        (
            "- Synthetic fixture warning: price data is not live or "
            "historical market data."
            if manifest["price_data_type"] == "synthetic_fixture"
            else "- Synthetic fixture warning: not applicable."
        ),
        f"- Data Root: {manifest['price_data_root'] or 'Not used'}",
        f"- Live Data Enabled: {str(manifest['live_data_enabled']).lower()}",
        f"- Provider Status: {manifest['provider_status']}",
        (
            "- Live Provider Status: "
            f"{manifest.get('live_provider_status') or 'not_selected'}"
        ),
        (
            "- Live data is not enabled in this build. The live provider is "
            "a stub for future integration only."
        ),
        "",
        "## Quality Warnings",
        "",
        *[
            f"- {warning}"
            for warning in manifest["quality_warnings"]
        ],
        "",
        "## Grouped Research Summaries",
        "",
    ]
    lines.extend(
        _group_summary(
            rows,
            "readiness_label",
            "Readiness Label (`readiness_label`)",
            manifest["minimum_group_size"],
        )
    )
    lines.extend(
        _group_summary(
            rows,
            "source_verification_status",
            "Source Verification Status (`source_verification_status`)",
            manifest["minimum_group_size"],
        )
    )
    blocker_rows = []
    for row in rows:
        copy = dict(row)
        blocker_count = int(row.get("promotion_blocking_count") or 0)
        copy["blocking_category_group"] = _blocker_group(blocker_count)
        blocker_rows.append(copy)
    lines.extend(
        _group_summary(
            blocker_rows,
            "blocking_category_group",
            "Promotion-Blocking Count",
            manifest["minimum_group_size"],
        )
    )
    for interest_field in INTEREST_FIELDS:
        lines.extend(
            _group_summary(
                rows,
                interest_field,
                f"Investor Interest Level (`{interest_field}`)",
                manifest["minimum_group_size"],
            )
        )
    lines.extend(
        [
            "## Metrics Summary",
            "",
            f"- Sample Size: {metrics['sample_size']}",
            (
                "- Hit Rate vs Benchmark 12M: "
                f"{_metric_display(metrics['hit_rate_vs_benchmark_12m'])}"
            ),
            (
                "- Median Relative Return 12M: "
                f"{_metric_display(metrics['median_relative_return_12m'])}"
            ),
            (
                "- Positive Return Rate 12M: "
                f"{_metric_display(metrics['positive_return_rate_12m'])}"
            ),
            (
                "- Median Max Drawdown 12M: "
                f"{_metric_display(metrics['median_max_drawdown_12m'])}"
            ),
            (
                "- Small Sample Warning: "
                f"{_metric_display(metrics['small_sample_warning'])}"
            ),
            (
                "- Concentration Warning: "
                f"{_metric_display(metrics['concentration_warning'])}"
            ),
            (
                "- Synthetic Data Warning: "
                f"{_metric_display(metrics['synthetic_data_warning'])}"
            ),
            (
                "- Full Metrics JSON: "
                f"{manifest['metrics_summary_path']}"
            ),
            "",
            "## Grouped Metrics",
            "",
        ]
    )
    for field in (
        "readiness_label",
        "source_verification_status",
        "promotion_blocking_bucket",
    ):
        lines.extend(_compact_metrics_table(metrics, field))
    lines.extend(
        [
            "## Limitations",
            "",
            (
                "- Price histories are synthetic fixtures created for offline "
                "framework testing."
                if manifest["price_data_type"] == "synthetic_fixture"
                else (
                    "- Price histories use local CSV data supplied to the "
                    "provider."
                    if manifest["price_data_type"] == "local_csv"
                    else "- Live price histories are unavailable in this build."
                )
            ),
            "- Archived records may repeat a ticker across distinct runs.",
            "- The sample is too small for statistical inference.",
            "- Missing benchmark or ticker data remains explicitly missing.",
            "- Results evaluate associations only and do not define an investment strategy.",
            "",
            "## Safety Note",
            "",
            (
                "This backtest is not a recommendation, ranking, vote, average "
                "score, consensus, allocation instruction, rebalancing instruction, "
                "or trade signal. It is a research-only audit of archived fields."
            ),
            (
                "Results are research-only associations and must not be "
                "interpreted as investment advice or a trading strategy."
            ),
            *(
                [
                    (
                        "Historical trial ledgers are for research and pipeline "
                        "validation only and must not be interpreted as real "
                        "historical investment advice."
                    )
                ]
                if manifest["historical_trial_ledger"]
                else []
            ),
            "",
        ]
    )
    return "\n".join(lines)


def run_signal_backtest(
    *,
    ledger_path: Path,
    price_fixtures_path: Path,
    outputs_root: Path,
    price_provider: str = "fixture",
    lookback_years: int = 5,
    dedupe_mode: str = "latest_per_ticker_per_day",
    minimum_group_size: int = 5,
    walk_forward: bool = False,
    walk_forward_frequency: str = "yearly",
    run_label: str | None = None,
    generated_at: datetime | None = None,
) -> BacktestRunResult:
    """Evaluate archived signals against deterministic fixture price paths."""
    if lookback_years not in {2, 5, 10}:
        raise ValueError("lookback_years must be one of: 2, 5, 10.")
    if minimum_group_size < 1:
        raise ValueError("minimum_group_size must be at least 1.")
    if dedupe_mode not in DEDUPE_MODES:
        allowed = ", ".join(sorted(DEDUPE_MODES))
        raise ValueError(f"dedupe_mode must be one of: {allowed}.")
    if walk_forward_frequency != "yearly":
        raise ValueError("walk_forward_frequency must be yearly.")
    timestamp = generated_at or datetime.now(timezone.utc)
    cutoff = timestamp.replace(year=timestamp.year - lookback_years)
    loaded_records = _load_ledger(ledger_path)
    input_rows = len(loaded_records)
    readiness_trial = _is_readiness_trial(loaded_records)
    invalid_readiness_rows = 0
    readiness_warnings = []
    if readiness_trial:
        valid_records = []
        for index, record in enumerate(loaded_records, start=1):
            if _valid_readiness_trial_record(record):
                valid_records.append(record)
            else:
                invalid_readiness_rows += 1
                readiness_warnings.append(
                    f"Skipped readiness trial row {index}: safety fields are "
                    "missing or invalid."
                )
        loaded_records = valid_records
    trial_sources = sorted(
        {
            str(record.get("trial_signal_source") or "").strip()
            for record in loaded_records
            if str(record.get("trial_signal_source") or "").strip()
        }
    )
    historical_trial_ledger = bool(trial_sources)
    eligible_records = []
    for record in loaded_records:
        if record.get("status") != "completed":
            continue
        generated_at_value = _parse_generated_at(record.get("generated_at"))
        if generated_at_value is None or generated_at_value >= cutoff:
            eligible_records.append(record)
    noneligible_rows = len(loaded_records) - len(eligible_records)
    total_records_before_dedupe = len(eligible_records)
    records = _dedupe_records(eligible_records, dedupe_mode)
    duplicate_records_removed = total_records_before_dedupe - len(records)
    provider = create_price_provider(price_provider, price_fixtures_path)
    benchmark_result = provider.get_price_history("SPY")
    rows = [
        _evaluate_record(record, provider, benchmark_result)
        for record in records
    ]
    price_column_used_by_ticker = {
        str(row["ticker"]): str(row.get("price_column_used") or "")
        for row in rows
        if row.get("price_column_used")
    }
    if benchmark_result.price_column_used:
        price_column_used_by_ticker["SPY"] = (
            benchmark_result.price_column_used
        )
    evaluated_records = sum(
        str(row["data_status"]).startswith("complete") for row in rows
    )
    skipped_records = len(rows) - evaluated_records
    group_fields = (
        "readiness_label",
        "source_verification_status",
        *INTEREST_FIELDS,
    )
    small_groups = []
    for field in group_fields:
        counts: dict[str, int] = {}
        for row in rows:
            label = str(row.get(field) or "Missing")
            counts[label] = counts.get(label, 0) + 1
        small_groups.extend(
            f"{field}: {label} ({_record_word(count)})"
            for label, count in counts.items()
            if count < minimum_group_size
        )
    blocker_counts: dict[str, int] = {}
    for row in rows:
        label = _blocker_group(
            int(row.get("promotion_blocking_count") or 0)
        )
        blocker_counts[label] = blocker_counts.get(label, 0) + 1
    small_groups.extend(
        f"promotion_blocking_count: {label} ({_record_word(count)})"
        for label, count in blocker_counts.items()
        if count < minimum_group_size
    )
    small_sample_warning = (
        len(rows) < minimum_group_size or bool(small_groups)
    )
    quality_warnings = []
    quality_warnings.extend(readiness_warnings)
    if readiness_trial:
        quality_warnings.append(
            "Readiness trial rows are research-only artifacts and are not "
            "actionable signals."
        )
    if provider.data_type == "synthetic_fixture":
        quality_warnings.append(
            "Synthetic fixture price data is for framework testing only."
        )
    if provider.provider_status != "available":
        quality_warnings.append(
            "Live data provider is not implemented in this build. "
            "Use fixture or csv provider."
        )
    if duplicate_records_removed:
        quality_warnings.append(
            f"Dedupe removed {duplicate_records_removed} repeated archive records."
        )
    if small_sample_warning:
        quality_warnings.append(
            "Small sample: one or more grouped categories have fewer than "
            f"{minimum_group_size} records."
        )
        quality_warnings.extend(small_groups)

    backtests_root = Path(outputs_root) / "backtests"
    backtests_root.mkdir(parents=True, exist_ok=True)
    backtest_run_id = _allocate_run_id(
        backtests_root,
        timestamp,
        run_label,
    )
    backtest_folder = backtests_root / backtest_run_id
    backtest_folder.mkdir(parents=True, exist_ok=False)
    results_path = backtest_folder / "backtest_results.csv"
    with results_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    metrics = calculate_backtest_metrics(
        rows,
        price_data_type=provider.data_type,
    )
    metrics_summary_path = (
        backtest_folder / "backtest_metrics_summary.json"
    )
    metrics_summary_path.write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )
    metrics_summary_md_path = (
        backtest_folder / "backtest_metrics_summary.md"
    )
    metrics_summary_md_path.write_text(
        render_backtest_metrics_summary(metrics),
        encoding="utf-8",
    )
    benchmark_label = (
        (
            "SPY synthetic fixture"
            if provider.data_type == "synthetic_fixture"
            else f"SPY {provider.data_type}"
        )
        if benchmark_result.status == "available"
        else "Missing"
    )
    walk_forward_result = None
    if walk_forward:
        walk_forward_result = generate_walk_forward_outputs(
            rows=rows,
            output_dir=backtest_folder,
            context={
                "backtest_run_id": backtest_run_id,
                "ledger_path": str(ledger_path),
                "price_provider": provider.provider_name,
                "price_data_root": (
                    str(provider.data_root)
                    if provider.data_root is not None
                    else "Not used"
                ),
                "price_data_type": provider.data_type,
                "benchmark": benchmark_label,
            },
            frequency=walk_forward_frequency,
            minimum_group_size=minimum_group_size,
        )
    manifest = {
        "backtest_run_id": backtest_run_id,
        "ledger_path": str(ledger_path),
        "backtest_run_type": (
            "readiness_trial" if readiness_trial else "standard"
        ),
        "source_ledger_type": (
            "historical_readiness_trial_ledger"
            if readiness_trial
            else "standard_signal_ledger"
        ),
        "readiness_only": readiness_trial,
        "not_trade_signal": readiness_trial,
        "not_recommendation": readiness_trial,
        "not_allocation_instruction": readiness_trial,
        "safety_notice": (
            READINESS_TRIAL_SAFETY_NOTICE if readiness_trial else None
        ),
        "input_rows": input_rows,
        "evaluated_rows": len(records),
        "skipped_rows": invalid_readiness_rows + noneligible_rows,
        "invalid_readiness_rows": invalid_readiness_rows,
        "historical_trial_ledger": historical_trial_ledger,
        "trial_signal_source": ";".join(trial_sources) or None,
        "price_fixtures_path": str(price_fixtures_path),
        "price_provider": price_provider,
        "price_provider_name": provider.provider_name,
        "price_data_root": (
            str(provider.data_root) if provider.data_root is not None else None
        ),
        "live_data_enabled": provider.live_data_enabled,
        "provider_status": provider.provider_status,
        "live_provider_status": (
            "not_implemented"
            if provider.provider_name == "live_stub"
            else None
        ),
        "outputs_root": str(outputs_root),
        "lookback_years": lookback_years,
        "dedupe_mode": dedupe_mode,
        "total_records_before_dedupe": total_records_before_dedupe,
        "evaluated_records_after_dedupe": len(records),
        "duplicate_records_removed": duplicate_records_removed,
        "evaluated_records": evaluated_records,
        "skipped_records": skipped_records,
        "group_small_sample_warning": small_sample_warning,
        "minimum_group_size": minimum_group_size,
        "price_data_type": provider.data_type,
        "price_column_used_by_ticker": price_column_used_by_ticker,
        "quality_warnings": quality_warnings,
        "tickers": sorted({str(row["ticker"]) for row in rows}),
        "forward_windows": ["3m", "6m", "12m"],
        "benchmark": benchmark_label,
        "walk_forward_enabled": walk_forward,
        "walk_forward_frequency": (
            walk_forward_frequency if walk_forward else None
        ),
        "walk_forward_summary_path": (
            str(walk_forward_result.summary_path)
            if walk_forward_result
            else None
        ),
        "walk_forward_results_path": (
            str(walk_forward_result.results_path)
            if walk_forward_result
            else None
        ),
        "walk_forward_metrics_path": (
            str(walk_forward_result.metrics_path)
            if walk_forward_result
            else None
        ),
        "walk_forward_periods_evaluated": (
            walk_forward_result.metrics["total_periods"]
            if walk_forward_result
            else 0
        ),
        "results_path": str(results_path),
        "summary_path": str(backtest_folder / "backtest_summary.md"),
        "metrics_summary_path": str(metrics_summary_path),
        "metrics_summary_md_path": str(metrics_summary_md_path),
        "overall_sample_size": metrics["sample_size"],
        "small_sample_warning": metrics["small_sample_warning"],
        "synthetic_data_warning": metrics["synthetic_data_warning"],
        "status": "completed",
    }
    manifest_text = json.dumps(manifest, indent=2)
    manifest_path = backtest_folder / "backtest_manifest.json"
    manifest_path.write_text(manifest_text, encoding="utf-8")
    summary_path = backtest_folder / "backtest_summary.md"
    summary_path.write_text(
        _render_summary(manifest, rows, metrics),
        encoding="utf-8",
    )
    latest_manifest_path = backtests_root / "latest_backtest_manifest.json"
    latest_manifest_path.write_text(manifest_text, encoding="utf-8")
    return BacktestRunResult(
        backtest_run_id=backtest_run_id,
        backtest_folder=backtest_folder,
        summary_path=summary_path,
        results_path=results_path,
        metrics_summary_path=metrics_summary_path,
        metrics_summary_md_path=metrics_summary_md_path,
        manifest_path=manifest_path,
        latest_manifest_path=latest_manifest_path,
        evaluated_records=evaluated_records,
        skipped_records=skipped_records,
        metrics=metrics,
        backtest_run_type=manifest["backtest_run_type"],
        walk_forward_summary_path=(
            walk_forward_result.summary_path
            if walk_forward_result
            else None
        ),
        walk_forward_results_path=(
            walk_forward_result.results_path
            if walk_forward_result
            else None
        ),
        walk_forward_metrics_path=(
            walk_forward_result.metrics_path
            if walk_forward_result
            else None
        ),
        walk_forward_periods_evaluated=(
            walk_forward_result.metrics["total_periods"]
            if walk_forward_result
            else 0
        ),
    )
