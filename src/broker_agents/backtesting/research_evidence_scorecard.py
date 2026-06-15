"""Research-only evidence scorecard for expanded readiness trials."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This research evidence scorecard is not a financial score, "
    "recommendation, ranking, allocation instruction, rebalancing "
    "instruction, trade signal, execution instruction, strategy validation, "
    "or investment advice."
)
NEXT_RESEARCH_ACTION = "prepare_research_gatekeeper_with_hold_bias"
STATUS_SCORES = {
    "strong_positive": 2,
    "positive": 1,
    "neutral": 0,
    "warning": -1,
    "negative": -2,
    "blocker": -4,
    "unavailable": 0,
}
CORE_FACTORS = {
    "benchmark_relative_performance",
    "walk_forward_stability",
    "diagnostic_status",
    "clean_evidence_strength",
    "data_quality_integrity",
}
FACTOR_LABELS = {
    "sample_size_strength": "Sample Size Strength",
    "clean_evidence_strength": "Clean Evidence Strength",
    "warning_evidence_control": "Warning Evidence Control",
    "benchmark_relative_performance": "Benchmark-Relative Performance",
    "absolute_forward_performance": "Absolute Forward Performance",
    "walk_forward_stability": "Walk-Forward Stability",
    "diagnostic_status": "Diagnostic Status",
    "decision_conservatism": "Decision Conservatism",
    "expanded_cohort_effect": "Expanded Cohort Effect",
    "period_sensitivity": "Period Sensitivity",
    "metadata_diversity": "Metadata Diversity",
    "delayed_anchor_effect": "Delayed Anchor Effect",
    "outlier_dependence": "Outlier Dependence",
    "data_quality_integrity": "Data Quality Integrity",
}


@dataclass(frozen=True)
class ScorecardFactor:
    """One weighted and auditable research evidence factor."""

    factor_code: str
    label: str
    status: str
    weight: int
    evidence: dict
    interpretation: str

    @property
    def weighted_score(self) -> int:
        """Return the deterministic weighted factor contribution."""
        return STATUS_SCORES[self.status] * self.weight

    def to_dict(self) -> dict:
        """Return a JSON-ready factor row."""
        return {**asdict(self), "weighted_score": self.weighted_score}


@dataclass(frozen=True)
class ResearchEvidenceScorecard:
    """Consolidated research status for an expanded readiness trial."""

    scorecard_run_id: str
    generated_at: str
    analysis_run_id: str
    expanded_trial_run_id: str
    backtest_run_id: str
    prior_backtest_run_id: str
    scorecard_status: str
    research_evidence_classification: str
    research_decision: str
    raw_score: int
    max_possible_score: int
    normalized_score_percent: float
    negative_factor_count: int
    warning_factor_count: int
    blocker_count: int
    factor_results: list[dict]
    positive_factors: list[str]
    warning_factors: list[str]
    negative_factors: list[str]
    blocker_factors: list[str]
    key_strengths: list[str]
    key_weaknesses: list[str]
    main_interpretation: str
    recommended_next_research_action: str
    limitations: list[str]
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready scorecard."""
        return asdict(self)


@dataclass(frozen=True)
class ResearchEvidenceScorecardFiles:
    """Generated scorecard files and structured result."""

    scorecard_folder: Path
    markdown_path: Path
    json_path: Path
    factors_csv_path: Path
    latest_manifest_path: Path
    scorecard: ResearchEvidenceScorecard


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_expanded_trial_analysis_manifest(
    *,
    outputs_root: Path,
    analysis_run_id: str | None = None,
) -> dict:
    """Load one analysis manifest or the latest completed analysis."""
    root = Path(outputs_root) / "expanded_trial_analyses"
    if analysis_run_id:
        path = root / str(analysis_run_id) / "expanded_trial_analysis_report.json"
    else:
        path = root / "latest_expanded_trial_analysis_manifest.json"
    if not path.is_file():
        raise FileNotFoundError(f"Expanded trial analysis manifest not found: {path}")
    payload = _load_json(path)
    payload["_manifest_path"] = str(path)
    return payload


