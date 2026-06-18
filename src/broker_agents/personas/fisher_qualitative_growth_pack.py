"""BO-008 Fisher qualitative growth evidence pack."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report is a Fisher-specific evidence pack only. It does not create "
    "investor decisions, recommendations, rankings, allocation instructions, "
    "rebalancing instructions, trade signals, execution instructions, strategy "
    "validation, or investment advice."
)
WORK_ORDER_ID = "BO-008"
WORK_ORDER_TITLE = "Fisher Qualitative Growth Evidence Pack"
NEXT_WORK_ORDER = "BO-009 Buffett/Munger Quality and Risk Pack"
REVIEW_STATUS = "requirements_pack_completed_but_review_blocked_by_gatekeeper_hold"


@dataclass(frozen=True)
class FisherQualitativeGrowthPackReport:
    """Structured BO-008 Fisher evidence pack."""

    fisher_growth_pack_run_id: str
    generated_at: str
    bogle_benchmark_pack_run_id: str
    persona_evidence_pack_run_id: str
    metadata_diversity_recheck_run_id: str
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
    fisher_growth_pack_status: str
    fisher_growth_summary: dict
    fisher_qualitative_evidence_matrix: list[dict]
    fisher_scuttlebutt_proxy_matrix: list[dict]
    fisher_growth_risk_matrix: list[dict]
    fisher_evidence_requirements_status: list[dict]
    fisher_required_controls: dict
    recommended_next_work_order: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class FisherQualitativeGrowthPackFiles:
    """Generated BO-008 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    qualitative_matrix_csv_path: Path
    scuttlebutt_proxy_csv_path: Path
    growth_risk_csv_path: Path
    requirements_status_csv_path: Path
    required_controls_path: Path
    latest_manifest_path: Path
    report: FisherQualitativeGrowthPackReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_bogle_benchmark_pack_manifest(
    *,
    outputs_root: Path,
    bogle_benchmark_pack_run_id: str | None = None,
) -> dict:
    """Load one BO-007 report or the latest BO-007 manifest."""
    root = Path(outputs_root) / "bogle_benchmark_index_packs"
    path = (
        root
        / bogle_benchmark_pack_run_id
        / "bogle_benchmark_index_comparison_pack.json"
        if bogle_benchmark_pack_run_id
        else root / "latest_bogle_benchmark_index_pack_manifest.json"
    )
    label = (
        "Bogle benchmark pack report"
        if bogle_benchmark_pack_run_id
        else "Bogle benchmark pack manifest"
    )
    return _load_required_json(path, label)


def load_bogle_benchmark_pack_report(
    *,
    outputs_root: Path,
    bogle_benchmark_pack_run_id: str,
) -> dict:
    """Load the BO-007 report for a run id."""
    path = (
        Path(outputs_root)
        / "bogle_benchmark_index_packs"
        / bogle_benchmark_pack_run_id
        / "bogle_benchmark_index_comparison_pack.json"
    )
    return _load_required_json(path, "Bogle benchmark pack report")


def load_persona_evidence_pack_report(
    *,
    outputs_root: Path,
    persona_evidence_pack_run_id: str,
) -> dict:
    """Load the linked BO-006 persona evidence requirements report."""
    path = (
        Path(outputs_root)
        / "persona_evidence_pack_requirements"
        / persona_evidence_pack_run_id
        / "persona_evidence_pack_requirements_report.json"
    )
    return _load_required_json(path, "Persona evidence pack report")


def load_metadata_diversity_recheck_report(
    *,
    outputs_root: Path,
    metadata_diversity_recheck_run_id: str,
) -> dict:
    """Load the linked BO-005 metadata recheck report."""
    path = (
        Path(outputs_root)
        / "metadata_diversity_rechecks"
        / metadata_diversity_recheck_run_id
        / "metadata_diversity_recheck_report.json"
    )
    return _load_optional_json(path)


