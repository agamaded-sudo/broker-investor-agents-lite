"""BO-006 persona-specific evidence pack requirements."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report defines evidence requirements only. It does not create "
    "investor decisions, recommendations, rankings, allocation instructions, "
    "rebalancing instructions, trade signals, execution instructions, strategy "
    "validation, or investment advice."
)
WORK_ORDER_ID = "BO-006"
WORK_ORDER_TITLE = "Persona-Specific Evidence Pack Requirements"
NEXT_WORK_ORDER = "BO-007 Bogle Benchmark / Index Comparison Pack"
PERSONAS = ("Buffett", "Munger", "Fisher", "Lynch", "Bogle")
COMMON_ARTIFACTS = (
    "research_gatekeeper_report",
    "research_evidence_scorecard",
    "expanded_trial_results_analysis",
    "backtest_driver_decomposition",
    "outlier_repair_path",
    "walk_forward_repair_plan",
    "delayed_anchor_repair",
    "metadata_diversity_recheck",
)
PERSONA_ARTIFACTS = {
    "Buffett": "buffett_owner_earnings_and_intrinsic_value_pack",
    "Munger": "munger_quality_and_risk_pack",
    "Fisher": "fisher_qualitative_growth_pack",
    "Lynch": "lynch_story_category_growth_pack",
    "Bogle": "bogle_index_comparison_pack",
}
ISSUE_PRIORITY = {
    "benchmark_relative_underperformance": "P0",
    "walk_forward_instability": "P0",
    "expanded_cohort_underperformance": "P0",
    "period_sensitivity": "P1",
    "outlier_dependence": "P0",
    "delayed_anchor_effect": "P1",
    "metadata_diversity_partial_concentration": "P2",
    "investor_interest_low_diversity": "P2",
    "persona_specific_evidence_gaps": "P1",
    "qualitative_depth_gaps": "P2",
    "index_comparison_gap": "P1",
}


@dataclass(frozen=True)
class PersonaEvidencePackRequirementsReport:
    """Structured BO-006 requirements report."""

    persona_evidence_pack_run_id: str
    generated_at: str
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
    persona_evidence_pack_status: str
    persona_requirement_matrix: list[dict]
    persona_evidence_gap_linkage: list[dict]
    persona_required_artifacts: list[dict]
    persona_checklists: dict
    common_requirements: dict
    recommended_next_work_order: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class PersonaEvidencePackRequirementsFiles:
    """Generated BO-006 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    matrix_csv_path: Path
    gap_linkage_csv_path: Path
    required_artifacts_csv_path: Path
    checklists_path: Path
    latest_manifest_path: Path
    report: PersonaEvidencePackRequirementsReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_metadata_diversity_recheck_manifest(
    *,
    outputs_root: Path,
    metadata_diversity_recheck_run_id: str | None = None,
) -> dict:
    """Load one BO-005 report or the latest BO-005 manifest."""
    root = Path(outputs_root) / "metadata_diversity_rechecks"
    path = (
        root
        / str(metadata_diversity_recheck_run_id)
        / "metadata_diversity_recheck_report.json"
        if metadata_diversity_recheck_run_id
        else root / "latest_metadata_diversity_recheck_manifest.json"
    )
    payload = _load_required_json(path, "Metadata diversity recheck manifest")
    payload["_manifest_path"] = str(path)
    return payload


def load_metadata_diversity_recheck_report(
    *, outputs_root: Path, metadata_diversity_recheck_run_id: str
) -> dict:
    """Load a complete BO-005 metadata diversity report."""
    path = (
        Path(outputs_root)
        / "metadata_diversity_rechecks"
        / str(metadata_diversity_recheck_run_id)
        / "metadata_diversity_recheck_report.json"
    )
    return _load_required_json(path, "Metadata diversity recheck report")


def load_delayed_anchor_repair_report(
    *, outputs_root: Path, delayed_anchor_repair_run_id: str
) -> dict:
    return _load_optional_json(
        Path(outputs_root)
        / "delayed_anchor_repairs"
        / str(delayed_anchor_repair_run_id)
        / "delayed_anchor_repair_report.json"
    )


def load_walk_forward_repair_report(
    *, outputs_root: Path, walk_forward_repair_run_id: str
) -> dict:
    return _load_optional_json(
        Path(outputs_root)
        / "walk_forward_repair_plans"
        / str(walk_forward_repair_run_id)
        / "walk_forward_repair_plan_report.json"
    )