def load_expanded_trial_analysis_report(
    *,
    outputs_root: Path,
    analysis_run_id: str,
) -> dict:
    """Load the complete expanded trial analysis JSON."""
    path = (
        Path(outputs_root)
        / "expanded_trial_analyses"
        / str(analysis_run_id)
        / "expanded_trial_analysis_report.json"
    )
    if not path.is_file():
        raise FileNotFoundError(f"Expanded trial analysis report not found: {path}")
    return _load_json(path)


def load_expanded_trial_summary(
    *,
    outputs_root: Path,
    expanded_trial_run_id: str,
) -> dict:
    """Load the expanded trial summary linked by the analysis."""
    path = (
        Path(outputs_root)
        / "expanded_ticker_trials"
        / str(expanded_trial_run_id)
        / "expanded_ticker_trial_summary.json"
    )
    if not path.is_file():
        raise FileNotFoundError(f"Expanded trial summary not found: {path}")
    return _load_json(path)


def load_backtest_reports(
    *,
    outputs_root: Path,
    backtest_run_id: str,
) -> dict:
    """Load the manifest and linked readiness reports used by factors."""
    folder = Path(outputs_root) / "backtests" / str(backtest_run_id)
    manifest_path = folder / "backtest_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Backtest manifest not found: {manifest_path}")
    return {
        "manifest": _load_json(manifest_path),
        "decision": _load_json(folder / "readiness_trial_decision_report.json"),
        "diagnostic": _load_json(
            folder / "readiness_trial_diagnostic_report.json"
        ),
        "clean_coverage": _load_json(
            folder / "clean_coverage_sensitivity_report.json"
        ),
        "delayed_anchor": _load_json(
            folder / "delayed_anchor_impact_report.json"
        ),
        "outlier": _load_json(folder / "outlier_sensitivity_report.json"),
        "walk_forward": _load_json(folder / "walk_forward_metrics.json"),
    }


def _factor(
    code: str,
    status: str,
    evidence: dict,
    interpretation: str,
) -> ScorecardFactor:
    return ScorecardFactor(
        factor_code=code,
        label=FACTOR_LABELS[code],
        status=status,
        weight=2 if code in CORE_FACTORS else 1,
        evidence=evidence,
        interpretation=interpretation,
    )


def _find(items: list[dict], field: str, value: str) -> dict:
    return next((item for item in items if item.get(field) == value), {})