def load_delayed_anchor_repair_report(
    *,
    outputs_root: Path,
    delayed_anchor_repair_run_id: str,
) -> dict:
    """Load the linked BO-004 delayed-anchor report."""
    path = (
        Path(outputs_root)
        / "delayed_anchor_repairs"
        / delayed_anchor_repair_run_id
        / "delayed_anchor_repair_report.json"
    )
    return _load_optional_json(path)


def load_walk_forward_repair_report(
    *,
    outputs_root: Path,
    walk_forward_repair_run_id: str,
) -> dict:
    """Load the linked BO-003 walk-forward report."""
    path = (
        Path(outputs_root)
        / "walk_forward_repair_plans"
        / walk_forward_repair_run_id
        / "walk_forward_repair_plan_report.json"
    )
    return _load_optional_json(path)


def load_outlier_repair_report(
    *,
    outputs_root: Path,
    outlier_repair_run_id: str,
) -> dict:
    """Load the linked BO-002 outlier report."""
    path = (
        Path(outputs_root)
        / "outlier_repair_paths"
        / outlier_repair_run_id
        / "outlier_repair_path_report.json"
    )
    return _load_optional_json(path)


def load_backtest_driver_decomposition_report(
    *,
    outputs_root: Path,
    decomposition_run_id: str,
) -> dict:
    """Load the linked BO-001 driver decomposition."""
    path = (
        Path(outputs_root)
        / "backtest_driver_decompositions"
        / decomposition_run_id
        / "backtest_driver_decomposition_report.json"
    )
    return _load_optional_json(path)


def load_research_scorecard_report(
    *,
    outputs_root: Path,
    scorecard_run_id: str,
) -> dict:
    """Load the linked research evidence scorecard."""
    path = (
        Path(outputs_root)
        / "research_evidence_scorecards"
        / scorecard_run_id
        / "research_evidence_scorecard_report.json"
    )
    return _load_optional_json(path)


def load_expanded_trial_analysis_report(
    *,
    outputs_root: Path,
    analysis_run_id: str,
) -> dict:
    """Load the linked expanded trial analysis."""
    path = (
        Path(outputs_root)
        / "expanded_trial_analyses"
        / analysis_run_id
        / "expanded_trial_analysis_report.json"
    )
    return _load_optional_json(path)


def _fisher_checklist(persona_pack: dict) -> list[str]:
    checklists = persona_pack.get("persona_checklists", {})
    if isinstance(checklists, dict):
        items = checklists.get("Fisher", [])
        if isinstance(items, list):
            return [str(item) for item in items]
    return []


def build_fisher_growth_summary(
    *,
    fisher_pack_run_id: str,
    bogle_pack: dict,
    persona_pack: dict,
    metadata: dict,
    walk_forward: dict,
) -> dict:
    """Build Fisher-specific summary without asking Fisher for a decision."""
    concentration = metadata.get("concentration_classification", {})
    checklist = _fisher_checklist(persona_pack)
    return {
        "fisher_pack_run_id": fisher_pack_run_id,
        "gatekeeper_decision": "hold",
        "progression_allowed": False,
        "fisher_review_allowed": False,
        "qualitative_depth_status": "qualitative_evidence_gaps_remain",
        "growth_evidence_status": (
            "requirements_defined_or_partially_documented"
            if checklist
            else "requirements_defined"
        ),
        "product_pipeline_evidence_status": "missing_or_insufficient",
        "innovation_evidence_status": "missing_or_insufficient",
        "management_depth_evidence_status": "missing_or_insufficient",
        "scuttlebutt_proxy_status": "missing_or_insufficient",
        "market_expansion_evidence_status": "missing_or_insufficient",
        "metadata_concentration_status": concentration.get(
            "metadata_diversity_status", "materially_concentrated"
        ),
        "walk_forward_stability_status": (
            "unstable"
            if walk_forward.get("walk_forward_repair_status") == "completed"
            else "requires_documentation"
        ),
        "main_fisher_finding": (
            "Fisher review requires stronger qualitative growth, product, "
            "management, and market evidence before any persona review."
        ),
        "review_status": REVIEW_STATUS,
        "source_bogle_review_allowed": bogle_pack.get("bogle_benchmark_summary", {}).get(
            "bogle_review_allowed", False
        ),
    }


