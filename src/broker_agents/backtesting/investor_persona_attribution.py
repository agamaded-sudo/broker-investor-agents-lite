"""Research-only evidence attribution for independent investor personas."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This attribution report does not ask investor personas for decisions, "
    "does not combine or rank them, and is not a recommendation, consensus, "
    "allocation instruction, rebalancing instruction, trade signal, execution "
    "instruction, strategy validation, or investment advice."
)
NEXT_RESEARCH_ACTION = "backoffice_evidence_quality_attribution"
COMMON_HOLDING_FACTORS = [
    "unstable research evidence",
    "negative benchmark-relative performance",
    "unstable walk-forward results",
    "expanded cohort underperformance",
    "period sensitivity",
    "outlier dependence",
    "delayed anchor caution",
    "research gatekeeper hold",
]


@dataclass(frozen=True)
class PersonaAttribution:
    """Persona-specific mapping from evidence quality to future review needs."""

    persona: str
    persona_focus: list[str]
    gatekeeper_effect: str
    persona_readiness_status: str
    evidence_strengths_for_persona: list[str]
    evidence_weaknesses_for_persona: list[str]
    blocking_or_holding_factors: list[str]
    evidence_needed_before_persona_review: list[str]
    backoffice_follow_up_requests: list[str]
    safety_note: str

    def to_dict(self) -> dict:
        """Return a JSON-ready attribution row."""
        return asdict(self)


@dataclass(frozen=True)
class InvestorPersonaAttributionReport:
    """Attribution report linked to one research gatekeeper run."""

    attribution_run_id: str
    generated_at: str
    gatekeeper_run_id: str
    scorecard_run_id: str
    analysis_run_id: str
    expanded_trial_run_id: str
    backtest_run_id: str
    research_evidence_classification: str
    research_decision: str
    gatekeeper_decision: str
    progression_allowed: bool
    hold_bias: bool
    attribution_status: str
    persona_attributions: list[dict]
    cross_persona_summary: dict
    common_holding_factors: list[str]
    recommended_next_research_action: str
    limitations: list[str]
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class InvestorPersonaAttributionFiles:
    """Generated persona attribution files and structured report."""

    attribution_folder: Path
    markdown_path: Path
    json_path: Path
    matrix_csv_path: Path
    latest_manifest_path: Path
    report: InvestorPersonaAttributionReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_research_gatekeeper_manifest(
    *,
    outputs_root: Path,
    gatekeeper_run_id: str | None = None,
) -> dict:
    """Load one gatekeeper report or the latest gatekeeper manifest."""
    root = Path(outputs_root) / "research_gatekeepers"
    path = (
        root / str(gatekeeper_run_id) / "research_gatekeeper_report.json"
        if gatekeeper_run_id
        else root / "latest_research_gatekeeper_manifest.json"
    )
    payload = _load_required_json(path, "Research gatekeeper manifest")
    payload["_manifest_path"] = str(path)
    return payload


def load_research_gatekeeper_report(
    *,
    outputs_root: Path,
    gatekeeper_run_id: str,
) -> dict:
    """Load the complete gatekeeper JSON for a selected run."""
    path = (
        Path(outputs_root)
        / "research_gatekeepers"
        / str(gatekeeper_run_id)
        / "research_gatekeeper_report.json"
    )
    return _load_required_json(path, "Research gatekeeper report")


def load_research_evidence_scorecard_report(
    *,
    outputs_root: Path,
    scorecard_run_id: str,
) -> dict:
    """Load linked scorecard context when it remains available."""
    path = (
        Path(outputs_root)
        / "research_evidence_scorecards"
        / str(scorecard_run_id)
        / "research_evidence_scorecard_report.json"
    )
    return _load_optional_json(path)


def load_expanded_trial_analysis_report(
    *,
    outputs_root: Path,
    analysis_run_id: str,
) -> dict:
    """Load linked expanded-trial analysis context when available."""
    path = (
        Path(outputs_root)
        / "expanded_trial_analyses"
        / str(analysis_run_id)
        / "expanded_trial_analysis_report.json"
    )
    return _load_optional_json(path)


def _readiness_status(
    *,
    persona: str,
    gatekeeper: dict,
) -> str:
    if gatekeeper.get("progression_allowed"):
        return "persona_review_possible_after_repair"
    if persona == "Lynch Agent":
        return "persona_review_possible_for_watchlist_only"
    if persona == "Bogle Agent":
        return "not_ready_for_persona_review"
    return "persona_review_possible_after_repair"


def _persona_templates() -> list[dict]:
    return [
        {
            "persona": "Buffett Agent",
            "focus": [
                "durable business quality",
                "owner earnings",
                "intrinsic value discipline",
                "margin of safety",
                "long-term predictability",
                "management and capital allocation",
                "evidence stability",
            ],
            "strengths": [
                "Clean evidence is available across a meaningful subset.",
                "Data-quality integrity and decision conservatism are intact.",
                "Warning-heavy evidence is absent.",
            ],
            "weaknesses": [
                "Long-term evidence is unstable across periods.",
                "Benchmark-relative evidence weakened after universe expansion.",
                "Outlier and cohort sensitivity reduce confidence in predictability.",
            ],
            "holding": [
                "unstable walk-forward results",
                "expanded cohort underperformance",
                "period and outlier sensitivity",
            ],
            "needed": [
                "More stable long-term owner earnings evidence.",
                "Robust valuation history and intrinsic value ranges.",
                "A wider and longer historical sample.",
                "An explanation of benchmark-relative underperformance.",
                "Company-level durable moat evidence.",
                "Margin-of-safety evidence under conservative assumptions.",
            ],
            "follow_up": [
                "Refresh normalized owner earnings histories.",
                "Extend historical valuation and capital-allocation evidence.",
                "Document moat durability and management stewardship by company.",
            ],
        },
        {
            "persona": "Munger Agent",
            "focus": [
                "inversion",
                "incentives",
                "avoiding stupidity",
                "business quality",
                "capital allocation",
                "hidden risks",
                "robustness under stress",
                "valuation discipline",
            ],
            "strengths": [
                "The expanded run completed without operational failures.",
                "Clean evidence exists and warning-heavy evidence is absent.",
                "The governance layer is refusing premature progression.",
            ],
            "weaknesses": [
                "Outlier and period sensitivity expose failure modes.",
                "Unstable walk-forward evidence raises inversion questions.",
                "Delayed anchors remain a material timing caution.",
            ],
            "holding": [
                "outlier dependence",
                "delayed anchor effect",
                "period sensitivity",
                "unstable walk-forward results",
            ],
            "needed": [
                "A documented failure-mode and inversion analysis.",
                "Incentive and capital-allocation evidence.",
                "A hidden-risk and avoidable-error decomposition.",
                "Evidence that results do not depend on timing or outliers.",
                "An updated hidden-stupidity checklist.",
            ],
            "follow_up": [
                "Prepare incentive and capital-allocation work orders.",
                "Run a company-level failure-mode audit.",
                "Separate anchor timing, cohort, and outlier risks.",
            ],
        },
        {
            "persona": "Fisher Agent",
            "focus": [
                "qualitative growth",
                "management depth",
                "sales and scuttlebutt evidence",
                "research and product pipeline",
                "long-term growth runway",
                "operational excellence",
                "evidence depth",
            ],
            "strengths": [
                "The larger sample supplies broader company coverage.",
                "Clean evidence and valid ledger construction support future review.",
                "Short historical instability does not replace qualitative research.",
            ],
            "weaknesses": [
                "Expanded-cohort evidence is unstable.",
                "Qualitative management and product evidence remains too shallow.",
                "Period effects may be masking the durability of growth quality.",
            ],
            "holding": [
                "expanded cohort underperformance",
                "missing qualitative depth",
                "period sensitivity",
            ],
            "needed": [
                "Product and long-term growth runway evidence.",
                "Management depth and execution-quality evidence.",
                "Competitive-position and operational-excellence evidence.",
                "Customer, channel, and scuttlebutt indicators.",
                "Evidence that growth quality survives different market periods.",
            ],
            "follow_up": [
                "Expand management and product-pipeline evidence packs.",
                "Collect structured customer and competitive-position indicators.",
                "Map growth durability against historical periods.",
            ],
        },
        {
            "persona": "Lynch Agent",
            "focus": [
                "understandable company story",
                "category classification",
                "growth at reasonable price",
                "earnings growth versus price",
                "company-specific attribution",
                "story deterioration",
                "expectations versus reality",
            ],
            "strengths": [
                "Ticker-level attribution is available across a wider universe.",
                "Clean and warning evidence remain separated.",
                "The expanded trial exposes which company stories did not generalize.",
            ],
            "weaknesses": [
                "The broad expanded story underperformed the prior core cohort.",
                "Period sensitivity suggests regime-dependent narratives.",
                "Benchmark-relative weakness limits research readiness.",
            ],
            "holding": [
                "expanded cohort underperformance",
                "period sensitivity",
                "benchmark-relative weakness",
            ],
            "needed": [
                "A category-by-company review.",
                "Growth and PEG context.",
                "Evidence of earnings-story persistence.",
                "Company-level attribution by ticker.",
                "An explanation of which ticker stories weakened after expansion.",
            ],
            "follow_up": [
                "Refresh category and growth-PEG mappings.",
                "Prepare ticker-level earnings-story persistence summaries.",
                "Compare expectations with subsequent operating evidence.",
            ],
        },
        {
            "persona": "Bogle Agent",
            "focus": [
                "broad diversification",
                "index exposure",
                "cost and simplicity",
                "concentration avoidance",
                "skepticism toward active selection",
                "benchmark-relative evidence",
            ],
            "strengths": [
                "The universe expanded and data-quality controls remained sound.",
                "Concentration and metadata diversity are measured explicitly.",
                "The benchmark comparison is visible rather than suppressed.",
            ],
            "weaknesses": [
                "Median benchmark-relative performance is negative.",
                "The benchmark hit rate remains below one half.",
                "Instability and partial concentration reinforce active-selection skepticism.",
            ],
            "holding": [
                "negative benchmark-relative performance",
                "low benchmark hit rate",
                "unstable evidence",
                "partial concentration",
            ],
            "needed": [
                "Improved benchmark-relative evidence.",
                "Evidence that active selection adds value versus the index.",
                "A concentration-risk explanation.",
                "Index overlap and diversification comparisons.",
                "A simple cost-aware active-versus-index research comparison.",
            ],
            "follow_up": [
                "Refresh index-overlap and concentration analysis.",
                "Prepare benchmark-relative attribution by period and cohort.",
                "Document the simplest diversified comparison baseline.",
            ],
        },
    ]


def attribute_evidence_to_personas(
    *,
    gatekeeper: dict,
    scorecard: dict,
    analysis: dict,
) -> list[PersonaAttribution]:
    """Build five independent persona evidence attributions."""
    del scorecard, analysis
    decision = gatekeeper.get("gatekeeper_decision") or "unknown"
    progression_allowed = bool(gatekeeper.get("progression_allowed"))
    gatekeeper_effect = (
        "The gatekeeper hold prevents persona review progression until the "
        "persona-specific evidence gaps are repaired."
        if not progression_allowed
        else "Research progression is allowed, subject to persona evidence gaps."
    )
    return [
        PersonaAttribution(
            persona=template["persona"],
            persona_focus=template["focus"],
            gatekeeper_effect=gatekeeper_effect,
            persona_readiness_status=_readiness_status(
                persona=template["persona"],
                gatekeeper=gatekeeper,
            ),
            evidence_strengths_for_persona=template["strengths"],
            evidence_weaknesses_for_persona=template["weaknesses"],
            blocking_or_holding_factors=template["holding"],
            evidence_needed_before_persona_review=template["needed"],
            backoffice_follow_up_requests=template["follow_up"],
            safety_note=(
                f"This is evidence attribution for {template['persona']} under "
                f"the `{decision}` governance state, not a persona decision."
            ),
        )
        for template in _persona_templates()
    ]


def build_investor_persona_attribution(
    *,
    attribution_run_id: str,
    generated_at: str,
    gatekeeper: dict,
    scorecard: dict,
    analysis: dict,
) -> InvestorPersonaAttributionReport:
    """Build an independent persona attribution report."""
    attributions = attribute_evidence_to_personas(
        gatekeeper=gatekeeper,
        scorecard=scorecard,
        analysis=analysis,
    )
    counts = {
        status: sum(
            item.persona_readiness_status == status for item in attributions
        )
        for status in (
            "not_ready_for_persona_review",
            "persona_review_possible_after_repair",
            "persona_review_possible_for_watchlist_only",
            "persona_review_ready",
        )
    }
    progression_allowed = bool(gatekeeper.get("progression_allowed"))
    attribution_status = (
        "persona_progression_blocked_by_gatekeeper_hold"
        if not progression_allowed
        and gatekeeper.get("gatekeeper_decision") in {"hold", "block"}
        else "persona_progression_requires_repair"
        if counts["persona_review_possible_after_repair"]
        else "persona_watchlist_only"
        if counts["persona_review_possible_for_watchlist_only"]
        else "persona_review_ready"
    )
    persona_needs = {
        item.persona: item.evidence_needed_before_persona_review
        for item in attributions
    }
    limitations = [
        "This report attributes existing evidence; it does not run investor agents.",
        "Persona mappings do not alter philosophies, scores, or final decisions.",
        "No persona comparison, aggregation, vote, or consensus is produced.",
    ]
    if not scorecard:
        limitations.append(
            "The linked scorecard report was unavailable; gatekeeper context "
            "and conservative persona templates were used."
        )
    if not analysis:
        limitations.append(
            "The linked expanded-trial analysis report was unavailable."
        )
    return InvestorPersonaAttributionReport(
        attribution_run_id=attribution_run_id,
        generated_at=generated_at,
        gatekeeper_run_id=str(gatekeeper.get("gatekeeper_run_id") or ""),
        scorecard_run_id=str(gatekeeper.get("scorecard_run_id") or ""),
        analysis_run_id=str(gatekeeper.get("analysis_run_id") or ""),
        expanded_trial_run_id=str(
            gatekeeper.get("expanded_trial_run_id") or ""
        ),
        backtest_run_id=str(gatekeeper.get("backtest_run_id") or ""),
        research_evidence_classification=str(
            scorecard.get("research_evidence_classification")
            or gatekeeper.get("research_evidence_classification")
            or ""
        ),
        research_decision=str(
            scorecard.get("research_decision")
            or gatekeeper.get("research_decision")
            or ""
        ),
        gatekeeper_decision=str(
            gatekeeper.get("gatekeeper_decision") or ""
        ),
        progression_allowed=progression_allowed,
        hold_bias=bool(gatekeeper.get("hold_bias")),
        attribution_status=attribution_status,
        persona_attributions=[item.to_dict() for item in attributions],
        cross_persona_summary={
            "personas_not_ready_count": counts[
                "not_ready_for_persona_review"
            ],
            "personas_repair_possible_count": counts[
                "persona_review_possible_after_repair"
            ],
            "personas_watchlist_only_count": counts[
                "persona_review_possible_for_watchlist_only"
            ],
            "personas_ready_count": counts["persona_review_ready"],
            "common_holding_factors": COMMON_HOLDING_FACTORS,
            "persona_specific_evidence_needs": persona_needs,
            "overall_persona_attribution_status": attribution_status,
        },
        common_holding_factors=COMMON_HOLDING_FACTORS,
        recommended_next_research_action=NEXT_RESEARCH_ACTION,
        limitations=limitations,
    )


def _join(items: list[str]) -> str:
    return "; ".join(items)


def render_investor_persona_attribution_report(
    report: InvestorPersonaAttributionReport,
) -> str:
    """Render the attribution report as Markdown."""
    data = report.to_dict()
    summary = data["cross_persona_summary"]
    lines = [
        "# Investor-Agent Attribution by Persona",
        "",
        "## Executive Summary",
        "",
        f"- Attribution Run ID: {data['attribution_run_id']}",
        f"- Gatekeeper Run ID: {data['gatekeeper_run_id']}",
        f"- Gatekeeper Decision: {data['gatekeeper_decision']}",
        f"- Progression Allowed: {str(data['progression_allowed']).lower()}",
        f"- Hold Bias: {str(data['hold_bias']).lower()}",
        f"- Attribution Status: {data['attribution_status']}",
        (
            "- Main Interpretation: The gatekeeper hold prevents persona review "
            "progression, while distinct evidence repair paths remain visible."
        ),
        (
            "- Next Research Action: "
            f"{data['recommended_next_research_action']}"
        ),
        "",
        "## Important Boundary",
        "",
        (
            "This report does not ask investor agents for buy, sell, or hold "
            "decisions. It only maps current research evidence to "
            "persona-specific evidence needs. Personas remain independent; "
            "they are not ranked, averaged, voted, or combined into consensus."
        ),
        "",
        "## Gatekeeper Context",
        "",
        (
            "- Research Evidence Classification: "
            f"{data['research_evidence_classification']}"
        ),
        f"- Research Decision: {data['research_decision']}",
        f"- Gatekeeper Decision: {data['gatekeeper_decision']}",
        f"- Progression Allowed: {str(data['progression_allowed']).lower()}",
        "",
        "## Persona Attribution Matrix",
        "",
        (
            "| Persona | Readiness Status | Gatekeeper Effect | "
            "Key Holding Factors | Evidence Needed Before Review |"
        ),
        "|---|---|---|---|---|",
    ]
    for item in data["persona_attributions"]:
        lines.append(
            f"| {item['persona']} | {item['persona_readiness_status']} | "
            f"{item['gatekeeper_effect']} | "
            f"{_join(item['blocking_or_holding_factors'])} | "
            f"{_join(item['evidence_needed_before_persona_review'])} |"
        )
    for item in data["persona_attributions"]:
        lines.extend(
            [
                "",
                f"## {item['persona']} Attribution",
                "",
                f"- Readiness Status: {item['persona_readiness_status']}",
                f"- Gatekeeper Effect: {item['gatekeeper_effect']}",
                f"- Persona Focus: {_join(item['persona_focus'])}",
                "- Evidence Strengths:",
                *[
                    f"  - {value}"
                    for value in item["evidence_strengths_for_persona"]
                ],
                "- Evidence Weaknesses:",
                *[
                    f"  - {value}"
                    for value in item["evidence_weaknesses_for_persona"]
                ],
                "- Evidence Needed Before Review:",
                *[
                    f"  - {value}"
                    for value in item["evidence_needed_before_persona_review"]
                ],
                "- Backoffice Follow-Up Requests:",
                *[
                    f"  - {value}"
                    for value in item["backoffice_follow_up_requests"]
                ],
            ]
        )
    lines.extend(["", "## Common Holding Factors", ""])
    lines.extend(f"- {item}" for item in data["common_holding_factors"])
    lines.extend(["", "## Persona-Specific Evidence Needs", ""])
    for persona, needs in summary["persona_specific_evidence_needs"].items():
        lines.append(f"- {persona}: {_join(needs)}")
    lines.extend(
        [
            "",
            "## What This Suggests",
            "",
            "- Investor personas should not be asked for final decisions yet.",
            (
                "- The current state should be routed to backoffice evidence "
                "quality attribution."
            ),
            "- Each persona requires a distinct evidence repair path.",
            "",
            "## What This Does Not Suggest",
            "",
            "- It does not rank investor personas.",
            "- It does not create consensus.",
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


def write_investor_persona_attribution_report(
    *,
    outputs_root: Path,
    gatekeeper_run_id: str | None = None,
    generated_at: datetime | None = None,
) -> InvestorPersonaAttributionFiles:
    """Load linked research artifacts and write persona attribution outputs."""
    outputs_root = Path(outputs_root)
    timestamp = generated_at or datetime.now(timezone.utc)
    manifest = load_research_gatekeeper_manifest(
        outputs_root=outputs_root,
        gatekeeper_run_id=gatekeeper_run_id,
    )
    selected_id = str(
        gatekeeper_run_id or manifest.get("gatekeeper_run_id") or ""
    )
    if not selected_id:
        raise ValueError("Gatekeeper run ID is required.")
    gatekeeper = (
        manifest
        if gatekeeper_run_id
        else load_research_gatekeeper_report(
            outputs_root=outputs_root,
            gatekeeper_run_id=selected_id,
        )
    )
    scorecard_id = str(gatekeeper.get("scorecard_run_id") or "")
    analysis_id = str(gatekeeper.get("analysis_run_id") or "")
    scorecard = (
        load_research_evidence_scorecard_report(
            outputs_root=outputs_root,
            scorecard_run_id=scorecard_id,
        )
        if scorecard_id
        else {}
    )
    analysis = (
        load_expanded_trial_analysis_report(
            outputs_root=outputs_root,
            analysis_run_id=analysis_id,
        )
        if analysis_id
        else {}
    )

    root = outputs_root / "investor_persona_attributions"
    root.mkdir(parents=True, exist_ok=True)
    base = timestamp.strftime("%Y%m%d_%H%M%S")
    run_id = base
    suffix = 2
    while (root / run_id).exists():
        run_id = f"{base}_{suffix:02d}"
        suffix += 1
    report = build_investor_persona_attribution(
        attribution_run_id=run_id,
        generated_at=timestamp.isoformat(),
        gatekeeper=gatekeeper,
        scorecard=scorecard,
        analysis=analysis,
    )
    folder = root / run_id
    folder.mkdir(parents=True, exist_ok=False)
    markdown_path = folder / "investor_persona_attribution_report.md"
    json_path = folder / "investor_persona_attribution_report.json"
    matrix_path = folder / "investor_persona_attribution_matrix.csv"
    markdown_path.write_text(
        render_investor_persona_attribution_report(report),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )
    with matrix_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "persona",
                "persona_focus",
                "gatekeeper_effect",
                "persona_readiness_status",
                "evidence_strengths_for_persona",
                "evidence_weaknesses_for_persona",
                "blocking_or_holding_factors",
                "evidence_needed_before_persona_review",
                "backoffice_follow_up_requests",
                "safety_note",
            ),
        )
        writer.writeheader()
        for item in report.persona_attributions:
            writer.writerow(
                {
                    **item,
                    **{
                        key: _join(item[key])
                        for key in (
                            "persona_focus",
                            "evidence_strengths_for_persona",
                            "evidence_weaknesses_for_persona",
                            "blocking_or_holding_factors",
                            "evidence_needed_before_persona_review",
                            "backoffice_follow_up_requests",
                        )
                    },
                }
            )
    latest_path = (
        root / "latest_investor_persona_attribution_manifest.json"
    )
    latest_path.write_text(
        json.dumps(
            {
                "attribution_run_id": report.attribution_run_id,
                "gatekeeper_run_id": report.gatekeeper_run_id,
                "scorecard_run_id": report.scorecard_run_id,
                "analysis_run_id": report.analysis_run_id,
                "expanded_trial_run_id": report.expanded_trial_run_id,
                "backtest_run_id": report.backtest_run_id,
                "research_evidence_classification": (
                    report.research_evidence_classification
                ),
                "research_decision": report.research_decision,
                "gatekeeper_decision": report.gatekeeper_decision,
                "progression_allowed": report.progression_allowed,
                "hold_bias": report.hold_bias,
                "attribution_status": report.attribution_status,
                "recommended_next_research_action": (
                    report.recommended_next_research_action
                ),
                "attribution_folder": str(folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "matrix_csv_path": str(matrix_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return InvestorPersonaAttributionFiles(
        attribution_folder=folder,
        markdown_path=markdown_path,
        json_path=json_path,
        matrix_csv_path=matrix_path,
        latest_manifest_path=latest_path,
        report=report,
    )