def load_outlier_repair_report(
    *, outputs_root: Path, outlier_repair_run_id: str
) -> dict:
    return _load_optional_json(
        Path(outputs_root)
        / "outlier_repair_paths"
        / str(outlier_repair_run_id)
        / "outlier_repair_path_report.json"
    )


def load_backtest_driver_decomposition_report(
    *, outputs_root: Path, decomposition_run_id: str
) -> dict:
    return _load_optional_json(
        Path(outputs_root)
        / "backtest_driver_decompositions"
        / str(decomposition_run_id)
        / "backtest_driver_decomposition_report.json"
    )


def load_investor_persona_attribution_report(
    *, outputs_root: Path, investor_persona_attribution_run_id: str
) -> dict:
    return _load_optional_json(
        Path(outputs_root)
        / "investor_persona_attributions"
        / str(investor_persona_attribution_run_id)
        / "investor_persona_attribution_report.json"
    )


def load_backoffice_attribution_report(
    *, outputs_root: Path, backoffice_attribution_run_id: str
) -> dict:
    return _load_optional_json(
        Path(outputs_root)
        / "backoffice_evidence_quality_attributions"
        / str(backoffice_attribution_run_id)
        / "backoffice_evidence_quality_attribution_report.json"
    )


def _persona_status(persona: str, persona_attribution: dict) -> str:
    lookup = {
        item.get("persona", "").replace(" Agent", ""): item
        for item in persona_attribution.get("persona_attributions", [])
    }
    return lookup.get(persona, {}).get(
        "persona_readiness_status", "not_ready_for_persona_review"
    )


def _primary_blockers(persona: str) -> list[str]:
    common = [
        "gatekeeper_hold",
        "benchmark_relative_underperformance",
        "walk_forward_instability",
        "expanded_cohort_underperformance",
    ]
    persona_specific = {
        "Buffett": ["owner_earnings_gap", "intrinsic_value_gap"],
        "Munger": ["inversion_gap", "hidden_risk_gap"],
        "Fisher": ["qualitative_growth_gap", "scuttlebutt_proxy_gap"],
        "Lynch": ["story_category_gap", "growth_valuation_gap"],
        "Bogle": ["index_comparison_gap", "concentration_risk_gap"],
    }
    return common + persona_specific[persona]


def build_persona_pack_checklists() -> dict:
    """Create persona-specific evidence checklists."""
    return {
        "Buffett": [
            "durable business quality evidence",
            "normalized owner earnings evidence",
            "intrinsic value range with assumptions",
            "margin of safety discussion without recommendation",
            "capital allocation evidence",
            "balance sheet and debt risk evidence",
            "long-term economics",
            "management quality and incentives evidence",
            "historical benchmark-relative weakness explanation",
            "current_core vs expanded_cohort separation",
            "anchor and walk-forward controls",
            "why evidence is not yet sufficient for review",
        ],
        "Munger": [
            "business quality and moat evidence",
            "incentives and agency risk evidence",
            "inversion/risk checklist",
            "hidden stupidity / failure mode checklist",
            "capital allocation discipline",
            "balance sheet resilience",
            "outlier dependence explanation",
            "negative cohort drag explanation",
            "qualitative depth requirements",
            "source verification requirements",
            "why evidence is not yet sufficient for review",
        ],
        "Fisher": [
            "qualitative growth evidence",
            "product pipeline evidence",
            "R&D / innovation evidence",
            "sales organization evidence",
            "market expansion evidence",
            "management depth",
            "customer / competitive scuttlebutt proxy evidence",
            "durable growth runway evidence",
            "evidence separating concentrated metadata groups",
            "qualitative evidence gaps",
            "why evidence is not yet sufficient for review",
        ],
        "Lynch": [
            "company story evidence",
            "category classification evidence",
            "growth versus valuation evidence",
            "PEG or growth reasonableness evidence where available",
            "simple understandable thesis",
            "earnings trend evidence",
            "balance sheet sanity check",
            "expanded cohort underperformance explanation",
            "category and universe group concentration controls",
            "why evidence is not yet sufficient for review",
        ],
        "Bogle": [
            "benchmark-relative evidence",
            "index comparison evidence",
            "broad index alternative framing",
            "concentration risk evidence",
            "sector/category concentration evidence",
            "cost/tax/friction-neutral discussion if applicable",
            "single-stock versus index exposure limitations",
            "full sample vs benchmark comparison",
            "clean-anchor/delayed-anchor separation",
            "walk-forward stability controls",
            "why evidence is not yet sufficient for review",
        ],
    }