def build_fisher_qualitative_evidence_matrix() -> list[dict]:
    """Build Fisher qualitative evidence requirement rows."""
    rows = [
        (
            "product_pipeline",
            "Product pipeline depth, launches, and lifecycle evidence.",
            "Product pipeline evidence is central to Fisher growth durability.",
        ),
        (
            "R&D_innovation",
            "Research, development, and innovation evidence.",
            "Fisher needs proof that growth is supported by innovation capacity.",
        ),
        (
            "sales_organization",
            "Sales organization quality and execution evidence.",
            "Sales execution helps distinguish durable growth from temporary demand.",
        ),
        (
            "market_expansion",
            "Market expansion and addressable runway evidence.",
            "Fisher review requires evidence that growth runway can persist.",
        ),
        (
            "management_depth",
            "Management depth and operating excellence evidence.",
            "Fisher emphasizes management capability behind long-term growth.",
        ),
        (
            "customer_evidence",
            "Customer evidence and adoption signals.",
            "Customer evidence is a local substitute for scuttlebutt depth.",
        ),
        (
            "competitive_position",
            "Competitive position and differentiation evidence.",
            "Fisher requires evidence that growth quality can survive competition.",
        ),
        (
            "durable_growth_runway",
            "Durable growth runway evidence.",
            "Long-term runway must be documented before Fisher review.",
        ),
        (
            "qualitative_growth_consistency",
            "Consistency of growth quality across periods and cohorts.",
            "Qualitative evidence should explain instability rather than ignore it.",
        ),
        (
            "cohort_specific_growth_evidence",
            "Current-core and expanded-cohort growth evidence.",
            "Expanded cohort weakness limits Fisher generalization.",
        ),
        (
            "metadata_concentration_controls",
            "Metadata concentration controls.",
            "Concentration can make growth evidence less representative.",
        ),
        (
            "walk_forward_stability_controls",
            "Walk-forward stability controls.",
            "Fisher review needs period effects separated from growth quality.",
        ),
        (
            "anchor_controls",
            "Clean-anchor and delayed-anchor controls.",
            "Anchor quality affects whether evidence can be reviewed cleanly.",
        ),
        (
            "outlier_controls",
            "Outlier and top-contributor controls.",
            "Fisher evidence must not depend on one contributor or period.",
        ),
        (
            "no_recommendation_boundary",
            "No recommendation boundary.",
            "The pack documents requirements only and asks for no Fisher decision.",
        ),
    ]
    return [
        {
            "evidence_dimension": dimension,
            "current_status": (
                "documented_boundary" if dimension == "no_recommendation_boundary" else "missing_or_insufficient"
            ),
            "available_artifacts": (
                "persona_evidence_pack_requirements; linked repair reports"
                if dimension != "no_recommendation_boundary"
                else "fisher_qualitative_growth_pack"
            ),
            "missing_evidence": missing,
            "fisher_relevance": relevance,
            "required_before_review": dimension != "no_recommendation_boundary",
            "evidence_depth_label": (
                "boundary_documented"
                if dimension == "no_recommendation_boundary"
                else "qualitative_depth_gap"
            ),
            "safety_boundary": "Evidence requirements only; Fisher review remains blocked.",
        }
        for dimension, missing, relevance in rows
    ]


def build_fisher_scuttlebutt_proxy_matrix() -> list[dict]:
    """Build Fisher scuttlebutt proxy requirement rows from local-only evidence."""
    rows = [
        "customer_adoption",
        "customer_retention",
        "product_quality",
        "sales_execution",
        "competitive_feedback",
        "supplier_or_ecosystem_feedback",
        "employee_or_management_depth_proxy",
        "market_reputation",
        "innovation_validation",
    ]
    return [
        {
            "proxy_area": area,
            "current_status": "unavailable_locally",
            "available_proxy": "not_available_in_current_local_artifacts",
            "missing_proxy": f"{area} qualitative proxy evidence",
            "evidence_source_type": "local_artifacts_only",
            "fisher_relevance": (
                "Fisher-style review needs qualitative proxy evidence before "
                "any future persona review."
            ),
            "required_next_step": (
                "Prepare local, source-verified qualitative evidence without "
                "web scraping or live API calls."
            ),
        }
        for area in rows
    ]


