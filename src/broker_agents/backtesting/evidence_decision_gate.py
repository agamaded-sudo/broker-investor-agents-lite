"""Research-stage evidence gate for readiness trial backtests."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This evidence decision gate governs research-stage progression only. "
    "It is not a recommendation, ranking, vote, average score, consensus, "
    "allocation instruction, rebalancing instruction, trade signal, "
    "execution instruction, investment advice, or strategy validation."
)
CRITERIA_FIELDS = (
    "criterion",
    "status",
    "critical",
    "evidence",
    "interpretation",
)


@dataclass(frozen=True)
class EvidenceGateCriterion:
    """One auditable gate criterion."""

    criterion: str
    status: str
    critical: bool
    evidence: dict
    interpretation: str

    def to_dict(self) -> dict:
        """Return a JSON-ready representation."""
        return asdict(self)


@dataclass(frozen=True)
class EvidenceDecisionGateReport:
    """Structured clean-versus-warning research progression gate."""

    gate_run_id: str
    generated_at: str
    source_backtest_run_id: str | None
    source_backtest_manifest_path: str | None
    source_reports: dict
    gate_outcome: str
    gate_status: str
    critical_pass_count: int
    warn_count: int
    block_count: int
    criteria_results: list[dict]
    evidence_summary: dict
    blockers: list[str]
    warnings: list[str]
    next_research_action: str
    limitations: list[str]
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready representation."""
        return asdict(self)


@dataclass(frozen=True)
class EvidenceDecisionGateFiles:
    """Generated gate artifact paths and content."""

    gate_folder: Path
    markdown_path: Path
    json_path: Path
    criteria_csv_path: Path
    latest_manifest_path: Path
    report: EvidenceDecisionGateReport


def _load_json(path: Path | None) -> dict:
    if path is None or not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _linked_json(manifest: dict, field: str) -> tuple[Path | None, dict]:
    value = manifest.get(field)
    path = Path(value) if value else None
    return path, _load_json(path)


def _limited_financials_count(clean_report: dict) -> int:
    limited = clean_report.get("subset_diagnostics", {}).get(
        "limited_financials",
        {},
    )
    return int(limited.get("sample_size") or 0)


