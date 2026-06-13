"""Yearly cohort validation for research-only backtest result rows."""

import csv
from dataclasses import dataclass
import json
from pathlib import Path

from broker_agents.backtesting.backtest_metrics import (
    calculate_backtest_metrics,
)

READINESS_TRIAL_WALK_FORWARD_NOTICE = (
    "This readiness trial walk-forward backtest evaluates readiness-only "
    "research artifacts by time period. It is not a recommendation backtest, "
    "ranking backtest, allocation backtest, rebalancing backtest, trade signal "
    "backtest, or execution instruction."
)
WALK_FORWARD_FIELDS = (
    "period",
    "period_start",
    "period_end",
    "period_start_date",
    "period_end_date",
    "sample_size",
    "tickers",
    "median_forward_return_3m",
    "median_forward_return_6m",
    "median_forward_return_12m",
    "average_forward_return_3m",
    "average_forward_return_6m",
    "average_forward_return_12m",
    "median_relative_return_3m",
    "median_relative_return_6m",
    "median_relative_return_12m",
    "hit_rate_vs_benchmark_3m",
    "hit_rate_vs_benchmark_6m",
    "hit_rate_vs_benchmark_12m",
    "positive_return_rate_3m",
    "positive_return_rate_6m",
    "positive_return_rate_12m",
    "median_max_drawdown_12m",
    "small_sample_warning",
    "concentration_warning",
    "data_status",
)


@dataclass(frozen=True)
class WalkForwardResult:
    """Artifacts and metrics generated for one walk-forward run."""

    summary_path: Path
    results_path: Path
    metrics_path: Path
    metrics: dict


def _ticker_concentration_warning(rows: list[dict]) -> bool:
    """Return true when one ticker exceeds 40% of a cohort."""
    if not rows:
        return False
    counts: dict[str, int] = {}
    for row in rows:
        ticker = str(row.get("ticker") or "Missing")
        counts[ticker] = counts.get(ticker, 0) + 1
    return any(count / len(rows) > 0.40 for count in counts.values())


def _yearly_cohorts(rows: list[dict]) -> dict[str, list[dict]]:
    """Group rows with valid signal dates by calendar year."""
    cohorts: dict[str, list[dict]] = {}
    for row in rows:
        signal_date = str(row.get("signal_date") or "")
        if len(signal_date) < 4:
            continue
        cohorts.setdefault(signal_date[:4], []).append(row)
    return dict(sorted(cohorts.items()))


def _period_row(
    period: str,
    rows: list[dict],
    price_data_type: str,
    minimum_group_size: int,
) -> dict:
    """Calculate one yearly cohort using the shared backtest metrics."""
    metrics = calculate_backtest_metrics(
        rows,
        price_data_type=price_data_type,
    )
    evaluated_rows = [
        row
        for row in rows
        if str(row.get("data_status", "")).startswith("complete")
    ]
    result = {
        "period": period,
        "period_start": f"{period}-01-01",
        "period_end": f"{period}-12-31",
        "period_start_date": f"{period}-01-01",
        "period_end_date": f"{period}-12-31",
        "sample_size": metrics["sample_size"],
        "tickers": ";".join(metrics["evaluated_tickers"]),
        "small_sample_warning": (
            metrics["sample_size"] < minimum_group_size
        ),
        "concentration_warning": _ticker_concentration_warning(
            evaluated_rows
        ),
        "data_status": (
            "complete" if evaluated_rows else "no_evaluated_records"
        ),
    }
    for months in (3, 6, 12):
        for prefix in (
            "median_forward_return",
            "average_forward_return",
            "median_relative_return",
            "hit_rate_vs_benchmark",
            "positive_return_rate",
        ):
            field = f"{prefix}_{months}m"
            result[field] = metrics[field]
    result["median_max_drawdown_12m"] = metrics[
        "median_max_drawdown_12m"
    ]
    return result


def _stability_observation(periods: list[dict]) -> str:
    """Summarize period signs without creating an investment conclusion."""
    values = [
        period["median_relative_return_12m"]
        for period in periods
        if period["median_relative_return_12m"] is not None
    ]
    if len(values) < 2:
        return "insufficient_periods"
    if all(value > 0 for value in values):
        return "consistently_positive_relative_12m"
    if all(value < 0 for value in values):
        return "consistently_negative_relative_12m"
    return "mixed_period_results"