def build_fisher_growth_risk_matrix() -> list[dict]:
    """Build Fisher growth risk rows mapped to current issue codes."""
    rows = [
        (
            "qualitative_depth_gap",
            "Qualitative depth gap",
            "qualitative_growth_evidence",
            "qualitative_depth_gaps",
            "high",
            "Fisher review cannot proceed without qualitative depth.",
            "Build product, management, customer, and market evidence pack.",
        ),
        (
            "product_pipeline_gap",
            "Product pipeline gap",
            "product_pipeline",
            "qualitative_depth_gaps",
            "high",
            "Product pipeline is core to Fisher growth durability.",
            "Document product pipeline and innovation evidence locally.",
        ),
        (
            "scuttlebutt_proxy_gap",
            "Scuttlebutt proxy gap",
            "customer_competitive_proxy",
            "persona_specific_evidence_gaps",
            "high",
            "Fisher needs customer and competitive proxy evidence.",
            "Prepare local scuttlebutt proxy artifacts.",
        ),
        (
            "metadata_concentration_limits_generalization",
            "Metadata concentration limits generalization",
            "metadata_controls",
            "metadata_diversity_partial_concentration",
            "moderate",
            "Concentration limits how growth evidence generalizes.",
            "Report sector/category/cohort concentration controls.",
        ),
        (
            "expanded_cohort_underperformance",
            "Expanded cohort underperformance",
            "cohort_growth_evidence",
            "expanded_cohort_underperformance",
            "high",
            "Expanded cohort weakness must be explained before Fisher review.",
            "Separate current_core and expanded_cohort evidence.",
        ),
        (
            "walk_forward_instability",
            "Walk-forward instability",
            "period_growth_evidence",
            "walk_forward_instability",
            "high",
            "Period instability can mask growth quality.",
            "Report supportive and post-2021 periods separately.",
        ),
        (
            "outlier_dependence",
            "Outlier dependence",
            "outlier_controls",
            "outlier_dependence",
            "high",
            "Growth evidence must not depend on one ticker or date.",
            "Report ex-NVDA and ex-top-contributor controls.",
        ),
        (
            "delayed_anchor_effect",
            "Delayed anchor effect",
            "anchor_controls",
            "delayed_anchor_effect",
            "moderate",
            "Anchor limitations affect the evidence review package.",
            "Separate clean-anchor and delayed-anchor views.",
        ),
        (
            "benchmark_relative_underperformance",
            "Benchmark-relative underperformance",
            "benchmark_context",
            "benchmark_relative_underperformance",
            "moderate",
            "Relative weakness is context for qualitative growth sufficiency.",
            "Explain absolute versus benchmark-relative evidence.",
        ),
        (
            "no_persona_review_until_gatekeeper_allows",
            "No persona review until Gatekeeper allows",
            "gatekeeper_hold",
            "persona_specific_evidence_gaps",
            "critical",
            "Fisher review remains blocked while Gatekeeper is HOLD.",
            "Rerun Gatekeeper after repair before any review.",
        ),
    ]
    return [
        {
            "risk_code": code,
            "risk_label": label,
            "affected_evidence": affected,
            "linked_issue_code": issue,
            "severity": severity,
            "fisher_relevance": relevance,
            "required_control": control,
        }
        for code, label, affected, issue, severity, relevance, control in rows
    ]


