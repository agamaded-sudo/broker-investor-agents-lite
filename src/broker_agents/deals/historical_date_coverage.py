"""Offline date preset resolution and historical fixture coverage checks."""

from dataclasses import asdict, dataclass, field
from datetime import date
import json
from pathlib import Path

from broker_agents.backtesting.price_history import (
    add_months,
    first_point_on_or_after,
    load_local_csv_price_history,
)
from broker_agents.historical.historical_financials import (
    filter_financials_as_of,
    historical_financials_path,
    load_historical_financials_csv,
)

DATE_PRESETS = {
    "annual_3": (
        "2021-06-30",
        "2022-06-30",
        "2023-06-30",
    ),
    "semiannual_6": (
        "2021-06-30",
        "2021-12-31",
        "2022-06-30",
        "2022-12-31",
        "2023-06-30",
        "2023-12-31",
    ),
    "quarterly_9": (
        "2021-06-30",
        "2021-12-31",
        "2022-06-30",
        "2022-12-31",
        "2023-03-31",
        "2023-06-30",
        "2023-09-30",
        "2023-12-31",
        "2024-03-31",
    ),
}


@dataclass(frozen=True)
class HistoricalDateCoverageRecord:
    """Coverage evidence for one requested historical date."""

    as_of_date: str
    usable: bool
    status: str
    price_coverage_by_ticker: dict[str, dict] = field(default_factory=dict)
    financials_coverage_by_ticker: dict[str, dict] = field(
        default_factory=dict
    )
    ticker_coverage_quality: dict[str, dict] = field(default_factory=dict)
    coverage_quality_label: str = "unsupported"
    coverage_quality_severity: str = "unsupported"
    has_delayed_price_anchor: bool = False
    has_limited_financials: bool = False
    has_unsupported_outcome_anchor: bool = False
    warning_count: int = 0
    reason_count: int = 0
    warnings: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize one coverage record."""
        return asdict(self)


@dataclass(frozen=True)
class HistoricalDateCoverageReport:
    """Aggregate local fixture coverage for requested dates."""

    date_preset: str | None
    requested_dates: list[str]
    tickers: list[str]
    usable_dates: list[str]
    skipped_dates: list[str]
    validation_status: str
    date_records: list[HistoricalDateCoverageRecord]
    coverage_quality_counts: dict[str, int] = field(default_factory=dict)
    coverage_severity_counts: dict[str, int] = field(default_factory=dict)
    clean_date_count: int = 0
    warning_date_count: int = 0
    unsupported_date_count: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize the aggregate report."""
        return {
            **asdict(self),
            "date_records": [
                record.to_dict() for record in self.date_records
            ],
        }


def resolve_historical_date_preset(name: str) -> list[str]:
    """Resolve one supported historical readiness date preset."""
    normalized = str(name).strip().lower()
    if normalized not in DATE_PRESETS:
        allowed = ", ".join(DATE_PRESETS)
        raise ValueError(
            f"Unknown historical date preset '{name}'. "
            f"Supported presets: {allowed}."
        )
    return list(DATE_PRESETS[normalized])


def classify_coverage_quality(
    *,
    has_delayed_price_anchor: bool,
    has_limited_financials: bool,
    has_unsupported_outcome_anchor: bool,
    has_other_warnings: bool = False,
) -> tuple[str, str]:
    """Classify one date or ticker-date using conservative guardrails."""
    if has_unsupported_outcome_anchor:
        return "unsupported", "unsupported"
    if has_delayed_price_anchor and has_limited_financials:
        return "delayed_anchor_and_limited_financials", "high"
    if has_delayed_price_anchor:
        return "delayed_price_anchor", "moderate"
    if has_limited_financials:
        return "limited_financials", "moderate"
    if has_other_warnings:
        return "usable_with_warnings", "low"
    return "clean", "none"


def coverage_guardrail_status(severity: str) -> str:
    """Map quality severity to a stable trial guardrail status."""
    if severity == "none":
        return "clean"
    if severity in {"low", "moderate"}:
        return "research_usable_with_warnings"
    if severity == "high":
        return "warning_heavy"
    return "unsupported_excluded"


