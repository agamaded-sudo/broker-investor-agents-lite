"""BO-005 metadata diversity recheck for held research evidence."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean, median

SAFETY_NOTICE = (
    "This report analyzes metadata diversity and research repair only. It does "
    "not create an investment decision, recommendation, ranking, allocation "
    "instruction, rebalancing instruction, trade signal, execution "
    "instruction, strategy validation, or investment advice."
)
WORK_ORDER_ID = "BO-005"
WORK_ORDER_TITLE = "Metadata Diversity Recheck"
NEXT_WORK_ORDER = "BO-006 Persona-Specific Evidence Pack Requirements"
UNKNOWN = "unknown"
INTEREST_FIELDS = (
    "buffett_interest_level",
    "munger_interest_level",
    "fisher_interest_level",
    "lynch_interest_level",
    "bogle_interest_level",
)


@dataclass(frozen=True)
class MetadataDiversityRecheckReport:
    """Structured BO-005 metadata diversity report."""

    metadata_diversity_recheck_run_id: str
    generated_at: str
    delayed_anchor_repair_run_id: str
    walk_forward_repair_run_id: str
    outlier_repair_run_id: str
    decomposition_run_id: str
    backoffice_attribution_run_id: str
    investor_persona_attribution_run_id: str
    gatekeeper_run_id: str
    scorecard_run_id: str
    analysis_run_id: str
    expanded_trial_run_id: str
    backtest_run_id: str
    work_order_id: str
    work_order_title: str
    metadata_diversity_recheck_status: str
    metadata_matrix_summary: dict
    sector_diversity_analysis: list[dict]
    category_diversity_analysis: list[dict]
    universe_group_diversity_analysis: list[dict]
    cohort_diversity_analysis: list[dict]
    investor_interest_diversity_analysis: list[dict]
    concentration_classification: dict
    metadata_retest_controls: dict
    recommended_next_work_order: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class MetadataDiversityRecheckFiles:
    """Generated BO-005 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    metadata_matrix_csv_path: Path
    sector_csv_path: Path
    category_csv_path: Path
    universe_group_csv_path: Path
    cohort_csv_path: Path
    investor_interest_csv_path: Path
    retest_controls_path: Path
    latest_manifest_path: Path
    report: MetadataDiversityRecheckReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_delayed_anchor_repair_manifest(
    *,
    outputs_root: Path,
    delayed_anchor_repair_run_id: str | None = None,
) -> dict:
    """Load one BO-004 report or the latest BO-004 manifest."""
    root = Path(outputs_root) / "delayed_anchor_repairs"
    path = (
        root
        / str(delayed_anchor_repair_run_id)
        / "delayed_anchor_repair_report.json"
        if delayed_anchor_repair_run_id
        else root / "latest_delayed_anchor_repair_manifest.json"
    )
    payload = _load_required_json(path, "Delayed anchor repair manifest")
    payload["_manifest_path"] = str(path)
    return payload


def load_delayed_anchor_repair_report(
    *, outputs_root: Path, delayed_anchor_repair_run_id: str
) -> dict:
    """Load a complete BO-004 delayed anchor repair report."""
    path = (
        Path(outputs_root)
        / "delayed_anchor_repairs"
        / str(delayed_anchor_repair_run_id)
        / "delayed_anchor_repair_report.json"
    )
    return _load_required_json(path, "Delayed anchor repair report")


def load_walk_forward_repair_report(
    *, outputs_root: Path, walk_forward_repair_run_id: str
) -> dict:
    """Load linked BO-003 walk-forward repair context if available."""
    return _load_optional_json(
        Path(outputs_root)
        / "walk_forward_repair_plans"
        / str(walk_forward_repair_run_id)
        / "walk_forward_repair_plan_report.json"
    )


def load_outlier_repair_report(
    *, outputs_root: Path, outlier_repair_run_id: str
) -> dict:
    """Load linked BO-002 outlier repair context if available."""
    return _load_optional_json(
        Path(outputs_root)
        / "outlier_repair_paths"
        / str(outlier_repair_run_id)
        / "outlier_repair_path_report.json"
    )