def derive_persona_evidence_gaps() -> dict[str, list[str]]:
    """Return required issue-code linkage by persona."""
    common = [
        "benchmark_relative_underperformance",
        "walk_forward_instability",
        "expanded_cohort_underperformance",
        "period_sensitivity",
        "outlier_dependence",
        "delayed_anchor_effect",
        "metadata_diversity_partial_concentration",
        "investor_interest_low_diversity",
        "persona_specific_evidence_gaps",
    ]
    return {
        "Buffett": common + ["qualitative_depth_gaps"],
        "Munger": common + ["qualitative_depth_gaps"],
        "Fisher": common + ["qualitative_depth_gaps"],
        "Lynch": common + ["qualitative_depth_gaps"],
        "Bogle": common + ["index_comparison_gap"],
    }


def _why_issue_matters(persona: str, issue: str) -> str:
    phrases = {
        "benchmark_relative_underperformance": "weakens comparison against the benchmark baseline",
        "walk_forward_instability": "prevents stable historical review",
        "expanded_cohort_underperformance": "shows prior core evidence did not generalize",
        "period_sensitivity": "shows timing dependence",
        "outlier_dependence": "requires contributor controls before review",
        "delayed_anchor_effect": "requires clean-anchor and delayed-anchor separation",
        "metadata_diversity_partial_concentration": "limits generalization across metadata groups",
        "investor_interest_low_diversity": "limits persona metadata differentiation",
        "persona_specific_evidence_gaps": "blocks persona-specific review preparation",
        "qualitative_depth_gaps": "leaves persona qualitative requirements incomplete",
        "index_comparison_gap": "blocks benchmark and index framing required for Bogle",
    }
    return f"For {persona}, this {phrases.get(issue, 'requires repair evidence')}."


def build_persona_requirement_matrix(
    *, persona_attribution: dict, checklists: dict
) -> list[dict]:
    """Create one requirement row per persona."""
    rows = []
    for persona in PERSONAS:
        rows.append(
            {
                "persona": persona,
                "current_persona_status": _persona_status(persona, persona_attribution),
                "gatekeeper_allowed": False,
                "primary_blockers": _primary_blockers(persona),
                "evidence_pack_required": True,
                "quantitative_evidence_required": [
                    "benchmark-relative evidence",
                    "current_core vs expanded_cohort controls",
                    "walk-forward controls",
                    "outlier controls",
                ],
                "qualitative_evidence_required": [
                    item
                    for item in checklists[persona]
                    if "evidence" in item or "checklist" in item
                ],
                "source_evidence_required": [
                    "source verification requirements",
                    "no fabricated metadata or coverage",
                ],
                "metadata_controls_required": [
                    "sector/category/universe_group/cohort separation",
                ],
                "anchor_controls_required": [
                    "clean-anchor and delayed-anchor separate reporting",
                ],
                "walk_forward_controls_required": [
                    "post-2021 periods and supportive period controls",
                ],
                "outlier_controls_required": [
                    "Ex-NVDA and ex-top-2 controls",
                ],
                "benchmark_controls_required": [
                    "absolute and benchmark-relative evidence separately",
                ],
                "minimum_required_artifacts": list(COMMON_ARTIFACTS)
                + [PERSONA_ARTIFACTS[persona]],
                "cannot_review_until": [
                    "gatekeeper hold is cleared",
                    "persona evidence pack is completed",
                    "repair controls are rerun and documented",
                ],
                "next_backoffice_action": PERSONA_ARTIFACTS[persona],
                "readiness_after_pack": "requirements_defined_only",
                "safety_boundary": (
                    "Requirements only; no persona decision or progression."
                ),
            }
        )
    return rows


def build_persona_readiness_blockers(matrix: list[dict]) -> dict:
    """Summarize conservative readiness blockers."""
    return {
        row["persona"]: row["primary_blockers"] for row in matrix
    }


def build_persona_evidence_gap_linkage(checklists: dict) -> list[dict]:
    """Create persona-to-issue evidence gap linkage rows."""
    gaps = derive_persona_evidence_gaps()
    rows = []
    for persona, issues in gaps.items():
        for issue in issues:
            rows.append(
                {
                    "persona": persona,
                    "issue_code": issue,
                    "issue_priority": ISSUE_PRIORITY[issue],
                    "why_it_matters_to_persona": _why_issue_matters(persona, issue),
                    "required_evidence": "; ".join(checklists[persona][:4]),
                    "blocking_status": "blocks_persona_review_until_repaired",
                }
            )
    return rows


