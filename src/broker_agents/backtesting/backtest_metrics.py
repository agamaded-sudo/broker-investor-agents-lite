"""Descriptive research metrics for deduped backtest result rows."""

from collections.abc import Callable
from statistics import mean, median

INTEREST_GROUP_FIELDS = (
    "buffett_interest_level",
    "munger_interest_level",
    "fisher_interest_level",
    "lynch_interest_level",
    "bogle_interest_level",
)
GROUP_FIELDS = (
    "readiness_label",
    "source_verification_status",
    "promotion_blocking_bucket",
    *INTEREST_GROUP_FIELDS,
)


def _numeric_values(rows: list[dict], field: str) -> list[float]:
    """Return valid numeric values while ignoring missing fields."""
    values = []
    for row in rows:
        value = row.get(field)
        if value in {"", None}:
            continue
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            continue
    return values


def _statistic(
    rows: list[dict],
    field: str,
    calculator: Callable[[list[float]], float],
) -> float | None:
    """Calculate one statistic or return null when no values exist."""
    values = _numeric_values(rows, field)
    return round(calculator(values), 6) if values else None


def _rate(rows: list[dict], field: str) -> float | None:
    """Return the share of valid values greater than zero."""
    values = _numeric_values(rows, field)
    if not values:
        return None
    return round(sum(value > 0 for value in values) / len(values), 6)


def _blocker_bucket(row: dict) -> str:
    """Map the result blocker count to a research grouping."""
    try:
        count = int(row.get("promotion_blocking_count") or 0)
    except (TypeError, ValueError):
        count = 0
    if count == 0:
        return "no_blockers"
    if count <= 2:
        return "one_or_two_blockers"
    return "three_or_more_blockers"


def _group_metrics(rows: list[dict], field: str) -> list[dict]:
    """Calculate compact 12-month metrics for one grouping field."""
    groups: dict[str, list[dict]] = {}
    for row in rows:
        if field == "promotion_blocking_bucket":
            label = _blocker_bucket(row)
        else:
            label = str(row.get(field) or "Missing")
        groups.setdefault(label, []).append(row)
    return [
        {
            "group_name": label,
            "sample_size": len(group),
            "median_forward_return_12m": _statistic(
                group,
                "forward_return_12m",
                median,
            ),
            "average_forward_return_12m": _statistic(
                group,
                "forward_return_12m",
                mean,
            ),
            "median_relative_return_12m": _statistic(
                group,
                "relative_return_12m",
                median,
            ),
            "hit_rate_vs_benchmark_12m": _rate(
                group,
                "relative_return_12m",
            ),
            "positive_return_rate_12m": _rate(
                group,
                "forward_return_12m",
            ),
            "median_max_drawdown_12m": _statistic(
                group,
                "max_drawdown_12m",
                median,
            ),
            "small_sample_warning": len(group) < 5,
        }
        for label, group in sorted(groups.items())
    ]


def _concentration_details(rows: list[dict]) -> list[str]:
    """Describe ticker or category shares above the 40% threshold."""
    sample_size = len(rows)
    if sample_size == 0:
        return []
    details = []
    ticker_counts: dict[str, int] = {}
    for row in rows:
        ticker = str(row.get("ticker") or "Missing")
        ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1
    details.extend(
        f"ticker:{ticker}={count / sample_size:.3f}"
        for ticker, count in sorted(ticker_counts.items())
        if count / sample_size > 0.40
    )
    for field in GROUP_FIELDS:
        counts: dict[str, int] = {}
        for row in rows:
            label = (
                _blocker_bucket(row)
                if field == "promotion_blocking_bucket"
                else str(row.get(field) or "Missing")
            )
            counts[label] = counts.get(label, 0) + 1
        details.extend(
            f"{field}:{label}={count / sample_size:.3f}"
            for label, count in sorted(counts.items())
            if count / sample_size > 0.40
        )
    return details


