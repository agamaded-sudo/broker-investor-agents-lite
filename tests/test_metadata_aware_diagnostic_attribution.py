"""Tests for metadata-aware readiness trial attribution diagnostics."""

from broker_agents.backtesting.readiness_trial_diagnostic_report import (
    assess_group_diversity,
    build_readiness_trial_diagnostic_report,
    render_readiness_trial_diagnostic_report,
)

INTEREST_FIELDS = (
    "buffett_interest_level",
    "munger_interest_level",
    "fisher_interest_level",
    "lynch_interest_level",
    "bogle_interest_level",
)


def _group(
    name: str,
    sample_size: int,
    median_12m: float,
    median_relative_12m: float,
    hit_rate: float,
) -> dict:
    return {
        "group_name": name,
        "sample_size": sample_size,
        "median_forward_return_12m": median_12m,
        "average_forward_return_12m": median_12m,
        "median_relative_return_12m": median_relative_12m,
        "hit_rate_vs_benchmark_12m": hit_rate,
        "positive_return_rate_12m": hit_rate,
        "median_max_drawdown_12m": -0.10,
        "small_sample_warning": sample_size < 5,
    }


def _metrics() -> dict:
    grouped = {
        "readiness_label": [
            _group(
                "Investor Review Possible with Evidence Gaps",
                3,
                0.217949,
                0.337949,
                0.666667,
            ),
            _group(
                "Ready for Investor Review",
                9,
                0.313725,
                0.112593,
                0.777778,
            ),
        ],
        "source_verification_status": [
            _group(
                "partially verified (mixed)",
                9,
                0.313725,
                0.112593,
                0.777778,
            ),
            _group(
                "partially verified (placeholder-heavy)",
                3,
                0.217949,
                0.337949,
                0.666667,
            ),
        ],
        "promotion_blocking_bucket": [
            _group("moderate_blockers", 12, 0.265837, 0.126261, 0.75)
        ],
        "buffett_interest_level": [
            _group("Watchlist Interest", 12, 0.265837, 0.126261, 0.75)
        ],
        "munger_interest_level": [
            _group("Conditional Interest", 12, 0.265837, 0.126261, 0.75)
        ],
        "fisher_interest_level": [
            _group("Needs More Evidence", 12, 0.265837, 0.126261, 0.75)
        ],
        "lynch_interest_level": [
            _group("Watchlist Interest", 12, 0.265837, 0.126261, 0.75)
        ],
        "bogle_interest_level": [
            _group("Low Interest", 12, 0.265837, 0.126261, 0.75)
        ],
    }
    return {
        "median_forward_return_3m": 0.019511,
        "median_forward_return_6m": 0.108843,
        "median_forward_return_12m": 0.265837,
        "average_forward_return_12m": 0.469876,
        "median_relative_return_12m": 0.126261,
        "hit_rate_vs_benchmark_3m": 0.666667,
        "hit_rate_vs_benchmark_6m": 0.583333,
        "hit_rate_vs_benchmark_12m": 0.75,
        "worst_max_drawdown_12m": -0.491228,
        "concentration_warning": True,
        "concentration_details": [
            "readiness_label:Ready for Investor Review=0.750",
            "promotion_blocking_bucket:moderate_blockers=1.000",
        ],
        "metadata_enrichment_status_counts": {"partial": 12},
        "missing_metadata_fields": [],
        "grouped_metrics": grouped,
    }


def _rows() -> list[dict]:
    rows = []
    for index in range(12):
        ready = index < 9
        row = {
            "ticker": ("MSFT", "AAPL", "NVDA", "COST")[index % 4],
            "signal_date": f"{2021 + index // 4}-06-30",
            "forward_return_3m": "0.02",
            "forward_return_6m": "0.10",
            "forward_return_12m": str(0.20 + index / 20),
            "relative_return_12m": str(0.05 + index / 100),
            "data_status": "complete_local_csv",
            "metadata_enrichment_status": "partial",
            "readiness_label": (
                "Ready for Investor Review"
                if ready
                else "Investor Review Possible with Evidence Gaps"
            ),
            "source_verification_status": (
                "partially verified (mixed)"
                if ready
                else "partially verified (placeholder-heavy)"
            ),
            "promotion_blocking_bucket": "moderate_blockers",
            "buffett_interest_level": "Watchlist Interest",
            "munger_interest_level": "Conditional Interest",
            "fisher_interest_level": "Needs More Evidence",
            "lynch_interest_level": "Watchlist Interest",
            "bogle_interest_level": "Low Interest",
        }
        rows.append(row)
    return rows