def build_required_artifacts() -> list[dict]:
    """Build common and persona-specific artifact requirements."""
    rows = []
    for persona in PERSONAS:
        for artifact in COMMON_ARTIFACTS:
            rows.append(
                {
                    "persona": persona,
                    "artifact": artifact,
                    "required": True,
                    "purpose": "Common governance and repair context.",
                }
            )
        rows.append(
            {
                "persona": persona,
                "artifact": PERSONA_ARTIFACTS[persona],
                "required": True,
                "purpose": f"Persona-specific evidence package for {persona}.",
            }
        )
    return rows


def _common_requirements(metadata: dict) -> dict:
    return {
        "gatekeeper_decision": "hold",
        "progression_allowed": False,
        "metadata_diversity_status": metadata.get(
            "concentration_classification", {}
        ).get("metadata_diversity_status", "unknown"),
        "required_common_artifacts": list(COMMON_ARTIFACTS),
        "common_controls": [
            "current_core and expanded_cohort separation",
            "clean-anchor and delayed-anchor separation",
            "Ex-NVDA and ex-top-2 controls",
            "supportive-period and post-2021 period controls",
            "benchmark-relative and absolute evidence separation",
        ],
    }


def build_persona_evidence_pack_requirements(
    *,
    persona_evidence_pack_run_id: str,
    generated_at: str,
    metadata: dict,
    delayed_anchor: dict,
    walk_forward: dict,
    outlier: dict,
    decomposition: dict,
    persona_attribution: dict,
    backoffice: dict,
) -> PersonaEvidencePackRequirementsReport:
    """Build the full BO-006 persona evidence requirements report."""
    checklists = build_persona_pack_checklists()
    matrix = build_persona_requirement_matrix(
        persona_attribution=persona_attribution,
        checklists=checklists,
    )
    return PersonaEvidencePackRequirementsReport(
        persona_evidence_pack_run_id=persona_evidence_pack_run_id,
        generated_at=generated_at,
        metadata_diversity_recheck_run_id=str(
            metadata.get("metadata_diversity_recheck_run_id") or ""
        ),
        delayed_anchor_repair_run_id=str(
            metadata.get("delayed_anchor_repair_run_id") or ""
        ),
        walk_forward_repair_run_id=str(
            metadata.get("walk_forward_repair_run_id") or ""
        ),
        outlier_repair_run_id=str(metadata.get("outlier_repair_run_id") or ""),
        decomposition_run_id=str(metadata.get("decomposition_run_id") or ""),
        backoffice_attribution_run_id=str(
            metadata.get("backoffice_attribution_run_id") or ""
        ),
        investor_persona_attribution_run_id=str(
            metadata.get("investor_persona_attribution_run_id") or ""
        ),
        gatekeeper_run_id=str(metadata.get("gatekeeper_run_id") or ""),
        scorecard_run_id=str(metadata.get("scorecard_run_id") or ""),
        analysis_run_id=str(metadata.get("analysis_run_id") or ""),
        expanded_trial_run_id=str(metadata.get("expanded_trial_run_id") or ""),
        backtest_run_id=str(metadata.get("backtest_run_id") or ""),
        work_order_id=WORK_ORDER_ID,
        work_order_title=WORK_ORDER_TITLE,
        persona_evidence_pack_status="completed",
        persona_requirement_matrix=matrix,
        persona_evidence_gap_linkage=build_persona_evidence_gap_linkage(checklists),
        persona_required_artifacts=build_required_artifacts(),
        persona_checklists=checklists,
        common_requirements=_common_requirements(metadata),
        recommended_next_work_order=NEXT_WORK_ORDER,
    )


def _display(value) -> str:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value) or "None"
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return "" if value is None else str(value)


def _table_cell(value) -> str:
    return _display(value).replace("|", "\\|")


