"""BO-009 Buffett/Munger quality and risk evidence pack."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report is a Buffett/Munger evidence pack only. It does not create "
    "investor decisions, recommendations, rankings, allocation instructions, "
    "rebalancing instructions, trade signals, execution instructions, strategy "
    "validation, or investment advice."
)
WORK_ORDER_ID = "BO-009"
WORK_ORDER_TITLE = "Buffett/Munger Quality and Risk Pack"
NEXT_WORK_ORDER = "BO-010 Research Audit Trail Bundle"
REVIEW_STATUS = "requirements_pack_completed_but_review_blocked_by_gatekeeper_hold"


@dataclass(frozen=True)
class BuffettMungerQualityRiskPackReport:
    """Structured BO-009 Buffett/Munger evidence pack."""

    buffett_munger_pack_run_id: str
    generated_at: str
    fisher_growth_pack_run_id: str
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
    buffett_munger_pack_status: str
    buffett_quality_summary: dict
    munger_quality_summary: dict
    quality_evidence_matrix: list[dict]
    owner_earnings_intrinsic_value_requirements: list[dict]
    capital_allocation_balance_sheet_matrix: list[dict]
    munger_inversion_risk_matrix: list[dict]
    buffett_munger_evidence_requirements_status: list[dict]
    buffett_munger_required_controls: dict
    recommended_next_work_order: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class BuffettMungerQualityRiskPackFiles:
    """Generated BO-009 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    buffett_summary_path: Path
    munger_summary_path: Path
    quality_matrix_csv_path: Path
    owner_earnings_csv_path: Path
    capital_allocation_csv_path: Path
    munger_risk_csv_path: Path
    requirements_status_csv_path: Path
    required_controls_path: Path
    latest_manifest_path: Path
    report: BuffettMungerQualityRiskPackReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_fisher_growth_pack_manifest(
    *,
    outputs_root: Path,
    fisher_growth_pack_run_id: str | None = None,
) -> dict:
    """Load one BO-008 report or the latest BO-008 manifest."""
    root = Path(outputs_root) / "fisher_qualitative_growth_packs"
    path = (
        root
        / fisher_growth_pack_run_id
        / "fisher_qualitative_growth_evidence_pack.json"
        if fisher_growth_pack_run_id
        else root / "latest_fisher_qualitative_growth_pack_manifest.json"
    )
    label = (
        "Fisher growth pack report"
        if fisher_growth_pack_run_id
        else "Fisher growth pack manifest"
    )
    return _load_required_json(path, label)


def load_fisher_growth_pack_report(
    *,
    outputs_root: Path,
    fisher_growth_pack_run_id: str,
) -> dict:
    """Load the BO-008 report for a run id."""
    path = (
        Path(outputs_root)
        / "fisher_qualitative_growth_packs"
        / fisher_growth_pack_run_id
        / "fisher_qualitative_growth_evidence_pack.json"
    )
    return _load_required_json(path, "Fisher growth pack report")


def load_bogle_benchmark_pack_report(
    *,
    outputs_root: Path,
    bogle_benchmark_pack_run_id: str,
) -> dict:
    """Load the linked BO-007 Bogle benchmark pack."""
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
    """Load the linked BO-006 persona evidence pack."""
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
    """Load the linked BO-005 metadata report."""
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


def build_buffett_quality_summary(*, buffett_munger_pack_run_id: str) -> dict:
    """Build Buffett-specific quality summary."""
    return {
        "buffett_munger_pack_run_id": buffett_munger_pack_run_id,
        "buffett_review_allowed": False,
        "gatekeeper_decision": "hold",
        "progression_allowed": False,
        "durable_business_quality_status": "missing_or_insufficient",
        "owner_earnings_status": "missing_or_insufficient",
        "intrinsic_value_assumption_status": "missing_or_insufficient",
        "capital_allocation_status": "missing_or_insufficient",
        "balance_sheet_resilience_status": "missing_or_insufficient",
        "management_quality_status": "missing_or_insufficient",
        "margin_of_safety_discussion_status": "requirements_defined_without_recommendation",
        "benchmark_relative_context_status": "documented_negative_context",
        "main_buffett_finding": (
            "Buffett review requires stronger durable quality, owner earnings, "
            "valuation assumptions, and capital allocation evidence before any "
            "persona review."
        ),
        "review_status": REVIEW_STATUS,
    }