def load_evidence_gate_inputs(
    *,
    outputs_root: Path,
    backtest_run_id: str,
) -> dict:
    """Load a readiness trial and its linked governance reports."""
    folder = Path(outputs_root) / "backtests" / str(backtest_run_id)
    manifest_path = folder / "backtest_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"Backtest manifest not found for run {backtest_run_id}: "
            f"{manifest_path}"
        )
    manifest = _load_json(manifest_path)
    if manifest.get("backtest_run_type") != "readiness_trial":
        raise ValueError(
            f"Backtest run {backtest_run_id} is not a readiness_trial."
        )
    report_fields = {
        "clean_coverage": "clean_coverage_sensitivity_report_json_path",
        "delayed_anchor": "delayed_anchor_impact_report_json_path",
        "outlier": "outlier_sensitivity_report_json_path",
        "decision": "readiness_trial_decision_report_json_path",
        "diagnostic": "readiness_trial_diagnostic_report_json_path",
    }
    source_reports = {}
    reports = {}
    missing_inputs = []
    for name, field in report_fields.items():
        path, payload = _linked_json(manifest, field)
        source_reports[name] = str(path) if path else None
        reports[name] = payload
        if not payload:
            missing_inputs.append(name)

    comparison_manifest_path = (
        Path(outputs_root)
        / "clean_coverage_comparisons"
        / "latest_clean_coverage_comparison_manifest.json"
    )
    comparison_manifest = _load_json(comparison_manifest_path)
    source_reports["clean_coverage_comparison"] = (
        str(comparison_manifest_path) if comparison_manifest else None
    )

    clean_report = reports["clean_coverage"]
    clean_subset = clean_report.get("subset_diagnostics", {}).get(
        "clean_records",
        {},
    )
    delayed_assessment = reports["delayed_anchor"].get(
        "impact_assessment",
        {},
    )
    outlier_assessment = reports["outlier"].get(
        "outlier_impact_assessment",
        {},
    )
    decision_report = reports["decision"]
    diagnostic_report = reports["diagnostic"]
    tickers = (
        diagnostic_report.get("evaluated_tickers")
        or decision_report.get("tickers_evaluated")
        or manifest.get("tickers")
        or []
    )
    sample_size = int(
        manifest.get("overall_sample_size")
        or manifest.get("evaluated_rows")
        or decision_report.get("sample_size")
        or 0
    )
    return {
        "backtest_run_id": str(
            manifest.get("backtest_run_id") or backtest_run_id
        ),
        "manifest_path": str(manifest_path),
        "source_reports": source_reports,
        "missing_inputs": missing_inputs,
        "sample_size": sample_size,
        "ticker_count": len(set(tickers)),
        "tickers": sorted(set(tickers)),
        "concentration_warning": bool(
            decision_report.get("concentration_warning")
            or diagnostic_report.get(
                "concentration_diagnostics",
                {},
            ).get("concentration_warning")
        ),
        "clean_record_count": int(
            manifest.get("clean_record_count")
            or clean_subset.get("sample_size")
            or 0
        ),
        "warning_record_count": int(
            manifest.get("warning_record_count") or 0
        ),
        "warning_heavy_record_count": int(
            manifest.get("warning_heavy_record_count") or 0
        ),
        "limited_financials_record_count": _limited_financials_count(
            clean_report
        ),
        "clean_only_available": bool(
            manifest.get("clean_only_available")
            or clean_subset.get("available")
        ),
        "clean_coverage_sensitivity_status": (
            manifest.get("clean_coverage_sensitivity_status")
            or clean_report.get("sensitivity_status")
        ),
        "clean_median_relative_return_12m": clean_subset.get(
            "median_relative_return_12m"
        ),
        "clean_hit_rate_vs_benchmark_12m": clean_subset.get(
            "hit_rate_vs_benchmark_12m"
        ),
        "delayed_anchor_impact_status": (
            delayed_assessment.get("impact_status")
            or manifest.get("delayed_anchor_impact_status")
        ),
        "delayed_anchor_materially_stronger": bool(
            delayed_assessment.get("delayed_anchor_materially_stronger")
            or manifest.get("delayed_anchor_materially_stronger")
        ),
        "no_delayed_anchor_positive": bool(
            delayed_assessment.get("no_delayed_anchor_positive")
            or manifest.get("no_delayed_anchor_positive")
        ),
        "outlier_dependence_status": (
            outlier_assessment.get("outlier_dependence_status")
            or manifest.get("outlier_dependence_status")
        ),
        "ex_nvda_positive": bool(
            outlier_assessment.get("ex_nvda_positive")
            or manifest.get("ex_nvda_positive")
        ),
        "ex_top_2_positive": bool(
            outlier_assessment.get("ex_top_2_positive")
            or manifest.get("ex_top_2_positive")
        ),
        "statistical_validity": (
            decision_report.get("statistical_validity")
            or manifest.get("statistical_validity")
        ),
        "decision_status": (
            decision_report.get("decision_status")
            or manifest.get("decision_status")
        ),
        "diagnostic_status": (
            diagnostic_report.get("diagnostic_status")
            or manifest.get("diagnostic_status")
        ),
        "comparison_status": comparison_manifest.get("comparison_status"),
    }


def find_latest_evidence_gate_backtest(outputs_root: Path) -> str:
    """Find the latest completed readiness trial with clean sensitivity."""
    root = Path(outputs_root) / "backtests"
    candidates = []
    for folder in root.iterdir() if root.is_dir() else []:
        manifest_path = folder / "backtest_manifest.json"
        if not manifest_path.is_file():
            continue
        try:
            manifest = _load_json(manifest_path)
        except (OSError, json.JSONDecodeError):
            continue
        if (
            manifest.get("backtest_run_type") == "readiness_trial"
            and manifest.get("status") == "completed"
            and manifest.get("clean_coverage_sensitivity_status")
        ):
            candidates.append(
                str(manifest.get("backtest_run_id") or folder.name)
            )
    if not candidates:
        raise ValueError(
            "No completed readiness trial with clean-coverage sensitivity "
            "was found."
        )
    return max(candidates)


def _criterion(
    name: str,
    status: str,
    evidence: dict,
    interpretation: str,
    *,
    critical: bool = True,
) -> EvidenceGateCriterion:
    return EvidenceGateCriterion(
        criterion=name,
        status=status,
        critical=critical,
        evidence=evidence,
        interpretation=interpretation,
    )


