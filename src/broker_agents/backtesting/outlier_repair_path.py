"""BO-002 outlier and Ex-NVDA repair path for held research evidence."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean, median

SAFETY_NOTICE = (
    "This report decomposes and controls research evidence only. It does not "
    "create an investment decision, recommendation, ranking, allocation "
    "instruction, rebalancing instruction, trade signal, execution "
    "instruction, strategy validation, or investment advice."
)
WORK_ORDER_ID = "BO-002"
WORK_ORDER_TITLE = "Outlier and Ex-NVDA Repair Path"
NEXT_WORK_ORDER = "BO-003 Walk-Forward Stability Repair Plan"
SUPPORTIVE_DATE = "2021-06-30"


@dataclass(frozen=True)
class OutlierRepairPathReport:
    """Structured BO-002 repair path result."""

    outlier_repair_run_id: str
    generated_at: str
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
    outlier_repair_status: str
    scenario_analysis: list[dict]
    contributor_attribution: dict
    dependence_classification: dict
    retest_spec: dict
    recommended_next_work_order: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class OutlierRepairPathFiles:
    """Generated repair-path files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    scenario_csv_path: Path
    contributor_csv_path: Path
    retest_spec_path: Path
    latest_manifest_path: Path
    report: OutlierRepairPathReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_backtest_driver_decomposition_manifest(
    *,
    outputs_root: Path,
    decomposition_run_id: str | None = None,
) -> dict:
    """Load one BO-001 report or the latest BO-001 manifest."""
    root = Path(outputs_root) / "backtest_driver_decompositions"
    path = (
        root / str(decomposition_run_id) / "backtest_driver_decomposition_report.json"
        if decomposition_run_id
        else root / "latest_backtest_driver_decomposition_manifest.json"
    )
    payload = _load_required_json(path, "Backtest driver decomposition manifest")
    payload["_manifest_path"] = str(path)
    return payload


def load_backtest_driver_decomposition_report(
    *, outputs_root: Path, decomposition_run_id: str
) -> dict:
    """Load a complete BO-001 decomposition report."""
    path = (
        Path(outputs_root)
        / "backtest_driver_decompositions"
        / str(decomposition_run_id)
        / "backtest_driver_decomposition_report.json"
    )
    return _load_required_json(path, "Backtest driver decomposition report")


def load_backoffice_attribution_report(
    *, outputs_root: Path, backoffice_attribution_run_id: str
) -> dict:
    """Load linked Backoffice attribution context if available."""
    return _load_optional_json(
        Path(outputs_root)
        / "backoffice_evidence_quality_attributions"
        / str(backoffice_attribution_run_id)
        / "backoffice_evidence_quality_attribution_report.json"
    )


def load_research_scorecard_report(
    *, outputs_root: Path, scorecard_run_id: str
) -> dict:
    """Load linked research scorecard context if available."""
    return _load_optional_json(
        Path(outputs_root)
        / "research_evidence_scorecards"
        / str(scorecard_run_id)
        / "research_evidence_scorecard_report.json"
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
        "median_forward_return_12m": _round(median(forward) if forward else None),
        "median_relative_return_12m": _round(median(relative) if relative else None),
        "average_relative_return_12m": _round(mean(relative) if relative else None),
        "hit_rate_vs_benchmark_12m": _round(hit_rate),
        "worst_max_drawdown_12m": _round(min(drawdown) if drawdown else None),
    }


def _relative_positive(summary: dict) -> bool:
    value = summary.get("median_relative_return_12m")
    return bool(value is not None and value > 0)


def _hit_rate_passes(summary: dict) -> bool:
    value = summary.get("hit_rate_vs_benchmark_12m")
    return bool(value is not None and value >= 0.5)


def _scenario_result_label(summary: dict, baseline: dict) -> str:
    records = int(summary.get("records") or 0)
    relative = summary.get("median_relative_return_12m")
    baseline_relative = baseline.get("median_relative_return_12m")
    if records == 0:
        return "not_applicable"
    if records < 5:
        return "insufficient_records"
    if _relative_positive(summary) and _hit_rate_passes(summary):
        return "survives_outlier_control"
    if (
        relative is not None
        and baseline_relative is not None
        and relative > baseline_relative
    ):
        return "improves_but_not_enough"
    return "fails_outlier_control"