def build_munger_quality_summary(*, buffett_munger_pack_run_id: str) -> dict:
    """Build Munger-specific quality and risk summary."""
    return {
        "buffett_munger_pack_run_id": buffett_munger_pack_run_id,
        "munger_review_allowed": False,
        "gatekeeper_decision": "hold",
        "progression_allowed": False,
        "moat_quality_status": "missing_or_insufficient",
        "incentives_status": "missing_or_insufficient",
        "inversion_risk_status": "missing_or_insufficient",
        "hidden_stupidity_status": "missing_or_insufficient",
        "capital_allocation_discipline_status": "missing_or_insufficient",
        "balance_sheet_resilience_status": "missing_or_insufficient",
        "agency_risk_status": "missing_or_insufficient",
        "failure_mode_status": "missing_or_insufficient",
        "main_munger_finding": (
            "Munger review requires stronger moat, incentives, inversion, and "
            "failure-mode evidence before any persona review."
        ),
        "review_status": REVIEW_STATUS,
    }


def build_quality_evidence_matrix() -> list[dict]:
    """Build shared Buffett/Munger quality evidence rows."""
    rows = [
        ("durable_business_quality", "Buffett"),
        ("moat_or_competitive_advantage", "Buffett and Munger"),
        ("normalized_owner_earnings", "Buffett"),
        ("intrinsic_value_assumptions", "Buffett"),
        ("capital_allocation", "Buffett and Munger"),
        ("balance_sheet_resilience", "Buffett and Munger"),
        ("debt_and_liquidity_risk", "Buffett and Munger"),
        ("management_quality", "Buffett"),
        ("incentives_and_agency_risk", "Munger"),
        ("long_term_economics", "Buffett"),
        ("reinvestment_runway", "Buffett and Munger"),
        ("earnings_quality", "Buffett and Munger"),
        ("downside_risk", "Munger"),
        ("benchmark_relative_context", "Buffett and Munger"),
        ("current_core_vs_expanded_cohort", "Buffett and Munger"),
        ("walk_forward_stability_controls", "Buffett and Munger"),
        ("anchor_controls", "Buffett and Munger"),
        ("outlier_controls", "Buffett and Munger"),
        ("no_recommendation_boundary", "Buffett and Munger"),
    ]
    return [
        {
            "evidence_dimension": dimension,
            "persona_relevance": relevance,
            "current_status": (
                "documented_boundary"
                if dimension == "no_recommendation_boundary"
                else "missing_or_insufficient"
            ),
            "available_artifacts": "persona_evidence_pack_requirements; linked repair reports",
            "missing_evidence": (
                "No investor decision, valuation recommendation, ranking, allocation, or signal."
                if dimension == "no_recommendation_boundary"
                else f"{dimension} evidence remains required before review."
            ),
            "required_before_review": dimension != "no_recommendation_boundary",
            "evidence_depth_label": (
                "boundary_documented"
                if dimension == "no_recommendation_boundary"
                else "quality_risk_depth_gap"
            ),
            "safety_boundary": (
                "Evidence requirements only; Buffett and Munger reviews remain blocked."
            ),
        }
        for dimension, relevance in rows
    ]


def build_owner_earnings_intrinsic_value_requirements() -> list[dict]:
    """Build Buffett owner-earnings and valuation-assumption requirement rows."""
    rows = [
        "normalized_owner_earnings_history",
        "owner_earnings_adjustments",
        "maintenance_capex_assumption",
        "working_capital_adjustment",
        "normalized_free_cash_flow",
        "intrinsic_value_range_assumptions",
        "discount_rate_or_required_return_assumption",
        "terminal_growth_assumption",
        "margin_of_safety_discussion_without_recommendation",
        "valuation_sensitivity_analysis",
        "no_price_target_or_buy_signal",
    ]
    return [
        {
            "requirement_code": code,
            "requirement_label": code.replace("_", " "),
            "current_status": (
                "documented_boundary"
                if code == "no_price_target_or_buy_signal"
                else "missing_or_insufficient"
            ),
            "available_artifact": "persona_evidence_pack_requirements",
            "missing_evidence": (
                "No price target, valuation recommendation, or signal is produced."
                if code == "no_price_target_or_buy_signal"
                else f"{code.replace('_', ' ')} remains required."
            ),
            "required_assumptions": (
                "Do not compute or imply valuation outputs unless source evidence exists."
            ),
            "safety_boundary": "Requirements only; no intrinsic value recommendation is produced.",
        }
        for code in rows
    ]