def evaluate_scorecard_factors(
    *,
    analysis: dict,
    expanded: dict,
    reports: dict,
) -> list[ScorecardFactor]:
    """Build the fixed fourteen-factor research evidence scorecard."""
    manifest = reports["manifest"]
    clean_report = reports["clean_coverage"]
    delayed_report = reports["delayed_anchor"]
    outlier_report = reports["outlier"]
    sample_size = int(expanded.get("sample_size_after_dedupe") or 0)
    clean_count = int(expanded.get("clean_record_count") or 0)
    warning_count = int(expanded.get("warning_record_count") or 0)
    warning_heavy = int(expanded.get("warning_heavy_record_count") or 0)
    total = max(sample_size, clean_count + warning_count)
    clean_share = round(clean_count / total, 6) if total else 0.0
    relative = expanded.get("median_relative_return_12m")
    hit_rate = expanded.get("hit_rate_vs_benchmark_12m")
    absolute = expanded.get("median_forward_return_12m")
    walk_status = (
        expanded.get("walk_forward_stability_judgment")
        or manifest.get("walk_forward_stability_judgment")
    )
    diagnostic = expanded.get("diagnostic_status") or manifest.get(
        "diagnostic_status"
    )
    decision = expanded.get("decision_status") or manifest.get(
        "decision_status"
    )
    groups = analysis.get("universe_group_attribution") or []
    core = _find(groups, "universe_group", "current_core")
    added = _find(groups, "universe_group", "expanded_cohort")
    drivers = (
        analysis.get("expanded_trial_instability_explanation", {}).get(
            "primary_instability_drivers", []
        )
    )
    metadata_status = (
        analysis.get("metadata_diversity_recheck", {}).get(
            "metadata_diversity_status"
        )
    )
    delayed_status = (
        delayed_report.get("impact_status")
        or manifest.get("delayed_anchor_impact_status")
    )
    no_delayed_positive = bool(
        delayed_report.get("impact_assessment", {}).get(
            "no_delayed_anchor_positive"
        )
        or manifest.get("no_delayed_anchor_positive")
    )
    outlier_status = (
        outlier_report.get("outlier_dependence_status")
        or manifest.get("outlier_dependence_status")
    )
    ex_nvda_positive = bool(
        outlier_report.get("outlier_impact_assessment", {}).get(
            "ex_nvda_positive"
        )
        or manifest.get("ex_nvda_positive")
    )
    ex_top_2_positive = bool(
        outlier_report.get("outlier_impact_assessment", {}).get(
            "ex_top_2_positive"
        )
        or manifest.get("ex_top_2_positive")
    )
    clean_subset = clean_report.get("subset_diagnostics", {}).get(
        "clean_records", {}
    )

    factors = [
        _factor(
            "sample_size_strength",
            "positive" if sample_size >= 30 else "warning",
            {
                "sample_size_after_dedupe": sample_size,
                "prior_sample_size": analysis.get(
                    "prior_trial_comparison", {}
                ).get("prior", {}).get("sample_size"),
            },
            (
                "The expanded sample is materially larger than the prior trial, "
                "but remains limited for broad validation."
            ),
        ),
        _factor(
            "clean_evidence_strength",
            (
                "positive"
                if clean_count >= 5 and clean_share >= 0.5
                else "warning"
            ),
            {
                "clean_record_count": clean_count,
                "clean_share": clean_share,
                "clean_median_relative_return_12m": clean_subset.get(
                    "median_relative_return_12m"
                ),
            },
            (
                "Clean evidence is available at useful research scale, though "
                "its benchmark-relative result remains weak."
            ),
        ),
        _factor(
            "warning_evidence_control",
            "positive" if warning_heavy == 0 else "warning",
            {
                "warning_record_count": warning_count,
                "warning_heavy_record_count": warning_heavy,
            },
            (
                "Warning-bearing evidence remains visible and no evaluated "
                "records are warning-heavy."
            ),
        ),
        _factor(
            "benchmark_relative_performance",
            (
                "negative"
                if relative is not None
                and hit_rate is not None
                and (relative < 0 or hit_rate < 0.5)
                else "positive"
            ),
            {
                "median_relative_return_12m": relative,
                "hit_rate_vs_benchmark_12m": hit_rate,
            },
            (
                "Median benchmark-relative performance is negative and fewer "
                "than half of records exceeded the benchmark."
            ),
        ),
        _factor(
            "absolute_forward_performance",
            "positive" if absolute is not None and absolute > 0 else "negative",
            {"median_forward_return_12m": absolute},
            (
                "Median absolute 12M outcome is positive, but this does not "
                "offset weak benchmark-relative evidence."
            ),
        ),
        _factor(
            "walk_forward_stability",
            (
                "negative"
                if walk_status in {"unstable", "mixed", "insufficient_periods"}
                else "positive"
            ),
            {"walk_forward_stability_judgment": walk_status},
            "Yearly walk-forward results are not stable across periods.",
        ),
        _factor(
            "diagnostic_status",
            (
                "negative"
                if diagnostic == "unstable_needs_deeper_review"
                else "warning"
            ),
            {"diagnostic_status": diagnostic},
            "The diagnostic report requires deeper review before progression.",
        ),
        _factor(
            "decision_conservatism",
            (
                "positive"
                if decision
                in {"needs_more_samples", "not_decision_grade", "diagnostic_only"}
                else "warning"
            ),
            {"decision_status": decision},
            "The decision layer remains conservative and has not claimed validation.",
        ),
        _factor(
            "expanded_cohort_effect",
            (
                "negative"
                if added.get("median_relative_return_12m") is not None
                and core.get("median_relative_return_12m") is not None
                and added["median_relative_return_12m"]
                < core["median_relative_return_12m"]
                else "neutral"
            ),
            {
                "current_core_median_relative_return_12m": core.get(
                    "median_relative_return_12m"
                ),
                "expanded_cohort_median_relative_return_12m": added.get(
                    "median_relative_return_12m"
                ),
                "expanded_cohort_hit_rate": added.get(
                    "hit_rate_vs_benchmark_12m"
                ),
            },
            "The added cohort materially weakened the prior core result.",
        ),
        _factor(
            "period_sensitivity",
            "negative" if "period_sensitivity" in drivers else "neutral",
            {
                "driver_present": "period_sensitivity" in drivers,
                "date_attribution": analysis.get("date_attribution", []),
            },
            "The result changes materially across historical periods.",
        ),
        _factor(
            "metadata_diversity",
            (
                "warning"
                if metadata_status == "partially_concentrated"
                else "negative"
                if metadata_status == "concentrated_needs_expansion"
                else "positive"
            ),
            {
                "metadata_diversity_status": metadata_status,
                "low_diversity_fields": analysis.get(
                    "metadata_diversity_recheck", {}
                ).get("low_diversity_fields", []),
            },
            (
                "Ticker structure diversified, while several readiness and "
                "investor-interest fields remain low-diversity."
            ),
        ),
        _factor(
            "delayed_anchor_effect",
            (
                "negative"
                if delayed_status == "delayed_anchor_present_no_delayed_positive"
                or not no_delayed_positive
                else "warning"
            ),
            {
                "delayed_anchor_impact_status": delayed_status,
                "no_delayed_anchor_positive": no_delayed_positive,
            },
            (
                "Non-delayed records do not remain positive on the established "
                "impact test, so anchor timing remains a material caution."
            ),
        ),
        _factor(
            "outlier_dependence",
            (
                "negative"
                if outlier_status
                in {"result_sensitive_to_nvda", "result_sensitive_to_top_outliers"}
                or not ex_nvda_positive
                or not ex_top_2_positive
                else "warning"
            ),
            {
                "outlier_dependence_status": outlier_status,
                "ex_nvda_positive": ex_nvda_positive,
                "ex_top_2_positive": ex_top_2_positive,
            },
            "The expanded result does not survive established outlier controls.",
        ),
        _factor(
            "data_quality_integrity",
            (
                "strong_positive"
                if int(expanded.get("failed_runs") or 0) == 0
                and expanded.get("trial_ledger_validation_status") == "valid"
                and warning_heavy == 0
                else "warning"
            ),
            {
                "completed_runs": expanded.get("completed_runs"),
                "failed_runs": expanded.get("failed_runs"),
                "trial_ledger_validation_status": expanded.get(
                    "trial_ledger_validation_status"
                ),
                "warning_heavy_record_count": warning_heavy,
            },
            (
                "The expanded research pipeline completed without run failures, "
                "the ledger validated, and warning-heavy evidence is absent."
            ),
        ),
    ]
    return factors