def build_fisher_evidence_requirements_status() -> list[dict]:
    """Build Fisher checklist status rows."""
    rows = [
        ("qualitative_growth_evidence", "Qualitative growth evidence"),
        ("product_pipeline_evidence", "Product pipeline evidence"),
        ("R&D_or_innovation_evidence", "R&D or innovation evidence"),
        ("sales_organization_evidence", "Sales organization evidence"),
        ("market_expansion_evidence", "Market expansion evidence"),
        ("management_depth_evidence", "Management depth evidence"),
        (
            "customer_competitive_scuttlebutt_proxy",
            "Customer and competitive scuttlebutt proxy evidence",
        ),
        ("durable_growth_runway_evidence", "Durable growth runway evidence"),
        ("concentrated_metadata_controls", "Concentrated metadata controls"),
        ("current_core_vs_expanded_cohort", "Current-core versus expanded-cohort"),
        ("walk_forward_stability_controls", "Walk-forward stability controls"),
        ("no_recommendation_boundary", "No recommendation boundary"),
    ]
    result = []
    for code, label in rows:
        boundary = code == "no_recommendation_boundary"
        result.append(
            {
                "requirement_code": code,
                "requirement_label": label,
                "current_status": (
                    "documented" if boundary else "missing_or_insufficient"
                ),
                "supporting_artifact": (
                    "fisher_qualitative_growth_pack"
                    if boundary
                    else "persona_evidence_pack_requirements"
                ),
                "gap_remaining": (
                    "No Fisher decision, recommendation, ranking, allocation, "
                    "or trade signal is produced."
                    if boundary
                    else f"{label} remains required before Fisher review."
                ),
                "required_before_review": not boundary,
                "safety_boundary": "Requirement documentation only; Fisher review remains blocked.",
            }
        )
    return result


def build_fisher_required_controls() -> dict:
    """Build Fisher-specific required controls."""
    return {
        "control_id": "BO-008-fisher-required-controls",
        "purpose": "Define qualitative growth controls required before future Fisher review.",
        "required_controls": [
            "Report product pipeline evidence without creating a recommendation.",
            "Report R&D and innovation evidence from local source-verified artifacts.",
            "Report sales organization and market expansion evidence.",
            "Report management depth evidence.",
            "Report customer and competitive scuttlebutt proxy evidence.",
            "Report current_core and expanded_cohort growth evidence separately.",
            "Report metadata concentration controls.",
            "Report walk-forward, anchor, and outlier controls.",
            "Gatekeeper must be rerun after repair before progression.",
        ],
        "required_reporting_views": [
            "product_pipeline",
            "R&D_innovation",
            "sales_organization",
            "market_expansion",
            "management_depth",
            "customer_evidence",
            "competitive_position",
            "durable_growth_runway",
        ],
        "local_evidence_constraints": [
            "No web scraping.",
            "No live API calls.",
            "No fabricated qualitative facts.",
            "Unavailable qualitative facts must be marked missing_or_insufficient.",
        ],
        "safety_constraints": [
            "No Fisher decision.",
            "No growth-stock recommendation.",
            "No company ranking.",
            "No allocation or target weight.",
            "No rebalancing instruction.",
            "No trade signal or execution instruction.",
        ],
    }