def _interpret_scenario(code: str, label: str) -> str:
    if code == "ex_nvda":
        return "Ex-NVDA evidence is reported separately to test ticker dependence."
    if code.startswith("ex_top"):
        return "Excluding leading positive contributors tests contributor dependence."
    if code == "current_core_only":
        return "Current-core evidence is isolated from the expanded cohort."
    if code == "expanded_cohort_only":
        return "Expanded-cohort evidence is isolated from current-core records."
    if code == "ex_supportive_date_2021_06_30":
        return "Supportive-date exclusion tests whether one period carries evidence."
    if code == "negative_dates_only":
        return "Negative dates are isolated to document period sensitivity."
    if code == "ex_severe_negative_ticker_nflx":
        return "NFLX exclusion tests whether severe negative drag explains weakness."
    if code == "ex_expanded_negative_tickers":
        return "Expanded negative tickers are excluded to test composition effects."
    if label == "survives_outlier_control":
        return "This scenario remains positive after the control."
    if label == "improves_but_not_enough":
        return "This scenario improves but remains below research-control thresholds."
    if label == "insufficient_records":
        return "This scenario has too few records for stable interpretation."
    if label == "not_applicable":
        return "This scenario has no available records."
    return "This scenario does not survive the outlier control."


def _top_positive_tickers(rows: list[dict], count: int) -> list[str]:
    summaries = []
    for ticker, ticker_rows in _group(rows, "ticker").items():
        summary = _metric_summary(ticker_rows)
        value = summary.get("average_relative_return_12m")
        summaries.append((ticker, value if value is not None else -999.0))
    return [ticker for ticker, _value in sorted(summaries, key=lambda item: item[1], reverse=True)[:count]]


