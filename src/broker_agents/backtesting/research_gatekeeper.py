"""Research-only governance gate for evidence scorecards."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This research gatekeeper is a non-actionable governance control. It is "
    "not a recommendation, ranking, allocation instruction, rebalancing "
    "instruction, trade signal, execution instruction, strategy validation, "
    "or investment advice."
)
NEXT_RESEARCH_ACTION = "run_deeper_research_or_repair_before_progression"
REQUIRED_BEFORE_PROGRESSION = [
    "Deepen cohort attribution.",
    "Add dates or broaden the universe with coverage validation.",
    "Repair or reduce delayed-anchor exposure.",
    "Recheck outlier dependence.",
    "Recheck benchmark-relative evidence.",
    "Recheck walk-forward stability.",
    "Improve metadata diversity where possible.",
]
RULE_LABELS = {
    "scorecard_status_rule": "Scorecard Status",
    "classification_rule": "Evidence Classification",
    "research_decision_rule": "Research Decision",
    "benchmark_relative_rule": "Benchmark-Relative Evidence",
    "walk_forward_rule": "Walk-Forward Stability",
    "diagnostic_rule": "Diagnostic Status",
    "expanded_cohort_rule": "Expanded Cohort Effect",
    "period_sensitivity_rule": "Period Sensitivity",
    "outlier_dependence_rule": "Outlier Dependence",
    "delayed_anchor_rule": "Delayed Anchor Effect",
    "data_quality_integrity_rule": "Data Quality Integrity",
    "clean_evidence_rule": "Clean Evidence",
    "warning_heavy_rule": "Warning-Heavy Evidence",
    "blocker_factor_rule": "Blocker Factors",
    "progression_safety_rule": "Progression Safety",
}


@dataclass(frozen=True)
class GatekeeperRule:
    """One deterministic governance rule."""

    rule_code: str
    label: str
    status: str
    severity: str
    evidence: dict
    interpretation: str

    def to_dict(self) -> dict:
        """Return a JSON-ready rule row."""
        return asdict(self)


@dataclass(frozen=True)
class ResearchGatekeeperReport:
    """Governance verdict derived from one research evidence scorecard."""

    gatekeeper_run_id: str
    generated_at: str
    scorecard_run_id: str
    analysis_run_id: str
    expanded_trial_run_id: str
    backtest_run_id: str
    research_evidence_classification: str
    research_decision: str
    gatekeeper_status: str
    gatekeeper_decision: str
    progression_allowed: bool
    hold_bias: bool
    research_progression_status: str
    rule_results: list[dict]
    pass_rules: list[str]
    warning_rules: list[str]
    hold_rules: list[str]
    block_rules: list[str]
    main_gatekeeper_rationale: str
    required_before_progression: list[str]
    recommended_next_research_action: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class ResearchGatekeeperFiles:
    """Generated gatekeeper files and structured report."""

    gatekeeper_folder: Path
    markdown_path: Path
    json_path: Path
    rules_csv_path: Path
    latest_manifest_path: Path
    report: ResearchGatekeeperReport


def _load_json(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Research scorecard artifact not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_research_evidence_scorecard_manifest(
    *,
    outputs_root: Path,
    scorecard_run_id: str | None = None,
) -> dict:
    """Load one scorecard report or the latest scorecard manifest."""
    root = Path(outputs_root) / "research_evidence_scorecards"
    path = (
        root
        / str(scorecard_run_id)
        / "research_evidence_scorecard_report.json"
        if scorecard_run_id
        else root / "latest_research_evidence_scorecard_manifest.json"
    )
    payload = _load_json(path)
    payload["_manifest_path"] = str(path)
    return payload


def load_research_evidence_scorecard_report(
    *,
    outputs_root: Path,
    scorecard_run_id: str,
) -> dict:
    """Load the complete scorecard JSON for a selected run."""
    path = (
        Path(outputs_root)
        / "research_evidence_scorecards"
        / str(scorecard_run_id)
        / "research_evidence_scorecard_report.json"
    )
    return _load_json(path)


def _factor_map(scorecard: dict) -> dict[str, dict]:
    return {
        str(factor.get("factor_code")): factor
        for factor in scorecard.get("factor_results", [])
        if factor.get("factor_code")
    }


def _rule(
    code: str,
    status: str,
    severity: str,
    evidence: dict,
    interpretation: str,
) -> GatekeeperRule:
    return GatekeeperRule(
        rule_code=code,
        label=RULE_LABELS[code],
        status=status,
        severity=severity,
        evidence=evidence,
        interpretation=interpretation,
    )


def _factor_rule(
    *,
    code: str,
    factor: dict,
    negative_status: str = "hold",
) -> GatekeeperRule:
    factor_status = factor.get("status", "unavailable")
    mapping = {
        "strong_positive": ("pass", "info"),
        "positive": ("pass", "info"),
        "neutral": ("pass", "info"),
        "warning": ("warn", "caution"),
        "negative": (negative_status, "material"),
        "blocker": ("block", "critical"),
        "unavailable": ("unavailable", "caution"),
    }
    status, severity = mapping.get(
        str(factor_status), ("unavailable", "caution")
    )
    return _rule(
        code,
        status,
        severity,
        {
            "factor_status": factor_status,
            "factor_evidence": factor.get("evidence", {}),
        },
        factor.get("interpretation")
        or "The linked scorecard factor is unavailable.",
    )


def evaluate_gatekeeper_rules(scorecard: dict) -> list[GatekeeperRule]:
    """Evaluate the fixed governance rules against a scorecard."""
    factors = _factor_map(scorecard)
    scorecard_status = scorecard.get("scorecard_status")
    classification = scorecard.get("research_evidence_classification")
    research_decision = scorecard.get("research_decision")
    blocker_count = int(scorecard.get("blocker_count") or 0)

    if scorecard_status == "scorecard_completed":
        status_rule = ("pass", "info")
    elif scorecard_status == "scorecard_completed_with_warnings":
        status_rule = ("warn", "caution")
    elif scorecard_status:
        status_rule = ("block", "critical")
    else:
        status_rule = ("unavailable", "critical")

    if classification == "blocked_research_evidence":
        classification_rule = ("block", "critical")
    elif classification == "unstable_research_evidence":
        classification_rule = ("hold", "material")
    elif classification in {
        "weak_research_evidence",
        "preliminary_mixed_evidence",
    }:
        classification_rule = ("warn", "caution")
    elif classification:
        classification_rule = ("pass", "info")
    else:
        classification_rule = ("unavailable", "critical")

    if research_decision == "block_research_progression":
        decision_rule = ("block", "critical")
    elif research_decision == "hold_for_deeper_analysis":
        decision_rule = ("hold", "material")
    elif research_decision == "proceed_to_gatekeeper_with_warnings":
        decision_rule = ("warn", "caution")
    elif research_decision:
        decision_rule = ("pass", "info")
    else:
        decision_rule = ("unavailable", "critical")

    warning_factor = factors.get("warning_evidence_control", {})
    warning_heavy = int(
        warning_factor.get("evidence", {}).get(
            "warning_heavy_record_count", 0
        )
        or 0
    )
    if warning_heavy == 0:
        warning_rule = ("pass", "info")
    else:
        warning_rule = ("hold", "material")

    if blocker_count:
        blocker_rule = ("block", "critical")
    else:
        blocker_rule = ("pass", "info")

    if blocker_count or classification == "blocked_research_evidence":
        progression_rule = ("block", "critical")
    elif (
        classification == "unstable_research_evidence"
        or research_decision == "hold_for_deeper_analysis"
    ):
        progression_rule = ("hold", "material")
    elif scorecard_status == "scorecard_completed_with_warnings":
        progression_rule = ("warn", "caution")
    else:
        progression_rule = ("pass", "info")

    return [
        _rule(
            "scorecard_status_rule",
            *status_rule,
            {"scorecard_status": scorecard_status},
            (
                "The scorecard completed with warnings that must remain "
                "visible in the governance verdict."
            ),
        ),
        _rule(
            "classification_rule",
            *classification_rule,
            {"research_evidence_classification": classification},
            "Unstable research evidence requires a hold.",
        ),
        _rule(
            "research_decision_rule",
            *decision_rule,
            {"research_decision": research_decision},
            "The scorecard explicitly calls for deeper analysis.",
        ),
        _factor_rule(
            code="benchmark_relative_rule",
            factor=factors.get("benchmark_relative_performance", {}),
        ),
        _factor_rule(
            code="walk_forward_rule",
            factor=factors.get("walk_forward_stability", {}),
        ),
        _factor_rule(
            code="diagnostic_rule",
            factor=factors.get("diagnostic_status", {}),
        ),
        _factor_rule(
            code="expanded_cohort_rule",
            factor=factors.get("expanded_cohort_effect", {}),
        ),
        _factor_rule(
            code="period_sensitivity_rule",
            factor=factors.get("period_sensitivity", {}),
        ),
        _factor_rule(
            code="outlier_dependence_rule",
            factor=factors.get("outlier_dependence", {}),
        ),
        _factor_rule(
            code="delayed_anchor_rule",
            factor=factors.get("delayed_anchor_effect", {}),
        ),
        _factor_rule(
            code="data_quality_integrity_rule",
            factor=factors.get("data_quality_integrity", {}),
        ),
        _factor_rule(
            code="clean_evidence_rule",
            factor=factors.get("clean_evidence_strength", {}),
        ),
        _rule(
            "warning_heavy_rule",
            *warning_rule,
            {"warning_heavy_record_count": warning_heavy},
            (
                "No warning-heavy records are present."
                if warning_heavy == 0
                else "Warning-heavy evidence requires a research hold."
            ),
        ),
        _rule(
            "blocker_factor_rule",
            *blocker_rule,
            {"blocker_count": blocker_count},
            (
                "No scorecard blocker factors are present."
                if blocker_count == 0
                else "Scorecard blocker factors prevent progression."
            ),
        ),
        _rule(
            "progression_safety_rule",
            *progression_rule,
            {
                "research_evidence_classification": classification,
                "research_decision": research_decision,
                "blocker_count": blocker_count,
            },
            (
                "Progression is held because unstable evidence outweighs "
                "successful execution and data-quality controls."
            ),
        ),
    ]


def classify_gatekeeper_decision(
    scorecard: dict,
    rules: list[GatekeeperRule],
) -> str:
    """Return the conservative governance decision."""
    if any(
        rule.status == "block" and rule.severity == "critical"
        for rule in rules
    ):
        return "block"
    if (
        scorecard.get("research_evidence_classification")
        == "unstable_research_evidence"
        or scorecard.get("research_decision") == "hold_for_deeper_analysis"
        or any(rule.status == "hold" for rule in rules)
    ):
        return "hold"
    if any(rule.status == "warn" for rule in rules):
        return "proceed_with_warnings"
    return "proceed"


def run_research_gatekeeper(
    *,
    gatekeeper_run_id: str,
    generated_at: str,
    scorecard: dict,
) -> ResearchGatekeeperReport:
    """Convert one evidence scorecard into a governance verdict."""
    rules = evaluate_gatekeeper_rules(scorecard)
    decision = classify_gatekeeper_decision(scorecard, rules)
    grouped = {
        status: [
            rule.rule_code for rule in rules if rule.status == status
        ]
        for status in ("pass", "warn", "hold", "block")
    }
    if decision == "block":
        gatekeeper_status = "completed_with_block"
        progression_status = "blocked_from_research_progression"
    elif decision == "hold":
        gatekeeper_status = "completed_with_hold"
        progression_status = "held_for_deeper_research"
    elif decision == "proceed_with_warnings":
        gatekeeper_status = "completed_with_warnings"
        progression_status = "research_progression_allowed_with_warnings"
    else:
        gatekeeper_status = "completed"
        progression_status = "research_progression_allowed"
    return ResearchGatekeeperReport(
        gatekeeper_run_id=gatekeeper_run_id,
        generated_at=generated_at,
        scorecard_run_id=str(scorecard.get("scorecard_run_id") or ""),
        analysis_run_id=str(scorecard.get("analysis_run_id") or ""),
        expanded_trial_run_id=str(
            scorecard.get("expanded_trial_run_id") or ""
        ),
        backtest_run_id=str(scorecard.get("backtest_run_id") or ""),
        research_evidence_classification=str(
            scorecard.get("research_evidence_classification") or ""
        ),
        research_decision=str(scorecard.get("research_decision") or ""),
        gatekeeper_status=gatekeeper_status,
        gatekeeper_decision=decision,
        progression_allowed=decision in {"proceed", "proceed_with_warnings"},
        hold_bias=decision == "hold",
        research_progression_status=progression_status,
        rule_results=[rule.to_dict() for rule in rules],
        pass_rules=grouped["pass"],
        warning_rules=grouped["warn"],
        hold_rules=grouped["hold"],
        block_rules=grouped["block"],
        main_gatekeeper_rationale=(
            "Execution and data-quality integrity are sound, but negative "
            "benchmark-relative evidence, unstable walk-forward results, "
            "cohort weakness, period sensitivity, and sensitivity controls "
            "require deeper research before progression."
        ),
        required_before_progression=REQUIRED_BEFORE_PROGRESSION,
        recommended_next_research_action=NEXT_RESEARCH_ACTION,
    )


def render_research_gatekeeper_report(
    report: ResearchGatekeeperReport,
) -> str:
    """Render a conservative Markdown governance report."""
    data = report.to_dict()
    lines = [
        "# Research Gatekeeper Report",
        "",
        "## Executive Summary",
        "",
        f"- Gatekeeper Run ID: {data['gatekeeper_run_id']}",
        f"- Scorecard Run ID: {data['scorecard_run_id']}",
        (
            "- Research Evidence Classification: "
            f"{data['research_evidence_classification']}"
        ),
        f"- Research Decision: {data['research_decision']}",
        f"- Gatekeeper Decision: {data['gatekeeper_decision']}",
        f"- Progression Allowed: {str(data['progression_allowed']).lower()}",
        f"- Hold Bias: {str(data['hold_bias']).lower()}",
        f"- Main Rationale: {data['main_gatekeeper_rationale']}",
        (
            "- Next Research Action: "
            f"{data['recommended_next_research_action']}"
        ),
        "",
        "## Gatekeeper Verdict",
        "",
        f"- Decision: {data['gatekeeper_decision']}",
        f"- Progression Allowed: {str(data['progression_allowed']).lower()}",
        "- Why: Expanded evidence is unstable and requires deeper research.",
        "",
        "## Rule Results",
        "",
        "| Rule | Status | Severity | Evidence | Interpretation |",
        "|---|---|---|---|---|",
    ]
    for rule in data["rule_results"]:
        evidence = json.dumps(rule["evidence"], sort_keys=True).replace(
            "|", "/"
        )
        lines.append(
            f"| {rule['label']} | {rule['status']} | {rule['severity']} | "
            f"{evidence} | {rule['interpretation']} |"
        )
    lines.extend(["", "## Passing Evidence", ""])
    lines.extend(
        [
            "- Data-quality integrity passed.",
            "- Clean evidence is available.",
            "- No warning-heavy records are present.",
            "- No blocker factors are present.",
            "- Expanded trial execution succeeded.",
            "",
            "## Holding Evidence",
            "",
            "- Evidence classification is unstable_research_evidence.",
            "- Research decision is hold_for_deeper_analysis.",
            "- Benchmark-relative evidence is negative.",
            "- Walk-forward stability is unstable.",
            "- The expanded cohort weakened the prior core result.",
            "- Period, outlier, and delayed-anchor sensitivity remain material.",
            "",
            "## Required Before Progression",
            "",
        ]
    )
    lines.extend(
        f"- {item}" for item in data["required_before_progression"]
    )
    lines.extend(
        [
            "",
            "## Relationship to Scorecard",
            "",
            (
                "The scorecard classified the evidence as "
                "`unstable_research_evidence`. The gatekeeper converts that "
                "classification into a hold and prevents premature progression."
            ),
            "",
            "## What This Suggests",
            "",
            "- The research system is functioning conservatively.",
            (
                "- Positive execution quality does not override unstable "
                "research evidence."
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


def write_research_gatekeeper_report(
    *,
    outputs_root: Path,
    scorecard_run_id: str | None = None,
    generated_at: datetime | None = None,
) -> ResearchGatekeeperFiles:
    """Load a scorecard and write all gatekeeper artifacts."""
    outputs_root = Path(outputs_root)
    timestamp = generated_at or datetime.now(timezone.utc)
    manifest = load_research_evidence_scorecard_manifest(
        outputs_root=outputs_root,
        scorecard_run_id=scorecard_run_id,
    )
    selected_id = str(
        scorecard_run_id or manifest.get("scorecard_run_id") or ""
    )
    if not selected_id:
        raise ValueError("Scorecard run ID is required.")
    scorecard = (
        manifest
        if scorecard_run_id
        else load_research_evidence_scorecard_report(
            outputs_root=outputs_root,
            scorecard_run_id=selected_id,
        )
    )

    root = outputs_root / "research_gatekeepers"
    root.mkdir(parents=True, exist_ok=True)
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    run_id = base
    suffix = 2
    while (root / run_id).exists():
        run_id = f"{base}_{suffix:02d}"
        suffix += 1
    report = run_research_gatekeeper(
        gatekeeper_run_id=run_id,
        generated_at=timestamp.isoformat(),
        scorecard=scorecard,
    )
    folder = root / run_id
    folder.mkdir(parents=True, exist_ok=False)
    markdown_path = folder / "research_gatekeeper_report.md"
    json_path = folder / "research_gatekeeper_report.json"
    rules_path = folder / "research_gatekeeper_rules.csv"
    markdown_path.write_text(
        render_research_gatekeeper_report(report),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )
    with rules_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "rule_code",
                "label",
                "status",
                "severity",
                "evidence",
                "interpretation",
            ),
        )
        writer.writeheader()
        for rule in report.rule_results:
            writer.writerow(
                {
                    **rule,
                    "evidence": json.dumps(
                        rule["evidence"], sort_keys=True
                    ),
                }
            )
    latest_path = root / "latest_research_gatekeeper_manifest.json"
    latest_path.write_text(
        json.dumps(
            {
                "gatekeeper_run_id": report.gatekeeper_run_id,
                "scorecard_run_id": report.scorecard_run_id,
                "analysis_run_id": report.analysis_run_id,
                "expanded_trial_run_id": report.expanded_trial_run_id,
                "backtest_run_id": report.backtest_run_id,
                "gatekeeper_status": report.gatekeeper_status,
                "gatekeeper_decision": report.gatekeeper_decision,
                "progression_allowed": report.progression_allowed,
                "hold_bias": report.hold_bias,
                "research_progression_status": (
                    report.research_progression_status
                ),
                "recommended_next_research_action": (
                    report.recommended_next_research_action
                ),
                "gatekeeper_folder": str(folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "rules_csv_path": str(rules_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return ResearchGatekeeperFiles(
        gatekeeper_folder=folder,
        markdown_path=markdown_path,
        json_path=json_path,
        rules_csv_path=rules_path,
        latest_manifest_path=latest_path,
        report=report,
    )