def _price_coverage(
    *,
    price_root: Path,
    ticker: str,
    as_of_date: date,
) -> tuple[dict, list[str], list[str]]:
    """Check start and 12M price anchors under current backtest semantics."""
    path = Path(price_root) / f"{ticker.lower()}.csv"
    warnings = []
    reasons = []
    if not path.is_file():
        reasons.append(f"{ticker}: price CSV is missing.")
        return {"file_found": False, "path": str(path)}, warnings, reasons
    try:
        points, price_column = load_local_csv_price_history(path)
    except (OSError, ValueError) as exc:
        reasons.append(f"{ticker}: invalid price CSV: {exc}")
        return {"file_found": True, "path": str(path)}, warnings, reasons
    start = first_point_on_or_after(points, as_of_date)
    target_end = add_months(as_of_date, 12)
    end = first_point_on_or_after(points, target_end)
    if start is None:
        reasons.append(f"{ticker}: no price anchor on or after {as_of_date}.")
    if end is None:
        reasons.append(
            f"{ticker}: no 12M outcome anchor on or after {target_end}."
        )
    if start is not None and start.date > as_of_date:
        warnings.append(
            f"{ticker}: start anchor is delayed to {start.date.isoformat()}."
        )
    if end is not None and end.date > target_end:
        warnings.append(
            f"{ticker}: 12M anchor is delayed to {end.date.isoformat()}."
        )
    return (
        {
            "file_found": True,
            "path": str(path),
            "price_column_used": price_column,
            "start_anchor": start.date.isoformat() if start else None,
            "target_end_date": target_end.isoformat(),
            "end_anchor_12m": end.date.isoformat() if end else None,
            "usable": start is not None and end is not None,
        },
        warnings,
        reasons,
    )


def _financials_coverage(
    *,
    financials_root: Path | None,
    ticker: str,
    as_of_date: str,
) -> tuple[dict, list[str], list[str]]:
    """Check local financial file availability and point-in-time rows."""
    warnings = []
    reasons = []
    if financials_root is None:
        reasons.append(f"{ticker}: financials root is not configured.")
        return {"file_found": False}, warnings, reasons
    path = historical_financials_path(financials_root, ticker)
    if not path.is_file():
        reasons.append(f"{ticker}: historical financials CSV is missing.")
        return {"file_found": False, "path": str(path)}, warnings, reasons
    try:
        rows = load_historical_financials_csv(path)
        filtered = filter_financials_as_of(rows, as_of_date)
    except (OSError, ValueError) as exc:
        reasons.append(f"{ticker}: invalid historical financials CSV: {exc}")
        return {"file_found": True, "path": str(path)}, warnings, reasons
    if filtered.rows_after_filter == 0:
        warnings.append(
            f"{ticker}: no financial rows were available by {as_of_date}; "
            "the run remains readiness-only."
        )
    warnings.extend(f"{ticker}: {warning}" for warning in filtered.warnings)
    return (
        {
            "file_found": True,
            "path": str(path),
            "rows_before_filter": filtered.rows_before_filter,
            "rows_available_as_of": filtered.rows_after_filter,
            "future_rows_excluded_count": (
                filtered.future_rows_excluded_count
            ),
            "rows_missing_availability_date_count": (
                filtered.rows_missing_availability_date_count
            ),
            "status": filtered.status,
        },
        warnings,
        reasons,
    )