def test_group_diversity_preserves_small_sample_and_dominance_limits() -> None:
    readiness = assess_group_diversity(
        _metrics()["grouped_metrics"]["readiness_label"]
    )
    interest = assess_group_diversity(
        _metrics()["grouped_metrics"]["buffett_interest_level"]
    )

    assert readiness["group_count"] == 2
    assert readiness["total_records"] == 12
    assert readiness["max_group_share"] == 0.75
    assert readiness["smallest_group_sample_size"] == 3
    assert readiness["small_sample_limited"] is True
    assert readiness["has_useful_diversity"] is False
    assert interest["group_count"] == 1
    assert interest["max_group_share"] == 1.0
    assert interest["has_useful_diversity"] is False
    assert interest["attribution_status"] == "low_diversity"


def test_metadata_attribution_json_and_markdown_are_conservative() -> None:
    report = build_readiness_trial_diagnostic_report(
        manifest={
            "backtest_run_id": "metadata-attribution",
            "backtest_run_type": "readiness_trial",
            "walk_forward_enabled": True,
            "walk_forward_stability_judgment": "unstable",
            "duplicate_records_removed": 50,
        },
        metrics=_metrics(),
        rows=_rows(),
    )
    payload = report.to_dict()
    attribution = payload["metadata_attribution_diagnostics"]

    assert attribution["metadata_enrichment_detected"] is True
    assert attribution["metadata_enrichment_status_counts"] == {
        "partial": 12
    }
    assert attribution["missing_metadata_fields"] == []
    readiness = attribution["readiness_label_attribution"]
    assert len(readiness["groups"]) == 2
    assert readiness["groups"][0]["small_sample_warning"] is True
    assert readiness["group_diversity"]["max_group_share"] == 0.75
    assert readiness["group_diversity"]["has_useful_diversity"] is False
    assert "higher median absolute 12M outcome" in readiness["interpretation"]
    assert "preliminary" in readiness["interpretation"]
    source = attribution["source_verification_attribution"]
    assert len(source["groups"]) == 2
    for field in INTEREST_FIELDS:
        interest = attribution["investor_interest_attribution"][field]
        assert interest["group_diversity"]["group_count"] == 1
        assert interest["group_diversity"]["max_group_share"] == 1.0
        assert interest["group_diversity"]["has_useful_diversity"] is False
    blockers = attribution["promotion_blocking_attribution"]
    assert blockers["group_diversity"]["group_count"] == 1
    assert blockers["group_diversity"]["has_useful_diversity"] is False
    assert any(
        "Metadata enrichment is detected" in finding
        for finding in report.key_findings
    )
    assert any(
        "No causal or decision-grade inference" in finding
        for finding in report.key_findings
    )

    markdown = render_readiness_trial_diagnostic_report(report)
    summary = markdown.split("## Aggregate Result Review", maxsplit=1)[0]
    assert "low metadata diversity" in summary
    assert "missing metadata" not in summary.lower()
    for heading in (
        "Metadata Attribution Review",
        "Readiness Label Attribution",
        "Source Verification Attribution",
        "Investor Interest Attribution",
        "Promotion Blocking Attribution",
        "Attribution Limitations",
    ):
        assert heading in markdown
    assert "Investor interest metadata is present but has low diversity" in (
        markdown
    )
    assert "current trial set lacks useful diversity" in markdown
    assert "Grouped associations do not establish causal relationships." in (
        markdown
    )


def test_missing_metadata_summary_keeps_existing_warning() -> None:
    metrics = _metrics()
    metrics["metadata_enrichment_status_counts"] = {"not_available": 12}
    metrics["grouped_metrics"] = {
        field: [_group("Missing", 12, 0.265837, 0.126261, 0.75)]
        for field in metrics["grouped_metrics"]
    }
    rows = [
        {
            **row,
            "metadata_enrichment_status": "not_available",
            **{
                field: "Missing"
                for field in (
                    "readiness_label",
                    "source_verification_status",
                    *INTEREST_FIELDS,
                )
            },
        }
        for row in _rows()
    ]
    report = build_readiness_trial_diagnostic_report(
        manifest={
            "backtest_run_id": "missing-attribution",
            "backtest_run_type": "readiness_trial",
            "walk_forward_stability_judgment": "unstable",
        },
        metrics=metrics,
        rows=rows,
    )

    markdown = render_readiness_trial_diagnostic_report(report)
    summary = markdown.split("## Aggregate Result Review", maxsplit=1)[0]
    assert "missing metadata" in summary.lower()
    assert report.metadata_attribution_diagnostics[
        "metadata_enrichment_detected"
    ] is False