def calculate_backtest_metrics(
    rows: list[dict],
    *,
    price_data_type: str,
) -> dict:
    """Calculate overall and grouped research metrics from result rows."""
    evaluated_rows = [
        row
        for row in rows
        if str(row.get("data_status", "")).startswith("complete")
    ]
    metrics = {
        "sample_size": len(evaluated_rows),
        "evaluated_tickers": sorted(
            {str(row.get("ticker")) for row in evaluated_rows}
        ),
    }
    for months in (3, 6, 12):
        metrics[f"median_forward_return_{months}m"] = _statistic(
            evaluated_rows,
            f"forward_return_{months}m",
            median,
        )
        metrics[f"average_forward_return_{months}m"] = _statistic(
            evaluated_rows,
            f"forward_return_{months}m",
            mean,
        )
        metrics[f"median_relative_return_{months}m"] = _statistic(
            evaluated_rows,
            f"relative_return_{months}m",
            median,
        )
        metrics[f"average_relative_return_{months}m"] = _statistic(
            evaluated_rows,
            f"relative_return_{months}m",
            mean,
        )
        metrics[f"hit_rate_vs_benchmark_{months}m"] = _rate(
            evaluated_rows,
            f"relative_return_{months}m",
        )
        metrics[f"positive_return_rate_{months}m"] = _rate(
            evaluated_rows,
            f"forward_return_{months}m",
        )
    drawdowns = _numeric_values(evaluated_rows, "max_drawdown_12m")
    forward_12m = _numeric_values(evaluated_rows, "forward_return_12m")
    concentration_details = _concentration_details(evaluated_rows)
    metrics.update(
        {
            "median_max_drawdown_12m": (
                round(median(drawdowns), 6) if drawdowns else None
            ),
            "worst_max_drawdown_12m": (
                round(min(drawdowns), 6) if drawdowns else None
            ),
            "highest_forward_return_12m": (
                round(max(forward_12m), 6) if forward_12m else None
            ),
            "lowest_forward_return_12m": (
                round(min(forward_12m), 6) if forward_12m else None
            ),
            "small_sample_warning": len(evaluated_rows) < 10,
            "concentration_warning": bool(concentration_details),
            "concentration_details": concentration_details,
            "synthetic_data_warning": price_data_type == "synthetic_fixture",
            "grouped_metrics": {
                field: _group_metrics(evaluated_rows, field)
                for field in GROUP_FIELDS
            },
        }
    )
    return metrics


def _display(value: object) -> str:
    """Format optional numeric metrics for Markdown."""
    if value is None:
        return "Missing"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def render_backtest_metrics_summary(metrics: dict) -> str:
    """Render a standalone compact metrics artifact."""
    lines = [
        "# Backtest Metrics Summary",
        "",
        "## Overall Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for field in (
        "sample_size",
        "median_forward_return_3m",
        "median_forward_return_6m",
        "median_forward_return_12m",
        "average_forward_return_3m",
        "average_forward_return_6m",
        "average_forward_return_12m",
        "median_relative_return_12m",
        "hit_rate_vs_benchmark_12m",
        "positive_return_rate_12m",
        "median_max_drawdown_12m",
        "worst_max_drawdown_12m",
        "highest_forward_return_12m",
        "lowest_forward_return_12m",
        "small_sample_warning",
        "concentration_warning",
        "synthetic_data_warning",
    ):
        lines.append(f"| {field} | {_display(metrics.get(field))} |")
    lines.extend(
        [
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
        lines.extend(
            [
                f"### {field}",
                "",
                (
                    "| Group | Sample Size | Median 12M Return | "
                    "Median Relative 12M Return | Hit Rate vs Benchmark 12M | "
                    "Small Sample Warning |"
                ),
                "|---|---:|---:|---:|---:|---|",
            ]
        )
        for group in metrics["grouped_metrics"][field]:
            lines.append(
                f"| {group['group_name']} | {group['sample_size']} | "
                f"{_display(group['median_forward_return_12m'])} | "
                f"{_display(group['median_relative_return_12m'])} | "
                f"{_display(group['hit_rate_vs_benchmark_12m'])} | "
                f"{_display(group['small_sample_warning'])} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Safety Note",
            "",
            (
                "This backtest is not a recommendation, ranking, vote, average "
                "score, consensus, allocation instruction, rebalancing instruction, "
                "or trade signal."
            ),
            (
                "Results are research-only associations and must not be "
                "interpreted as investment advice or a trading strategy."
            ),
            "",
        ]
    )
    return "\n".join(lines)