def _ticker_quality(
    *,
    ticker: str,
    benchmark_ticker: str,
    price_coverage: dict[str, dict],
    financials_coverage: dict[str, dict],
    warnings: list[str],
    reasons: list[str],
) -> dict:
    """Build ticker-level quality metadata from local coverage evidence."""
    relevant_prefixes = (f"{ticker}:", f"{benchmark_ticker}:")
    ticker_warnings = [
        warning
        for warning in warnings
        if warning.startswith(relevant_prefixes)
    ]
    ticker_reasons = [
        reason for reason in reasons if reason.startswith(relevant_prefixes)
    ]
    ticker_price = price_coverage.get(ticker, {})
    benchmark_price = price_coverage.get(benchmark_ticker, {})
    financials = financials_coverage.get(ticker, {})
    delayed = any(
        (
            coverage.get("start_anchor")
            and coverage.get("start_anchor") != coverage.get("as_of_date")
        )
        or (
            coverage.get("end_anchor_12m")
            and coverage.get("end_anchor_12m")
            != coverage.get("target_end_date")
        )
        for coverage in (ticker_price, benchmark_price)
    )
    limited_financials = (
        int(financials.get("rows_available_as_of") or 0) == 0
        or int(financials.get("rows_missing_availability_date_count") or 0) > 0
    )
    unsupported = bool(ticker_reasons) or not ticker_price.get(
        "end_anchor_12m"
    ) or not benchmark_price.get("end_anchor_12m")
    label, severity = classify_coverage_quality(
        has_delayed_price_anchor=delayed,
        has_limited_financials=limited_financials,
        has_unsupported_outcome_anchor=unsupported,
        has_other_warnings=bool(ticker_warnings),
    )
    return {
        "coverage_quality_label": label,
        "coverage_quality_severity": severity,
        "date_coverage_status": (
            "unsupported" if unsupported else "usable_with_warnings"
            if ticker_warnings
            else "usable"
        ),
        "has_delayed_price_anchor": delayed,
        "has_limited_financials": limited_financials,
        "has_unsupported_outcome_anchor": unsupported,
        "warning_count": len(ticker_warnings),
        "reason_count": len(ticker_reasons),
        "coverage_guardrail_status": coverage_guardrail_status(severity),
    }


def validate_historical_date_coverage(
    *,
    requested_dates: list[str],
    tickers: list[str],
    price_root: Path,
    financials_root: Path | None,
    date_preset: str | None = None,
    benchmark_ticker: str = "SPY",
) -> HistoricalDateCoverageReport:
    """Validate local price outcomes and financial input availability."""
    date_records = []
    all_warnings = []
    checked_tickers = list(dict.fromkeys([*tickers, benchmark_ticker]))
    for value in requested_dates:
        try:
            parsed_date = date.fromisoformat(value)
        except ValueError:
            date_records.append(
                HistoricalDateCoverageRecord(
                    as_of_date=value,
                    usable=False,
                    status="unsupported",
                    coverage_quality_label="unsupported",
                    coverage_quality_severity="unsupported",
                    has_unsupported_outcome_anchor=True,
                    reason_count=1,
                    reasons=[f"Invalid ISO date: {value}."],
                )
            )
            continue
        price_coverage = {}
        financials_coverage = {}
        warnings = []
        reasons = []
        for ticker in checked_tickers:
            coverage, ticker_warnings, ticker_reasons = _price_coverage(
                price_root=price_root,
                ticker=ticker,
                as_of_date=parsed_date,
            )
            price_coverage[ticker] = coverage
            coverage["as_of_date"] = value
            warnings.extend(ticker_warnings)
            reasons.extend(ticker_reasons)
        for ticker in tickers:
            coverage, ticker_warnings, ticker_reasons = _financials_coverage(
                financials_root=financials_root,
                ticker=ticker,
                as_of_date=value,
            )
            financials_coverage[ticker] = coverage
            warnings.extend(ticker_warnings)
            reasons.extend(ticker_reasons)
        usable = not reasons
        ticker_quality = {
            ticker: _ticker_quality(
                ticker=ticker,
                benchmark_ticker=benchmark_ticker,
                price_coverage=price_coverage,
                financials_coverage=financials_coverage,
                warnings=warnings,
                reasons=reasons,
            )
            for ticker in tickers
        }
        delayed = any(
            item["has_delayed_price_anchor"]
            for item in ticker_quality.values()
        )
        limited = any(
            item["has_limited_financials"]
            for item in ticker_quality.values()
        )
        unsupported = not usable
        label, severity = classify_coverage_quality(
            has_delayed_price_anchor=delayed,
            has_limited_financials=limited,
            has_unsupported_outcome_anchor=unsupported,
            has_other_warnings=bool(warnings),
        )
        status = "unsupported" if unsupported else (
            "usable_with_warnings" if warnings else "usable"
        )
        date_records.append(
            HistoricalDateCoverageRecord(
                as_of_date=value,
                usable=usable,
                status=status,
                price_coverage_by_ticker=price_coverage,
                financials_coverage_by_ticker=financials_coverage,
                ticker_coverage_quality=ticker_quality,
                coverage_quality_label=label,
                coverage_quality_severity=severity,
                has_delayed_price_anchor=delayed,
                has_limited_financials=limited,
                has_unsupported_outcome_anchor=unsupported,
                warning_count=len(warnings),
                reason_count=len(reasons),
                warnings=warnings,
                reasons=reasons,
            )
        )
        all_warnings.extend(
            f"{value}: {warning}" for warning in warnings
        )
        all_warnings.extend(f"{value}: {reason}" for reason in reasons)
    usable_dates = [
        record.as_of_date for record in date_records if record.usable
    ]
    skipped_dates = [
        record.as_of_date for record in date_records if not record.usable
    ]
    if not usable_dates:
        validation_status = "insufficient_coverage"
    elif skipped_dates or all_warnings:
        validation_status = "valid_with_warnings"
    else:
        validation_status = "valid"
    quality_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    for record in date_records:
        quality_counts[record.coverage_quality_label] = (
            quality_counts.get(record.coverage_quality_label, 0) + 1
        )
        severity_counts[record.coverage_quality_severity] = (
            severity_counts.get(record.coverage_quality_severity, 0) + 1
        )
    return HistoricalDateCoverageReport(
        date_preset=date_preset,
        requested_dates=list(requested_dates),
        tickers=list(tickers),
        usable_dates=usable_dates,
        skipped_dates=skipped_dates,
        validation_status=validation_status,
        date_records=date_records,
        coverage_quality_counts=dict(sorted(quality_counts.items())),
        coverage_severity_counts=dict(sorted(severity_counts.items())),
        clean_date_count=quality_counts.get("clean", 0),
        warning_date_count=sum(
            count
            for label, count in quality_counts.items()
            if label not in {"clean", "unsupported"}
        ),
        unsupported_date_count=quality_counts.get("unsupported", 0),
        warnings=all_warnings,
    )