def classify_research_evidence(
    factors: list[ScorecardFactor],
    *,
    diagnostic_status: str | None,
) -> str:
    """Classify evidence conservatively using explicit factor rules."""
    statuses = {factor.factor_code: factor.status for factor in factors}
    if any(factor.status == "blocker" for factor in factors):
        return "blocked_research_evidence"
    if (
        statuses.get("benchmark_relative_performance") == "negative"
        and statuses.get("walk_forward_stability") == "negative"
    ) or diagnostic_status == "unstable_needs_deeper_review":
        return "unstable_research_evidence"
    raw_score = sum(factor.weighted_score for factor in factors)
    if raw_score < 0:
        return "weak_research_evidence"
    if statuses.get("sample_size_strength") == "warning":
        return "preliminary_mixed_evidence"
    if statuses.get("walk_forward_stability") == "positive" and raw_score >= 10:
        return "moderate_research_evidence"
    return "preliminary_mixed_evidence"


def build_research_evidence_scorecard(
    *,
    scorecard_run_id: str,
    generated_at: str,
    analysis: dict,
    expanded: dict,
    reports: dict,
) -> ResearchEvidenceScorecard:
    """Build one deterministic, non-actionable research evidence scorecard."""
    factors = evaluate_scorecard_factors(
        analysis=analysis,
        expanded=expanded,
        reports=reports,
    )
    raw_score = sum(factor.weighted_score for factor in factors)
    max_score = sum(STATUS_SCORES["strong_positive"] * factor.weight for factor in factors)
    normalized = round(raw_score / max_score * 100, 2) if max_score else 0.0
    positive = [
        factor.factor_code
        for factor in factors
        if factor.status in {"positive", "strong_positive"}
    ]
    warnings = [
        factor.factor_code for factor in factors if factor.status == "warning"
    ]
    negatives = [
        factor.factor_code for factor in factors if factor.status == "negative"
    ]
    blockers = [
        factor.factor_code for factor in factors if factor.status == "blocker"
    ]
    diagnostic = expanded.get("diagnostic_status") or reports["manifest"].get(
        "diagnostic_status"
    )
    classification = classify_research_evidence(
        factors,
        diagnostic_status=diagnostic,
    )
    missing = [
        name
        for name, payload in reports.items()
        if name != "manifest" and not payload
    ]
    scorecard_status = (
        "scorecard_blocked_missing_inputs"
        if not analysis or not expanded or not reports.get("manifest")
        else "scorecard_completed_with_warnings"
        if warnings or negatives
        else "scorecard_completed"
    )
    return ResearchEvidenceScorecard(
        scorecard_run_id=scorecard_run_id,
        generated_at=generated_at,
        analysis_run_id=str(analysis.get("analysis_run_id") or ""),
        expanded_trial_run_id=str(analysis.get("expanded_trial_run_id") or ""),
        backtest_run_id=str(analysis.get("backtest_run_id") or ""),
        prior_backtest_run_id=str(
            analysis.get("prior_backtest_run_id") or ""
        ),
        scorecard_status=scorecard_status,
        research_evidence_classification=classification,
        research_decision=(
            "block_research_progression"
            if blockers
            else "hold_for_deeper_analysis"
            if classification == "unstable_research_evidence"
            else "proceed_to_gatekeeper_with_warnings"
        ),
        raw_score=raw_score,
        max_possible_score=max_score,
        normalized_score_percent=normalized,
        negative_factor_count=len(negatives),
        warning_factor_count=len(warnings),
        blocker_count=len(blockers),
        factor_results=[factor.to_dict() for factor in factors],
        positive_factors=positive,
        warning_factors=warnings,
        negative_factors=negatives,
        blocker_factors=blockers,
        key_strengths=[
            "The expanded sample completed without failed runs.",
            "The trial ledger validated successfully.",
            "Clean evidence is available and warning-heavy evidence is absent.",
            "Decision conservatism remains intact.",
        ],
        key_weaknesses=[
            "Median benchmark-relative 12M performance is negative.",
            "The benchmark hit rate is below one half.",
            "Walk-forward stability is unstable.",
            "The added ticker cohort weakened the prior core result.",
            "The result is period-sensitive and outlier-sensitive.",
            "Several readiness metadata fields remain low-diversity.",
        ],
        main_interpretation=(
            "The expanded trial has good research execution integrity, but its "
            "performance evidence weakened after broadening. Negative "
            "benchmark-relative results, unstable periods, and sensitivity "
            "controls support a research hold rather than progression."
        ),
        recommended_next_research_action=NEXT_RESEARCH_ACTION,
        limitations=[
            "This scorecard summarizes existing research artifacts only.",
            "Factor weights are deterministic governance weights, not financial weights.",
            "The sample and metadata diversity remain limited.",
            *(
                ["Some linked reports were unavailable: " + ", ".join(missing)]
                if missing
                else []
            ),
        ],
    )