def render_persona_evidence_pack_requirements_report(
    report: PersonaEvidencePackRequirementsReport,
) -> str:
    """Render BO-006 as Markdown."""
    data = report.to_dict()
    lines = [
        "# Persona-Specific Evidence Pack Requirements Report",
        "",
        "## Executive Summary",
        "",
        f"- Persona Evidence Pack Run ID: {data['persona_evidence_pack_run_id']}",
        (
            "- Metadata Diversity Recheck Run ID: "
            f"{data['metadata_diversity_recheck_run_id']}"
        ),
        f"- Work Order ID: {data['work_order_id']}",
        f"- Backtest Run ID: {data['backtest_run_id']}",
        "- Gatekeeper Decision: hold",
        "- Progression Allowed: false",
        (
            "- Main Finding: Persona review remains blocked; BO-006 defines "
            "persona-specific evidence requirements only."
        ),
        f"- Recommended Next Work Order: {data['recommended_next_work_order']}",
        "",
        "## Important Boundary",
        "",
        (
            "This report defines evidence requirements only. It does not create "
            "investor decisions, rankings, recommendations, allocations, "
            "rebalancing instructions, trade signals, or execution instructions."
        ),
        "",
        "## Source Context",
        "",
        "- Gatekeeper Decision: hold",
        "- Progression Allowed: false",
        f"- Current Work Order: {data['work_order_id']}",
        (
            "- Reason: persona-specific evidence gaps, qualitative depth gaps, "
            "and investor-interest low diversity."
        ),
        "",
        "## Common Evidence Requirements",
        "",
        f"- Required Artifacts: {_display(data['common_requirements']['required_common_artifacts'])}",
        f"- Common Controls: {_display(data['common_requirements']['common_controls'])}",
    ]
    for persona in PERSONAS:
        lines.extend(["", f"## {persona} Evidence Pack Requirements", ""])
        for item in data["persona_checklists"][persona]:
            lines.append(f"- [ ] {item}")
    lines.extend(
        [
            "",
            "## Evidence Gap Linkage",
            "",
            "| Persona | Issue Code | Priority | Why It Matters | Required Evidence | Blocking Status |",
            "|---|---|---|---|---|---|",
        ]
    )
    for item in data["persona_evidence_gap_linkage"]:
        lines.append(
            f"| {item['persona']} | {item['issue_code']} | "
            f"{item['issue_priority']} | "
            f"{_table_cell(item['why_it_matters_to_persona'])} | "
            f"{_table_cell(item['required_evidence'])} | "
            f"{item['blocking_status']} |"
        )
    lines.extend(
        [
            "",
            "## Persona Requirement Matrix",
            "",
            (
                "| Persona | Current Status | Gatekeeper Allowed | Primary Blockers | "
                "Readiness After Pack |"
            ),
            "|---|---|---|---|---|",
        ]
    )
    for item in data["persona_requirement_matrix"]:
        lines.append(
            f"| {item['persona']} | {item['current_persona_status']} | "
            f"{str(item['gatekeeper_allowed']).lower()} | "
            f"{_table_cell(item['primary_blockers'])} | "
            f"{item['readiness_after_pack']} |"
        )
    lines.extend(
        [
            "",
            "## Required Artifacts",
            "",
            "| Persona | Artifact | Required | Purpose |",
            "|---|---|---|---|",
        ]
    )
    for item in data["persona_required_artifacts"]:
        lines.append(
            f"| {item['persona']} | {item['artifact']} | "
            f"{str(item['required']).lower()} | {item['purpose']} |"
        )
    lines.extend(
        [
            "",
            "## What This Suggests",
            "",
            "- Persona review remains blocked by Gatekeeper HOLD.",
            (
                "- Backoffice can now build persona-specific evidence packs in "
                "the correct order."
            ),
            "",
            "## What This Does Not Suggest",
            "",
            "- It does not ask personas to decide.",
            "- It does not rank personas.",
            "- It does not rank companies.",
            "- It does not recommend buying or selling.",
            "- It does not validate investor agents.",
            "- It does not create a trade signal.",
            "- It does not justify allocation or rebalancing.",
            "",
            "## Next Work Order",
            "",
            f"- {data['recommended_next_work_order']}",
            "",
            "## Safety Notice",
            "",
            data["safety_notice"],
            "",
        ]
    )
    return "\n".join(lines)


def _csv_value(value) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return "" if value is None else str(value)


def _write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in fields})