def build_fisher_qualitative_growth_pack(
    *,
    fisher_growth_pack_run_id: str,
    generated_at: str,
    bogle_pack: dict,
    persona_pack: dict,
    metadata: dict,
    delayed_anchor: dict,
    walk_forward: dict,
    outlier: dict,
    decomposition: dict,
    scorecard: dict,
    expanded_analysis: dict,
) -> FisherQualitativeGrowthPackReport:
    """Build the BO-008 Fisher qualitative growth evidence pack."""
    del delayed_anchor, outlier, decomposition, scorecard, expanded_analysis
    return FisherQualitativeGrowthPackReport(
        fisher_growth_pack_run_id=fisher_growth_pack_run_id,
        generated_at=generated_at,
        bogle_benchmark_pack_run_id=bogle_pack["bogle_benchmark_pack_run_id"],
        persona_evidence_pack_run_id=bogle_pack["persona_evidence_pack_run_id"],
        metadata_diversity_recheck_run_id=bogle_pack["metadata_diversity_recheck_run_id"],
        delayed_anchor_repair_run_id=bogle_pack["delayed_anchor_repair_run_id"],
        walk_forward_repair_run_id=bogle_pack["walk_forward_repair_run_id"],
        outlier_repair_run_id=bogle_pack["outlier_repair_run_id"],
        decomposition_run_id=bogle_pack["decomposition_run_id"],
        backoffice_attribution_run_id=bogle_pack["backoffice_attribution_run_id"],
        investor_persona_attribution_run_id=bogle_pack[
            "investor_persona_attribution_run_id"
        ],
        gatekeeper_run_id=bogle_pack["gatekeeper_run_id"],
        scorecard_run_id=bogle_pack["scorecard_run_id"],
        analysis_run_id=bogle_pack["analysis_run_id"],
        expanded_trial_run_id=bogle_pack["expanded_trial_run_id"],
        backtest_run_id=bogle_pack["backtest_run_id"],
        work_order_id=WORK_ORDER_ID,
        work_order_title=WORK_ORDER_TITLE,
        fisher_growth_pack_status="completed",
        fisher_growth_summary=build_fisher_growth_summary(
            fisher_pack_run_id=fisher_growth_pack_run_id,
            bogle_pack=bogle_pack,
            persona_pack=persona_pack,
            metadata=metadata,
            walk_forward=walk_forward,
        ),
        fisher_qualitative_evidence_matrix=build_fisher_qualitative_evidence_matrix(),
        fisher_scuttlebutt_proxy_matrix=build_fisher_scuttlebutt_proxy_matrix(),
        fisher_growth_risk_matrix=build_fisher_growth_risk_matrix(),
        fisher_evidence_requirements_status=build_fisher_evidence_requirements_status(),
        fisher_required_controls=build_fisher_required_controls(),
        recommended_next_work_order=NEXT_WORK_ORDER,
    )


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _format_value(value: object) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _markdown_table(rows: list[dict], columns: list[tuple[str, str]]) -> list[str]:
    header = "| " + " | ".join(label for label, _ in columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| "
        + " | ".join(_format_value(row.get(key)) for _, key in columns)
        + " |"
        for row in rows
    ]
    return [header, separator, *body]