def load_backtest_driver_decomposition_report(
    *, outputs_root: Path, decomposition_run_id: str
) -> dict:
    """Load linked BO-001 decomposition context if available."""
    return _load_optional_json(
        Path(outputs_root)
        / "backtest_driver_decompositions"
        / str(decomposition_run_id)
        / "backtest_driver_decomposition_report.json"
    )


def load_expanded_trial_analysis_report(
    *, outputs_root: Path, analysis_run_id: str
) -> dict:
    """Load linked expanded trial analysis context if available."""
    return _load_optional_json(
        Path(outputs_root)
        / "expanded_trial_analyses"
        / str(analysis_run_id)
        / "expanded_trial_analysis_report.json"
    )


def load_backtest_results(
    *, outputs_root: Path, backtest_run_id: str
) -> list[dict]:
    """Load linked expanded backtest rows."""
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


def _round(value: float | None) -> float | None:
    return None if value is None else round(value, 6)


def _clean_text(value: object) -> str:
    text = str(value or "").strip()
    return text if text else UNKNOWN


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
        item["sector"] = _clean_text(row.get("sector") or ticker_meta.get("sector"))
        item["category"] = _clean_text(
            row.get("category") or ticker_meta.get("category")
        )
        item["universe_group"] = _clean_text(
            row.get("universe_group") or ticker_meta.get("universe_group")
        )
        item["cohort"] = (
            "current_core"
            if item["universe_group"] == "current_core"
            else "expanded_cohort"
        )
        item["anchor_bucket"] = (
            "delayed_anchor"
            if str(row.get("has_delayed_price_anchor", "")).lower() == "true"
            else "clean_anchor"
            if str(row.get("has_delayed_price_anchor", "")).lower() == "false"
            else UNKNOWN
        )
        enriched.append(item)
    return enriched


def _metric_summary(rows: list[dict]) -> dict:
    relative = [
        value
        for value in (_as_float(row, "relative_return_12m") for row in rows)
        if value is not None
    ]
    hit_rate = None
    if relative:
        hit_rate = sum(value > 0 for value in relative) / len(relative)
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
        "clean_anchor_records": sum(
            row.get("anchor_bucket") == "clean_anchor" for row in rows
        ),
        "delayed_anchor_records": sum(
            row.get("anchor_bucket") == "delayed_anchor" for row in rows
        ),
        "median_relative_return_12m": _round(median(relative) if relative else None),
        "hit_rate_vs_benchmark_12m": _round(hit_rate),
    }


def _driver_label(summary: dict) -> str:
    relative = summary.get("median_relative_return_12m")
    hit_rate = summary.get("hit_rate_vs_benchmark_12m")
    if relative is None or hit_rate is None:
        return "insufficient_evidence"
    if relative > 0 and hit_rate >= 0.5:
        return "positive_driver"
    if relative < 0 and hit_rate < 0.5:
        return "negative_driver"
    return "mixed_driver"


def _interest_label(rows: list[dict]) -> str:
    labels = []
    for field in INTEREST_FIELDS:
        values = sorted({_clean_text(row.get(field)) for row in rows})
        if values and values != [UNKNOWN]:
            labels.append(f"{field}:{'/'.join(values)}")
    return " | ".join(labels) if labels else UNKNOWN