def write_persona_evidence_pack_requirements_report(
    *,
    outputs_root: Path,
    metadata_diversity_recheck_run_id: str | None = None,
    generated_at: datetime | None = None,
) -> PersonaEvidencePackRequirementsFiles:
    """Load BO-006 inputs and write persona evidence pack requirement artifacts."""
    outputs_root = Path(outputs_root)
    timestamp = generated_at or datetime.now(timezone.utc)
    manifest = load_metadata_diversity_recheck_manifest(
        outputs_root=outputs_root,
        metadata_diversity_recheck_run_id=metadata_diversity_recheck_run_id,
    )
    selected_id = str(
        metadata_diversity_recheck_run_id
        or manifest.get("metadata_diversity_recheck_run_id")
        or ""
    )
    if not selected_id:
        raise ValueError("Metadata diversity recheck run ID is required.")
    metadata = (
        manifest
        if metadata_diversity_recheck_run_id
        else load_metadata_diversity_recheck_report(
            outputs_root=outputs_root,
            metadata_diversity_recheck_run_id=selected_id,
        )
    )
    delayed_anchor = load_delayed_anchor_repair_report(
        outputs_root=outputs_root,
        delayed_anchor_repair_run_id=str(
            metadata.get("delayed_anchor_repair_run_id") or ""
        ),
    )
    walk_forward = load_walk_forward_repair_report(
        outputs_root=outputs_root,
        walk_forward_repair_run_id=str(metadata.get("walk_forward_repair_run_id") or ""),
    )
    outlier = load_outlier_repair_report(
        outputs_root=outputs_root,
        outlier_repair_run_id=str(metadata.get("outlier_repair_run_id") or ""),
    )
    decomposition = load_backtest_driver_decomposition_report(
        outputs_root=outputs_root,
        decomposition_run_id=str(metadata.get("decomposition_run_id") or ""),
    )
    persona_attribution = load_investor_persona_attribution_report(
        outputs_root=outputs_root,
        investor_persona_attribution_run_id=str(
            metadata.get("investor_persona_attribution_run_id") or ""
        ),
    )
    backoffice = load_backoffice_attribution_report(
        outputs_root=outputs_root,
        backoffice_attribution_run_id=str(
            metadata.get("backoffice_attribution_run_id") or ""
        ),
    )
    root = outputs_root / "persona_evidence_pack_requirements"
    root.mkdir(parents=True, exist_ok=True)
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    run_id = base
    suffix = 2
    while (root / run_id).exists():
        run_id = f"{base}_{suffix:02d}"
        suffix += 1
    report = build_persona_evidence_pack_requirements(
        persona_evidence_pack_run_id=run_id,
        generated_at=timestamp.isoformat(),
        metadata=metadata,
        delayed_anchor=delayed_anchor,
        walk_forward=walk_forward,
        outlier=outlier,
        decomposition=decomposition,
        persona_attribution=persona_attribution,
        backoffice=backoffice,
    )
    folder = root / run_id
    folder.mkdir(parents=True, exist_ok=False)
    markdown_path = folder / "persona_evidence_pack_requirements_report.md"
    json_path = folder / "persona_evidence_pack_requirements_report.json"
    matrix_path = folder / "persona_requirement_matrix.csv"
    gap_path = folder / "persona_evidence_gap_linkage.csv"
    artifacts_path = folder / "persona_required_artifacts.csv"
    checklists_path = folder / "persona_checklists.json"
    markdown_path.write_text(
        render_persona_evidence_pack_requirements_report(report),
        encoding="utf-8",
    )
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(matrix_path, report.persona_requirement_matrix)
    _write_csv(gap_path, report.persona_evidence_gap_linkage)
    _write_csv(artifacts_path, report.persona_required_artifacts)
    checklists_path.write_text(
        json.dumps(report.persona_checklists, indent=2),
        encoding="utf-8",
    )
    latest_path = root / "latest_persona_evidence_pack_requirements_manifest.json"
    latest_payload = {
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
        "persona_evidence_pack_status": report.persona_evidence_pack_status,
        "recommended_next_work_order": report.recommended_next_work_order,
        "output_folder": str(folder),
        "report_path": str(markdown_path),
        "report_json_path": str(json_path),
        "matrix_csv_path": str(matrix_path),
        "gap_linkage_csv_path": str(gap_path),
        "required_artifacts_csv_path": str(artifacts_path),
        "checklists_path": str(checklists_path),
        "safety_notice": report.safety_notice,
    }
    latest_path.write_text(json.dumps(latest_payload, indent=2), encoding="utf-8")
    return PersonaEvidencePackRequirementsFiles(
        output_folder=folder,
        markdown_path=markdown_path,
        json_path=json_path,
        matrix_csv_path=matrix_path,
        gap_linkage_csv_path=gap_path,
        required_artifacts_csv_path=artifacts_path,
        checklists_path=checklists_path,
        latest_manifest_path=latest_path,
        report=report,
    )
