"""Run an expanded readiness trial from a validated eligible universe."""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

import yaml

from broker_agents.deals.historical_readiness_multidate import (
    run_historical_readiness_multidate,
)

EXPANDED_TRIAL_NOTICE = (
    "This expanded ticker trial evaluates readiness-only historical research "
    "artifacts from a coverage-validated local universe."
)
SAFETY_NOTICE = (
    "This expanded ticker readiness trial is research-only. It is not a "
    "recommendation, ranking, allocation instruction, rebalancing instruction, "
    "trade signal, execution instruction, or investment advice."
)
PRIOR_BACKTEST_RUN_ID = "20260614_205804"


@dataclass(frozen=True)
class ExpandedTickerTrialResult:
    """Files and headline values for one expanded readiness trial."""

    expanded_trial_run_id: str
    expanded_trial_folder: Path
    summary_path: Path
    summary_json_path: Path
    latest_manifest_path: Path
    source_validation_run_id: str | None
    eligible_tickers: list[str]
    requested_dates: list[str]
    usable_dates: list[str]
    skipped_dates: list[str]
    completed_runs: int
    failed_runs: int
    trial_ledger_validation_status: str
    backtest_run_id: str | None
    sample_size_after_dedupe: int | None
    clean_record_count: int
    warning_record_count: int
    warning_heavy_record_count: int
    diagnostic_status: str | None
    decision_status: str | None
    walk_forward_stability_judgment: str | None
    status: str