def _format(value) -> str:
    if value is None:
        return "Not available"
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def render_research_evidence_scorecard(
    scorecard: ResearchEvidenceScorecard,
) -> str:
    """Render the scorecard as a conservative Markdown report."""
    data = scorecard.to_dict()
    factors = data["factor_results"]
    positive_count = len(data["positive_factors"])
    lines = [
        "# Research Evidence Scorecard",
        "",
        "## Executive Summary",
        "",
        f"- Scorecard Run ID: {data['scorecard_run_id']}",
        f"- Analysis Run ID: {data['analysis_run_id']}",
        f"- Expanded Trial Run ID: {data['expanded_trial_run_id']}",
        f"- Backtest Run ID: {data['backtest_run_id']}",
        (
            "- Research Evidence Classification: "
            f"{data['research_evidence_classification']}"
        ),
        f"- Research Decision: {data['research_decision']}",
        f"- Main Interpretation: {data['main_interpretation']}",
        (
            "- Next Research Action: "
            f"{data['recommended_next_research_action']}"
        ),
        "",
        "## Scorecard Summary",
        "",
        f"- Raw Score: {data['raw_score']}",
        f"- Maximum Possible Score: {data['max_possible_score']}",
        f"- Normalized Score: {data['normalized_score_percent']}%",
        f"- Positive Factor Count: {positive_count}",
        f"- Warning Factor Count: {data['warning_factor_count']}",
        f"- Negative Factor Count: {data['negative_factor_count']}",
        f"- Blocker Count: {data['blocker_count']}",
        "",
        "## Factor Results",
        "",
        "| Factor | Status | Weight | Evidence | Interpretation |",
        "|---|---|---:|---|---|",
    ]
    for factor in factors:
        evidence = json.dumps(factor["evidence"], sort_keys=True).replace(
            "|", "/"
        )
        lines.append(
            f"| {factor['label']} | {factor['status']} | "
            f"{factor['weight']} | {evidence} | "
            f"{factor['interpretation']} |"
        )
    for title, key in (
        ("Key Strengths", "key_strengths"),
        ("Key Weaknesses", "key_weaknesses"),
    ):
        lines.extend(["", f"## {title}", ""])
        lines.extend(f"- {item}" for item in data[key])
    lines.extend(
        [
            "",
            "## Research Classification",
            "",
            (
                "The evidence is classified as "
                f"`{data['research_evidence_classification']}` because "
                "benchmark-relative performance and walk-forward stability "
                "are negative despite sound execution and clean data coverage."
            ),
            "",
            "## Research Decision",
            "",
            (
                f"The research decision is `{data['research_decision']}`. "
                "The expanded sample completed successfully, but the evidence "
                "requires deeper analysis before any progression."
            ),
            "",
            "## Relationship to Prior Evidence",
            "",
            (
                "The prior four-ticker result was promising but unproven. The "
                "expanded twelve-ticker result weakened, so the earlier evidence "
                "did not generalize cleanly."
            ),
            "",
            "## What This Suggests",
            "",
            "- The system correctly detected weakened evidence after expansion.",
            "- The pipeline should continue to gatekeeping with a hold bias.",
            "- The result is useful as a research diagnostic.",
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
            "## Next Research Action",
            "",
            f"- Action Code: {data['recommended_next_research_action']}",
            "",
            "## Safety Notice",
            "",
            data["safety_notice"],
            "",
        ]
    )
    return "\n".join(lines)