def build_capital_allocation_balance_sheet_matrix() -> list[dict]:
    """Build shared capital allocation and balance sheet requirement rows."""
    rows = [
        "buyback_discipline",
        "reinvestment_discipline",
        "acquisition_discipline",
        "dividend_policy_context",
        "debt_maturity_profile",
        "interest_coverage",
        "liquidity_resilience",
        "balance_sheet_optionalities",
        "dilution_or_share_count_trend",
        "capital_allocation_mistake_history",
    ]
    return [
        {
            "evidence_area": area,
            "current_status": "missing_or_insufficient",
            "available_artifact": "persona_evidence_pack_requirements",
            "missing_evidence": f"{area.replace('_', ' ')} evidence remains required.",
            "buffett_relevance": "Buffett needs capital allocation and balance sheet evidence before review.",
            "munger_relevance": "Munger needs discipline and resilience evidence before review.",
            "required_before_review": True,
        }
        for area in rows
    ]


def build_munger_inversion_risk_matrix() -> list[dict]:
    """Build Munger inversion and failure-mode risk rows."""
    rows = [
        ("incentive_misalignment", "persona_specific_evidence_gaps", "high"),
        ("agency_risk", "persona_specific_evidence_gaps", "high"),
        ("balance_sheet_fragility", "qualitative_depth_gaps", "high"),
        ("capital_allocation_error", "qualitative_depth_gaps", "high"),
        ("moat_deterioration", "qualitative_depth_gaps", "high"),
        ("accounting_quality_risk", "qualitative_depth_gaps", "moderate"),
        ("hidden_stupidity_or_complexity", "persona_specific_evidence_gaps", "high"),
        ("overreliance_on_outliers", "outlier_dependence", "high"),
        ("expanded_cohort_underperformance", "expanded_cohort_underperformance", "high"),
        ("walk_forward_instability", "walk_forward_instability", "high"),
        ("delayed_anchor_effect", "delayed_anchor_effect", "moderate"),
        (
            "metadata_concentration_limits_generalization",
            "metadata_diversity_partial_concentration",
            "moderate",
        ),
        ("benchmark_relative_underperformance", "benchmark_relative_underperformance", "moderate"),
        ("no_persona_review_until_gatekeeper_allows", "persona_specific_evidence_gaps", "critical"),
    ]
    return [
        {
            "risk_code": code,
            "risk_label": code.replace("_", " "),
            "linked_issue_code": issue,
            "current_status": "requires_inversion_review",
            "severity": severity,
            "munger_relevance": (
                "Munger review requires this risk to be inverted and documented."
            ),
            "required_control": (
                "Document local evidence, failure mode, and mitigation requirement "
                "before any Munger review."
            ),
        }
        for code, issue, severity in rows
    ]


def build_buffett_munger_evidence_requirements_status() -> list[dict]:
    """Build Buffett and Munger checklist status rows."""
    buffett = [
        "durable_business_quality_evidence",
        "owner_earnings_evidence",
        "intrinsic_value_assumption_evidence",
        "margin_of_safety_discussion_without_recommendation",
        "capital_allocation_evidence",
        "balance_sheet_risk_evidence",
        "management_quality_evidence",
        "long_term_economics_evidence",
        "walk_forward_and_anchor_controls",
        "current_core_vs_expanded_cohort",
        "no_recommendation_boundary",
    ]
    munger = [
        "moat_quality_evidence",
        "incentives_agency_risk_evidence",
        "inversion_risk_checklist",
        "hidden_stupidity_failure_mode_checklist",
        "capital_allocation_discipline_evidence",
        "balance_sheet_resilience_evidence",
        "outlier_dependence_explanation",
        "expanded_cohort_drag_explanation",
        "source_verification_requirements",
        "no_recommendation_boundary",
    ]
    rows = []
    for persona, requirements in (("Buffett", buffett), ("Munger", munger)):
        for code in requirements:
            boundary = code == "no_recommendation_boundary"
            rows.append(
                {
                    "persona": persona,
                    "requirement_code": code,
                    "requirement_label": code.replace("_", " "),
                    "current_status": "documented" if boundary else "missing_or_insufficient",
                    "supporting_artifact": (
                        "buffett_munger_quality_risk_pack"
                        if boundary
                        else "persona_evidence_pack_requirements"
                    ),
                    "gap_remaining": (
                        "No persona decision, valuation recommendation, ranking, allocation, or signal is produced."
                        if boundary
                        else f"{code.replace('_', ' ')} remains required."
                    ),
                    "required_before_review": not boundary,
                    "safety_boundary": (
                        "Requirement documentation only; persona review remains blocked."
                    ),
                }
            )
    return rows