def _render_markdown(report: FisherQualitativeGrowthPackReport) -> str:
    summary = report.fisher_growth_summary
    lines = [
        "# Fisher Qualitative Growth Evidence Pack",
        "",
        "## Executive Summary",
        "",
        f"* Fisher Growth Pack Run ID: {report.fisher_growth_pack_run_id}",
        f"* Bogle Benchmark Pack Run ID: {report.bogle_benchmark_pack_run_id}",
        f"* Work Order ID: {report.work_order_id}",
        f"* Backtest Run ID: {report.backtest_run_id}",
        f"* Gatekeeper Decision: {summary['gatekeeper_decision']}",
        f"* Progression Allowed: {str(summary['progression_allowed']).lower()}",
        f"* Fisher Review Allowed: {str(summary['fisher_review_allowed']).lower()}",
        f"* Main Fisher Finding: {summary['main_fisher_finding']}",
        f"* Recommended Next Work Order: {report.recommended_next_work_order}",
        "",
        "## Important Boundary",
        "",
        (
            "This report is a Fisher-specific evidence pack only. It does not "
            "create investor decisions, rankings, recommendations, allocations, "
            "rebalancing instructions, trade signals, or execution instructions."
        ),
        "",
        "## Source Context",
        "",
        "* Gatekeeper Decision: hold",
        "* Progression Allowed: false",
        "* Fisher Review Allowed: false",
        "* Current work order: BO-008",
        "* Reason: qualitative_depth_gaps and persona-specific evidence gaps",
        "",
        "## Fisher Growth Summary",
        "",
        f"* Qualitative Depth Status: {summary['qualitative_depth_status']}",
        f"* Growth Evidence Status: {summary['growth_evidence_status']}",
        f"* Product Pipeline Evidence Status: {summary['product_pipeline_evidence_status']}",
        f"* Innovation Evidence Status: {summary['innovation_evidence_status']}",
        f"* Management Depth Evidence Status: {summary['management_depth_evidence_status']}",
        f"* Scuttlebutt Proxy Status: {summary['scuttlebutt_proxy_status']}",
        f"* Metadata Concentration Status: {summary['metadata_concentration_status']}",
        f"* Walk-Forward Stability Status: {summary['walk_forward_stability_status']}",
        f"* Review Status: {summary['review_status']}",
        "",
        "## Qualitative Evidence Matrix",
        "",
        *_markdown_table(
            report.fisher_qualitative_evidence_matrix,
            [
                ("Evidence Dimension", "evidence_dimension"),
                ("Status", "current_status"),
                ("Fisher Relevance", "fisher_relevance"),
                ("Missing Evidence", "missing_evidence"),
                ("Required Before Review", "required_before_review"),
            ],
        ),
        "",
        "## Scuttlebutt Proxy Matrix",
        "",
        *_markdown_table(
            report.fisher_scuttlebutt_proxy_matrix,
            [
                ("Proxy Area", "proxy_area"),
                ("Status", "current_status"),
                ("Available Proxy", "available_proxy"),
                ("Missing Proxy", "missing_proxy"),
                ("Required Next Step", "required_next_step"),
            ],
        ),
        "",
        "## Fisher Growth Risk Matrix",
        "",
        *_markdown_table(
            report.fisher_growth_risk_matrix,
            [
                ("Risk", "risk_code"),
                ("Severity", "severity"),
                ("Fisher Relevance", "fisher_relevance"),
                ("Required Control", "required_control"),
            ],
        ),
        "",
        "## Evidence Requirements Status",
        "",
        *_markdown_table(
            report.fisher_evidence_requirements_status,
            [
                ("Requirement", "requirement_code"),
                ("Status", "current_status"),
                ("Supporting Artifact", "supporting_artifact"),
                ("Gap Remaining", "gap_remaining"),
                ("Required Before Review", "required_before_review"),
            ],
        ),
        "",
        "## Fisher-Specific Interpretation",
        "",
        "* Fisher requires qualitative depth because growth quality cannot be inferred from backtest rows alone.",
        "* Product pipeline and innovation evidence matter because durable growth depends on repeatable execution.",
        "* Scuttlebutt proxy evidence matters because local artifacts do not yet document customer, competitive, or ecosystem feedback.",
        "* Metadata concentration limits generalization because evidence remains concentrated by cohort and metadata groups.",
        "* Fisher review remains blocked while Gatekeeper remains HOLD.",
        "* No recommendation is produced; this pack defines requirements only.",
        "",
        "## What This Suggests",
        "",
        "* Fisher evidence pack requirements are documented.",
        "* Fisher review remains blocked while Gatekeeper remains HOLD.",
        "* Backoffice should proceed to Buffett/Munger quality and risk pack next.",
        "",
        "## What This Does Not Suggest",
        "",
        "* It does not ask Fisher to decide.",
        "* It does not recommend any company.",
        "* It does not rank companies.",
        "* It does not create allocation or rebalancing.",
        "* It does not create a trade signal.",
        "* It does not validate a strategy.",
        "",
        "## Next Work Order",
        "",
        f"* {report.recommended_next_work_order}",
        "",
        "## Safety Notice",
        "",
        report.safety_notice,
        "",
    ]
    return "\n".join(lines)