def evaluate_clean_evidence(summary: dict) -> list[EvidenceGateCriterion]:
    """Evaluate clean evidence availability and preliminary direction."""
    clean_count = int(summary.get("clean_record_count") or 0)
    available = bool(summary.get("clean_only_available"))
    sensitivity = summary.get("clean_coverage_sensitivity_status")
    availability_pass = (
        clean_count >= 5
        and available
        and sensitivity in {"clean_supported_preliminary", "clean_supported"}
    )
    median_relative = summary.get("clean_median_relative_return_12m")
    hit_rate = summary.get("clean_hit_rate_vs_benchmark_12m")
    positive = (
        median_relative is not None
        and hit_rate is not None
        and float(median_relative) > 0
        and float(hit_rate) >= 0.5
    )
    return [
        _criterion(
            "clean_evidence_available",
            "pass" if availability_pass else "block",
            {
                "clean_record_count": clean_count,
                "clean_only_available": available,
                "sensitivity_status": sensitivity,
            },
            (
                "At least five clean records support a preliminary research "
                "comparison."
                if availability_pass
                else "Clean evidence is not sufficient for this research gate."
            ),
        ),
        _criterion(
            "clean_evidence_positive",
            "pass" if positive else "block",
            {
                "median_relative_return_12m": median_relative,
                "hit_rate_vs_benchmark_12m": hit_rate,
            },
            (
                "The clean subset is positive on the gate's preliminary "
                "relative-median and hit-rate checks."
                if positive
                else "The clean subset does not pass the preliminary checks."
            ),
        ),
    ]


def evaluate_warning_evidence(summary: dict) -> list[EvidenceGateCriterion]:
    """Evaluate warning-heavy and limited-financials representation."""
    sample = int(summary.get("sample_size") or 0)
    heavy = int(summary.get("warning_heavy_record_count") or 0)
    limited = int(summary.get("limited_financials_record_count") or 0)

    def status_for(count: int) -> str:
        if count == 0:
            return "pass"
        if sample and count / sample >= 0.5:
            return "block"
        return "warn"

    return [
        _criterion(
            "warning_heavy_controlled",
            status_for(heavy),
            {
                "warning_heavy_record_count": heavy,
                "sample_size": sample,
                "share": round(heavy / sample, 6) if sample else None,
            },
            (
                "No warning-heavy records are in the evaluated sample."
                if heavy == 0
                else "Warning-heavy records remain visible in the sample."
            ),
        ),
        _criterion(
            "limited_financials_controlled",
            status_for(limited),
            {
                "limited_financials_record_count": limited,
                "sample_size": sample,
                "share": round(limited / sample, 6) if sample else None,
            },
            (
                "No limited-financials records are in the evaluated sample."
                if limited == 0
                else "Limited-financials records remain visible in the sample."
            ),
        ),
    ]


def evaluate_blockers(summary: dict) -> list[EvidenceGateCriterion]:
    """Evaluate delayed-anchor and outlier dependency cautions."""
    delayed_status = summary.get("delayed_anchor_impact_status")
    no_delayed_positive = bool(summary.get("no_delayed_anchor_positive"))
    delayed_block = (
        delayed_status not in {None, "delayed_anchor_not_present"}
        and not no_delayed_positive
    )
    delayed_warn = (
        delayed_status == "delayed_anchor_may_be_lifting_results"
        and no_delayed_positive
    )
    outlier_status = summary.get("outlier_dependence_status")
    ex_nvda_positive = bool(summary.get("ex_nvda_positive"))
    ex_top_2_positive = bool(summary.get("ex_top_2_positive"))
    outlier_block = not ex_nvda_positive or not ex_top_2_positive
    outlier_warn = (
        outlier_status == "nvda_lifts_average_but_result_survives"
        and ex_nvda_positive
        and ex_top_2_positive
    )
    return [
        _criterion(
            "delayed_anchor_not_blocking",
            "block" if delayed_block else ("warn" if delayed_warn else "pass"),
            {
                "impact_status": delayed_status,
                "delayed_anchor_materially_stronger": bool(
                    summary.get("delayed_anchor_materially_stronger")
                ),
                "no_delayed_anchor_positive": no_delayed_positive,
            },
            (
                "Non-delayed records are not positive, so anchor dependency "
                "blocks broader expansion."
                if delayed_block
                else (
                    "Delayed anchors may lift results, but non-delayed records "
                    "remain positive."
                    if delayed_warn
                    else "Delayed-anchor evidence does not create a blocker."
                )
            ),
        ),
        _criterion(
            "outlier_not_blocking",
            "block" if outlier_block else ("warn" if outlier_warn else "pass"),
            {
                "outlier_dependence_status": outlier_status,
                "ex_nvda_positive": ex_nvda_positive,
                "ex_top_2_positive": ex_top_2_positive,
            },
            (
                "Outlier-controlled subsets are not positive, so outlier "
                "dependency blocks broader expansion."
                if outlier_block
                else (
                    "NVDA lifts the average, but the ex-NVDA and ex-top-2 "
                    "subsets remain positive."
                    if outlier_warn
                    else "Outlier evidence does not create a blocker."
                )
            ),
        ),
    ]