def build_buffett_munger_required_controls() -> dict:
    """Build Buffett/Munger required controls."""
    return {
        "control_id": "BO-009-buffett-munger-required-controls",
        "purpose": "Define quality, valuation-assumption, inversion, and risk controls before future Buffett or Munger review.",
        "required_controls": [
            "Report Buffett and Munger requirements separately.",
            "Document durable business quality, moat, and long-term economics locally.",
            "Document owner earnings assumptions without computing new valuation outputs.",
            "Document intrinsic value assumptions without a price target or recommendation.",
            "Document capital allocation and balance sheet resilience.",
            "Document incentives, agency risks, inversion risks, and failure modes.",
            "Report current_core and expanded_cohort separately.",
            "Report walk-forward, anchor, and outlier controls.",
            "Gatekeeper must be rerun after repair before progression.",
        ],
        "local_evidence_constraints": [
            "No web scraping.",
            "No live API calls.",
            "No fabricated qualitative facts.",
            "Do not compute new intrinsic values unless source artifacts already contain them.",
        ],
        "safety_constraints": [
            "No Buffett decision.",
            "No Munger decision.",
            "No intrinsic value recommendation.",
            "No price target.",
            "No company ranking.",
            "No allocation or target weight.",
            "No rebalancing instruction.",
            "No trade signal or execution instruction.",
        ],
    }