def write_fisher_qualitative_growth_pack_report(
    *,
    outputs_root: Path,
    bogle_benchmark_pack_run_id: str | None = None,
) -> FisherQualitativeGrowthPackFiles:
    """Write BO-008 Fisher qualitative growth pack artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_bogle_benchmark_pack_manifest(
        outputs_root=outputs_root,
        bogle_benchmark_pack_run_id=bogle_benchmark_pack_run_id,
    )
    bogle_run_id = manifest["bogle_benchmark_pack_run_id"]
    bogle_pack = load_bogle_benchmark_pack_report(
        outputs_root=outputs_root,
        bogle_benchmark_pack_run_id=bogle_run_id,
    )
    persona_pack = load_persona_evidence_pack_report(
        outputs_root=outputs_root,
        persona_evidence_pack_run_id=bogle_pack["persona_evidence_pack_run_id"],
    )
    metadata = load_metadata_diversity_recheck_report(
        outputs_root=outputs_root,
        metadata_diversity_recheck_run_id=bogle_pack["metadata_diversity_recheck_run_id"],
    )
    delayed_anchor = load_delayed_anchor_repair_report(
        outputs_root=outputs_root,
        delayed_anchor_repair_run_id=bogle_pack["delayed_anchor_repair_run_id"],
    )
    walk_forward = load_walk_forward_repair_report(
        outputs_root=outputs_root,
        walk_forward_repair_run_id=bogle_pack["walk_forward_repair_run_id"],
    )
    outlier = load_outlier_repair_report(
        outputs_root=outputs_root,
        outlier_repair_run_id=bogle_pack["outlier_repair_run_id"],
    )
    decomposition = load_backtest_driver_decomposition_report(
        outputs_root=outputs_root,
        decomposition_run_id=bogle_pack["decomposition_run_id"],
    )
    scorecard = load_research_scorecard_report(
        outputs_root=outputs_root,
        scorecard_run_id=bogle_pack["scorecard_run_id"],
    )
    expanded_analysis = load_expanded_trial_analysis_report(
        outputs_root=outputs_root,
        analysis_run_id=bogle_pack["analysis_run_id"],
    )

    generated_at = datetime.now(timezone.utc)
    fisher_run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_fisher_qualitative_growth_pack(
        fisher_growth_pack_run_id=fisher_run_id,
        generated_at=generated_at.isoformat(),
        bogle_pack=bogle_pack,
        persona_pack=persona_pack,
        metadata=metadata,
        delayed_anchor=delayed_anchor,
        walk_forward=walk_forward,
        outlier=outlier,
        decomposition=decomposition,
        scorecard=scorecard,
        expanded_analysis=expanded_analysis,
    )

    root = outputs_root / "fisher_qualitative_growth_packs"
    output_folder = root / fisher_run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "fisher_qualitative_growth_evidence_pack.md"
    json_path = output_folder / "fisher_qualitative_growth_evidence_pack.json"
    qualitative_matrix_csv_path = output_folder / "fisher_qualitative_evidence_matrix.csv"
    scuttlebutt_proxy_csv_path = output_folder / "fisher_scuttlebutt_proxy_matrix.csv"
    growth_risk_csv_path = output_folder / "fisher_growth_risk_matrix.csv"
    requirements_status_csv_path = output_folder / "fisher_evidence_requirements_status.csv"
    required_controls_path = output_folder / "fisher_required_controls.json"
    latest_manifest_path = root / "latest_fisher_qualitative_growth_pack_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(qualitative_matrix_csv_path, report.fisher_qualitative_evidence_matrix)
    _write_csv(scuttlebutt_proxy_csv_path, report.fisher_scuttlebutt_proxy_matrix)
    _write_csv(growth_risk_csv_path, report.fisher_growth_risk_matrix)
    _write_csv(requirements_status_csv_path, report.fisher_evidence_requirements_status)
    required_controls_path.write_text(
        json.dumps(report.fisher_required_controls, indent=2),
        encoding="utf-8",
    )
    latest_manifest_path.write_text(
        json.dumps(
            {
                "fisher_growth_pack_run_id": report.fisher_growth_pack_run_id,
                "bogle_benchmark_pack_run_id": report.bogle_benchmark_pack_run_id,
                "persona_evidence_pack_run_id": report.persona_evidence_pack_run_id,
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
                "fisher_growth_pack_status": report.fisher_growth_pack_status,
                "recommended_next_work_order": report.recommended_next_work_order,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "qualitative_matrix_csv_path": str(qualitative_matrix_csv_path),
                "scuttlebutt_proxy_csv_path": str(scuttlebutt_proxy_csv_path),
                "growth_risk_csv_path": str(growth_risk_csv_path),
                "requirements_status_csv_path": str(requirements_status_csv_path),
                "required_controls_path": str(required_controls_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return FisherQualitativeGrowthPackFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        qualitative_matrix_csv_path=qualitative_matrix_csv_path,
        scuttlebutt_proxy_csv_path=scuttlebutt_proxy_csv_path,
        growth_risk_csv_path=growth_risk_csv_path,
        requirements_status_csv_path=requirements_status_csv_path,
        required_controls_path=required_controls_path,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