def load_eligible_ticker_universe(path: Path) -> tuple[list[str], dict]:
    """Load a validated eligible universe without inferring extra tickers."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Eligible universe file not found: {path}")
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid eligible universe YAML {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Eligible universe YAML must contain a mapping.")
    values = payload.get("tickers")
    if values is None:
        values = payload.get("eligible_tickers")
    if not isinstance(values, list):
        raise ValueError("Eligible universe must contain a tickers list.")
    tickers = []
    for value in values:
        ticker = value.get("ticker") if isinstance(value, dict) else value
        normalized = str(ticker or "").strip().upper()
        if normalized:
            tickers.append(normalized)
    tickers = list(dict.fromkeys(tickers))
    if not tickers:
        raise ValueError("Eligible universe does not contain any tickers.")
    return tickers, payload


def _load_json(path: Path | None) -> dict:
    if not path or not Path(path).is_file():
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _allocate_run_id(root: Path, timestamp: datetime) -> str:
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    candidate = base
    suffix = 2
    while (root / candidate).exists():
        candidate = f"{base}_{suffix:02d}"
        suffix += 1
    return candidate


def _source_output_validation(outputs_root: Path, source_run_id: str | None) -> dict:
    path = (
        Path(outputs_root)
        / "expanded_ticker_coverage_validations"
        / "latest_expanded_ticker_coverage_output_validation_manifest.json"
    )
    payload = _load_json(path)
    if payload.get("source_validation_run_id") != source_run_id:
        return {}
    return payload


def _metric(metrics: dict, key: str):
    return metrics.get(key)


def _render_summary(summary: dict) -> str:
    prior = summary["prior_trial_comparison"]
    lines = [
        "# Expanded Ticker Readiness Trial Summary",
        "",
        "## Executive Summary",
        "",
        f"- Expanded Trial Run ID: {summary['expanded_trial_run_id']}",
        f"- Source Validation Run ID: {summary['source_validation_run_id'] or 'Unknown'}",
        f"- Eligible Tickers: {len(summary['eligible_tickers'])}",
        f"- Completed Runs: {summary['completed_runs']}",
        f"- Failed Runs: {summary['failed_runs']}",
        f"- Backtest Run ID: {summary['backtest_run_id'] or 'Not run'}",
        f"- Main Finding: {summary['main_finding']}",
        "",
        "## Expanded Universe",
        "",
        ", ".join(summary["eligible_tickers"]),
        "",
        "## Date Coverage",
        "",
        f"- Requested Dates: {', '.join(summary['requested_dates'])}",
        f"- Usable Dates: {', '.join(summary['usable_dates']) or 'None'}",
        f"- Skipped Dates: {', '.join(summary['skipped_dates']) or 'None'}",
        "",
        "## Trial Ledger Status",
        "",
        f"- Trial Ledger: {summary['trial_ledger_path'] or 'Not exported'}",
        f"- Validation Status: {summary['trial_ledger_validation_status']}",
        "",
        "## Backtest Snapshot",
        "",
        f"- Sample Size After Dedupe: {summary['sample_size_after_dedupe'] or 0}",
        f"- Clean Records: {summary['clean_record_count']}",
        f"- Warning Records: {summary['warning_record_count']}",
        f"- Warning-Heavy Records: {summary['warning_heavy_record_count']}",
        f"- Median 12M: {summary['median_forward_return_12m']}",
        f"- Median Relative 12M: {summary['median_relative_return_12m']}",
        f"- Hit Rate 12M: {summary['hit_rate_vs_benchmark_12m']}",
        f"- Worst Drawdown: {summary['worst_max_drawdown_12m']}",
        f"- Diagnostic Status: {summary['diagnostic_status'] or 'Not run'}",
        f"- Decision Status: {summary['decision_status'] or 'Not run'}",
        f"- Statistical Validity: {summary['statistical_validity'] or 'Not run'}",
        (
            "- Walk-Forward Stability: "
            f"{summary['walk_forward_stability_judgment'] or 'Not run'}"
        ),
        "",
        "## Comparison to Prior 4-Ticker Trial",
        "",
        "| Metric | Prior | Expanded |",
        "|---|---:|---:|",
        f"| Sample Size | {prior['prior_sample_size']} | {summary['sample_size_after_dedupe'] or 0} |",
        f"| Clean Records | {prior['prior_clean_record_count']} | {summary['clean_record_count']} |",
        f"| Warning Records | {prior['prior_warning_record_count']} | {summary['warning_record_count']} |",
        f"| Warning-Heavy Records | {prior['prior_warning_heavy_record_count']} | {summary['warning_heavy_record_count']} |",
        f"| Diagnostic Status | {prior['prior_diagnostic_status']} | {summary['diagnostic_status'] or 'Not run'} |",
        f"| Decision Status | {prior['prior_decision_status']} | {summary['decision_status'] or 'Not run'} |",
        "",
        "## What This Suggests",
        "",
        "- The readiness pipeline can be evaluated across a broader local fixture universe.",
        "- Clean and warning-bearing evidence remain separated.",
        "- Broader research can continue while existing cautions remain visible.",
        "",
        "## What This Does Not Suggest",
        "",
        "- It does not prove a strategy.",
        "- It does not validate investor agents.",
        "- It does not create an investment recommendation.",
        "- It does not create a trade signal.",
        "- It does not justify allocation or rebalancing.",
        "",
        "## Next Research Action",
        "",
        f"- Action Code: {summary['next_research_action']}",
        "",
        "## Safety Notice",
        "",
        summary["safety_notice"],
        "",
    ]
    return "\n".join(lines)


def run_expanded_ticker_readiness_trial(
    *,
    eligible_universe: Path,
    date_preset: str | None,
    as_of_dates: str | list[str] | None,
    examples_root: Path,
    outputs_root: Path,
    fixtures_root: Path,
    portfolio_context: Path | None,
    financials_provider: str,
    financials_root: Path,
    price_fixtures_path: Path,
    export_trial_ledger: bool,
    validate_trial_ledger: bool,
    run_readiness_backtest: bool,
    walk_forward: bool,
    trial_ledger_path: Path = Path(
        "data/inputs/trial_ledgers/historical_readiness_trial_ledger.csv"
    ),
    generated_at: datetime | None = None,
) -> ExpandedTickerTrialResult:
    """Execute the validated universe through the existing readiness pipeline."""
    tickers, universe = load_eligible_ticker_universe(eligible_universe)
    source_validation_run_id = (
        str(universe.get("validation_run_id"))
        if universe.get("validation_run_id")
        else None
    )
    output_validation = _source_output_validation(
        Path(outputs_root), source_validation_run_id
    )
    if output_validation and not output_validation.get(
        "readiness_for_expanded_trial", False
    ):
        raise ValueError("Expanded ticker coverage output is not ready for trial.")

    timestamp = generated_at or datetime.now(timezone.utc)
    root = Path(outputs_root) / "expanded_ticker_trials"
    root.mkdir(parents=True, exist_ok=True)
    run_id = _allocate_run_id(root, timestamp)
    folder = root / run_id
    folder.mkdir(parents=True, exist_ok=False)

    multidate = run_historical_readiness_multidate(
        tickers=tickers,
        as_of_dates=as_of_dates,
        date_preset=date_preset,
        examples_root=examples_root,
        outputs_root=outputs_root,
        fixtures_root=fixtures_root,
        portfolio_context=portfolio_context,
        financials_provider=financials_provider,
        financials_root=financials_root,
        export_trial_ledger=export_trial_ledger,
        validate_trial_ledger=validate_trial_ledger,
        run_readiness_backtest=run_readiness_backtest,
        trial_ledger_path=trial_ledger_path,
        price_fixtures_path=price_fixtures_path,
        walk_forward=walk_forward,
        walk_forward_frequency="yearly",
        generated_at=timestamp,
    )
    multidate_manifest = _load_json(multidate.manifest_path)
    backtest_manifest_path = multidate_manifest.get("readiness_backtest_manifest")
    backtest_manifest = _load_json(
        Path(backtest_manifest_path) if backtest_manifest_path else None
    )
    metrics_path = backtest_manifest.get("metrics_summary_path")
    metrics = _load_json(Path(metrics_path) if metrics_path else None)
    prior_folder = Path(outputs_root) / "backtests" / PRIOR_BACKTEST_RUN_ID
    prior_manifest = _load_json(prior_folder / "backtest_manifest.json")

    warnings_exist = bool(
        multidate.skipped_dates
        or multidate.total_failed_runs
        or multidate_manifest.get("pipeline_warnings")
        or output_validation.get("output_validation_status") == "ready_with_warnings"
    )
    if multidate.total_completed_runs == 0:
        status = "expanded_trial_failed"
    elif multidate.total_failed_runs or (
        run_readiness_backtest and not multidate.readiness_backtest_run
    ):
        status = "expanded_trial_incomplete"
    elif warnings_exist:
        status = "expanded_trial_completed_with_warnings"
    else:
        status = "expanded_trial_completed"

    summary = {
        "expanded_trial_run_id": run_id,
        "generated_at": timestamp.isoformat(),
        "expanded_trial": True,
        "source_validation_run_id": source_validation_run_id,
        "source_output_validation_run_id": output_validation.get(
            "validation_check_run_id"
        ),
        "source_output_validation_status": output_validation.get(
            "output_validation_status"
        ),
        "eligible_universe_path": str(eligible_universe),
        "eligible_ticker_count": len(tickers),
        "eligible_tickers": tickers,
        "requested_dates": multidate.resolved_as_of_dates,
        "usable_dates": multidate.usable_dates,
        "skipped_dates": multidate.skipped_dates,
        "expected_usable_records": len(tickers) * len(multidate.usable_dates),
        "completed_runs": multidate.total_completed_runs,
        "failed_runs": multidate.total_failed_runs,
        "multidate_run_id": multidate.multidate_run_id,
        "multidate_manifest_path": str(multidate.manifest_path),
        "trial_ledger_path": multidate_manifest.get("trial_ledger_path"),
        "trial_ledger_validation_status": (
            multidate.trial_ledger_validation_status
        ),
        "backtest_run_id": multidate_manifest.get("readiness_backtest_run_id"),
        "backtest_manifest_path": backtest_manifest_path,
        "sample_size_after_dedupe": multidate.sample_size_after_dedupe,
        "clean_record_count": int(backtest_manifest.get("clean_record_count", 0)),
        "warning_record_count": int(
            backtest_manifest.get("warning_record_count", 0)
        ),
        "warning_heavy_record_count": int(
            backtest_manifest.get("warning_heavy_record_count", 0)
        ),
        "median_forward_return_12m": _metric(
            metrics, "median_forward_return_12m"
        ),
        "median_relative_return_12m": _metric(
            metrics, "median_relative_return_12m"
        ),
        "hit_rate_vs_benchmark_12m": _metric(
            metrics, "hit_rate_vs_benchmark_12m"
        ),
        "worst_max_drawdown_12m": _metric(metrics, "worst_max_drawdown_12m"),
        "diagnostic_status": backtest_manifest.get("diagnostic_status"),
        "decision_status": backtest_manifest.get("decision_status"),
        "statistical_validity": backtest_manifest.get("statistical_validity"),
        "walk_forward_stability_judgment": backtest_manifest.get(
            "walk_forward_stability_judgment"
        ),
        "expanded_trial_notice": EXPANDED_TRIAL_NOTICE,
        "main_finding": (
            "The validated expanded universe completed with clean and warning "
            "evidence separated; the broader sample is "
            f"{backtest_manifest.get('diagnostic_status', 'diagnostic-only')} "
            "and the decision remains conservative."
            if backtest_manifest
            else (
                "The validated expanded universe completed, but no readiness "
                "backtest interpretation was requested."
            )
            if status != "expanded_trial_failed"
            else "The expanded trial did not produce completed readiness runs."
        ),
        "prior_trial_comparison": {
            "prior_backtest_run_id": PRIOR_BACKTEST_RUN_ID,
            "prior_sample_size": prior_manifest.get("overall_sample_size", 20),
            "prior_clean_record_count": prior_manifest.get(
                "clean_record_count", 12
            ),
            "prior_warning_record_count": prior_manifest.get(
                "warning_record_count", 8
            ),
            "prior_warning_heavy_record_count": prior_manifest.get(
                "warning_heavy_record_count", 0
            ),
            "prior_diagnostic_status": prior_manifest.get(
                "diagnostic_status", "promising_but_unproven"
            ),
            "prior_decision_status": prior_manifest.get(
                "decision_status", "needs_more_samples"
            ),
        },
        "next_research_action": "analyze_expanded_trial_results",
        "safety_notice": SAFETY_NOTICE,
        "status": status,
    }
    json_path = folder / "expanded_ticker_trial_summary.json"
    markdown_path = folder / "expanded_ticker_trial_summary.md"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    markdown_path.write_text(_render_summary(summary), encoding="utf-8")
    latest_path = root / "latest_expanded_ticker_trial_manifest.json"
    latest = {
        **summary,
        "expanded_trial_folder": str(folder),
        "summary_path": str(markdown_path),
        "summary_json_path": str(json_path),
    }
    latest_path.write_text(json.dumps(latest, indent=2), encoding="utf-8")
    return ExpandedTickerTrialResult(
        expanded_trial_run_id=run_id,
        expanded_trial_folder=folder,
        summary_path=markdown_path,
        summary_json_path=json_path,
        latest_manifest_path=latest_path,
        source_validation_run_id=source_validation_run_id,
        eligible_tickers=tickers,
        requested_dates=multidate.resolved_as_of_dates,
        usable_dates=multidate.usable_dates,
        skipped_dates=multidate.skipped_dates,
        completed_runs=multidate.total_completed_runs,
        failed_runs=multidate.total_failed_runs,
        trial_ledger_validation_status=(
            multidate.trial_ledger_validation_status
        ),
        backtest_run_id=multidate_manifest.get("readiness_backtest_run_id"),
        sample_size_after_dedupe=multidate.sample_size_after_dedupe,
        clean_record_count=summary["clean_record_count"],
        warning_record_count=summary["warning_record_count"],
        warning_heavy_record_count=summary["warning_heavy_record_count"],
        diagnostic_status=summary["diagnostic_status"],
        decision_status=summary["decision_status"],
        walk_forward_stability_judgment=summary[
            "walk_forward_stability_judgment"
        ],
        status=status,
    )