def build_buffett_munger_quality_risk_pack(
    *,
    buffett_munger_pack_run_id: str,
    generated_at: str,
    fisher_pack: dict,
    bogle_pack: dict,
    persona_pack: dict,
    metadata: dict,
    delayed_anchor: dict,
    walk_forward: dict,
    outlier: dict,
    decomposition: dict,
    scorecard: dict,
    expanded_analysis: dict,
) -> BuffettMungerQualityRiskPackReport:
    """Build the BO-009 Buffett/Munger quality and risk pack."""
    del bogle_pack, persona_pack, metadata, delayed_anchor, walk_forward
    del outlier, decomposition, scorecard, expanded_analysis
    return BuffettMungerQualityRiskPackReport(
        buffett_munger_pack_run_id=buffett_munger_pack_run_id,
        generated_at=generated_at,
        fisher_growth_pack_run_id=fisher_pack["fisher_growth_pack_run_id"],
        bogle_benchmark_pack_run_id=fisher_pack["bogle_benchmark_pack_run_id"],
        persona_evidence_pack_run_id=fisher_pack["persona_evidence_pack_run_id"],
        metadata_diversity_recheck_run_id=fisher_pack["metadata_diversity_recheck_run_id"],
        delayed_anchor_repair_run_id=fisher_pack["delayed_anchor_repair_run_id"],
        walk_forward_repair_run_id=fisher_pack["walk_forward_repair_run_id"],
        outlier_repair_run_id=fisher_pack["outlier_repair_run_id"],
        decomposition_run_id=fisher_pack["decomposition_run_id"],
        backoffice_attribution_run_id=fisher_pack["backoffice_attribution_run_id"],
        investor_persona_attribution_run_id=fisher_pack[
            "investor_persona_attribution_run_id"
        ],
        gatekeeper_run_id=fisher_pack["gatekeeper_run_id"],
        scorecard_run_id=fisher_pack["scorecard_run_id"],
        analysis_run_id=fisher_pack["analysis_run_id"],
        expanded_trial_run_id=fisher_pack["expanded_trial_run_id"],
        backtest_run_id=fisher_pack["backtest_run_id"],
        work_order_id=WORK_ORDER_ID,
        work_order_title=WORK_ORDER_TITLE,
        buffett_munger_pack_status="completed",
        buffett_quality_summary=build_buffett_quality_summary(
            buffett_munger_pack_run_id=buffett_munger_pack_run_id
        ),
        munger_quality_summary=build_munger_quality_summary(
            buffett_munger_pack_run_id=buffett_munger_pack_run_id
        ),
        quality_evidence_matrix=build_quality_evidence_matrix(),
        owner_earnings_intrinsic_value_requirements=(
            build_owner_earnings_intrinsic_value_requirements()
        ),
        capital_allocation_balance_sheet_matrix=(
            build_capital_allocation_balance_sheet_matrix()
        ),
        munger_inversion_risk_matrix=build_munger_inversion_risk_matrix(),
        buffett_munger_evidence_requirements_status=(
            build_buffett_munger_evidence_requirements_status()
        ),
        buffett_munger_required_controls=build_buffett_munger_required_controls(),
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


def _render_markdown(report: BuffettMungerQualityRiskPackReport) -> str:
    buffett = report.buffett_quality_summary
    munger = report.munger_quality_summary
    lines = [
        "# Buffett/Munger Quality and Risk Pack",
        "",
        "## Executive Summary",
        "",
        f"* Buffett/Munger Pack Run ID: {report.buffett_munger_pack_run_id}",
        f"* Fisher Growth Pack Run ID: {report.fisher_growth_pack_run_id}",
        f"* Work Order ID: {report.work_order_id}",
        f"* Backtest Run ID: {report.backtest_run_id}",
        f"* Gatekeeper Decision: {buffett['gatekeeper_decision']}",
        f"* Progression Allowed: {str(buffett['progression_allowed']).lower()}",
        f"* Buffett Review Allowed: {str(buffett['buffett_review_allowed']).lower()}",
        f"* Munger Review Allowed: {str(munger['munger_review_allowed']).lower()}",
        f"* Main Buffett Finding: {buffett['main_buffett_finding']}",
        f"* Main Munger Finding: {munger['main_munger_finding']}",
        f"* Recommended Next Work Order: {report.recommended_next_work_order}",
        "",
        "## Important Boundary",
        "",
        (
            "This report is a Buffett/Munger evidence pack only. It does not "
            "create investor decisions, rankings, recommendations, allocations, "
            "rebalancing instructions, trade signals, or execution instructions."
        ),
        "",
        "## Source Context",
        "",
        "* Gatekeeper Decision: hold",
        "* Progression Allowed: false",
        "* Buffett Review Allowed: false",
        "* Munger Review Allowed: false",
        "* Current work order: BO-009",
        "* Reason: quality, risk, valuation, incentive, and qualitative evidence gaps",
        "",
        "## Buffett Quality Summary",
        "",
        f"* Durable Business Quality Status: {buffett['durable_business_quality_status']}",
        f"* Owner Earnings Status: {buffett['owner_earnings_status']}",
        f"* Intrinsic Value Assumption Status: {buffett['intrinsic_value_assumption_status']}",
        f"* Capital Allocation Status: {buffett['capital_allocation_status']}",
        f"* Balance Sheet Resilience Status: {buffett['balance_sheet_resilience_status']}",
        f"* Management Quality Status: {buffett['management_quality_status']}",
        f"* Review Status: {buffett['review_status']}",
        "",
        "## Munger Quality Summary",
        "",
        f"* Moat Quality Status: {munger['moat_quality_status']}",
        f"* Incentives Status: {munger['incentives_status']}",
        f"* Inversion Risk Status: {munger['inversion_risk_status']}",
        f"* Hidden Stupidity Status: {munger['hidden_stupidity_status']}",
        f"* Agency Risk Status: {munger['agency_risk_status']}",
        f"* Failure Mode Status: {munger['failure_mode_status']}",
        f"* Review Status: {munger['review_status']}",
        "",
        "## Quality Evidence Matrix",
        "",
        *_markdown_table(
            report.quality_evidence_matrix,
            [
                ("Evidence Dimension", "evidence_dimension"),
                ("Persona Relevance", "persona_relevance"),
                ("Status", "current_status"),
                ("Missing Evidence", "missing_evidence"),
                ("Required Before Review", "required_before_review"),
            ],
        ),
        "",
        "## Owner Earnings and Intrinsic Value Requirements",
        "",
        *_markdown_table(
            report.owner_earnings_intrinsic_value_requirements,
            [
                ("Requirement", "requirement_code"),
                ("Status", "current_status"),
                ("Missing Evidence", "missing_evidence"),
                ("Required Assumptions", "required_assumptions"),
                ("Safety Boundary", "safety_boundary"),
            ],
        ),
        "",
        "## Capital Allocation and Balance Sheet Matrix",
        "",
        *_markdown_table(
            report.capital_allocation_balance_sheet_matrix,
            [
                ("Area", "evidence_area"),
                ("Status", "current_status"),
                ("Buffett Relevance", "buffett_relevance"),
                ("Munger Relevance", "munger_relevance"),
                ("Required Before Review", "required_before_review"),
            ],
        ),
        "",
        "## Munger Inversion Risk Matrix",
        "",
        *_markdown_table(
            report.munger_inversion_risk_matrix,
            [
                ("Risk", "risk_code"),
                ("Severity", "severity"),
                ("Munger Relevance", "munger_relevance"),
                ("Required Control", "required_control"),
            ],
        ),
        "",
        "## Evidence Requirements Status",
        "",
        *_markdown_table(
            report.buffett_munger_evidence_requirements_status,
            [
                ("Persona", "persona"),
                ("Requirement", "requirement_code"),
                ("Status", "current_status"),
                ("Supporting Artifact", "supporting_artifact"),
                ("Gap Remaining", "gap_remaining"),
                ("Required Before Review", "required_before_review"),
            ],
        ),
        "",
        "## Buffett-Specific Interpretation",
        "",
        "* Durable quality matters because Buffett review requires evidence of long-term business resilience.",
        "* Owner earnings and intrinsic value assumptions must be documented before review.",
        "* Margin of safety discussion is a requirement only and cannot become a recommendation.",
        "* Capital allocation and balance sheet evidence matter because quality must survive stress.",
        "* Buffett review remains blocked while Gatekeeper remains HOLD.",
        "",
        "## Munger-Specific Interpretation",
        "",
        "* Moat, incentives, inversion, and failure modes matter because Munger review starts by avoiding obvious errors.",
        "* Hidden stupidity and agency risk must be documented before review.",
        "* Outlier dependence and expanded-cohort drag matter because they can conceal fragile evidence.",
        "* Munger review remains blocked while Gatekeeper remains HOLD.",
        "",
        "## What This Suggests",
        "",
        "* Buffett/Munger evidence pack requirements are documented.",
        "* Buffett and Munger reviews remain blocked while Gatekeeper remains HOLD.",
        "* Backoffice should proceed to Research Audit Trail Bundle next.",
        "",
        "## What This Does Not Suggest",
        "",
        "* It does not ask Buffett or Munger to decide.",
        "* It does not recommend any company.",
        "* It does not rank companies.",
        "* It does not create intrinsic value recommendation.",
        "* It does not create price target.",
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


def write_buffett_munger_quality_risk_pack_report(
    *,
    outputs_root: Path,
    fisher_growth_pack_run_id: str | None = None,
) -> BuffettMungerQualityRiskPackFiles:
    """Write BO-009 Buffett/Munger quality and risk pack artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_fisher_growth_pack_manifest(
        outputs_root=outputs_root,
        fisher_growth_pack_run_id=fisher_growth_pack_run_id,
    )
    fisher_run_id = manifest["fisher_growth_pack_run_id"]
    fisher_pack = load_fisher_growth_pack_report(
        outputs_root=outputs_root,
        fisher_growth_pack_run_id=fisher_run_id,
    )
    bogle_pack = load_bogle_benchmark_pack_report(
        outputs_root=outputs_root,
        bogle_benchmark_pack_run_id=fisher_pack["bogle_benchmark_pack_run_id"],
    )
    persona_pack = load_persona_evidence_pack_report(
        outputs_root=outputs_root,
        persona_evidence_pack_run_id=fisher_pack["persona_evidence_pack_run_id"],
    )
    metadata = load_metadata_diversity_recheck_report(
        outputs_root=outputs_root,
        metadata_diversity_recheck_run_id=fisher_pack["metadata_diversity_recheck_run_id"],
    )
    delayed_anchor = load_delayed_anchor_repair_report(
        outputs_root=outputs_root,
        delayed_anchor_repair_run_id=fisher_pack["delayed_anchor_repair_run_id"],
    )
    walk_forward = load_walk_forward_repair_report(
        outputs_root=outputs_root,
        walk_forward_repair_run_id=fisher_pack["walk_forward_repair_run_id"],
    )
    outlier = load_outlier_repair_report(
        outputs_root=outputs_root,
        outlier_repair_run_id=fisher_pack["outlier_repair_run_id"],
    )
    decomposition = load_backtest_driver_decomposition_report(
        outputs_root=outputs_root,
        decomposition_run_id=fisher_pack["decomposition_run_id"],
    )
    scorecard = load_research_scorecard_report(
        outputs_root=outputs_root,
        scorecard_run_id=fisher_pack["scorecard_run_id"],
    )
    expanded_analysis = load_expanded_trial_analysis_report(
        outputs_root=outputs_root,
        analysis_run_id=fisher_pack["analysis_run_id"],
    )

    generated_at = datetime.now(timezone.utc)
    pack_run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_buffett_munger_quality_risk_pack(
        buffett_munger_pack_run_id=pack_run_id,
        generated_at=generated_at.isoformat(),
        fisher_pack=fisher_pack,
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

    root = outputs_root / "buffett_munger_quality_risk_packs"
    output_folder = root / pack_run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "buffett_munger_quality_risk_pack.md"
    json_path = output_folder / "buffett_munger_quality_risk_pack.json"
    buffett_summary_path = output_folder / "buffett_quality_summary.json"
    munger_summary_path = output_folder / "munger_quality_summary.json"
    quality_matrix_csv_path = output_folder / "quality_evidence_matrix.csv"
    owner_earnings_csv_path = (
        output_folder / "owner_earnings_intrinsic_value_requirements.csv"
    )
    capital_allocation_csv_path = (
        output_folder / "capital_allocation_balance_sheet_matrix.csv"
    )
    munger_risk_csv_path = output_folder / "munger_inversion_risk_matrix.csv"
    requirements_status_csv_path = (
        output_folder / "buffett_munger_evidence_requirements_status.csv"
    )
    required_controls_path = output_folder / "buffett_munger_required_controls.json"
    latest_manifest_path = root / "latest_buffett_munger_quality_risk_pack_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    buffett_summary_path.write_text(
        json.dumps(report.buffett_quality_summary, indent=2),
        encoding="utf-8",
    )
    munger_summary_path.write_text(
        json.dumps(report.munger_quality_summary, indent=2),
        encoding="utf-8",
    )
    _write_csv(quality_matrix_csv_path, report.quality_evidence_matrix)
    _write_csv(
        owner_earnings_csv_path,
        report.owner_earnings_intrinsic_value_requirements,
    )
    _write_csv(
        capital_allocation_csv_path,
        report.capital_allocation_balance_sheet_matrix,
    )
    _write_csv(munger_risk_csv_path, report.munger_inversion_risk_matrix)
    _write_csv(
        requirements_status_csv_path,
        report.buffett_munger_evidence_requirements_status,
    )
    required_controls_path.write_text(
        json.dumps(report.buffett_munger_required_controls, indent=2),
        encoding="utf-8",
    )
    latest_manifest_path.write_text(
        json.dumps(
            {
                "buffett_munger_pack_run_id": report.buffett_munger_pack_run_id,
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
                "buffett_munger_pack_status": report.buffett_munger_pack_status,
                "recommended_next_work_order": report.recommended_next_work_order,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "buffett_summary_path": str(buffett_summary_path),
                "munger_summary_path": str(munger_summary_path),
                "quality_matrix_csv_path": str(quality_matrix_csv_path),
                "owner_earnings_csv_path": str(owner_earnings_csv_path),
                "capital_allocation_csv_path": str(capital_allocation_csv_path),
                "munger_risk_csv_path": str(munger_risk_csv_path),
                "requirements_status_csv_path": str(requirements_status_csv_path),
                "required_controls_path": str(required_controls_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return BuffettMungerQualityRiskPackFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        buffett_summary_path=buffett_summary_path,
        munger_summary_path=munger_summary_path,
        quality_matrix_csv_path=quality_matrix_csv_path,
        owner_earnings_csv_path=owner_earnings_csv_path,
        capital_allocation_csv_path=capital_allocation_csv_path,
        munger_risk_csv_path=munger_risk_csv_path,
        requirements_status_csv_path=requirements_status_csv_path,
        required_controls_path=required_controls_path,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