def _context_criteria(summary: dict) -> list[EvidenceGateCriterion]:
    sample = int(summary.get("sample_size") or 0)
    if sample < 5:
        sample_status = "block"
    elif (
        sample < 30
        or summary.get("statistical_validity") == "limited_sample"
    ):
        sample_status = "warn"
    else:
        sample_status = "pass"
    ticker_count = int(summary.get("ticker_count") or 0)
    concentration_status = (
        "warn"
        if ticker_count < 10 or summary.get("concentration_warning")
        else "pass"
    )
    conservative = summary.get("decision_status") in {
        "needs_more_samples",
        "not_decision_grade",
        "diagnostic_only",
    }
    diagnostic = summary.get("diagnostic_status")
    diagnostic_status = (
        "pass"
        if diagnostic in {"promising_but_unproven", "diagnostic_only"}
        else "warn"
    )
    return [
        _criterion(
            "sample_size_limited",
            sample_status,
            {
                "sample_size": sample,
                "statistical_validity": summary.get("statistical_validity"),
            },
            (
                "The sample supports research-stage progression but remains "
                "limited."
                if sample_status == "warn"
                else "Sample-size requirements were evaluated."
            ),
            critical=False,
        ),
        _criterion(
            "concentration_limited",
            concentration_status,
            {
                "ticker_count": ticker_count,
                "concentration_warning": bool(
                    summary.get("concentration_warning")
                ),
            },
            (
                "The ticker universe remains concentrated and should be "
                "expanded."
                if concentration_status == "warn"
                else "Ticker concentration does not create a caution."
            ),
            critical=False,
        ),
        _criterion(
            "decision_conservatism_preserved",
            "pass" if conservative else "block",
            {"decision_status": summary.get("decision_status")},
            (
                "The existing decision remains conservative."
                if conservative
                else "The existing decision is not sufficiently conservative."
            ),
        ),
        _criterion(
            "diagnostic_promising",
            diagnostic_status,
            {"diagnostic_status": diagnostic},
            (
                "The diagnostic supports broader research while remaining "
                "unproven."
                if diagnostic_status == "pass"
                else "The diagnostic does not yet support broader research."
            ),
            critical=False,
        ),
    ]


def _gate_outcome(
    summary: dict,
    criteria: list[EvidenceGateCriterion],
) -> str:
    if summary.get("missing_inputs"):
        return "insufficient_inputs"
    by_name = {item.criterion: item.status for item in criteria}
    if by_name.get("sample_size_limited") == "block":
        return "insufficient_sample_for_gate"
    if by_name.get("clean_evidence_available") == "block":
        return "blocked_by_clean_evidence_absence"
    if by_name.get("clean_evidence_positive") == "block":
        return "continue_data_quality_repair"
    if by_name.get("warning_heavy_controlled") == "block":
        return "blocked_by_warning_heavy_evidence"
    if by_name.get("limited_financials_controlled") == "block":
        return "continue_data_quality_repair"
    if by_name.get("delayed_anchor_not_blocking") == "block":
        return "blocked_by_delayed_anchor_dependency"
    if by_name.get("outlier_not_blocking") == "block":
        return "blocked_by_outlier_dependency"
    if any(item.status == "block" for item in criteria):
        return "continue_data_quality_repair"
    return "research_ready_for_broader_trial"


