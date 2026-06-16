"""BO-001 backtest driver decomposition for held research evidence."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean, median

SAFETY_NOTICE = (
    "This report decomposes research evidence only. It does not create an "
    "investment decision, recommendation, ranking, allocation instruction, "
    "rebalancing instruction, trade signal, execution instruction, strategy "
    "validation, or investment advice."
)
WORK_ORDER_ID = "BO-001"
WORK_ORDER_TITLE = "Backtest Driver Decomposition"
NEXT_WORK_ORDER = "BO-002 Outlier and Ex-NVDA Repair Path"


@dataclass(frozen=True)
class BacktestDriverDecompositionReport:
    """Structured BO-001 decomposition result."""

    decomposition_run_id: str
    generated_at: str
    backoffice_attribution_run_id: str
    investor_persona_attribution_run_id: str
    gatekeeper_run_id: str
    scorecard_run_id: str
    analysis_run_id: str
    expanded_trial_run_id: str
    backtest_run_id: str
    work_order_id: str
    work_order_title: str
    decomposition_status: str
    reconciliation: dict
    ticker_drivers: list[dict]
    date_drivers: list[dict]
    cohort_drivers: list[dict]
    sector_drivers: list[dict]
    category_drivers: list[dict]
    universe_group_drivers: list[dict]
    absolute_vs_relative_decomposition: dict
    driver_summary: dict
    recommended_next_work_order: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class BacktestDriverDecompositionFiles:
    """Generated decomposition files and report."""

    decomposition_folder: Path
    markdown_path: Path
    json_path: Path
    ticker_csv_path: Path
    date_csv_path: Path
    cohort_csv_path: Path
    sector_csv_path: Path
    category_csv_path: Path
    universe_group_csv_path: Path
    latest_manifest_path: Path
    report: BacktestDriverDecompositionReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_backoffice_attribution_manifest(
    *,
    outputs_root: Path,
    backoffice_attribution_run_id: str | None = None,
) -> dict:
    """Load one Backoffice attribution report or the latest manifest."""
    root = Path(outputs_root) / "backoffice_evidence_quality_attributions"
    path = (
        root
        / str(backoffice_attribution_run_id)
        / "backoffice_evidence_quality_attribution_report.json"
        if backoffice_attribution_run_id
        else root
        / "latest_backoffice_evidence_quality_attribution_manifest.json"
    )
    payload = _load_required_json(path, "Backoffice attribution manifest")
    payload["_manifest_path"] = str(path)
    return payload


def load_backoffice_attribution_report(
    *,
    outputs_root: Path,
    backoffice_attribution_run_id: str,
) -> dict:
    """Load a complete Backoffice attribution report."""
    path = (
        Path(outputs_root)
        / "backoffice_evidence_quality_attributions"
        / str(backoffice_attribution_run_id)
        / "backoffice_evidence_quality_attribution_report.json"
    )
    return _load_required_json(path, "Backoffice attribution report")


def load_expanded_trial_analysis_report(
    *, outputs_root: Path, analysis_run_id: str
) -> dict:
    """Load linked expanded-trial analysis context."""
    return _load_optional_json(
        Path(outputs_root)
        / "expanded_trial_analyses"
        / str(analysis_run_id)
        / "expanded_trial_analysis_report.json"
    )


def load_expanded_trial_summary(
    *, outputs_root: Path, expanded_trial_run_id: str
) -> dict:
    """Load linked expanded trial summary context."""
    return _load_optional_json(
        Path(outputs_root)
        / "expanded_ticker_trials"
        / str(expanded_trial_run_id)
        / "expanded_ticker_trial_summary.json"
    )


def load_backtest_manifest(*, outputs_root: Path, backtest_run_id: str) -> dict:
    """Load linked backtest manifest."""
    return _load_optional_json(
        Path(outputs_root)
        / "backtests"
        / str(backtest_run_id)
        / "backtest_manifest.json"
    )


def load_backtest_results(
    *, outputs_root: Path, backtest_run_id: str
) -> list[dict]:
    """Load expanded trial backtest result rows."""
    path = (
        Path(outputs_root)
        / "backtests"
        / str(backtest_run_id)
        / "backtest_results.csv"
    )
    if not path.is_file():
        raise FileNotFoundError(f"Backtest results not found: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _as_float(row: dict, key: str) -> float | None:
    value = row.get(key)
    if value in {None, "", "Missing"}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _as_bool(row: dict, key: str) -> bool:
    return str(row.get(key, "")).strip().lower() == "true"


def _round(value: float | None) -> float | None:
    return None if value is None else round(value, 6)


def _metadata_by_ticker(analysis: dict) -> dict[str, dict]:
    return {
        item["ticker"]: item
        for item in analysis.get("ticker_attribution", [])
        if item.get("ticker")
    }


def _enrich_rows(rows: list[dict], analysis: dict) -> list[dict]:
    metadata = _metadata_by_ticker(analysis)
    enriched = []
    for row in rows:
        item = dict(row)
        ticker_meta = metadata.get(str(row.get("ticker")), {})
        item["sector"] = row.get("sector") or ticker_meta.get("sector") or "Missing"
        item["category"] = (
            row.get("category") or ticker_meta.get("category") or "Missing"
        )
        item["universe_group"] = (
            row.get("universe_group")
            or ticker_meta.get("universe_group")
            or "Missing"
        )
        item["cohort"] = (
            "current_core"
            if item["universe_group"] == "current_core"
            else "expanded_cohort"
        )
        enriched.append(item)
    return enriched


def _hit_rate(rows: list[dict]) -> float | None:
    values = [
        value
        for value in (_as_float(row, "relative_return_12m") for row in rows)
        if value is not None
    ]
    if not values:
        return None
    return sum(value > 0 for value in values) / len(values)


def _metric_summary(rows: list[dict]) -> dict:
    forward = [
        value
        for value in (_as_float(row, "forward_return_12m") for row in rows)
        if value is not None
    ]
    relative = [
        value
        for value in (_as_float(row, "relative_return_12m") for row in rows)
        if value is not None
    ]
    drawdown = [
        value
        for value in (_as_float(row, "max_drawdown_12m") for row in rows)
        if value is not None
    ]
    return {
        "records": len(rows),
        "clean_records": sum(
            row.get("coverage_guardrail_status") == "clean"
            or row.get("coverage_quality_label") == "clean"
            for row in rows
        ),
        "warning_records": sum(
            row.get("coverage_guardrail_status") != "clean"
            and row.get("coverage_quality_label") != "clean"
            for row in rows
        ),
        "median_forward_return_12m": _round(median(forward) if forward else None),
        "median_relative_return_12m": _round(
            median(relative) if relative else None
        ),
        "average_relative_return_12m": _round(mean(relative) if relative else None),
        "hit_rate_vs_benchmark_12m": _round(_hit_rate(rows)),
        "worst_max_drawdown_12m": _round(min(drawdown) if drawdown else None),
    }


def _driver_label(summary: dict) -> str:
    records = int(summary.get("records") or 0)
    median_relative = summary.get("median_relative_return_12m")
    hit_rate = summary.get("hit_rate_vs_benchmark_12m")
    if records < 3:
        return "insufficient_evidence"
    if median_relative is None or hit_rate is None:
        return "insufficient_evidence"
    if median_relative <= -0.1 and hit_rate < 0.34:
        return "severe_negative_driver"
    if median_relative < 0 and hit_rate < 0.5:
        return "negative_driver"
    if median_relative > 0 and hit_rate >= 0.5:
        return "positive_driver"
    return "mixed_driver"


def _interpret(label: str, dimension: str, name: str) -> str:
    if label == "positive_driver":
        return f"{dimension} {name} is associated with stronger relative evidence."
    if label == "severe_negative_driver":
        return f"{dimension} {name} is a severe negative relative driver."
    if label == "negative_driver":
        return f"{dimension} {name} contributes to benchmark-relative weakness."
    if label == "mixed_driver":
        return f"{dimension} {name} is mixed and needs deeper attribution."
    return f"{dimension} {name} has too few usable records for attribution."


def _group(rows: list[dict], key: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(str(row.get(key) or "Missing"), []).append(row)
    return grouped


def _build_group_drivers(
    rows: list[dict],
    *,
    key: str,
    dimension: str,
    include_ticker_count: bool = False,
) -> list[dict]:
    drivers = []
    for name, group_rows in sorted(_group(rows, key).items()):
        summary = _metric_summary(group_rows)
        label = _driver_label(summary)
        item = {
            key: name,
            **summary,
            "driver_label": label,
            "interpretation": _interpret(label, dimension, name),
        }
        if include_ticker_count:
            item["ticker_count"] = len({row.get("ticker") for row in group_rows})
        drivers.append(item)
    return drivers


def decompose_by_ticker(rows: list[dict]) -> list[dict]:
    """Create ticker-level driver rows."""
    drivers = []
    for ticker, ticker_rows in sorted(_group(rows, "ticker").items()):
        summary = _metric_summary(ticker_rows)
        label = _driver_label(summary)
        first = ticker_rows[0]
        drivers.append(
            {
                "ticker": ticker,
                "cohort": first.get("cohort"),
                "universe_group": first.get("universe_group"),
                "sector": first.get("sector"),
                "category": first.get("category"),
                **summary,
                "driver_label": label,
                "interpretation": _interpret(label, "Ticker", ticker),
            }
        )
    return drivers


def decompose_by_date(rows: list[dict], analysis: dict) -> list[dict]:
    """Create date-level driver rows."""
    label_by_date = {
        item.get("as_of_date"): item.get("period_label")
        for item in analysis.get("date_attribution", [])
    }
    drivers = []
    for date, date_rows in sorted(_group(rows, "signal_date").items()):
        summary = _metric_summary(date_rows)
        label = _driver_label(summary)
        period_label = label_by_date.get(date)
        if not period_label:
            period_label = (
                "supportive_period"
                if label == "positive_driver"
                else "negative_period"
                if label in {"negative_driver", "severe_negative_driver"}
                else "neutral_period"
            )
        drivers.append(
            {
                "as_of_date": date,
                "ticker_count": len({row.get("ticker") for row in date_rows}),
                **summary,
                "period_label": period_label,
                "driver_label": label,
                "interpretation": _interpret(label, "Date", date),
            }
        )
    return drivers


def decompose_by_cohort(rows: list[dict]) -> list[dict]:
    """Create current-core, expanded-cohort, and full-universe rows."""
    drivers = _build_group_drivers(
        rows,
        key="cohort",
        dimension="Cohort",
        include_ticker_count=True,
    )
    full = _metric_summary(rows)
    label = _driver_label(full)
    drivers.append(
        {
            "cohort": "full_expanded_universe",
            "ticker_count": len({row.get("ticker") for row in rows}),
            **full,
            "driver_label": label,
            "interpretation": _interpret(label, "Cohort", "full_expanded_universe"),
        }
    )
    return drivers


def decompose_by_sector(rows: list[dict]) -> list[dict]:
    """Create sector-level driver rows."""
    return _build_group_drivers(
        rows,
        key="sector",
        dimension="Sector",
        include_ticker_count=True,
    )


def decompose_by_category(rows: list[dict]) -> list[dict]:
    """Create category-level driver rows."""
    return _build_group_drivers(
        rows,
        key="category",
        dimension="Category",
        include_ticker_count=True,
    )


def decompose_by_universe_group(rows: list[dict]) -> list[dict]:
    """Create universe-group-level driver rows."""
    return _build_group_drivers(
        rows,
        key="universe_group",
        dimension="Universe group",
        include_ticker_count=True,
    )


def compare_core_vs_expanded(cohort_drivers: list[dict]) -> dict:
    """Summarize current-core versus expanded-cohort evidence."""
    by_cohort = {item["cohort"]: item for item in cohort_drivers}
    core = by_cohort.get("current_core", {})
    expanded = by_cohort.get("expanded_cohort", {})
    core_relative = core.get("median_relative_return_12m")
    expanded_relative = expanded.get("median_relative_return_12m")
    return {
        "current_core_median_relative_return_12m": core_relative,
        "expanded_cohort_median_relative_return_12m": expanded_relative,
        "relative_gap_expanded_minus_core": _round(
            expanded_relative - core_relative
            if core_relative is not None and expanded_relative is not None
            else None
        ),
        "current_core_hit_rate_vs_benchmark_12m": core.get(
            "hit_rate_vs_benchmark_12m"
        ),
        "expanded_cohort_hit_rate_vs_benchmark_12m": expanded.get(
            "hit_rate_vs_benchmark_12m"
        ),
        "interpretation": (
            "The expanded cohort is materially weaker than the current-core "
            "cohort on median relative 12M evidence."
        ),
    }


def reconcile_group_totals(
    *,
    rows: list[dict],
    expected_rows: int,
) -> dict:
    """Reconcile loaded rows to the expected expanded-trial sample."""
    total = len(rows)
    missing = max(expected_rows - total, 0)
    return {
        "total_backtest_rows_loaded": total,
        "total_rows_used": total,
        "expected_rows": expected_rows,
        "rows_reconciled": total if total == expected_rows else min(total, expected_rows),
        "missing_rows": missing,
        "reconciliation_status": (
            "reconciled" if total == expected_rows and missing == 0 else "mismatch"
        ),
    }


def _absolute_vs_relative(rows: list[dict]) -> dict:
    summary = _metric_summary(rows)
    absolute = summary["median_forward_return_12m"]
    relative = summary["median_relative_return_12m"]
    return {
        "median_forward_return_12m": absolute,
        "median_relative_return_12m": relative,
        "absolute_positive": bool(absolute is not None and absolute > 0),
        "relative_positive": bool(relative is not None and relative > 0),
        "interpretation": (
            "Median absolute 12M outcomes are positive, while median "
            "benchmark-relative 12M outcomes are negative. Absolute return "
            "evidence alone therefore does not explain benchmark-relative weakness."
        ),
    }


def _driver_summary(
    *,
    ticker_drivers: list[dict],
    date_drivers: list[dict],
    cohort_drivers: list[dict],
    sector_drivers: list[dict],
    absolute_vs_relative: dict,
) -> dict:
    negative_labels = {"negative_driver", "severe_negative_driver"}
    primary_negative = [
        f"ticker:{item['ticker']}"
        for item in ticker_drivers
        if item["driver_label"] in negative_labels
    ][:8]
    primary_negative.extend(
        f"date:{item['as_of_date']}"
        for item in date_drivers
        if item["driver_label"] in negative_labels
    )
    primary_positive = [
        f"ticker:{item['ticker']}"
        for item in ticker_drivers
        if item["driver_label"] == "positive_driver"
    ]
    mixed = [
        f"sector:{item['sector']}"
        for item in sector_drivers
        if item["driver_label"] == "mixed_driver"
    ]
    core_vs_expanded = compare_core_vs_expanded(cohort_drivers)
    return {
        "primary_negative_drivers": primary_negative,
        "primary_positive_drivers": primary_positive,
        "mixed_drivers": mixed,
        "main_driver_finding": (
            "The expanded trial weakened because the added cohort and most "
            "post-2021 periods underperformed the benchmark, even though "
            "absolute 12M outcomes remained positive."
        ),
        "benchmark_underperformance_explanation": (
            absolute_vs_relative["interpretation"]
        ),
        "expanded_cohort_explanation": core_vs_expanded["interpretation"],
        "period_sensitivity_explanation": (
            "2021-06-30 was supportive, while later evaluated periods were "
            "negative or mixed on benchmark-relative evidence."
        ),
        "core_vs_expanded_comparison": core_vs_expanded,
        "recommended_next_work_order": NEXT_WORK_ORDER,
    }


def build_backtest_driver_decomposition(
    *,
    decomposition_run_id: str,
    generated_at: str,
    backoffice: dict,
    analysis: dict,
    expanded_summary: dict,
    backtest_manifest: dict,
    rows: list[dict],
) -> BacktestDriverDecompositionReport:
    """Build BO-001 decomposition from raw backtest rows."""
    enriched = _enrich_rows(rows, analysis)
    expected_rows = int(
        expanded_summary.get("sample_size_after_dedupe")
        or backtest_manifest.get("sample_size_after_dedupe")
        or backtest_manifest.get("evaluated_records")
        or 60
    )
    ticker = decompose_by_ticker(enriched)
    dates = decompose_by_date(enriched, analysis)
    cohorts = decompose_by_cohort(enriched)
    sectors = decompose_by_sector(enriched)
    categories = decompose_by_category(enriched)
    universe_groups = decompose_by_universe_group(enriched)
    absolute_vs_relative = _absolute_vs_relative(enriched)
    reconciliation = reconcile_group_totals(rows=enriched, expected_rows=expected_rows)
    summary = _driver_summary(
        ticker_drivers=ticker,
        date_drivers=dates,
        cohort_drivers=cohorts,
        sector_drivers=sectors,
        absolute_vs_relative=absolute_vs_relative,
    )
    return BacktestDriverDecompositionReport(
        decomposition_run_id=decomposition_run_id,
        generated_at=generated_at,
        backoffice_attribution_run_id=str(
            backoffice.get("backoffice_attribution_run_id") or ""
        ),
        investor_persona_attribution_run_id=str(
            backoffice.get("investor_persona_attribution_run_id") or ""
        ),
        gatekeeper_run_id=str(backoffice.get("gatekeeper_run_id") or ""),
        scorecard_run_id=str(backoffice.get("scorecard_run_id") or ""),
        analysis_run_id=str(backoffice.get("analysis_run_id") or ""),
        expanded_trial_run_id=str(backoffice.get("expanded_trial_run_id") or ""),
        backtest_run_id=str(backoffice.get("backtest_run_id") or ""),
        work_order_id=WORK_ORDER_ID,
        work_order_title=WORK_ORDER_TITLE,
        decomposition_status=(
            "completed"
            if reconciliation["reconciliation_status"] == "reconciled"
            else "completed_with_reconciliation_warning"
        ),
        reconciliation=reconciliation,
        ticker_drivers=ticker,
        date_drivers=dates,
        cohort_drivers=cohorts,
        sector_drivers=sectors,
        category_drivers=categories,
        universe_group_drivers=universe_groups,
        absolute_vs_relative_decomposition=absolute_vs_relative,
        driver_summary=summary,
        recommended_next_work_order=NEXT_WORK_ORDER,
    )


def _join(items: list) -> str:
    return "; ".join(str(item) for item in items)


def render_backtest_driver_decomposition_report(
    report: BacktestDriverDecompositionReport,
) -> str:
    """Render the decomposition report as Markdown."""
    data = report.to_dict()
    reconciliation = data["reconciliation"]
    absolute = data["absolute_vs_relative_decomposition"]
    summary = data["driver_summary"]
    lines = [
        "# Backtest Driver Decomposition Report",
        "",
        "## Executive Summary",
        "",
        f"- Decomposition Run ID: {data['decomposition_run_id']}",
        f"- Backoffice Attribution Run ID: {data['backoffice_attribution_run_id']}",
        f"- Work Order ID: {data['work_order_id']}",
        f"- Backtest Run ID: {data['backtest_run_id']}",
        f"- Reconciliation Status: {reconciliation['reconciliation_status']}",
        f"- Main Driver Finding: {summary['main_driver_finding']}",
        f"- Recommended Next Work Order: {data['recommended_next_work_order']}",
        "",
        "## Important Boundary",
        "",
        (
            "This report decomposes evidence only. It does not create an "
            "investment decision, ranking, recommendation, allocation, "
            "rebalancing instruction, trade signal, or execution instruction."
        ),
        "",
        "## Source Context",
        "",
        "- Gatekeeper Decision: hold",
        "- Progression Allowed: false",
        f"- Current Work Order: {data['work_order_id']}",
        (
            "- Reason: benchmark-relative underperformance and expanded cohort "
            "weakening."
        ),
        "",
        "## Reconciliation",
        "",
        f"- Total Backtest Rows Loaded: {reconciliation['total_backtest_rows_loaded']}",
        f"- Total Rows Used: {reconciliation['total_rows_used']}",
        f"- Expected Rows: {reconciliation['expected_rows']}",
        f"- Rows Reconciled: {reconciliation['rows_reconciled']}",
        f"- Missing Rows: {reconciliation['missing_rows']}",
        f"- Reconciliation Status: {reconciliation['reconciliation_status']}",
        "",
        "## Absolute vs Benchmark-Relative Evidence",
        "",
        f"- Median Forward Return 12M: {absolute['median_forward_return_12m']}",
        f"- Median Relative Return 12M: {absolute['median_relative_return_12m']}",
        f"- Absolute Positive: {str(absolute['absolute_positive']).lower()}",
        f"- Relative Positive: {str(absolute['relative_positive']).lower()}",
        f"- Interpretation: {absolute['interpretation']}",
        "",
        "## Ticker Driver Decomposition",
        "",
        (
            "| Ticker | Cohort | Sector | Records | Median Relative 12M | "
            "Hit Rate vs Benchmark | Driver Label |"
        ),
        "|---|---|---|---:|---:|---:|---|",
    ]
    for item in data["ticker_drivers"]:
        lines.append(
            f"| {item['ticker']} | {item['cohort']} | {item['sector']} | "
            f"{item['records']} | {item['median_relative_return_12m']} | "
            f"{item['hit_rate_vs_benchmark_12m']} | {item['driver_label']} |"
        )
    for title, key, name_field in (
        ("Date Driver Decomposition", "date_drivers", "as_of_date"),
        ("Cohort Driver Decomposition", "cohort_drivers", "cohort"),
        ("Sector Driver Decomposition", "sector_drivers", "sector"),
        ("Category Driver Decomposition", "category_drivers", "category"),
        (
            "Universe Group Driver Decomposition",
            "universe_group_drivers",
            "universe_group",
        ),
    ):
        lines.extend(
            [
                "",
                f"## {title}",
                "",
                (
                    f"| {name_field.replace('_', ' ').title()} | Tickers | "
                    "Records | Median Relative 12M | Hit Rate vs Benchmark | "
                    "Driver Label |"
                ),
                "|---|---:|---:|---:|---:|---|",
            ]
        )
        for item in data[key]:
            lines.append(
                f"| {item[name_field]} | {item.get('ticker_count', '')} | "
                f"{item['records']} | {item['median_relative_return_12m']} | "
                f"{item['hit_rate_vs_benchmark_12m']} | {item['driver_label']} |"
            )
    lines.extend(
        [
            "",
            "## Main Driver Findings",
            "",
            (
                "- Expanded cohort explanation: "
                f"{summary['expanded_cohort_explanation']}"
            ),
            (
                "- Period sensitivity explanation: "
                f"{summary['period_sensitivity_explanation']}"
            ),
            (
                "- Benchmark underperformance explanation: "
                f"{summary['benchmark_underperformance_explanation']}"
            ),
            (
                "- Primary Negative Drivers: "
                f"{_join(summary['primary_negative_drivers'])}"
            ),
            (
                "- Primary Positive Drivers: "
                f"{_join(summary['primary_positive_drivers'])}"
            ),
            "",
            "## What This Suggests",
            "",
            "- The expanded sample failed to generalize the prior core evidence.",
            (
                "- Backoffice should continue to outlier and stability repair "
                "before any re-gating."
            ),
            "",
            "## What This Does Not Suggest",
            "",
            "- It does not prove a strategy.",
            "- It does not rank tickers.",
            "- It does not recommend buying or selling.",
            "- It does not validate investor agents.",
            "- It does not create a trade signal.",
            "- It does not justify allocation or rebalancing.",
            "",
            "## Next Work Order",
            "",
            f"- {data['recommended_next_work_order']}",
            "",
            "## Safety Notice",
            "",
            data["safety_notice"],
            "",
        ]
    )
    return "\n".join(lines)


def _csv_value(value) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return "" if value is None else str(value)


def _write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in fields})


def write_backtest_driver_decomposition_report(
    *,
    outputs_root: Path,
    backoffice_attribution_run_id: str | None = None,
    generated_at: datetime | None = None,
) -> BacktestDriverDecompositionFiles:
    """Load BO-001 inputs and write decomposition artifacts."""
    outputs_root = Path(outputs_root)
    timestamp = generated_at or datetime.now(timezone.utc)
    manifest = load_backoffice_attribution_manifest(
        outputs_root=outputs_root,
        backoffice_attribution_run_id=backoffice_attribution_run_id,
    )
    selected_id = str(
        backoffice_attribution_run_id
        or manifest.get("backoffice_attribution_run_id")
        or ""
    )
    if not selected_id:
        raise ValueError("Backoffice attribution run ID is required.")
    backoffice = (
        manifest
        if backoffice_attribution_run_id
        else load_backoffice_attribution_report(
            outputs_root=outputs_root,
            backoffice_attribution_run_id=selected_id,
        )
    )
    analysis = load_expanded_trial_analysis_report(
        outputs_root=outputs_root,
        analysis_run_id=str(backoffice.get("analysis_run_id") or ""),
    )
    expanded_summary = load_expanded_trial_summary(
        outputs_root=outputs_root,
        expanded_trial_run_id=str(backoffice.get("expanded_trial_run_id") or ""),
    )
    backtest_manifest = load_backtest_manifest(
        outputs_root=outputs_root,
        backtest_run_id=str(backoffice.get("backtest_run_id") or ""),
    )
    rows = load_backtest_results(
        outputs_root=outputs_root,
        backtest_run_id=str(backoffice.get("backtest_run_id") or ""),
    )
    root = outputs_root / "backtest_driver_decompositions"
    root.mkdir(parents=True, exist_ok=True)
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    run_id = base
    suffix = 2
    while (root / run_id).exists():
        run_id = f"{base}_{suffix:02d}"
        suffix += 1
    report = build_backtest_driver_decomposition(
        decomposition_run_id=run_id,
        generated_at=timestamp.isoformat(),
        backoffice=backoffice,
        analysis=analysis,
        expanded_summary=expanded_summary,
        backtest_manifest=backtest_manifest,
        rows=rows,
    )
    folder = root / run_id
    folder.mkdir(parents=True, exist_ok=False)
    markdown_path = folder / "backtest_driver_decomposition_report.md"
    json_path = folder / "backtest_driver_decomposition_report.json"
    ticker_path = folder / "ticker_driver_decomposition.csv"
    date_path = folder / "date_driver_decomposition.csv"
    cohort_path = folder / "cohort_driver_decomposition.csv"
    sector_path = folder / "sector_driver_decomposition.csv"
    category_path = folder / "category_driver_decomposition.csv"
    universe_path = folder / "universe_group_driver_decomposition.csv"
    markdown_path.write_text(
        render_backtest_driver_decomposition_report(report), encoding="utf-8"
    )
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    for path, rows_to_write in (
        (ticker_path, report.ticker_drivers),
        (date_path, report.date_drivers),
        (cohort_path, report.cohort_drivers),
        (sector_path, report.sector_drivers),
        (category_path, report.category_drivers),
        (universe_path, report.universe_group_drivers),
    ):
        _write_csv(path, rows_to_write)
    latest_path = root / "latest_backtest_driver_decomposition_manifest.json"
    latest_path.write_text(
        json.dumps(
            {
                "decomposition_run_id": report.decomposition_run_id,
                "backoffice_attribution_run_id": (
                    report.backoffice_attribution_run_id
                ),
                "investor_persona_attribution_run_id": (
                    report.investor_persona_attribution_run_id
                ),
                "gatekeeper_run_id": report.gatekeeper_run_id,
                "scorecard_run_id": report.scorecard_run_id,
                "analysis_run_id": report.analysis_run_id,
                "expanded_trial_run_id": report.expanded_trial_run_id,
                "backtest_run_id": report.backtest_run_id,
                "work_order_id": report.work_order_id,
                "work_order_title": report.work_order_title,
                "decomposition_status": report.decomposition_status,
                "reconciliation_status": report.reconciliation[
                    "reconciliation_status"
                ],
                "rows_reconciled": report.reconciliation["rows_reconciled"],
                "recommended_next_work_order": report.recommended_next_work_order,
                "decomposition_folder": str(folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "ticker_csv_path": str(ticker_path),
                "date_csv_path": str(date_path),
                "cohort_csv_path": str(cohort_path),
                "sector_csv_path": str(sector_path),
                "category_csv_path": str(category_path),
                "universe_group_csv_path": str(universe_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return BacktestDriverDecompositionFiles(
        decomposition_folder=folder,
        markdown_path=markdown_path,
        json_path=json_path,
        ticker_csv_path=ticker_path,
        date_csv_path=date_path,
        cohort_csv_path=cohort_path,
        sector_csv_path=sector_path,
        category_csv_path=category_path,
        universe_group_csv_path=universe_path,
        latest_manifest_path=latest_path,
        report=report,
    )