def _group(rows: list[dict], key: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(str(row.get(key) or "Missing"), []).append(row)
    return grouped


def _scenario(
    *,
    code: str,
    label: str,
    rows: list[dict],
    baseline: dict,
    excluded_tickers: list[str] | None = None,
    excluded_dates: list[str] | None = None,
) -> dict:
    excluded_tickers = excluded_tickers or []
    excluded_dates = excluded_dates or []
    included = [
        row
        for row in rows
        if str(row.get("ticker")) not in excluded_tickers
        and str(row.get("signal_date")) not in excluded_dates
    ]
    summary = _metric_summary(included)
    result_label = _scenario_result_label(summary, baseline)
    return {
        "scenario_code": code,
        "scenario_label": label,
        "excluded_tickers": excluded_tickers,
        "excluded_dates": excluded_dates,
        "included_tickers": sorted({str(row.get("ticker")) for row in included}),
        "included_dates": sorted({str(row.get("signal_date")) for row in included}),
        **summary,
        "relative_positive": _relative_positive(summary),
        "hit_rate_passes_threshold": _hit_rate_passes(summary),
        "scenario_result_label": result_label,
        "interpretation": _interpret_scenario(code, result_label),
    }


def compute_exclusion_scenarios(rows: list[dict], analysis: dict) -> list[dict]:
    """Compute required BO-002 exclusion and isolation scenarios."""
    enriched = _enrich_rows(rows, analysis)
    baseline = _metric_summary(enriched)
    top_1 = _top_positive_tickers(enriched, 1)
    top_2 = _top_positive_tickers(enriched, 2)
    top_3 = _top_positive_tickers(enriched, 3)
    current_core = sorted(
        {str(row.get("ticker")) for row in enriched if row.get("cohort") == "current_core"}
    )
    expanded = sorted(
        {str(row.get("ticker")) for row in enriched if row.get("cohort") == "expanded_cohort"}
    )
    negative_dates = sorted(
        {
            date
            for date, date_rows in _group(enriched, "signal_date").items()
            if not _relative_positive(_metric_summary(date_rows))
        }
    )
    expanded_negative = sorted(
        {
            ticker
            for ticker, ticker_rows in _group(enriched, "ticker").items()
            if ticker in expanded
            and not _relative_positive(_metric_summary(ticker_rows))
        }
    )
    return [
        _scenario(
            code="full_sample",
            label="Full sample",
            rows=enriched,
            baseline=baseline,
        ),
        _scenario(
            code="ex_nvda",
            label="Ex-NVDA",
            rows=enriched,
            baseline=baseline,
            excluded_tickers=["NVDA"],
        ),
        _scenario(
            code="ex_top_1_positive_contributor",
            label="Ex-top-1 positive contributor",
            rows=enriched,
            baseline=baseline,
            excluded_tickers=top_1,
        ),
        _scenario(
            code="ex_top_2_positive_contributors",
            label="Ex-top-2 positive contributors",
            rows=enriched,
            baseline=baseline,
            excluded_tickers=top_2,
        ),
        _scenario(
            code="ex_top_3_positive_contributors",
            label="Ex-top-3 positive contributors",
            rows=enriched,
            baseline=baseline,
            excluded_tickers=top_3,
        ),
        _scenario(
            code="ex_current_core",
            label="Ex-current-core",
            rows=enriched,
            baseline=baseline,
            excluded_tickers=current_core,
        ),
        _scenario(
            code="expanded_cohort_only",
            label="Expanded cohort only",
            rows=[row for row in enriched if row.get("cohort") == "expanded_cohort"],
            baseline=baseline,
        ),
        _scenario(
            code="current_core_only",
            label="Current core only",
            rows=[row for row in enriched if row.get("cohort") == "current_core"],
            baseline=baseline,
        ),
        _scenario(
            code="ex_supportive_date_2021_06_30",
            label="Ex-supportive date 2021-06-30",
            rows=enriched,
            baseline=baseline,
            excluded_dates=[SUPPORTIVE_DATE],
        ),
        _scenario(
            code="negative_dates_only",
            label="Negative dates only",
            rows=[row for row in enriched if row.get("signal_date") in negative_dates],
            baseline=baseline,
        ),
        _scenario(
            code="ex_severe_negative_ticker_nflx",
            label="Ex-severe-negative ticker NFLX",
            rows=enriched,
            baseline=baseline,
            excluded_tickers=["NFLX"],
        ),
        _scenario(
            code="ex_expanded_negative_tickers",
            label="Ex-expanded negative tickers",
            rows=enriched,
            baseline=baseline,
            excluded_tickers=expanded_negative,
        ),
    ]


def _contribution_label(summary: dict) -> str:
    relative = summary.get("median_relative_return_12m")
    hit_rate = summary.get("hit_rate_vs_benchmark_12m")
    if relative is None or hit_rate is None:
        return "insufficient_evidence"
    if relative > 0 and hit_rate >= 0.5:
        return "positive_contributor"
    if relative < 0 and hit_rate < 0.5:
        return "negative_contributor"
    return "mixed_contributor"


def _contributor_entry(dimension: str, key: str, rows: list[dict]) -> dict:
    summary = _metric_summary(rows)
    label = _contribution_label(summary)
    return {
        "dimension": dimension,
        "key": key,
        **summary,
        "contribution_label": label,
        "interpretation": (
            f"{dimension} {key} is a {label.replace('_', ' ')} in the expanded evidence."
        ),
    }


def _contributors_for(rows: list[dict], dimension: str, key: str) -> list[dict]:
    return [
        _contributor_entry(dimension, group_key, group_rows)
        for group_key, group_rows in sorted(_group(rows, key).items())
    ]


def _sort_contributors(
    contributors: list[dict], metric: str, reverse: bool, limit: int = 5
) -> list[dict]:
    return sorted(
        contributors,
        key=lambda item: item.get(metric)
        if item.get(metric) is not None
        else (-999 if reverse else 999),
        reverse=reverse,
    )[:limit]


def attribute_outlier_dependence(rows: list[dict], analysis: dict) -> dict:
    """Build contributor attribution across ticker, date, cohort, and sector."""
    enriched = _enrich_rows(rows, analysis)
    ticker = _contributors_for(enriched, "ticker", "ticker")
    dates = _contributors_for(enriched, "date", "signal_date")
    cohorts = _contributors_for(enriched, "cohort", "cohort")
    sectors = _contributors_for(enriched, "sector", "sector")
    return {
        "top_positive_contributors_by_average_relative": _sort_contributors(
            ticker, "average_relative_return_12m", True
        ),
        "top_positive_contributors_by_median_relative": _sort_contributors(
            ticker, "median_relative_return_12m", True
        ),
        "top_negative_contributors_by_average_relative": _sort_contributors(
            ticker, "average_relative_return_12m", False
        ),
        "top_negative_contributors_by_median_relative": _sort_contributors(
            ticker, "median_relative_return_12m", False
        ),
        "top_positive_dates": _sort_contributors(
            dates, "median_relative_return_12m", True
        ),
        "top_negative_dates": _sort_contributors(
            dates, "median_relative_return_12m", False
        ),
        "top_positive_cohorts": _sort_contributors(
            cohorts, "median_relative_return_12m", True
        ),
        "top_negative_cohorts": _sort_contributors(
            cohorts, "median_relative_return_12m", False
        ),
        "top_positive_sectors": _sort_contributors(
            sectors, "median_relative_return_12m", True
        ),
        "top_negative_sectors": _sort_contributors(
            sectors, "median_relative_return_12m", False
        ),
    }


def _scenario_by_code(scenarios: list[dict], code: str) -> dict:
    return next(item for item in scenarios if item["scenario_code"] == code)


def _dependence_from_failure(scenario: dict) -> str:
    label = scenario.get("scenario_result_label")
    if label in {"fails_outlier_control", "not_applicable"}:
        return "severe_dependence"
    if label == "improves_but_not_enough":
        return "moderate_dependence"
    if label == "insufficient_records":
        return "inconclusive"
    return "limited_dependence"


def classify_dependence(
    *, scenarios: list[dict], contributors: dict, scorecard: dict
) -> dict:
    """Classify outlier and composition dependence."""
    ex_nvda = _scenario_by_code(scenarios, "ex_nvda")
    ex_top_2 = _scenario_by_code(scenarios, "ex_top_2_positive_contributors")
    ex_supportive = _scenario_by_code(scenarios, "ex_supportive_date_2021_06_30")
    expanded = _scenario_by_code(scenarios, "expanded_cohort_only")
    ex_negative = _scenario_by_code(scenarios, "ex_expanded_negative_tickers")
    scorecard_status = "unknown"
    for factor in scorecard.get("factor_results", []):
        if factor.get("factor_code") == "outlier_dependence":
            scorecard_status = str(factor.get("status") or "unknown")
            break
    nvda_status = _dependence_from_failure(ex_nvda)
    top_status = _dependence_from_failure(ex_top_2)
    supportive_status = _dependence_from_failure(ex_supportive)
    cohort_status = _dependence_from_failure(expanded)
    negative_drag = (
        "moderate_dependence"
        if ex_negative.get("scenario_result_label") == "survives_outlier_control"
        else "severe_dependence"
    )
    statuses = {nvda_status, top_status, supportive_status, cohort_status}
    overall = (
        "outlier_dependence_confirmed_or_needs_retest"
        if "severe_dependence" in statuses or scorecard_status == "negative"
        else "outlier_dependence_limited_but_requires_documentation"
    )
    positive_names = [
        item["key"]
        for item in contributors["top_positive_contributors_by_average_relative"][:3]
    ]
    return {
        "outlier_dependence_status": scorecard_status,
        "nvda_dependence_status": nvda_status,
        "top_contributor_dependence_status": top_status,
        "supportive_date_dependence_status": supportive_status,
        "cohort_dependence_status": cohort_status,
        "negative_ticker_drag_status": negative_drag,
        "overall_outlier_repair_status": overall,
        "main_outlier_finding": (
            "Expanded evidence remains sensitive to NVDA, leading positive "
            f"contributors ({', '.join(positive_names)}), supportive timing, "
            "and current-core versus expanded-cohort composition."
        ),
        "recommended_next_work_order": NEXT_WORK_ORDER,
    }


def build_outlier_retest_spec(
    *, decomposition: dict, dependence: dict
) -> dict:
    """Build a non-actionable retest specification for BO-002 controls."""
    return {
        "retest_spec_id": "BO-002-retest-spec",
        "purpose": (
            "Document the controls needed to retest outlier, NVDA, date, and "
            "cohort dependence before any future research gate."
        ),
        "required_scenarios_to_rerun": [
            "ex_nvda",
            "ex_top_2_positive_contributors",
            "current_core_only",
            "expanded_cohort_only",
            "ex_supportive_date_2021_06_30",
        ],
        "required_controls": [
            "Ex-NVDA control must be reported separately.",
            "Ex-top-2 control must be reported separately.",
            "Current-core and expanded-cohort results must be separated.",
            "Supportive-date exclusion must be reported separately.",
            "Negative ticker drag must be documented by ticker and cohort.",
        ],
        "data_inputs_needed": [
            "backtest_results.csv",
            "backtest_driver_decomposition_report.json",
            "expanded_trial_analysis_report.json",
        ],
        "exclusion_rules": {
            "ex_nvda": ["NVDA"],
            "ex_top_2_positive_contributors": "highest average relative 12M contributors",
            "ex_supportive_date_2021_06_30": [SUPPORTIVE_DATE],
            "current_core_only": "include only current_core universe_group",
            "expanded_cohort_only": "include only non-current_core records",
        },
        "minimum_success_conditions": [
            "Ex-NVDA scenario must be reported separately.",
            "Ex-top-2 scenario must be reported separately.",
            "Current-core and expanded-cohort must be reported separately.",
            "Supportive-date exclusion must be reported separately.",
            "No future price information may be introduced.",
            "Gatekeeper must be rerun after repair before any progression.",
        ],
        "safety_constraints": [
            "Do not rerun investor agents for this control.",
            "Do not change original backtest results.",
            "Do not create recommendations, rankings, allocations, or trade signals.",
        ],
        "expected_outputs": [
            "outlier_repair_path_report.md",
            "outlier_repair_path_report.json",
            "outlier_scenario_analysis.csv",
            "contributor_attribution.csv",
        ],
        "source_decomposition_run_id": decomposition.get("decomposition_run_id"),
        "overall_outlier_repair_status": dependence.get(
            "overall_outlier_repair_status"
        ),
    }


def build_outlier_repair_path(
    *,
    outlier_repair_run_id: str,
    generated_at: str,
    decomposition: dict,
    backoffice: dict,
    scorecard: dict,
    analysis: dict,
    rows: list[dict],
) -> OutlierRepairPathReport:
    """Build the full BO-002 repair-path report."""
    scenarios = compute_exclusion_scenarios(rows, analysis)
    contributors = attribute_outlier_dependence(rows, analysis)
    dependence = classify_dependence(
        scenarios=scenarios,
        contributors=contributors,
        scorecard=scorecard,
    )
    retest_spec = build_outlier_retest_spec(
        decomposition=decomposition,
        dependence=dependence,
    )
    return OutlierRepairPathReport(
        outlier_repair_run_id=outlier_repair_run_id,
        generated_at=generated_at,
        decomposition_run_id=str(decomposition.get("decomposition_run_id") or ""),
        backoffice_attribution_run_id=str(
            decomposition.get("backoffice_attribution_run_id") or ""
        ),
        investor_persona_attribution_run_id=str(
            decomposition.get("investor_persona_attribution_run_id") or ""
        ),
        gatekeeper_run_id=str(decomposition.get("gatekeeper_run_id") or ""),
        scorecard_run_id=str(decomposition.get("scorecard_run_id") or ""),
        analysis_run_id=str(decomposition.get("analysis_run_id") or ""),
        expanded_trial_run_id=str(decomposition.get("expanded_trial_run_id") or ""),
        backtest_run_id=str(decomposition.get("backtest_run_id") or ""),
        work_order_id=WORK_ORDER_ID,
        work_order_title=WORK_ORDER_TITLE,
        outlier_repair_status="completed",
        scenario_analysis=scenarios,
        contributor_attribution=contributors,
        dependence_classification=dependence,
        retest_spec=retest_spec,
        recommended_next_work_order=NEXT_WORK_ORDER,
    )


def _display(value) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "None"
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return "" if value is None else str(value)


def _scenario_section(scenarios: list[dict], code: str) -> str:
    item = _scenario_by_code(scenarios, code)
    return (
        f"{item['scenario_label']}: records={item['records']}, "
        f"median_relative_12m={item['median_relative_return_12m']}, "
        f"hit_rate={item['hit_rate_vs_benchmark_12m']}, "
        f"result={item['scenario_result_label']}."
    )


def _flatten_contributors(contributors: dict) -> list[dict]:
    rows = []
    for bucket, values in contributors.items():
        for item in values:
            rows.append({"bucket": bucket, **item})
    return rows


def render_outlier_repair_path_report(report: OutlierRepairPathReport) -> str:
    """Render the BO-002 repair path as Markdown."""
    data = report.to_dict()
    scenarios = data["scenario_analysis"]
    dependence = data["dependence_classification"]
    lines = [
        "# Outlier and Ex-NVDA Repair Path Report",
        "",
        "## Executive Summary",
        "",
        f"- Outlier Repair Run ID: {data['outlier_repair_run_id']}",
        f"- Decomposition Run ID: {data['decomposition_run_id']}",
        f"- Work Order ID: {data['work_order_id']}",
        f"- Backtest Run ID: {data['backtest_run_id']}",
        f"- Main Outlier Finding: {dependence['main_outlier_finding']}",
        (
            "- Overall Outlier Repair Status: "
            f"{dependence['overall_outlier_repair_status']}"
        ),
        f"- Recommended Next Work Order: {data['recommended_next_work_order']}",
        "",
        "## Important Boundary",
        "",
        (
            "This report decomposes and controls research evidence only. It does "
            "not create an investment decision, ranking, recommendation, "
            "allocation, rebalancing instruction, trade signal, or execution "
            "instruction."
        ),
        "",
        "## Source Context",
        "",
        "- Gatekeeper Decision: hold",
        "- Progression Allowed: false",
        f"- Current Work Order: {data['work_order_id']}",
        "- Reason: outlier dependence / result sensitive to NVDA.",
        "",
        "## Scenario Analysis",
        "",
        (
            "| Scenario | Records | Median Relative 12M | Hit Rate vs Benchmark | "
            "Result Label | Interpretation |"
        ),
        "|---|---:|---:|---:|---|---|",
    ]
    for item in scenarios:
        lines.append(
            f"| {item['scenario_label']} | {item['records']} | "
            f"{item['median_relative_return_12m']} | "
            f"{item['hit_rate_vs_benchmark_12m']} | "
            f"{item['scenario_result_label']} | {item['interpretation']} |"
        )
    lines.extend(
        [
            "",
            "## Ex-NVDA Analysis",
            "",
            _scenario_section(scenarios, "ex_nvda"),
            "",
            "## Ex-Top Contributors Analysis",
            "",
            _scenario_section(scenarios, "ex_top_2_positive_contributors"),
            "",
            "## Core vs Expanded Cohort Analysis",
            "",
            _scenario_section(scenarios, "current_core_only"),
            _scenario_section(scenarios, "expanded_cohort_only"),
            "",
            "## Supportive Date Dependence",
            "",
            _scenario_section(scenarios, "ex_supportive_date_2021_06_30"),
            "",
            "## Negative Ticker Drag",
            "",
            _scenario_section(scenarios, "ex_severe_negative_ticker_nflx"),
            _scenario_section(scenarios, "ex_expanded_negative_tickers"),
            "",
            "## Contributor Attribution",
            "",
            (
                "- Positive contributors by average relative evidence: "
                f"{_display([item['key'] for item in data['contributor_attribution']['top_positive_contributors_by_average_relative'][:5]])}"
            ),
            (
                "- Negative contributors by average relative evidence: "
                f"{_display([item['key'] for item in data['contributor_attribution']['top_negative_contributors_by_average_relative'][:5]])}"
            ),
            "",
            "## Dependence Classification",
            "",
            f"- NVDA Dependence: {dependence['nvda_dependence_status']}",
            (
                "- Top Contributor Dependence: "
                f"{dependence['top_contributor_dependence_status']}"
            ),
            (
                "- Supportive Date Dependence: "
                f"{dependence['supportive_date_dependence_status']}"
            ),
            f"- Cohort Dependence: {dependence['cohort_dependence_status']}",
            f"- Negative Ticker Drag: {dependence['negative_ticker_drag_status']}",
            "",
            "## Retest Specification",
            "",
            (
                "- Required Scenarios: "
                f"{_display(data['retest_spec']['required_scenarios_to_rerun'])}"
            ),
            (
                "- Minimum Success Conditions: "
                f"{_display(data['retest_spec']['minimum_success_conditions'])}"
            ),
            "",
            "## What This Suggests",
            "",
            (
                "- Evidence should remain held until outlier dependence and "
                "walk-forward stability are repaired or clearly documented."
            ),
            "- Backoffice should proceed to BO-003.",
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


def write_outlier_repair_path_report(
    *,
    outputs_root: Path,
    decomposition_run_id: str | None = None,
    generated_at: datetime | None = None,
) -> OutlierRepairPathFiles:
    """Load BO-002 inputs and write outlier repair-path artifacts."""
    outputs_root = Path(outputs_root)
    timestamp = generated_at or datetime.now(timezone.utc)
    manifest = load_backtest_driver_decomposition_manifest(
        outputs_root=outputs_root,
        decomposition_run_id=decomposition_run_id,
    )
    selected_id = str(
        decomposition_run_id or manifest.get("decomposition_run_id") or ""
    )
    if not selected_id:
        raise ValueError("Backtest driver decomposition run ID is required.")
    decomposition = (
        manifest
        if decomposition_run_id
        else load_backtest_driver_decomposition_report(
            outputs_root=outputs_root,
            decomposition_run_id=selected_id,
        )
    )
    backoffice = load_backoffice_attribution_report(
        outputs_root=outputs_root,
        backoffice_attribution_run_id=str(
            decomposition.get("backoffice_attribution_run_id") or ""
        ),
    )
    scorecard = load_research_scorecard_report(
        outputs_root=outputs_root,
        scorecard_run_id=str(decomposition.get("scorecard_run_id") or ""),
    )
    analysis = load_expanded_trial_analysis_report(
        outputs_root=outputs_root,
        analysis_run_id=str(decomposition.get("analysis_run_id") or ""),
    )
    rows = load_backtest_results(
        outputs_root=outputs_root,
        backtest_run_id=str(decomposition.get("backtest_run_id") or ""),
    )
    root = outputs_root / "outlier_repair_paths"
    root.mkdir(parents=True, exist_ok=True)
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    run_id = base
    suffix = 2
    while (root / run_id).exists():
        run_id = f"{base}_{suffix:02d}"
        suffix += 1
    report = build_outlier_repair_path(
        outlier_repair_run_id=run_id,
        generated_at=timestamp.isoformat(),
        decomposition=decomposition,
        backoffice=backoffice,
        scorecard=scorecard,
        analysis=analysis,
        rows=rows,
    )
    folder = root / run_id
    folder.mkdir(parents=True, exist_ok=False)
    markdown_path = folder / "outlier_repair_path_report.md"
    json_path = folder / "outlier_repair_path_report.json"
    scenario_path = folder / "outlier_scenario_analysis.csv"
    contributor_path = folder / "contributor_attribution.csv"
    retest_path = folder / "outlier_retest_spec.json"
    markdown_path.write_text(
        render_outlier_repair_path_report(report), encoding="utf-8"
    )
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(scenario_path, report.scenario_analysis)
    _write_csv(contributor_path, _flatten_contributors(report.contributor_attribution))
    retest_path.write_text(
        json.dumps(report.retest_spec, indent=2),
        encoding="utf-8",
    )
    latest_path = root / "latest_outlier_repair_path_manifest.json"
    latest_payload = {
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
        "outlier_repair_status": report.outlier_repair_status,
        "overall_outlier_repair_status": report.dependence_classification[
            "overall_outlier_repair_status"
        ],
        "recommended_next_work_order": report.recommended_next_work_order,
        "output_folder": str(folder),
        "report_path": str(markdown_path),
        "report_json_path": str(json_path),
        "scenario_csv_path": str(scenario_path),
        "contributor_csv_path": str(contributor_path),
        "retest_spec_path": str(retest_path),
        "safety_notice": report.safety_notice,
    }
    latest_path.write_text(json.dumps(latest_payload, indent=2), encoding="utf-8")
    return OutlierRepairPathFiles(
        output_folder=folder,
        markdown_path=markdown_path,
        json_path=json_path,
        scenario_csv_path=scenario_path,
        contributor_csv_path=contributor_path,
        retest_spec_path=retest_path,
        latest_manifest_path=latest_path,
        report=report,
    )