def render_historical_date_coverage_report(
    report: HistoricalDateCoverageReport,
) -> str:
    """Render a concise local fixture coverage report."""
    lines = [
        "# Historical Date Coverage Report",
        "",
        f"- Date Preset: {report.date_preset or 'explicit'}",
        f"- Requested Dates: {', '.join(report.requested_dates)}",
        f"- Usable Dates: {', '.join(report.usable_dates) or 'None'}",
        f"- Skipped Dates: {', '.join(report.skipped_dates) or 'None'}",
        f"- Validation Status: {report.validation_status}",
        "",
        "## Quality Summary",
        "",
        f"- Coverage Quality Counts: {report.coverage_quality_counts}",
        f"- Coverage Severity Counts: {report.coverage_severity_counts}",
        f"- Clean Date Count: {report.clean_date_count}",
        f"- Warning Date Count: {report.warning_date_count}",
        f"- Unsupported Date Count: {report.unsupported_date_count}",
        "",
        (
            "| As-Of Date | Usable | Status | Quality | Severity | Delayed "
            "Anchor | Limited Financials | Unsupported Outcome | Warnings | "
            "Reasons |"
        ),
        "|---|---|---|---|---|---|---|---|---:|---:|",
    ]
    for record in report.date_records:
        lines.append(
            f"| {record.as_of_date} | {'Yes' if record.usable else 'No'} | "
            f"{record.status} | {record.coverage_quality_label} | "
            f"{record.coverage_quality_severity} | "
            f"{record.has_delayed_price_anchor} | "
            f"{record.has_limited_financials} | "
            f"{record.has_unsupported_outcome_anchor} | "
            f"{record.warning_count} | {record.reason_count} |"
        )
    lines.extend(
        [
            "",
            "Quality labels distinguish clean dates, generic warnings, "
            "delayed price anchors, limited financial coverage, combined "
            "high-severity warnings, and unsupported dates.",
            "",
            "Coverage uses local CSV fixtures only. Delayed price anchors are "
            "reported explicitly and unsupported dates are not fabricated.",
            "",
            "Warning-heavy records remain readiness-only research artifacts. "
            "This coverage report does not produce recommendations, rankings, "
            "allocation instructions, or trade signals.",
            "",
        ]
    )
    return "\n".join(lines)


def build_historical_date_coverage_report(
    *,
    report: HistoricalDateCoverageReport,
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Write JSON and Markdown coverage artifacts."""
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_historical_date_coverage_report(report),
        encoding="utf-8",
    )