def _display(value: object) -> str:
    """Format a compact optional value for Markdown."""
    if value is None:
        return "Missing"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _render_summary(context: dict, metrics: dict) -> str:
    """Render the standalone walk-forward research report."""
    lines = [
        "# Walk-Forward Historical Validation",
        "",
        "## 1. Run Context",
        "",
        f"- Backtest Run ID: {context['backtest_run_id']}",
        f"- Ledger Path: {context['ledger_path']}",
        f"- Price Provider: {context['price_provider']}",
        f"- Price Data Root: {context['price_data_root']}",
        f"- Frequency: {metrics['frequency']}",
        f"- Periods Evaluated: {metrics['total_periods']}",
        "- Forward Windows: 3 months, 6 months, 12 months",
        f"- Benchmark: {context['benchmark']}",
        "",
    ]
    if context.get("backtest_run_type") == "readiness_trial":
        lines.extend(
            [
                "## Readiness Trial Walk-Forward Notice",
                "",
                "- Backtest Run Type: readiness_trial",
                "- Readiness Only: Yes",
                "- Not Trade Signal: Yes",
                "- Not Recommendation: Yes",
                "- Not Allocation Instruction: Yes",
                f"- Safety Notice: {READINESS_TRIAL_WALK_FORWARD_NOTICE}",
                "",
                (
                    "These walk-forward results must not be interpreted as "
                    "investment recommendations or trading signals."
                ),
                "",
            ]
        )
    lines.extend(
        [
            "## 2. Period Results",
            "",
            (
                "| Period | Records | Median 12M Return | "
                "Median 12M Relative Return | Hit Rate vs Benchmark 12M | "
                "Small Sample Warning |"
            ),
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for period in metrics["periods"]:
        lines.append(
            f"| {period['period']} | {period['sample_size']} | "
            f"{_display(period['median_forward_return_12m'])} | "
            f"{_display(period['median_relative_return_12m'])} | "
            f"{_display(period['hit_rate_vs_benchmark_12m'])} | "
            f"{_display(period['small_sample_warning'])} |"
        )
    lines.extend(
        [
            "",
            "## 3. Stability Notes",
            "",
            (
                "- Stability Observation: "
                f"{metrics['stability_observation']}"
            ),
            (
                "- Periods With Positive Relative 12M: "
                f"{metrics['periods_with_positive_relative_12m']}"
            ),
            (
                "- Periods With Negative Relative 12M: "
                f"{metrics['periods_with_negative_relative_12m']}"
            ),
            (
                "- Periods With Small Sample Warning: "
                f"{metrics['periods_with_small_sample_warning']}"
            ),
            (
                "- Period-level differences describe historical associations "
                "only and may be sensitive to cohort composition."
            ),
            "",
            "## 4. Limitations",
            "",
            "- The trial ledger may contain synthetic or reconstructed inputs.",
            "- Period sample sizes may be small.",
            "- This does not simulate portfolio construction.",
            "- This does not define entry or exit rules.",
            "- This does not represent live trading.",
            "- Results depend on available price data.",
            "",
            "## 5. Safety Note",
            "",
            (
                "This walk-forward validation is not a recommendation, ranking, "
                "vote, average score, consensus, allocation instruction, "
                "rebalancing instruction, or trade signal."
            ),
            (
                "Historical trial ledgers are for research and pipeline "
                "validation only and must not be interpreted as real historical "
                "investment advice."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def generate_walk_forward_outputs(
    *,
    rows: list[dict],
    output_dir: Path,
    context: dict,
    frequency: str = "yearly",
    minimum_group_size: int = 5,
) -> WalkForwardResult:
    """Generate yearly cohort outputs beside the main backtest artifacts."""
    if frequency != "yearly":
        raise ValueError("walk_forward_frequency must be yearly.")
    periods = [
        _period_row(
            period,
            cohort,
            context["price_data_type"],
            minimum_group_size,
        )
        for period, cohort in _yearly_cohorts(rows).items()
    ]
    relative_values = [
        period["median_relative_return_12m"]
        for period in periods
        if period["median_relative_return_12m"] is not None
    ]
    metrics = {
        "enabled": True,
        "frequency": frequency,
        "periods": periods,
        "total_periods": len(periods),
        "periods_with_positive_relative_12m": sum(
            value > 0 for value in relative_values
        ),
        "periods_with_negative_relative_12m": sum(
            value < 0 for value in relative_values
        ),
        "periods_with_small_sample_warning": sum(
            period["small_sample_warning"] for period in periods
        ),
        "stability_observation": _stability_observation(periods),
    }
    output_dir = Path(output_dir)
    results_path = output_dir / "walk_forward_results.csv"
    with results_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=WALK_FORWARD_FIELDS)
        writer.writeheader()
        writer.writerows(periods)
    metrics_path = output_dir / "walk_forward_metrics.json"
    metrics_path.write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )
    summary_path = output_dir / "walk_forward_summary.md"
    summary_path.write_text(
        _render_summary(context, metrics),
        encoding="utf-8",
    )
    return WalkForwardResult(
        summary_path=summary_path,
        results_path=results_path,
        metrics_path=metrics_path,
        metrics=metrics,
    )
