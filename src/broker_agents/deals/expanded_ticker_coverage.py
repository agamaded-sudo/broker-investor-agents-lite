"""Offline coverage admission gate for an expanded readiness ticker universe."""

import csv
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
import json
from pathlib import Path

import yaml

from broker_agents.backtesting.price_history import (
    add_months,
    first_point_on_or_after,
    load_local_csv_price_history,
)
from broker_agents.deals.historical_date_coverage import (
    classify_coverage_quality,
)
from broker_agents.historical.historical_financials import (
    filter_financials_as_of,
    historical_financials_path,
    load_historical_financials_csv,
)

SAFETY_NOTICE = (
    "This expanded ticker coverage validation is a research infrastructure "
    "artifact. It is not a recommendation, ranking, allocation instruction, "
    "rebalancing instruction, trade signal, execution instruction, or "
    "investment advice."
)
MATRIX_FIELDS = (
    "ticker",
    "as_of_date",
    "eligibility",
    "coverage_quality",
    "coverage_severity",
    "financials_status",
    "price_anchor_status",
    "outcome_3m_available",
    "outcome_6m_available",
    "outcome_12m_available",
    "benchmark_12m_available",
    "has_delayed_price_anchor",
    "has_limited_financials",
    "main_limitation",
)


@dataclass(frozen=True)
class ExpandedTickerCoverageReport:
    """Structured expanded-universe coverage validation."""

    validation_run_id: str
    generated_at: str
    validation_status: str
    ticker_universe_path: str
    requested_tickers: list[str]
    requested_dates: list[str]
    eligible_tickers: list[str]
    caution_tickers: list[str]
    excluded_tickers: list[str]
    ticker_summaries: list[dict]
    ticker_date_matrix: list[dict]
    coverage_quality_counts: dict[str, int]
    eligibility_counts: dict[str, int]
    next_research_action: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class ExpandedTickerCoverageFiles:
    """Generated expanded-universe coverage artifact paths."""

    validation_folder: Path
    markdown_path: Path
    json_path: Path
    matrix_csv_path: Path
    eligible_universe_path: Path
    latest_manifest_path: Path
    report: ExpandedTickerCoverageReport