def _group(rows: list[dict], key: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(str(row.get(key) or UNKNOWN), []).append(row)
    return grouped


def build_metadata_matrix(rows: list[dict], analysis: dict) -> list[dict]:
    """Build one metadata matrix row per ticker."""
    enriched = _enrich_rows(rows, analysis)
    matrix = []
    for ticker, ticker_rows in sorted(_group(enriched, "ticker").items()):
        summary = _metric_summary(ticker_rows)
        first = ticker_rows[0]
        concentration_flags = []
        if first["sector"] == UNKNOWN:
            concentration_flags.append("sector_unknown")
        if first["category"] == UNKNOWN:
            concentration_flags.append("category_unknown")
        if first["universe_group"] == UNKNOWN:
            concentration_flags.append("universe_group_unknown")
        matrix.append(
            {
                "ticker": ticker,
                "cohort": first["cohort"],
                "universe_group": first["universe_group"],
                "sector": first["sector"],
                "category": first["category"],
                **summary,
                "driver_label": _driver_label(summary),
                "metadata_concentration_flags": (
                    ";".join(concentration_flags) if concentration_flags else "none"
                ),
                "investor_interest_label": _interest_label(ticker_rows),
                "source_verification_status": _clean_text(
                    first.get("source_verification_status")
                ),
                "promotion_blocking_bucket": _clean_text(
                    first.get("promotion_blocking_bucket")
                ),
            }
        )
    return matrix


def _concentration_label(share: float) -> str:
    if share >= 0.5:
        return "materially_concentrated"
    if share >= 0.34:
        return "partially_concentrated"
    return "diversified_enough_for_current_stage"


def _dimension_analysis(matrix: list[dict], key: str) -> list[dict]:
    total_tickers = len({row["ticker"] for row in matrix})
    total_records = sum(int(row["records"]) for row in matrix)
    output = []
    for name, rows_for_group in sorted(_group(matrix, key).items()):
        ticker_count = len({row["ticker"] for row in rows_for_group})
        record_count = sum(int(row["records"]) for row in rows_for_group)
        relative_values = [
            row["median_relative_return_12m"]
            for row in rows_for_group
            if row["median_relative_return_12m"] is not None
        ]
        hit_values = [
            row["hit_rate_vs_benchmark_12m"]
            for row in rows_for_group
            if row["hit_rate_vs_benchmark_12m"] is not None
        ]
        share_tickers = ticker_count / total_tickers if total_tickers else 0
        share_records = record_count / total_records if total_records else 0
        label = _concentration_label(max(share_tickers, share_records))
        output.append(
            {
                key: name,
                "ticker_count": ticker_count,
                "record_count": record_count,
                "share_of_tickers": _round(share_tickers),
                "share_of_records": _round(share_records),
                "median_relative_return_12m": _round(
                    median(relative_values) if relative_values else None
                ),
                "hit_rate_vs_benchmark_12m": _round(
                    mean(hit_values) if hit_values else None
                ),
                "concentration_label": label,
                "interpretation": (
                    f"{key} {name} is {label.replace('_', ' ')}."
                ),
            }
        )
    return output


def analyze_sector_diversity(matrix: list[dict]) -> list[dict]:
    """Analyze sector concentration."""
    return _dimension_analysis(matrix, "sector")


def analyze_category_diversity(matrix: list[dict]) -> list[dict]:
    """Analyze category concentration."""
    return _dimension_analysis(matrix, "category")


def analyze_universe_group_diversity(matrix: list[dict]) -> list[dict]:
    """Analyze universe-group concentration."""
    return _dimension_analysis(matrix, "universe_group")


def analyze_cohort_diversity(matrix: list[dict]) -> list[dict]:
    """Analyze cohort concentration."""
    return _dimension_analysis(matrix, "cohort")


def analyze_investor_interest_diversity(matrix: list[dict]) -> list[dict]:
    """Analyze investor-interest label diversity when available."""
    if not matrix or {row["investor_interest_label"] for row in matrix} == {UNKNOWN}:
        return [
            {
                "investor_interest_label": "investor_interest_diversity_limited",
                "ticker_count": len(matrix),
                "record_count": sum(int(row["records"]) for row in matrix),
                "share_of_tickers": 1.0 if matrix else 0.0,
                "share_of_records": 1.0 if matrix else 0.0,
                "interpretation": "Investor-interest diversity is limited or unavailable.",
            }
        ]
    return _dimension_analysis(matrix, "investor_interest_label")


def _source_verification_status(matrix: list[dict]) -> str:
    values = {row["source_verification_status"] for row in matrix}
    if not values or values == {UNKNOWN}:
        return "insufficient_metadata_detail"
    if len(values) == 1:
        return "partially_concentrated"
    return "diversified_enough_for_current_stage"


def _worst_concentration_status(rows: list[dict]) -> str:
    labels = {row.get("concentration_label") for row in rows}
    if "materially_concentrated" in labels:
        return "materially_concentrated"
    if "partially_concentrated" in labels:
        return "partially_concentrated"
    if "diversified_enough_for_current_stage" in labels:
        return "diversified_enough_for_current_stage"
    return "insufficient_metadata_detail"


def classify_metadata_concentration(
    *,
    matrix: list[dict],
    sector: list[dict],
    category: list[dict],
    universe_group: list[dict],
    cohort: list[dict],
    investor_interest: list[dict],
) -> dict:
    """Classify metadata concentration across dimensions."""
    sector_status = _worst_concentration_status(sector)
    category_status = _worst_concentration_status(category)
    universe_status = _worst_concentration_status(universe_group)
    cohort_status = _worst_concentration_status(cohort)
    interest_status = (
        "investor_interest_diversity_limited"
        if investor_interest
        and investor_interest[0].get("investor_interest_label")
        == "investor_interest_diversity_limited"
        else _worst_concentration_status(investor_interest)
    )
    statuses = {
        sector_status,
        category_status,
        universe_status,
        cohort_status,
    }
    if "materially_concentrated" in statuses:
        overall = "materially_concentrated"
    elif "partially_concentrated" in statuses:
        overall = "partially_concentrated"
    else:
        overall = "diversified_enough_for_current_stage"
    effect = (
        "metadata_concentration_supports_continued_hold"
        if overall in {"materially_concentrated", "partially_concentrated"}
        else "metadata_concentration_not_primary_hold_driver"
    )
    return {
        "metadata_diversity_status": overall,
        "sector_concentration_status": sector_status,
        "category_concentration_status": category_status,
        "universe_group_concentration_status": universe_status,
        "cohort_concentration_status": cohort_status,
        "investor_interest_diversity_status": interest_status,
        "source_verification_diversity_status": _source_verification_status(matrix),
        "metadata_effect_on_hold_status": effect,
        "main_metadata_finding": (
            "Expanded evidence remains metadata-concentrated enough to limit "
            "generalization; current-core and expanded-cohort views must stay "
            "separate before any future gatekeeper rerun."
        ),
        "recommended_next_work_order": NEXT_WORK_ORDER,
    }


def build_metadata_retest_controls() -> dict:
    """Create BO-005 metadata retest controls."""
    return {
        "retest_control_id": "BO-005-metadata-retest-controls",
        "purpose": (
            "Define metadata controls required before future research gatekeeping."
        ),
        "required_metadata_controls": [
            "Report current_core and expanded_cohort separately.",
            "Report sector and category exposure separately.",
            "Report universe_group exposure separately.",
            "Report metadata concentration flags.",
            "Do not generalize from concentrated metadata groups.",
            "Gatekeeper must be rerun after repair before progression.",
        ],
        "required_reporting_views": [
            "sector_diversity",
            "category_diversity",
            "universe_group_diversity",
            "cohort_diversity",
            "investor_interest_diversity",
        ],
        "minimum_metadata_requirements": [
            "Ticker, sector, category, universe_group, and cohort must be explicit or unknown.",
            "Unavailable metadata must not be fabricated.",
        ],
        "diversity_threshold_notes": [
            "Groups at or above 50 percent share are materially concentrated.",
            "Groups at or above 34 percent share are partially concentrated.",
        ],
        "next_gatekeeping_requirements": [
            "Gatekeeper must be rerun after repair before progression.",
            "Progression remains blocked while gatekeeper decision is hold.",
        ],
        "safety_constraints": [
            "Do not rerun investor agents for this recheck.",
            "Do not create recommendations, rankings, allocations, or trade signals.",
        ],
    }


def _matrix_summary(matrix: list[dict]) -> dict:
    unavailable = []
    for field in ("sector", "category", "universe_group", "cohort"):
        if any(row[field] == UNKNOWN for row in matrix):
            unavailable.append(field)
    return {
        "ticker_count": len({row["ticker"] for row in matrix}),
        "record_count": sum(int(row["records"]) for row in matrix),
        "sector_count": len({row["sector"] for row in matrix}),
        "category_count": len({row["category"] for row in matrix}),
        "universe_group_count": len({row["universe_group"] for row in matrix}),
        "cohort_count": len({row["cohort"] for row in matrix}),
        "unavailable_metadata_fields": unavailable,
    }


def build_metadata_diversity_recheck(
    *,
    metadata_diversity_recheck_run_id: str,
    generated_at: str,
    delayed_anchor: dict,
    walk_forward: dict,
    outlier: dict,
    decomposition: dict,
    analysis: dict,
    rows: list[dict],
) -> MetadataDiversityRecheckReport:
    """Build the full BO-005 metadata diversity recheck."""
    matrix = build_metadata_matrix(rows, analysis)
    sector = analyze_sector_diversity(matrix)
    category = analyze_category_diversity(matrix)
    universe = analyze_universe_group_diversity(matrix)
    cohort = analyze_cohort_diversity(matrix)
    investor_interest = analyze_investor_interest_diversity(matrix)
    classification = classify_metadata_concentration(
        matrix=matrix,
        sector=sector,
        category=category,
        universe_group=universe,
        cohort=cohort,
        investor_interest=investor_interest,
    )
    return MetadataDiversityRecheckReport(
        metadata_diversity_recheck_run_id=metadata_diversity_recheck_run_id,
        generated_at=generated_at,
        delayed_anchor_repair_run_id=str(
            delayed_anchor.get("delayed_anchor_repair_run_id") or ""
        ),
        walk_forward_repair_run_id=str(
            delayed_anchor.get("walk_forward_repair_run_id") or ""
        ),
        outlier_repair_run_id=str(delayed_anchor.get("outlier_repair_run_id") or ""),
        decomposition_run_id=str(delayed_anchor.get("decomposition_run_id") or ""),
        backoffice_attribution_run_id=str(
            delayed_anchor.get("backoffice_attribution_run_id") or ""
        ),
        investor_persona_attribution_run_id=str(
            delayed_anchor.get("investor_persona_attribution_run_id") or ""
        ),
        gatekeeper_run_id=str(delayed_anchor.get("gatekeeper_run_id") or ""),
        scorecard_run_id=str(delayed_anchor.get("scorecard_run_id") or ""),
        analysis_run_id=str(delayed_anchor.get("analysis_run_id") or ""),
        expanded_trial_run_id=str(delayed_anchor.get("expanded_trial_run_id") or ""),
        backtest_run_id=str(delayed_anchor.get("backtest_run_id") or ""),
        work_order_id=WORK_ORDER_ID,
        work_order_title=WORK_ORDER_TITLE,
        metadata_diversity_recheck_status="completed",
        metadata_matrix_summary=_matrix_summary(matrix),
        sector_diversity_analysis=sector,
        category_diversity_analysis=category,
        universe_group_diversity_analysis=universe,
        cohort_diversity_analysis=cohort,
        investor_interest_diversity_analysis=investor_interest,
        concentration_classification=classification,
        metadata_retest_controls=build_metadata_retest_controls(),
        recommended_next_work_order=NEXT_WORK_ORDER,
    )


def _display(value) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "None"
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return "" if value is None else str(value)


def _table_cell(value) -> str:
    return _display(value).replace("|", "\\|")


def _render_diversity_table(lines: list[str], title: str, key: str, rows: list[dict]) -> None:
    lines.extend(
        [
            "",
            f"## {title}",
            "",
            (
                f"| {key.replace('_', ' ').title()} | Tickers | Records | "
                "Share of Records | Median Relative 12M | Hit Rate | Concentration |"
            ),
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for item in rows:
        lines.append(
            f"| {_table_cell(item[key])} | {item['ticker_count']} | "
            f"{item['record_count']} | "
            f"{item['share_of_records']} | {item.get('median_relative_return_12m')} | "
            f"{item.get('hit_rate_vs_benchmark_12m')} | "
            f"{item.get('concentration_label', 'limited')} |"
        )


def render_metadata_diversity_recheck_report(
    report: MetadataDiversityRecheckReport,
) -> str:
    """Render BO-005 as Markdown."""
    data = report.to_dict()
    summary = data["metadata_matrix_summary"]
    classification = data["concentration_classification"]
    lines = [
        "# Metadata Diversity Recheck Report",
        "",
        "## Executive Summary",
        "",
        (
            "- Metadata Diversity Recheck Run ID: "
            f"{data['metadata_diversity_recheck_run_id']}"
        ),
        f"- Delayed Anchor Repair Run ID: {data['delayed_anchor_repair_run_id']}",
        f"- Work Order ID: {data['work_order_id']}",
        f"- Backtest Run ID: {data['backtest_run_id']}",
        f"- Main Metadata Finding: {classification['main_metadata_finding']}",
        f"- Metadata Diversity Status: {classification['metadata_diversity_status']}",
        f"- Recommended Next Work Order: {data['recommended_next_work_order']}",
        "",
        "## Important Boundary",
        "",
        (
            "This report analyzes metadata diversity and research repair only. "
            "It does not create an investment decision, ranking, recommendation, "
            "allocation, rebalancing instruction, trade signal, or execution "
            "instruction."
        ),
        "",
        "## Source Context",
        "",
        "- Gatekeeper Decision: hold",
        "- Progression Allowed: false",
        f"- Current Work Order: {data['work_order_id']}",
        "- Reason: metadata diversity partial concentration.",
        "",
        "## Metadata Matrix Summary",
        "",
        f"- Ticker Count: {summary['ticker_count']}",
        f"- Record Count: {summary['record_count']}",
        f"- Sector Count: {summary['sector_count']}",
        f"- Category Count: {summary['category_count']}",
        f"- Universe Group Count: {summary['universe_group_count']}",
        f"- Cohort Count: {summary['cohort_count']}",
        (
            "- Unavailable Metadata Fields: "
            f"{_display(summary['unavailable_metadata_fields'])}"
        ),
    ]
    _render_diversity_table(
        lines, "Sector Diversity", "sector", data["sector_diversity_analysis"]
    )
    _render_diversity_table(
        lines, "Category Diversity", "category", data["category_diversity_analysis"]
    )
    _render_diversity_table(
        lines,
        "Universe Group Diversity",
        "universe_group",
        data["universe_group_diversity_analysis"],
    )
    _render_diversity_table(
        lines, "Cohort Diversity", "cohort", data["cohort_diversity_analysis"]
    )
    _render_diversity_table(
        lines,
        "Investor Interest Diversity",
        "investor_interest_label",
        data["investor_interest_diversity_analysis"],
    )
    lines.extend(
        [
            "",
            "## Concentration Classification",
            "",
            f"- Sector: {classification['sector_concentration_status']}",
            f"- Category: {classification['category_concentration_status']}",
            (
                "- Universe Group: "
                f"{classification['universe_group_concentration_status']}"
            ),
            f"- Cohort: {classification['cohort_concentration_status']}",
            (
                "- Investor Interest: "
                f"{classification['investor_interest_diversity_status']}"
            ),
            (
                "- Metadata Effect on Hold: "
                f"{classification['metadata_effect_on_hold_status']}"
            ),
            "",
            "## Retest Controls",
            "",
            (
                "- Required Metadata Controls: "
                f"{_display(data['metadata_retest_controls']['required_metadata_controls'])}"
            ),
            (
                "- Required Reporting Views: "
                f"{_display(data['metadata_retest_controls']['required_reporting_views'])}"
            ),
            "",
            "## What This Suggests",
            "",
            (
                "- Evidence remains held if metadata concentration limits "
                "generalization."
            ),
            (
                "- Backoffice should proceed to persona-specific evidence pack "
                "requirements next."
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


def write_metadata_diversity_recheck_report(
    *,
    outputs_root: Path,
    delayed_anchor_repair_run_id: str | None = None,
    generated_at: datetime | None = None,
) -> MetadataDiversityRecheckFiles:
    """Load BO-005 inputs and write metadata diversity recheck artifacts."""
    outputs_root = Path(outputs_root)
    timestamp = generated_at or datetime.now(timezone.utc)
    manifest = load_delayed_anchor_repair_manifest(
        outputs_root=outputs_root,
        delayed_anchor_repair_run_id=delayed_anchor_repair_run_id,
    )
    selected_id = str(
        delayed_anchor_repair_run_id
        or manifest.get("delayed_anchor_repair_run_id")
        or ""
    )
    if not selected_id:
        raise ValueError("Delayed anchor repair run ID is required.")
    delayed_anchor = (
        manifest
        if delayed_anchor_repair_run_id
        else load_delayed_anchor_repair_report(
            outputs_root=outputs_root,
            delayed_anchor_repair_run_id=selected_id,
        )
    )
    walk_forward = load_walk_forward_repair_report(
        outputs_root=outputs_root,
        walk_forward_repair_run_id=str(
            delayed_anchor.get("walk_forward_repair_run_id") or ""
        ),
    )
    outlier = load_outlier_repair_report(
        outputs_root=outputs_root,
        outlier_repair_run_id=str(delayed_anchor.get("outlier_repair_run_id") or ""),
    )
    decomposition = load_backtest_driver_decomposition_report(
        outputs_root=outputs_root,
        decomposition_run_id=str(delayed_anchor.get("decomposition_run_id") or ""),
    )
    analysis = load_expanded_trial_analysis_report(
        outputs_root=outputs_root,
        analysis_run_id=str(delayed_anchor.get("analysis_run_id") or ""),
    )
    rows = load_backtest_results(
        outputs_root=outputs_root,
        backtest_run_id=str(delayed_anchor.get("backtest_run_id") or ""),
    )
    root = outputs_root / "metadata_diversity_rechecks"
    root.mkdir(parents=True, exist_ok=True)
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    run_id = base
    suffix = 2
    while (root / run_id).exists():
        run_id = f"{base}_{suffix:02d}"
        suffix += 1
    report = build_metadata_diversity_recheck(
        metadata_diversity_recheck_run_id=run_id,
        generated_at=timestamp.isoformat(),
        delayed_anchor=delayed_anchor,
        walk_forward=walk_forward,
        outlier=outlier,
        decomposition=decomposition,
        analysis=analysis,
        rows=rows,
    )
    matrix = build_metadata_matrix(rows, analysis)
    folder = root / run_id
    folder.mkdir(parents=True, exist_ok=False)
    markdown_path = folder / "metadata_diversity_recheck_report.md"
    json_path = folder / "metadata_diversity_recheck_report.json"
    matrix_path = folder / "metadata_matrix.csv"
    sector_path = folder / "sector_diversity_analysis.csv"
    category_path = folder / "category_diversity_analysis.csv"
    universe_path = folder / "universe_group_diversity_analysis.csv"
    cohort_path = folder / "cohort_diversity_analysis.csv"
    investor_path = folder / "investor_interest_diversity_analysis.csv"
    controls_path = folder / "metadata_retest_controls.json"
    markdown_path.write_text(
        render_metadata_diversity_recheck_report(report), encoding="utf-8"
    )
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(matrix_path, matrix)
    _write_csv(sector_path, report.sector_diversity_analysis)
    _write_csv(category_path, report.category_diversity_analysis)
    _write_csv(universe_path, report.universe_group_diversity_analysis)
    _write_csv(cohort_path, report.cohort_diversity_analysis)
    _write_csv(investor_path, report.investor_interest_diversity_analysis)
    controls_path.write_text(
        json.dumps(report.metadata_retest_controls, indent=2),
        encoding="utf-8",
    )
    latest_path = root / "latest_metadata_diversity_recheck_manifest.json"
    latest_payload = {
        "metadata_diversity_recheck_run_id": (
            report.metadata_diversity_recheck_run_id
        ),
        "delayed_anchor_repair_run_id": report.delayed_anchor_repair_run_id,
        "walk_forward_repair_run_id": report.walk_forward_repair_run_id,
        "outlier_repair_run_id": report.outlier_repair_run_id,
        "decomposition_run_id": report.decomposition_run_id,
        "backoffice_attribution_run_id": report.backoffice_attribution_run_id,
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
        "metadata_diversity_recheck_status": (
            report.metadata_diversity_recheck_status
        ),
        "metadata_diversity_status": report.concentration_classification[
            "metadata_diversity_status"
        ],
        "recommended_next_work_order": report.recommended_next_work_order,
        "output_folder": str(folder),
        "report_path": str(markdown_path),
        "report_json_path": str(json_path),
        "metadata_matrix_csv_path": str(matrix_path),
        "sector_csv_path": str(sector_path),
        "category_csv_path": str(category_path),
        "universe_group_csv_path": str(universe_path),
        "cohort_csv_path": str(cohort_path),
        "investor_interest_csv_path": str(investor_path),
        "retest_controls_path": str(controls_path),
        "safety_notice": report.safety_notice,
    }
    latest_path.write_text(json.dumps(latest_payload, indent=2), encoding="utf-8")
    return MetadataDiversityRecheckFiles(
        output_folder=folder,
        markdown_path=markdown_path,
        json_path=json_path,
        metadata_matrix_csv_path=matrix_path,
        sector_csv_path=sector_path,
        category_csv_path=category_path,
        universe_group_csv_path=universe_path,
        cohort_csv_path=cohort_path,
        investor_interest_csv_path=investor_path,
        retest_controls_path=controls_path,
        latest_manifest_path=latest_path,
        report=report,
    )