def build_evidence_decision_gate(
    *,
    gate_run_id: str,
    generated_at: str,
    evidence_summary: dict,
) -> EvidenceDecisionGateReport:
    """Build the formal clean-versus-warning research gate."""
    summary = evidence_summary or {}
    criteria = [
        *evaluate_clean_evidence(summary),
        *evaluate_warning_evidence(summary),
        *evaluate_blockers(summary),
        *_context_criteria(summary),
    ]
    if summary.get("missing_inputs"):
        criteria.append(
            _criterion(
                "required_inputs_available",
                "block",
                {"missing_inputs": summary["missing_inputs"]},
                "Required source reports are missing.",
            )
        )
    outcome = _gate_outcome(summary, criteria)
    blockers = [
        item.interpretation for item in criteria if item.status == "block"
    ]
    warnings = [
        item.interpretation for item in criteria if item.status == "warn"
    ]
    gate_status = (
        "blocked"
        if blockers
        else ("pass_with_warnings" if warnings else "pass")
    )
    next_action = (
        "expand_ticker_universe_with_coverage_validation"
        if outcome == "research_ready_for_broader_trial"
        else "resolve_gate_blockers_before_expansion"
    )
    return EvidenceDecisionGateReport(
        gate_run_id=gate_run_id,
        generated_at=generated_at,
        source_backtest_run_id=summary.get("backtest_run_id"),
        source_backtest_manifest_path=summary.get("manifest_path"),
        source_reports=summary.get("source_reports", {}),
        gate_outcome=outcome,
        gate_status=gate_status,
        critical_pass_count=sum(
            item.critical and item.status == "pass" for item in criteria
        ),
        warn_count=sum(item.status == "warn" for item in criteria),
        block_count=sum(item.status == "block" for item in criteria),
        criteria_results=[item.to_dict() for item in criteria],
        evidence_summary=summary,
        blockers=blockers,
        warnings=warnings,
        next_research_action=next_action,
        limitations=[
            "This gate permits research-stage progression only.",
            "The sample and ticker universe remain limited.",
            "Delayed-anchor and outlier cautions remain applicable.",
            "Positive preliminary evidence is not strategy validation.",
        ],
    )