def load_expanded_ticker_universe(path: Path) -> dict:
    """Load and normalize a research-only candidate universe YAML."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Ticker universe YAML not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows = payload.get("tickers")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Ticker universe YAML must contain a non-empty tickers list.")
    normalized = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or not str(row.get("ticker") or "").strip():
            raise ValueError("Each ticker universe entry must contain ticker.")
        ticker = str(row["ticker"]).strip().upper()
        if ticker in seen:
            raise ValueError(f"Duplicate ticker in universe: {ticker}")
        seen.add(ticker)
        normalized.append(
            {
                "ticker": ticker,
                "sector": row.get("sector"),
                "category": row.get("category"),
                "reason_for_inclusion": row.get("reason_for_inclusion"),
                "universe_group": row.get("universe_group"),
            }
        )
    return {
        "universe_name": payload.get("universe_name"),
        "purpose": payload.get("purpose"),
        "safety_notice": payload.get("safety_notice"),
        "tickers": normalized,
    }


def _load_prices(path: Path) -> tuple[list, str] | tuple[None, None]:
    if not path.is_file():
        return None, None
    try:
        return load_local_csv_price_history(path)
    except (OSError, ValueError):
        return None, None


def _anchor_summary(points: list | None, as_of_date: date) -> dict:
    targets = {
        "start": as_of_date,
        "3m": add_months(as_of_date, 3),
        "6m": add_months(as_of_date, 6),
        "12m": add_months(as_of_date, 12),
    }
    anchors = {
        name: first_point_on_or_after(points or [], target)
        for name, target in targets.items()
    }
    delayed = {
        name: bool(anchor and anchor.date > targets[name])
        for name, anchor in anchors.items()
    }
    return {
        "targets": {name: value.isoformat() for name, value in targets.items()},
        "anchors": {
            name: anchor.date.isoformat() if anchor else None
            for name, anchor in anchors.items()
        },
        "available": {
            name: anchor is not None for name, anchor in anchors.items()
        },
        "delayed": delayed,
        "has_delayed_anchor": any(delayed.values()),
    }


def _financial_summary(financials_root: Path, ticker: str, cutoff: str) -> dict:
    path = historical_financials_path(financials_root, ticker)
    if not path.is_file():
        return {
            "status": "missing_financials",
            "path": str(path),
            "rows_available_as_of": 0,
            "has_limited_financials": True,
        }
    try:
        rows = load_historical_financials_csv(path)
        filtered = filter_financials_as_of(rows, cutoff)
    except (OSError, ValueError) as exc:
        return {
            "status": "invalid_financials",
            "path": str(path),
            "rows_available_as_of": 0,
            "has_limited_financials": True,
            "error": str(exc),
        }
    if filtered.rows_after_filter:
        status = (
            "available_with_exclusions"
            if filtered.rows_missing_availability_date_count
            else "available_point_in_time"
        )
    elif filtered.future_rows_excluded_count:
        status = "future_only_financials"
    else:
        status = "no_financials_available_by_as_of"
    return {
        "status": status,
        "path": str(path),
        "rows_available_as_of": filtered.rows_after_filter,
        "future_rows_excluded_count": filtered.future_rows_excluded_count,
        "rows_missing_availability_date_count": (
            filtered.rows_missing_availability_date_count
        ),
        "has_limited_financials": (
            filtered.rows_after_filter == 0
            or filtered.rows_missing_availability_date_count > 0
        ),
    }


def validate_ticker_date_coverage(
    *,
    ticker: str,
    as_of_date: str,
    financials_root: Path,
    price_root: Path,
    benchmark_ticker: str = "SPY",
) -> dict:
    """Validate one ticker/date pair under expanded-trial admission rules."""
    try:
        cutoff = date.fromisoformat(as_of_date)
    except ValueError as exc:
        raise ValueError("as_of_date must use YYYY-MM-DD format.") from exc
    ticker_path = Path(price_root) / f"{ticker.lower()}.csv"
    benchmark_path = Path(price_root) / f"{benchmark_ticker.lower()}.csv"
    ticker_points, ticker_column = _load_prices(ticker_path)
    benchmark_points, benchmark_column = _load_prices(benchmark_path)
    ticker_anchors = _anchor_summary(ticker_points, cutoff)
    benchmark_anchors = _anchor_summary(benchmark_points, cutoff)
    financials = _financial_summary(financials_root, ticker, as_of_date)
    required_ticker_prices = all(
        ticker_anchors["available"][name]
        for name in ("start", "3m", "6m", "12m")
    )
    required_benchmark_prices = all(
        benchmark_anchors["available"][name]
        for name in ("start", "3m", "6m", "12m")
    )
    delayed = (
        ticker_anchors["has_delayed_anchor"]
        or benchmark_anchors["has_delayed_anchor"]
    )
    limited = bool(financials["has_limited_financials"])
    unsupported = not required_ticker_prices or not required_benchmark_prices
    quality, severity = classify_coverage_quality(
        has_delayed_price_anchor=delayed,
        has_limited_financials=limited,
        has_unsupported_outcome_anchor=unsupported,
    )
    if limited or unsupported:
        eligibility = "not_eligible"
    elif delayed:
        eligibility = "eligible_with_warnings"
    else:
        eligibility = "eligible_clean"
    limitations = []
    if limited:
        limitations.append(financials["status"])
    if not ticker_anchors["available"]["start"]:
        limitations.append("missing_price_anchor")
    for horizon in ("3m", "6m", "12m"):
        if not ticker_anchors["available"][horizon]:
            limitations.append(f"missing_{horizon}_outcome")
        if not benchmark_anchors["available"][horizon]:
            limitations.append(f"missing_benchmark_{horizon}_outcome")
    if delayed:
        limitations.append("delayed_price_anchor")
    return {
        "ticker": ticker.upper(),
        "as_of_date": as_of_date,
        "eligibility": eligibility,
        "coverage_quality": quality,
        "coverage_severity": severity,
        "financials_status": financials["status"],
        "financials_rows_available_by_asof": financials["rows_available_as_of"],
        "price_anchor_status": (
            "missing" if not required_ticker_prices else
            "delayed" if ticker_anchors["has_delayed_anchor"] else "available"
        ),
        "benchmark_anchor_status": (
            "missing" if not required_benchmark_prices else
            "delayed" if benchmark_anchors["has_delayed_anchor"] else "available"
        ),
        "outcome_3m_available": ticker_anchors["available"]["3m"],
        "outcome_6m_available": ticker_anchors["available"]["6m"],
        "outcome_12m_available": ticker_anchors["available"]["12m"],
        "benchmark_12m_available": benchmark_anchors["available"]["12m"],
        "has_delayed_price_anchor": delayed,
        "has_limited_financials": limited,
        "ticker_price_column": ticker_column,
        "benchmark_price_column": benchmark_column,
        "ticker_anchors": ticker_anchors,
        "benchmark_anchors": benchmark_anchors,
        "main_limitation": limitations[0] if limitations else "none",
        "limitations": limitations,
    }


def classify_ticker_eligibility(rows: list[dict]) -> dict:
    """Classify one ticker from its date-level admission records."""
    if not rows:
        return {
            "status": "excluded_insufficient_coverage",
            "clean_records": 0,
            "usable_records": 0,
            "not_eligible_records": 0,
            "main_limitation": "no_date_records",
        }
    clean = sum(row["eligibility"] == "eligible_clean" for row in rows)
    usable = sum(row["eligibility"] != "not_eligible" for row in rows)
    excluded = len(rows) - usable
    if clean >= 2 and excluded / len(rows) <= 0.5:
        status = "eligible_for_expanded_trial"
    elif clean >= 1 and usable >= 3:
        status = "eligible_with_caution"
    else:
        status = "excluded_insufficient_coverage"
    limitations = [
        row["main_limitation"]
        for row in rows
        if row["main_limitation"] != "none"
    ]
    return {
        "status": status,
        "clean_records": clean,
        "usable_records": usable,
        "not_eligible_records": excluded,
        "main_limitation": limitations[0] if limitations else "none",
    }


def build_expanded_ticker_coverage_report(
    *,
    validation_run_id: str,
    generated_at: str,
    ticker_universe_path: Path,
    universe: dict,
    requested_dates: list[str],
    financials_root: Path,
    price_root: Path,
) -> ExpandedTickerCoverageReport:
    """Build an expanded-universe admission report from local fixtures."""
    matrix = []
    ticker_summaries = []
    eligible = []
    caution = []
    excluded = []
    for entry in universe["tickers"]:
        ticker = entry["ticker"]
        rows = [
            validate_ticker_date_coverage(
                ticker=ticker,
                as_of_date=value,
                financials_root=financials_root,
                price_root=price_root,
            )
            for value in requested_dates
        ]
        matrix.extend(rows)
        classification = classify_ticker_eligibility(rows)
        summary = {**entry, **classification}
        ticker_summaries.append(summary)
        if classification["status"] == "eligible_for_expanded_trial":
            eligible.append(ticker)
        elif classification["status"] == "eligible_with_caution":
            caution.append(ticker)
        else:
            excluded.append(ticker)
    quality_counts: dict[str, int] = {}
    eligibility_counts: dict[str, int] = {}
    for row in matrix:
        quality = row["coverage_quality"]
        eligibility = row["eligibility"]
        quality_counts[quality] = quality_counts.get(quality, 0) + 1
        eligibility_counts[eligibility] = (
            eligibility_counts.get(eligibility, 0) + 1
        )
    if not eligible and not caution:
        status = "insufficient_coverage"
    elif excluded:
        status = "valid_with_exclusions"
    elif caution or any(
        row["eligibility"] != "eligible_clean" for row in matrix
    ):
        status = "valid_with_cautions"
    else:
        status = "valid"
    return ExpandedTickerCoverageReport(
        validation_run_id=validation_run_id,
        generated_at=generated_at,
        validation_status=status,
        ticker_universe_path=str(ticker_universe_path),
        requested_tickers=[entry["ticker"] for entry in universe["tickers"]],
        requested_dates=requested_dates,
        eligible_tickers=eligible,
        caution_tickers=caution,
        excluded_tickers=excluded,
        ticker_summaries=ticker_summaries,
        ticker_date_matrix=matrix,
        coverage_quality_counts=dict(sorted(quality_counts.items())),
        eligibility_counts=dict(sorted(eligibility_counts.items())),
        next_research_action="run_expanded_ticker_readiness_trial",
    )


def render_expanded_ticker_coverage_report(
    report: ExpandedTickerCoverageReport,
) -> str:
    """Render expanded ticker coverage validation as Markdown."""
    lines = [
        "# Expanded Ticker Coverage Validation Report",
        "",
        "## Executive Summary",
        "",
        f"- Validation Status: {report.validation_status}",
        f"- Requested Tickers: {', '.join(report.requested_tickers)}",
        f"- Eligible Tickers: {', '.join(report.eligible_tickers) or 'None'}",
        f"- Caution Tickers: {', '.join(report.caution_tickers) or 'None'}",
        f"- Excluded Tickers: {', '.join(report.excluded_tickers) or 'None'}",
        (
            "- Main Finding: Candidate admission is controlled by local "
            "point-in-time financial and price coverage."
        ),
        "",
        "## Eligibility Summary",
        "",
        (
            "| Ticker | Status | Clean Records | Usable Records | "
            "Not Eligible Records | Main Limitation |"
        ),
        "|---|---|---:|---:|---:|---|",
    ]
    for item in report.ticker_summaries:
        lines.append(
            f"| {item['ticker']} | {item['status']} | "
            f"{item['clean_records']} | {item['usable_records']} | "
            f"{item['not_eligible_records']} | {item['main_limitation']} |"
        )
    lines.extend(
        [
            "",
            "## Ticker-Date Coverage Matrix",
            "",
            (
                "| Ticker | Date | Eligibility | Coverage Quality | "
                "Financials Status | Price Anchor Status | 12M Outcome "
                "Available | Benchmark Available |"
            ),
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for row in report.ticker_date_matrix:
        lines.append(
            f"| {row['ticker']} | {row['as_of_date']} | "
            f"{row['eligibility']} | {row['coverage_quality']} | "
            f"{row['financials_status']} | {row['price_anchor_status']} | "
            f"{row['outcome_12m_available']} | "
            f"{row['benchmark_12m_available']} |"
        )
    lines.extend(
        [
            "",
            "## Eligible Universe",
            "",
            (
                "- Expanded Trial Eligible: "
                f"{', '.join(report.eligible_tickers) or 'None'}"
            ),
            (
                "- Caution-Only: "
                f"{', '.join(report.caution_tickers) or 'None'}"
            ),
            "",
            "## Excluded / Caution Notes",
            "",
        ]
    )
    notes = [
        item
        for item in report.ticker_summaries
        if item["status"] != "eligible_for_expanded_trial"
    ]
    if notes:
        lines.extend(
            f"- {item['ticker']}: {item['status']} "
            f"({item['main_limitation']})."
            for item in notes
        )
    else:
        lines.append("- No candidate tickers were excluded or caution-only.")
    lines.extend(
        [
            "",
            "## What This Suggests",
            "",
            "- The sample can expand while preserving coverage controls.",
            "",
            "## What This Does Not Suggest",
            "",
            "- It does not rank tickers.",
            "- It does not recommend tickers.",
            "- It does not validate investor agents.",
            "- It does not create trade signals.",
            "",
            "## Next Research Action",
            "",
            f"- Action Code: {report.next_research_action}",
            "",
            "## Safety Notice",
            "",
            report.safety_notice,
            "",
        ]
    )
    return "\n".join(lines)


def _allocate_run_id(root: Path, timestamp: datetime) -> str:
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    candidate = base
    suffix = 2
    while (root / candidate).exists():
        candidate = f"{base}_{suffix:02d}"
        suffix += 1
    return candidate


def write_expanded_ticker_coverage_report(
    *,
    ticker_universe_path: Path,
    requested_dates: list[str],
    financials_root: Path,
    price_root: Path,
    outputs_root: Path,
    generated_at: datetime | None = None,
) -> ExpandedTickerCoverageFiles:
    """Validate and write an expanded-universe coverage bundle."""
    timestamp = generated_at or datetime.now(timezone.utc)
    root = Path(outputs_root) / "expanded_ticker_coverage"
    root.mkdir(parents=True, exist_ok=True)
    run_id = _allocate_run_id(root, timestamp)
    folder = root / run_id
    folder.mkdir(parents=True, exist_ok=False)
    universe = load_expanded_ticker_universe(ticker_universe_path)
    report = build_expanded_ticker_coverage_report(
        validation_run_id=run_id,
        generated_at=timestamp.isoformat(),
        ticker_universe_path=ticker_universe_path,
        universe=universe,
        requested_dates=requested_dates,
        financials_root=financials_root,
        price_root=price_root,
    )
    markdown_path = folder / "expanded_ticker_coverage_report.md"
    json_path = folder / "expanded_ticker_coverage_report.json"
    matrix_csv_path = folder / "expanded_ticker_coverage_matrix.csv"
    eligible_universe_path = folder / "expanded_ticker_eligible_universe.yaml"
    latest_manifest_path = (
        root / "latest_expanded_ticker_coverage_manifest.json"
    )
    markdown_path.write_text(
        render_expanded_ticker_coverage_report(report),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )
    with matrix_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATRIX_FIELDS)
        writer.writeheader()
        for row in report.ticker_date_matrix:
            writer.writerow({field: row.get(field) for field in MATRIX_FIELDS})
    admitted = set(report.eligible_tickers + report.caution_tickers)
    eligible_payload = {
        "validation_run_id": run_id,
        "tickers": [ticker for ticker in report.requested_tickers if ticker in admitted],
        "eligible_tickers": [
            item for item in report.ticker_summaries if item["ticker"] in admitted
        ],
        "safety_notice": SAFETY_NOTICE,
    }
    eligible_universe_path.write_text(
        yaml.safe_dump(eligible_payload, sort_keys=False),
        encoding="utf-8",
    )
    latest_manifest = {
        "validation_run_id": run_id,
        "validation_status": report.validation_status,
        "validation_folder": str(folder),
        "report_path": str(markdown_path),
        "report_json_path": str(json_path),
        "matrix_csv_path": str(matrix_csv_path),
        "eligible_universe_path": str(eligible_universe_path),
        "eligible_tickers": report.eligible_tickers,
        "caution_tickers": report.caution_tickers,
        "excluded_tickers": report.excluded_tickers,
        "generated_at": timestamp.isoformat(),
        "next_research_action": report.next_research_action,
        "safety_notice": SAFETY_NOTICE,
    }
    latest_manifest_path.write_text(
        json.dumps(latest_manifest, indent=2),
        encoding="utf-8",
    )
    return ExpandedTickerCoverageFiles(
        validation_folder=folder,
        markdown_path=markdown_path,
        json_path=json_path,
        matrix_csv_path=matrix_csv_path,
        eligible_universe_path=eligible_universe_path,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