def write_research_evidence_scorecard_report(
    *,
    outputs_root: Path,
    analysis_run_id: str | None = None,
    expanded_trial_run_id: str | None = None,
    backtest_run_id: str | None = None,
    prior_backtest_run_id: str | None = None,
    generated_at: datetime | None = None,
) -> ResearchEvidenceScorecardFiles:
    """Load existing analysis artifacts and write scorecard outputs."""
    outputs_root = Path(outputs_root)
    timestamp = generated_at or datetime.now(timezone.utc)
    manifest = load_expanded_trial_analysis_manifest(
        outputs_root=outputs_root,
        analysis_run_id=analysis_run_id,
    )
    selected_analysis_id = str(
        analysis_run_id or manifest.get("analysis_run_id") or ""
    )
    if analysis_run_id:
        analysis = manifest
    else:
        analysis = load_expanded_trial_analysis_report(
            outputs_root=outputs_root,
            analysis_run_id=selected_analysis_id,
        )
    selected_expanded_id = str(
        expanded_trial_run_id
        or analysis.get("expanded_trial_run_id")
        or manifest.get("expanded_trial_run_id")
        or ""
    )
    selected_backtest_id = str(
        backtest_run_id
        or analysis.get("backtest_run_id")
        or manifest.get("backtest_run_id")
        or ""
    )
    if not selected_analysis_id or not selected_expanded_id or not selected_backtest_id:
        raise ValueError(
            "Analysis, expanded trial, and backtest run IDs are required."
        )
    expanded = load_expanded_trial_summary(
        outputs_root=outputs_root,
        expanded_trial_run_id=selected_expanded_id,
    )
    reports = load_backtest_reports(
        outputs_root=outputs_root,
        backtest_run_id=selected_backtest_id,
    )
    if prior_backtest_run_id:
        analysis = {**analysis, "prior_backtest_run_id": prior_backtest_run_id}

    root = outputs_root / "research_evidence_scorecards"
    root.mkdir(parents=True, exist_ok=True)
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    run_id = base
    suffix = 2
    while (root / run_id).exists():
        run_id = f"{base}_{suffix:02d}"
        suffix += 1
    scorecard = build_research_evidence_scorecard(
        scorecard_run_id=run_id,
        generated_at=timestamp.isoformat(),
        analysis=analysis,
        expanded=expanded,
        reports=reports,
    )
    folder = root / run_id
    folder.mkdir(parents=True, exist_ok=False)
    markdown_path = folder / "research_evidence_scorecard_report.md"
    json_path = folder / "research_evidence_scorecard_report.json"
    factors_path = folder / "research_evidence_scorecard_factors.csv"
    markdown_path.write_text(
        render_research_evidence_scorecard(scorecard),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(scorecard.to_dict(), indent=2),
        encoding="utf-8",
    )
    with factors_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "factor_code",
                "label",
                "status",
                "weight",
                "weighted_score",
                "evidence",
                "interpretation",
            ),
        )
        writer.writeheader()
        for factor in scorecard.factor_results:
            writer.writerow(
                {
                    **factor,
                    "evidence": json.dumps(
                        factor["evidence"], sort_keys=True
                    ),
                }
            )
    latest_path = root / "latest_research_evidence_scorecard_manifest.json"
    latest = {
        "scorecard_run_id": scorecard.scorecard_run_id,
        "analysis_run_id": scorecard.analysis_run_id,
        "expanded_trial_run_id": scorecard.expanded_trial_run_id,
        "backtest_run_id": scorecard.backtest_run_id,
        "prior_backtest_run_id": scorecard.prior_backtest_run_id,
        "scorecard_status": scorecard.scorecard_status,
        "research_evidence_classification": (
            scorecard.research_evidence_classification
        ),
        "research_decision": scorecard.research_decision,
        "recommended_next_research_action": (
            scorecard.recommended_next_research_action
        ),
        "scorecard_folder": str(folder),
        "report_path": str(markdown_path),
        "report_json_path": str(json_path),
        "factors_csv_path": str(factors_path),
        "safety_notice": scorecard.safety_notice,
    }
    latest_path.write_text(json.dumps(latest, indent=2), encoding="utf-8")
    return ResearchEvidenceScorecardFiles(
        scorecard_folder=folder,
        markdown_path=markdown_path,
        json_path=json_path,
        factors_csv_path=factors_path,
        latest_manifest_path=latest_path,
        scorecard=scorecard,
    )