def _display(value: object) -> str:
    if value is None:
        return "Missing"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def render_evidence_decision_gate_report(
    report: EvidenceDecisionGateReport,
) -> str:
    """Render the gate report as Markdown."""
    evidence = report.evidence_summary
    main_finding = (
        "Clean evidence is preliminary but sufficient to expand the research "
        "sample while all existing cautions remain visible."
        if report.gate_outcome == "research_ready_for_broader_trial"
        else "One or more gate criteria require attention before expansion."
    )
    lines = [
        "# Clean vs Warning Evidence Decision Gate",
        "",
        "## Executive Summary",
        "",
        f"- Gate Outcome: {report.gate_outcome}",
        f"- Gate Status: {report.gate_status}",
        f"- Source Backtest Run: {report.source_backtest_run_id}",
        f"- Main Finding: {main_finding}",
        "",
        "## Evidence Summary",
        "",
        f"- Clean Records: {evidence.get('clean_record_count', 0)}",
        f"- Warning Records: {evidence.get('warning_record_count', 0)}",
        (
            "- Warning-Heavy Records: "
            f"{evidence.get('warning_heavy_record_count', 0)}"
        ),
        (
            "- Clean Subset Sample: "
            f"{evidence.get('clean_record_count', 0)}"
        ),
        (
            "- Clean Median Relative 12M: "
            f"{_display(evidence.get('clean_median_relative_return_12m'))}"
        ),
        (
            "- Clean Hit Rate 12M: "
            f"{_display(evidence.get('clean_hit_rate_vs_benchmark_12m'))}"
        ),
        (
            "- Delayed Anchor Status: "
            f"{evidence.get('delayed_anchor_impact_status')}"
        ),
        (
            "- Outlier Status: "
            f"{evidence.get('outlier_dependence_status')}"
        ),
        f"- Decision Status: {evidence.get('decision_status')}",
        f"- Diagnostic Status: {evidence.get('diagnostic_status')}",
        "",
        "## Gate Criteria",
        "",
        "| Criterion | Status | Evidence | Interpretation |",
        "|---|---|---|---|",
    ]
    for item in report.criteria_results:
        evidence_text = json.dumps(item["evidence"], sort_keys=True)
        lines.append(
            f"| {item['criterion']} | {item['status']} | "
            f"`{evidence_text}` | {item['interpretation']} |"
        )
    lines.extend(["", "## Blockers", ""])
    if report.blockers:
        lines.extend(f"- {item}" for item in report.blockers)
    else:
        lines.append("- No hard blockers detected for broader research expansion.")
    lines.extend(["", "## Warnings", ""])
    if report.warnings:
        lines.extend(f"- {item}" for item in report.warnings)
    else:
        lines.append("- No warn-only issues were detected.")
    lines.extend(
        [
            "",
            "## Gate Decision",
            "",
            f"- Outcome: {report.gate_outcome}",
            "- This is permission to expand the research sample only.",
            "- This is not validation.",
            "",
            "## Required Next Research Action",
            "",
            f"- Action Code: {report.next_research_action}",
            "",
            "## What This Suggests",
            "",
            "- Broader research testing is methodologically justified.",
            "- Clean evidence is preliminary but present.",
            "- The pipeline can separate clean and warning-bearing evidence.",
            "",
            "## What This Does Not Suggest",
            "",
            "- It does not prove a strategy.",
            "- It does not validate investor agents.",
            "- It does not create an investment recommendation.",
            "- It does not create a trade signal.",
            "- It does not justify allocation or rebalancing.",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in report.limitations)
    lines.extend(["", "## Safety Notice", "", report.safety_notice, ""])
    return "\n".join(lines)


def _allocate_gate_id(root: Path, timestamp: datetime) -> str:
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    candidate = base
    suffix = 2
    while (root / candidate).exists():
        candidate = f"{base}_{suffix:02d}"
        suffix += 1
    return candidate


def write_evidence_decision_gate_report(
    *,
    outputs_root: Path,
    backtest_run_id: str,
    generated_at: datetime | None = None,
) -> EvidenceDecisionGateFiles:
    """Load a readiness trial and persist an evidence gate bundle."""
    timestamp = generated_at or datetime.now(timezone.utc)
    root = Path(outputs_root) / "evidence_decision_gates"
    root.mkdir(parents=True, exist_ok=True)
    gate_run_id = _allocate_gate_id(root, timestamp)
    folder = root / gate_run_id
    folder.mkdir(parents=True, exist_ok=False)
    summary = load_evidence_gate_inputs(
        outputs_root=outputs_root,
        backtest_run_id=backtest_run_id,
    )
    report = build_evidence_decision_gate(
        gate_run_id=gate_run_id,
        generated_at=timestamp.isoformat(),
        evidence_summary=summary,
    )
    markdown_path = folder / "evidence_decision_gate_report.md"
    json_path = folder / "evidence_decision_gate_report.json"
    criteria_csv_path = folder / "evidence_decision_gate_criteria.csv"
    latest_manifest_path = (
        root / "latest_evidence_decision_gate_manifest.json"
    )
    markdown_path.write_text(
        render_evidence_decision_gate_report(report),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )
    with criteria_csv_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=CRITERIA_FIELDS)
        writer.writeheader()
        for item in report.criteria_results:
            writer.writerow(
                {
                    **item,
                    "evidence": json.dumps(
                        item["evidence"],
                        sort_keys=True,
                    ),
                }
            )
    latest_manifest = {
        "gate_run_id": gate_run_id,
        "source_backtest_run_id": report.source_backtest_run_id,
        "gate_outcome": report.gate_outcome,
        "gate_status": report.gate_status,
        "gate_folder": str(folder),
        "report_path": str(markdown_path),
        "report_json_path": str(json_path),
        "criteria_csv_path": str(criteria_csv_path),
        "generated_at": timestamp.isoformat(),
        "next_research_action": report.next_research_action,
        "safety_notice": SAFETY_NOTICE,
    }
    latest_manifest_path.write_text(
        json.dumps(latest_manifest, indent=2),
        encoding="utf-8",
    )
    return EvidenceDecisionGateFiles(
        gate_folder=folder,
        markdown_path=markdown_path,
        json_path=json_path,
        criteria_csv_path=criteria_csv_path,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
