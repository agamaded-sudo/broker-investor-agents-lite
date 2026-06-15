"""Backoffice repair attribution for held research evidence."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "Backoffice only repairs, enriches, documents, and packages research "
    "evidence. It does not override governance, make investment decisions, "
    "rank securities or personas, create consensus, allocate capital, produce "
    "trade signals, or issue execution instructions."
)
NEXT_RESEARCH_ACTION = "execute_backoffice_repair_work_orders"
ALL_PERSONAS = [
    "Buffett Agent",
    "Munger Agent",
    "Fisher Agent",
    "Lynch Agent",
    "Bogle Agent",
]


@dataclass(frozen=True)
class EvidenceIssue:
    """One research evidence issue assigned to Backoffice."""

    issue_code: str
    issue_label: str
    severity: str
    source_layer: str
    source_evidence: dict
    affected_personas: list[str]
    backoffice_work_type: str
    recommended_action: str
    expected_output: str
    priority: str
    safety_note: str = (
        "Research evidence repair only; no investment judgment is produced."
    )

    def to_dict(self) -> dict:
        """Return a JSON-ready issue row."""
        return asdict(self)


@dataclass(frozen=True)
class BackofficeWorkOrder:
    """One concrete Backoffice repair or packaging work order."""

    work_order_id: str
    title: str
    priority: str
    status: str
    related_issue_codes: list[str]
    objective: str
    inputs_needed: list[str]
    proposed_steps: list[str]
    expected_artifacts: list[str]
    completion_criteria: list[str]
    safety_boundary: str = (
        "Evidence-quality work only; Gatekeeper must be rerun before progression."
    )

    def to_dict(self) -> dict:
        """Return a JSON-ready work-order row."""
        return asdict(self)


@dataclass(frozen=True)
class BackofficeEvidenceQualityReport:
    """Backoffice repair plan linked to a persona attribution."""

    backoffice_attribution_run_id: str
    generated_at: str
    investor_persona_attribution_run_id: str
    gatekeeper_run_id: str
    scorecard_run_id: str
    analysis_run_id: str
    expanded_trial_run_id: str
    backtest_run_id: str
    gatekeeper_decision: str
    progression_allowed: bool
    attribution_status: str
    evidence_issues: list[dict]
    work_orders: list[dict]
    backoffice_attribution_summary: dict
    main_backoffice_finding: str
    recommended_next_research_action: str
    limitations: list[str]
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class BackofficeEvidenceQualityFiles:
    """Generated Backoffice attribution files and report."""

    attribution_folder: Path
    markdown_path: Path
    json_path: Path
    issues_csv_path: Path
    work_orders_csv_path: Path
    latest_manifest_path: Path
    report: BackofficeEvidenceQualityReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_investor_persona_attribution_manifest(
    *,
    outputs_root: Path,
    attribution_run_id: str | None = None,
) -> dict:
    """Load one persona report or the latest persona manifest."""
    root = Path(outputs_root) / "investor_persona_attributions"
    path = (
        root
        / str(attribution_run_id)
        / "investor_persona_attribution_report.json"
        if attribution_run_id
        else root / "latest_investor_persona_attribution_manifest.json"
    )
    payload = _load_required_json(path, "Investor persona attribution manifest")
    payload["_manifest_path"] = str(path)
    return payload


def load_investor_persona_attribution_report(
    *,
    outputs_root: Path,
    attribution_run_id: str,
) -> dict:
    """Load the complete persona attribution report."""
    path = (
        Path(outputs_root)
        / "investor_persona_attributions"
        / str(attribution_run_id)
        / "investor_persona_attribution_report.json"
    )
    return _load_required_json(path, "Investor persona attribution report")


def load_research_gatekeeper_report(
    *, outputs_root: Path, gatekeeper_run_id: str
) -> dict:
    """Load linked gatekeeper context."""
    return _load_optional_json(
        Path(outputs_root)
        / "research_gatekeepers"
        / str(gatekeeper_run_id)
        / "research_gatekeeper_report.json"
    )


def load_research_evidence_scorecard_report(
    *, outputs_root: Path, scorecard_run_id: str
) -> dict:
    """Load linked scorecard context."""
    return _load_optional_json(
        Path(outputs_root)
        / "research_evidence_scorecards"
        / str(scorecard_run_id)
        / "research_evidence_scorecard_report.json"
    )


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


def _factor_map(scorecard: dict) -> dict[str, dict]:
    return {
        str(item.get("factor_code")): item
        for item in scorecard.get("factor_results", [])
        if item.get("factor_code")
    }


def _issue(
    code: str,
    label: str,
    severity: str,
    source_layer: str,
    source_evidence: dict,
    personas: list[str],
    work_type: str,
    action: str,
    output: str,
    priority: str,
) -> EvidenceIssue:
    return EvidenceIssue(
        issue_code=code,
        issue_label=label,
        severity=severity,
        source_layer=source_layer,
        source_evidence=source_evidence,
        affected_personas=personas,
        backoffice_work_type=work_type,
        recommended_action=action,
        expected_output=output,
        priority=priority,
    )


def attribute_evidence_issues_to_backoffice_work(
    *,
    persona_report: dict,
    gatekeeper: dict,
    scorecard: dict,
    analysis: dict,
) -> list[EvidenceIssue]:
    """Translate held evidence into twelve Backoffice issue categories."""
    factors = _factor_map(scorecard)
    persona_needs = persona_report.get("cross_persona_summary", {}).get(
        "persona_specific_evidence_needs", {}
    )
    metadata = analysis.get("metadata_diversity_recheck", {})
    common = [
        "Buffett Agent",
        "Munger Agent",
        "Lynch Agent",
        "Bogle Agent",
    ]
    return [
        _issue(
            "benchmark_relative_underperformance",
            "Benchmark-Relative Underperformance",
            "high",
            "research_evidence_scorecard",
            factors.get("benchmark_relative_performance", {}),
            [*common, "Fisher Agent"],
            "attribution_analysis",
            "Decompose relative outcomes by ticker, date, cohort, and sector.",
            "Benchmark-relative driver decomposition.",
            "P0",
        ),
        _issue(
            "walk_forward_instability",
            "Walk-Forward Instability",
            "high",
            "research_evidence_scorecard",
            factors.get("walk_forward_stability", {}),
            list(common),
            "robustness_retest",
            "Identify unstable periods and specify additional controls.",
            "Walk-forward stability repair plan.",
            "P0",
        ),
        _issue(
            "expanded_cohort_underperformance",
            "Expanded Cohort Underperformance",
            "high",
            "expanded_trial_analysis",
            factors.get("expanded_cohort_effect", {}),
            ALL_PERSONAS,
            "attribution_analysis",
            "Separate current-core and expanded-cohort drivers.",
            "Expanded cohort attribution table and narrative.",
            "P0",
        ),
        _issue(
            "period_sensitivity",
            "Period Sensitivity",
            "high",
            "expanded_trial_analysis",
            factors.get("period_sensitivity", {}),
            list(common),
            "robustness_retest",
            "Map supportive and negative periods and required date coverage.",
            "Period sensitivity matrix and retest specification.",
            "P1",
        ),
        _issue(
            "outlier_dependence",
            "Outlier Dependence",
            "high",
            "research_evidence_scorecard",
            factors.get("outlier_dependence", {}),
            ["Munger Agent", "Buffett Agent", "Bogle Agent", "Lynch Agent"],
            "robustness_retest",
            "Recheck ex-NVDA and top-contributor exclusions.",
            "Outlier-controlled sensitivity evidence.",
            "P0",
        ),
        _issue(
            "delayed_anchor_effect",
            "Delayed Anchor Effect",
            "moderate",
            "research_evidence_scorecard",
            factors.get("delayed_anchor_effect", {}),
            ALL_PERSONAS,
            "data_repair",
            "Separate or repair delayed-anchor exposure before retesting.",
            "Clean-anchor coverage and non-delayed sensitivity report.",
            "P1",
        ),
        _issue(
            "metadata_diversity_partial_concentration",
            "Metadata Diversity Partial Concentration",
            "moderate",
            "expanded_trial_analysis",
            metadata,
            ALL_PERSONAS,
            "metadata_recheck",
            "Recheck metadata coverage and document unavoidable concentration.",
            "Metadata diversity recheck report.",
            "P2",
        ),
        _issue(
            "investor_interest_low_diversity",
            "Investor Interest Low Diversity",
            "moderate",
            "expanded_trial_analysis",
            {"low_diversity_fields": metadata.get("low_diversity_fields", [])},
            ALL_PERSONAS,
            "persona_specific_packaging",
            "Improve structured coverage without fabricating persona values.",
            "Investor-interest metadata availability matrix.",
            "P2",
        ),
        _issue(
            "persona_specific_evidence_gaps",
            "Persona-Specific Evidence Gaps",
            "high",
            "investor_persona_attribution",
            {"persona_specific_evidence_needs": persona_needs},
            list(persona_needs) or ALL_PERSONAS,
            "persona_specific_packaging",
            "Create separate evidence requirements for each persona.",
            "Five independent persona evidence requirement packs.",
            "P1",
        ),
        _issue(
            "qualitative_depth_gaps",
            "Qualitative Depth Gaps",
            "moderate",
            "investor_persona_attribution",
            {
                name: persona_needs.get(name, [])
                for name in (
                    "Buffett Agent",
                    "Munger Agent",
                    "Fisher Agent",
                    "Lynch Agent",
                )
            },
            ["Buffett Agent", "Munger Agent", "Fisher Agent", "Lynch Agent"],
            "qualitative_packaging",
            "Enrich quality, management, growth, moat, and risk evidence.",
            "Persona-specific qualitative evidence packs.",
            "P2",
        ),
        _issue(
            "index_comparison_gap",
            "Index Comparison Gap",
            "high",
            "investor_persona_attribution",
            {"Bogle Agent": persona_needs.get("Bogle Agent", [])},
            ["Bogle Agent"],
            "evidence_enrichment",
            "Prepare benchmark, index-overlap, and concentration comparisons.",
            "Bogle benchmark and index comparison pack.",
            "P1",
        ),
        _issue(
            "documentation_and_audit_trail",
            "Documentation and Audit Trail",
            "low",
            "research_governance_chain",
            {
                "persona_attribution_run_id": persona_report.get(
                    "attribution_run_id"
                ),
                "gatekeeper_run_id": gatekeeper.get("gatekeeper_run_id"),
                "scorecard_run_id": scorecard.get("scorecard_run_id"),
                "analysis_run_id": analysis.get("analysis_run_id"),
            },
            ["Backoffice/System Governance"],
            "documentation_only",
            "Bundle linked artifacts, provenance, and safety notices.",
            "Research audit trail bundle.",
            "P3",
        ),
    ]


def _work_order_templates() -> list[dict]:
    return [
        {
            "id": "BO-001",
            "title": "Backtest Driver Decomposition",
            "priority": "P0",
            "issues": [
                "benchmark_relative_underperformance",
                "expanded_cohort_underperformance",
            ],
            "objective": (
                "Explain benchmark underperformance and expanded-cohort "
                "weakening by ticker, date, cohort, and sector."
            ),
            "inputs": [
                "Expanded trial analysis",
                "Backtest results",
                "Ticker and cohort metadata",
            ],
            "steps": [
                "Reconcile ticker, date, cohort, and sector contributions.",
                "Separate absolute and benchmark-relative effects.",
                "Document negative and mixed driver groups.",
            ],
            "artifacts": [
                "backtest_driver_decomposition.json",
                "backtest_driver_decomposition.md",
            ],
            "criteria": [
                "All 60 evaluated rows reconcile to grouped totals.",
                "Core-versus-expanded cohort differences are explicit.",
            ],
        },
        {
            "id": "BO-002",
            "title": "Outlier and Ex-NVDA Repair Path",
            "priority": "P0",
            "issues": ["outlier_dependence"],
            "objective": (
                "Recheck whether evidence survives without NVDA and the largest "
                "contributors, and identify the source of dependence."
            ),
            "inputs": ["Outlier sensitivity report", "Backtest results"],
            "steps": [
                "Reproduce ex-NVDA and top-outlier subsets.",
                "Attribute median and hit-rate changes.",
                "Specify an outlier-controlled rerun.",
            ],
            "artifacts": ["outlier_repair_path.md", "outlier_retest_spec.json"],
            "criteria": [
                "Ex-NVDA and ex-top-2 outcomes are reproducible.",
                "Dependence is assigned to ticker, date, or cohort composition.",
            ],
        },
        {
            "id": "BO-003",
            "title": "Walk-Forward Stability Repair Plan",
            "priority": "P0",
            "issues": ["walk_forward_instability", "period_sensitivity"],
            "objective": (
                "Identify periods that break stability and define additional "
                "dates or controls required for a meaningful rerun."
            ),
            "inputs": ["Walk-forward outputs", "Date attribution"],
            "steps": [
                "Map period-level failures.",
                "Check date and cohort composition.",
                "Define expanded date and control requirements.",
            ],
            "artifacts": ["walk_forward_repair_plan.md"],
            "criteria": [
                "Every unstable period has a documented driver.",
                "Rerun requirements contain no fabricated coverage.",
            ],
        },
        {
            "id": "BO-004",
            "title": "Delayed Anchor Exposure Repair",
            "priority": "P1",
            "issues": ["delayed_anchor_effect"],
            "objective": (
                "Reduce or separate delayed-anchor records and reevaluate "
                "clean, non-delayed evidence."
            ),
            "inputs": ["Delayed-anchor impact report", "Price fixtures"],
            "steps": [
                "Identify delayed ticker-date anchors.",
                "Add exact local coverage where legitimate.",
                "Specify non-delayed-only comparison.",
            ],
            "artifacts": ["delayed_anchor_repair_report.md"],
            "criteria": [
                "Delayed records are explicit and separable.",
                "No future price information is introduced.",
            ],
        },
        {
            "id": "BO-005",
            "title": "Metadata Diversity Recheck",
            "priority": "P2",
            "issues": [
                "metadata_diversity_partial_concentration",
                "investor_interest_low_diversity",
            ],
            "objective": (
                "Improve or document low-diversity metadata fields without "
                "fabricating values."
            ),
            "inputs": ["Trial ledger", "Local structured run artifacts"],
            "steps": [
                "Audit field availability by ticker and date.",
                "Recover values from structured local artifacts.",
                "Document fields that remain invariant or unavailable.",
            ],
            "artifacts": ["metadata_diversity_recheck.md", "metadata_matrix.csv"],
            "criteria": [
                "All missing and invariant fields are explicit.",
                "No inferred persona values are introduced.",
            ],
        },
        {
            "id": "BO-006",
            "title": "Persona-Specific Evidence Pack Requirements",
            "priority": "P1",
            "issues": ["persona_specific_evidence_gaps"],
            "objective": (
                "Prepare distinct evidence requirements for all five personas."
            ),
            "inputs": ["Investor persona attribution report"],
            "steps": [
                "Preserve persona independence.",
                "Map each need to a local evidence source or explicit gap.",
                "Create separate completion checklists.",
            ],
            "artifacts": ["persona_evidence_pack_requirements.md"],
            "criteria": [
                "All five personas have distinct requirements.",
                "No decision, ranking, vote, or consensus field is present.",
            ],
        },
        {
            "id": "BO-007",
            "title": "Bogle Benchmark / Index Comparison Pack",
            "priority": "P1",
            "issues": [
                "index_comparison_gap",
                "benchmark_relative_underperformance",
            ],
            "objective": (
                "Clarify active-selection evidence versus broad index exposure."
            ),
            "inputs": [
                "Benchmark-relative metrics",
                "Index overlap evidence",
                "Concentration evidence",
            ],
            "steps": [
                "Reconcile benchmark-relative outcomes.",
                "Update index overlap and concentration summaries.",
                "Document the simplest comparison baseline.",
            ],
            "artifacts": ["bogle_index_comparison_pack.md"],
            "criteria": [
                "Benchmark and index definitions are explicit.",
                "The pack remains descriptive and non-actionable.",
            ],
        },
        {
            "id": "BO-008",
            "title": "Fisher Qualitative Growth Evidence Pack",
            "priority": "P2",
            "issues": ["qualitative_depth_gaps"],
            "objective": (
                "Collect product, customer, management, and growth-runway "
                "evidence requirements."
            ),
            "inputs": ["Fisher persona needs", "Local company evidence packs"],
            "steps": [
                "Inventory product and pipeline evidence.",
                "Inventory management and customer indicators.",
                "Document unsupported qualitative claims.",
            ],
            "artifacts": ["fisher_qualitative_growth_requirements.md"],
            "criteria": [
                "Growth, management, customer, and competitive fields are covered.",
                "Unknowns remain explicit.",
            ],
        },
        {
            "id": "BO-009",
            "title": "Buffett/Munger Quality and Risk Pack",
            "priority": "P2",
            "issues": ["qualitative_depth_gaps", "outlier_dependence"],
            "objective": (
                "Collect owner earnings, valuation history, moat, incentives, "
                "capital allocation, and inversion risks."
            ),
            "inputs": [
                "Buffett and Munger persona needs",
                "Valuation and owner earnings artifacts",
            ],
            "steps": [
                "Refresh owner earnings and valuation history.",
                "Document moat, incentives, and capital allocation.",
                "Prepare inversion and failure-mode checklists.",
            ],
            "artifacts": ["buffett_munger_quality_risk_pack.md"],
            "criteria": [
                "Quality and risk evidence is sourced and dated.",
                "Valuation uncertainty remains explicit.",
            ],
        },
        {
            "id": "BO-010",
            "title": "Research Audit Trail Bundle",
            "priority": "P3",
            "issues": ["documentation_and_audit_trail"],
            "objective": "Bundle Task 103 through Task 108 artifacts and safety notices.",
            "inputs": ["Linked manifests and reports"],
            "steps": [
                "Collect artifact paths and run IDs.",
                "Verify provenance links.",
                "Bundle safety boundaries and next actions.",
            ],
            "artifacts": ["research_audit_trail_manifest.json"],
            "criteria": [
                "All linked run IDs resolve locally.",
                "The bundle records no changed source evidence.",
            ],
            "status": "documentation_only",
        },
    ]


def build_backoffice_work_orders() -> list[BackofficeWorkOrder]:
    """Build the fixed ten-work-order Backoffice repair queue."""
    return [
        BackofficeWorkOrder(
            work_order_id=item["id"],
            title=item["title"],
            priority=item["priority"],
            status=item.get("status", "ready_to_execute"),
            related_issue_codes=item["issues"],
            objective=item["objective"],
            inputs_needed=item["inputs"],
            proposed_steps=item["steps"],
            expected_artifacts=item["artifacts"],
            completion_criteria=item["criteria"],
        )
        for item in _work_order_templates()
    ]


def build_backoffice_evidence_quality_attribution(
    *,
    backoffice_attribution_run_id: str,
    generated_at: str,
    persona_report: dict,
    gatekeeper: dict,
    scorecard: dict,
    analysis: dict,
) -> BackofficeEvidenceQualityReport:
    """Build the held-evidence repair and enrichment plan."""
    issues = attribute_evidence_issues_to_backoffice_work(
        persona_report=persona_report,
        gatekeeper=gatekeeper,
        scorecard=scorecard,
        analysis=analysis,
    )
    orders = build_backoffice_work_orders()
    priority_counts = {
        priority: sum(issue.priority == priority for issue in issues)
        for priority in ("P0", "P1", "P2", "P3")
    }
    status_counts = {
        status: sum(order.status == status for order in orders)
        for status in ("ready_to_execute", "blocked", "documentation_only")
    }
    progression_allowed = bool(persona_report.get("progression_allowed"))
    summary = {
        "total_issues": len(issues),
        "p0_issues": priority_counts["P0"],
        "p1_issues": priority_counts["P1"],
        "p2_issues": priority_counts["P2"],
        "p3_issues": priority_counts["P3"],
        "total_work_orders": len(orders),
        "ready_to_execute_work_orders": status_counts["ready_to_execute"],
        "blocked_work_orders": status_counts["blocked"],
        "documentation_only_work_orders": status_counts[
            "documentation_only"
        ],
        "main_backoffice_finding": (
            "The evidence chain is operationally sound, but robustness, "
            "benchmark-relative attribution, anchor quality, metadata diversity, "
            "and persona-specific evidence packs require repair before re-gating."
        ),
        "recommended_next_research_action": NEXT_RESEARCH_ACTION,
    }
    limitations = [
        "Work orders describe research repair; they do not execute reruns.",
        "Linked source artifacts remain unchanged.",
        "Gatekeeper must be rerun after repair before any progression.",
    ]
    for label, payload in (
        ("gatekeeper", gatekeeper),
        ("scorecard", scorecard),
        ("expanded trial analysis", analysis),
    ):
        if not payload:
            limitations.append(f"The linked {label} report was unavailable.")
    return BackofficeEvidenceQualityReport(
        backoffice_attribution_run_id=backoffice_attribution_run_id,
        generated_at=generated_at,
        investor_persona_attribution_run_id=str(
            persona_report.get("attribution_run_id") or ""
        ),
        gatekeeper_run_id=str(persona_report.get("gatekeeper_run_id") or ""),
        scorecard_run_id=str(persona_report.get("scorecard_run_id") or ""),
        analysis_run_id=str(persona_report.get("analysis_run_id") or ""),
        expanded_trial_run_id=str(
            persona_report.get("expanded_trial_run_id") or ""
        ),
        backtest_run_id=str(persona_report.get("backtest_run_id") or ""),
        gatekeeper_decision=str(
            persona_report.get("gatekeeper_decision") or ""
        ),
        progression_allowed=progression_allowed,
        attribution_status=(
            "backoffice_repair_required_before_progression"
            if not progression_allowed
            else "backoffice_enrichment_required"
        ),
        evidence_issues=[issue.to_dict() for issue in issues],
        work_orders=[order.to_dict() for order in orders],
        backoffice_attribution_summary=summary,
        main_backoffice_finding=summary["main_backoffice_finding"],
        recommended_next_research_action=NEXT_RESEARCH_ACTION,
        limitations=limitations,
    )


def _join(items: list[str]) -> str:
    return "; ".join(items)


def render_backoffice_evidence_quality_report(
    report: BackofficeEvidenceQualityReport,
) -> str:
    """Render the Backoffice attribution as Markdown."""
    data = report.to_dict()
    lines = [
        "# Backoffice Evidence Quality Attribution Report",
        "",
        "## Executive Summary",
        "",
        (
            "- Backoffice Attribution Run ID: "
            f"{data['backoffice_attribution_run_id']}"
        ),
        (
            "- Investor Persona Attribution Run ID: "
            f"{data['investor_persona_attribution_run_id']}"
        ),
        f"- Gatekeeper Decision: {data['gatekeeper_decision']}",
        f"- Progression Allowed: {str(data['progression_allowed']).lower()}",
        f"- Attribution Status: {data['attribution_status']}",
        f"- Main Backoffice Finding: {data['main_backoffice_finding']}",
        (
            "- Next Research Action: "
            f"{data['recommended_next_research_action']}"
        ),
        "",
        "## Important Boundary",
        "",
        (
            "Backoffice does not make investment decisions or override the "
            "Gatekeeper. Backoffice only repairs, enriches, documents, and "
            "packages research evidence."
        ),
        "",
        "## Governance Context",
        "",
        f"- Gatekeeper Decision: {data['gatekeeper_decision']}",
        "- Investor Persona Progression: blocked",
        "- Personas Ready: 0",
        "- Current Status: repair required before progression",
        "",
        "## Evidence Issue Summary",
        "",
        (
            "| Issue | Severity | Priority | Source Layer | Affected Personas | "
            "Work Type | Recommended Action |"
        ),
        "|---|---|---|---|---|---|---|",
    ]
    for issue in data["evidence_issues"]:
        lines.append(
            f"| {issue['issue_label']} | {issue['severity']} | "
            f"{issue['priority']} | {issue['source_layer']} | "
            f"{_join(issue['affected_personas'])} | "
            f"{issue['backoffice_work_type']} | "
            f"{issue['recommended_action']} |"
        )
    lines.extend(
        [
            "",
            "## Backoffice Work Orders",
            "",
            (
                "| Work Order | Priority | Status | Objective | "
                "Expected Artifacts | Completion Criteria |"
            ),
            "|---|---|---|---|---|---|",
        ]
    )
    for order in data["work_orders"]:
        lines.append(
            f"| {order['title']} | {order['priority']} | {order['status']} | "
            f"{order['objective']} | {_join(order['expected_artifacts'])} | "
            f"{_join(order['completion_criteria'])} |"
        )
    for priority in ("P0", "P1", "P2", "P3"):
        lines.extend(["", f"## {priority} Work Orders", ""])
        for order in data["work_orders"]:
            if order["priority"] == priority:
                lines.extend(
                    [
                        f"### {order['title']}",
                        "",
                        f"- Status: {order['status']}",
                        f"- Objective: {order['objective']}",
                        f"- Inputs Needed: {_join(order['inputs_needed'])}",
                        f"- Proposed Steps: {_join(order['proposed_steps'])}",
                        (
                            "- Expected Artifacts: "
                            f"{_join(order['expected_artifacts'])}"
                        ),
                        (
                            "- Completion Criteria: "
                            f"{_join(order['completion_criteria'])}"
                        ),
                    ]
                )
    lines.extend(["", "## Persona Linkage", ""])
    for issue in data["evidence_issues"]:
        lines.append(
            f"- {issue['issue_label']}: {_join(issue['affected_personas'])}"
        )
    lines.extend(
        [
            "",
            "## What This Suggests",
            "",
            "- The system has reached a repair and enrichment phase.",
            "- The next work should be Backoffice-led, not investor-led.",
            "- No persona should progress until repair work is completed and re-gated.",
            "",
            "## What This Does Not Suggest",
            "",
            "- It does not prove a strategy.",
            "- It does not rank tickers or investor personas.",
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


def _csv_value(value) -> str:
    if isinstance(value, list):
        return _join(value)
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return str(value)


def write_backoffice_evidence_quality_report(
    *,
    outputs_root: Path,
    attribution_run_id: str | None = None,
    generated_at: datetime | None = None,
) -> BackofficeEvidenceQualityFiles:
    """Load linked artifacts and write Backoffice attribution outputs."""
    outputs_root = Path(outputs_root)
    timestamp = generated_at or datetime.now(timezone.utc)
    manifest = load_investor_persona_attribution_manifest(
        outputs_root=outputs_root,
        attribution_run_id=attribution_run_id,
    )
    selected_id = str(
        attribution_run_id or manifest.get("attribution_run_id") or ""
    )
    if not selected_id:
        raise ValueError("Investor persona attribution run ID is required.")
    persona_report = (
        manifest
        if attribution_run_id
        else load_investor_persona_attribution_report(
            outputs_root=outputs_root,
            attribution_run_id=selected_id,
        )
    )
    gatekeeper_id = str(persona_report.get("gatekeeper_run_id") or "")
    scorecard_id = str(persona_report.get("scorecard_run_id") or "")
    analysis_id = str(persona_report.get("analysis_run_id") or "")
    gatekeeper = (
        load_research_gatekeeper_report(
            outputs_root=outputs_root, gatekeeper_run_id=gatekeeper_id
        )
        if gatekeeper_id
        else {}
    )
    scorecard = (
        load_research_evidence_scorecard_report(
            outputs_root=outputs_root, scorecard_run_id=scorecard_id
        )
        if scorecard_id
        else {}
    )
    analysis = (
        load_expanded_trial_analysis_report(
            outputs_root=outputs_root, analysis_run_id=analysis_id
        )
        if analysis_id
        else {}
    )
    root = outputs_root / "backoffice_evidence_quality_attributions"
    root.mkdir(parents=True, exist_ok=True)
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    run_id = base
    suffix = 2
    while (root / run_id).exists():
        run_id = f"{base}_{suffix:02d}"
        suffix += 1
    report = build_backoffice_evidence_quality_attribution(
        backoffice_attribution_run_id=run_id,
        generated_at=timestamp.isoformat(),
        persona_report=persona_report,
        gatekeeper=gatekeeper,
        scorecard=scorecard,
        analysis=analysis,
    )
    folder = root / run_id
    folder.mkdir(parents=True, exist_ok=False)
    markdown_path = folder / "backoffice_evidence_quality_attribution_report.md"
    json_path = folder / "backoffice_evidence_quality_attribution_report.json"
    issues_path = folder / "backoffice_evidence_issues.csv"
    orders_path = folder / "backoffice_repair_work_orders.csv"
    markdown_path.write_text(
        render_backoffice_evidence_quality_report(report), encoding="utf-8"
    )
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2), encoding="utf-8"
    )
    for path, rows, fields in (
        (
            issues_path,
            report.evidence_issues,
            (
                "issue_code",
                "issue_label",
                "severity",
                "source_layer",
                "source_evidence",
                "affected_personas",
                "backoffice_work_type",
                "recommended_action",
                "expected_output",
                "priority",
                "safety_note",
            ),
        ),
        (
            orders_path,
            report.work_orders,
            (
                "work_order_id",
                "title",
                "priority",
                "status",
                "related_issue_codes",
                "objective",
                "inputs_needed",
                "proposed_steps",
                "expected_artifacts",
                "completion_criteria",
                "safety_boundary",
            ),
        ),
    ):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {key: _csv_value(row.get(key)) for key in fields}
                )
    latest_path = (
        root / "latest_backoffice_evidence_quality_attribution_manifest.json"
    )
    latest_path.write_text(
        json.dumps(
            {
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
                "gatekeeper_decision": report.gatekeeper_decision,
                "progression_allowed": report.progression_allowed,
                "attribution_status": report.attribution_status,
                "recommended_next_research_action": (
                    report.recommended_next_research_action
                ),
                "attribution_folder": str(folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "issues_csv_path": str(issues_path),
                "work_orders_csv_path": str(orders_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return BackofficeEvidenceQualityFiles(
        attribution_folder=folder,
        markdown_path=markdown_path,
        json_path=json_path,
        issues_csv_path=issues_path,
        work_orders_csv_path=orders_path,
        latest_manifest_path=latest_path,
        report=report,
    )
