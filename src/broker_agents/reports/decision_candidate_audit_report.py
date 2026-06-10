"""Audit reporting for provisional investor decision candidates."""

from pathlib import Path

import yaml

from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.backoffice.portfolio_context import merge_portfolio_context_into_pack
from broker_agents.calculators.bogle_benchmark_risk import (
    calculate_bogle_benchmark_risk,
)
from broker_agents.calculators.bogle_index_overlap import (
    calculate_bogle_index_overlap,
)
from broker_agents.calculators.decision_candidates import build_decision_candidate
from broker_agents.calculators.fisher_scuttlebutt import (
    build_fisher_scuttlebutt_checklist,
)
from broker_agents.calculators.intrinsic_value import (
    calculate_buffett_intrinsic_value_range,
)
from broker_agents.calculators.lynch_category_scoring import score_lynch_category
from broker_agents.calculators.munger_incentives import (
    score_munger_incentives_and_stupidity,
)
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
)
from broker_agents.reports.formatting import (
    format_millions,
    format_ratio_as_percent,
)

INVESTORS = {
    "buffett": "Warren Buffett",
    "munger": "Charlie Munger",
    "fisher": "Philip Fisher",
    "lynch": "Peter Lynch",
    "bogle": "John Bogle",
}

UPGRADE_DATA_NEEDS = {
    "buffett": (
        "Intrinsic value range validation, margin of safety validation, valuation history, "
        "and durable normalized owner earnings."
    ),
    "munger": (
        "Inversion-risk evidence, management incentives, capital-allocation rationality, "
        "and hidden-stupidity checks."
    ),
    "fisher": (
        "Business-model scuttlebutt, customer evidence, product adoption, retention, "
        "and innovation productivity."
    ),
    "lynch": (
        "PEG, category-specific growth proof, earnings durability, and valuation versus growth."
    ),
    "bogle": (
        "Portfolio context. Index overlap and current portfolio exposure are needed, together "
        "with benchmark-relative risk and permitted single-stock weight."
    ),
}


def _load_pack(path: Path) -> dict:
    """Load a YAML pack, returning an empty dictionary when unavailable."""
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _audit_status(candidate: dict) -> str:
    """Classify whether a candidate record is supported or still evidence constrained."""
    driver_count = len(candidate["positive_drivers"]) + len(candidate["negative_drivers"])
    blockers = candidate["decision_blockers"]
    rationale = str(candidate.get("rationale", "")).strip()
    confidence = str(candidate.get("candidate_confidence", "")).lower()
    if driver_count == 0 and not blockers:
        return "weak candidate record"
    if blockers and confidence in {"medium", "low"}:
        return "needs more evidence"
    if driver_count > 0 and rationale:
        return "supported"
    return "weak candidate record"


def _same_or_different(candidate: dict) -> str:
    """Compare the provisional candidate label with the official decision label."""
    return (
        "Same"
        if candidate["current_decision"] == candidate["candidate_decision"]
        else "Different"
    )


def _differentiation_findings(records: list[dict]) -> list[str]:
    """Summarize candidate differentiation without ranking companies."""
    findings: list[str] = []
    final_unique_total = 0
    candidate_unique_total = 0
    for investor_key, investor_name in INVESTORS.items():
        investor_records = [
            record for record in records if record["investor_key"] == investor_key
        ]
        candidates = {
            record["candidate"]["candidate_decision"] for record in investor_records
        }
        finals = {record["candidate"]["current_decision"] for record in investor_records}
        final_unique_total += len(finals)
        candidate_unique_total += len(candidates)
        if len(candidates) > 1:
            detail = "; ".join(
                f"{record['ticker']}: {record['candidate']['candidate_decision']}"
                for record in investor_records
            )
            findings.append(f"{investor_name} candidates differ by company: {detail}.")
        else:
            only_candidate = next(iter(candidates), "Not found")
            findings.append(
                f"{investor_name} candidates remain identical across companies: "
                f"{only_candidate}."
            )
    if candidate_unique_total > final_unique_total:
        findings.append(
            "Candidate logic is more differentiated than the official final decisions across "
            "the audited companies."
        )
    else:
        findings.append(
            "Candidate logic is not more differentiated than the official final decisions in "
            "this audit set."
        )
    return findings


def generate_decision_candidate_audit(
    tickers: list[str],
    outputs_root: Path,
    examples_root: Path,
    portfolio_context: dict | None = None,
) -> str:
    """Generate a deterministic audit of candidate decisions."""
    normalized_tickers = [ticker.strip().upper() for ticker in tickers if ticker.strip()]
    companies: list[dict] = []
    records: list[dict] = []

    for ticker in normalized_tickers:
        input_path = Path(examples_root) / f"{ticker.lower()}_input.yaml"
        output_dir = Path(outputs_root) / ticker
        pack = merge_portfolio_context_into_pack(
            _load_pack(input_path),
            portfolio_context or {},
        )
        identity = pack.get("company_identity", {})
        metadata = pack.get("metadata", {})
        company_name = str(
            identity.get("company_name")
            or metadata.get("company_name")
            or "Not found"
        )
        signals = extract_company_signals(pack)
        fisher_checklist = build_fisher_scuttlebutt_checklist(pack)
        lynch_scoring = score_lynch_category(pack)
        intrinsic_value = calculate_buffett_intrinsic_value_range(pack)
        munger_scoring = score_munger_incentives_and_stupidity(pack)
        bogle_overlap = calculate_bogle_index_overlap(pack)
        bogle_risk = calculate_bogle_benchmark_risk(pack)
        companies.append(
            {
                "ticker": ticker,
                "company_name": company_name,
                "business_model_type": signals["business_model_type"],
                "input_path": input_path,
                "output_dir": output_dir,
                "exists": input_path.exists() and output_dir.exists(),
                "fisher_checklist": fisher_checklist,
                "lynch_scoring": lynch_scoring,
                "intrinsic_value": intrinsic_value,
                "munger_scoring": munger_scoring,
                "bogle_overlap": bogle_overlap,
                "bogle_risk": bogle_risk,
            }
        )
        for investor_key, investor_name in INVESTORS.items():
            records.append(
                {
                    "ticker": ticker,
                    "investor_key": investor_key,
                    "investor_name": investor_name,
                    "candidate": build_decision_candidate(pack, investor_key),
                    "eligibility": evaluate_promotion_eligibility(pack, investor_key),
                }
            )

    lines = [
        "# Decision Candidate Audit Report",
        "",
        "## 1. Companies Audited",
        "",
        "| Ticker | Company | Business Model Type | Input File | Output Directory | Exists |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for company in companies:
        lines.append(
            f"| {company['ticker']} | {company['company_name']} | "
            f"{company['business_model_type']} | {company['input_path']} | "
            f"{company['output_dir']} | {'Yes' if company['exists'] else 'No'} |"
        )

    lines.extend(
        [
            "",
            "## 2. Important Disclaimer",
            "",
            "This audit does not create a recommendation, ranking, vote, average score, or consensus. It reviews candidate decisions only.",
            "",
            "## 3. Candidate vs Final Decision Table",
            "",
            "| Ticker | Investor | Final Decision | Decision Candidate | Candidate Confidence | Same or Different | Main Blocker |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for record in records:
        candidate = record["candidate"]
        main_blocker = (
            candidate["decision_blockers"][0]
            if candidate["decision_blockers"]
            else "None identified"
        )
        lines.append(
            f"| {record['ticker']} | {record['investor_name']} | "
            f"{candidate['current_decision']} | {candidate['candidate_decision']} | "
            f"{candidate['candidate_confidence']} | {_same_or_different(candidate)} | "
            f"{main_blocker} |"
        )

    lines.extend(
        [
            "",
            "## 4. Candidate Differentiation Findings",
            "",
            *[f"- {finding}" for finding in _differentiation_findings(records)],
            "",
            "## 5. Candidate Support Check",
            "",
            "| Ticker | Investor | Positive Drivers Count | Negative Drivers Count | Blockers Count | Audit Status |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for record in records:
        candidate = record["candidate"]
        lines.append(
            f"| {record['ticker']} | {record['investor_name']} | "
            f"{len(candidate['positive_drivers'])} | {len(candidate['negative_drivers'])} | "
            f"{len(candidate['decision_blockers'])} | {_audit_status(candidate)} |"
        )

    lines.extend(
        [
            "",
            "## 6. Upgrade Readiness Review",
            "",
            "| Ticker | Investor | Candidate | Main Data Needed Before Final Decision Upgrade |",
            "| --- | --- | --- | --- |",
        ]
    )
    for record in records:
        candidate = record["candidate"]
        main_blocker = (
            candidate["decision_blockers"][0]
            if candidate["decision_blockers"]
            else "No blocker recorded."
        )
        upgrade_need = UPGRADE_DATA_NEEDS[record["investor_key"]]
        if (
            record["investor_key"] == "bogle"
            and "portfolio context" not in main_blocker.lower()
        ):
            upgrade_need = (
                "Index overlap validation, benchmark-relative risk, and proposed position size."
            )
        data_needed = f"{upgrade_need} Current main blocker: {main_blocker}"
        lines.append(
            f"| {record['ticker']} | {record['investor_name']} | "
            f"{candidate['candidate_decision']} | {data_needed} |"
        )

    lines.extend(
        [
            "",
            "## 7. Promotion Eligibility Review",
            "",
            "| Ticker | Investor | Candidate | Promotion Eligibility | Auto-Promotion Allowed | Main Required Evidence |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for record in records:
        eligibility = record["eligibility"]
        main_evidence = (
            eligibility["required_evidence"][0]
            if eligibility["required_evidence"]
            else "No additional evidence recorded."
        )
        lines.append(
            f"| {record['ticker']} | {record['investor_name']} | "
            f"{eligibility['decision_candidate']} | "
            f"{eligibility['promotion_eligibility']} | "
            f"{'Yes' if eligibility['auto_promotion_allowed'] else 'No'} | "
            f"{main_evidence} |"
        )

    lines.extend(
        [
            "",
            "## 8. Buffett Intrinsic Value Review",
            "",
            "| Ticker | Intrinsic Value Low | Intrinsic Value Mid | Intrinsic Value High | Market Cap | Mid Margin of Safety | Valuation Gap | Confidence |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        intrinsic = company["intrinsic_value"]
        lines.append(
            f"| {company['ticker']} | "
            f"{format_millions(intrinsic['intrinsic_value_low'])} | "
            f"{format_millions(intrinsic['intrinsic_value_mid'])} | "
            f"{format_millions(intrinsic['intrinsic_value_high'])} | "
            f"{format_millions(intrinsic['market_cap'])} | "
            f"{format_ratio_as_percent(intrinsic['margin_of_safety_mid'])} | "
            f"{intrinsic['valuation_gap_label']} | "
            f"{intrinsic['intrinsic_value_confidence']} |"
        )

    lines.extend(
        [
            "",
            "## 9. Munger Incentives & Hidden-Stupidity Review",
            "",
            "| Ticker | Overall Munger Quality Score | Hidden-Stupidity Label | Main Evidence Gap | Munger Candidate |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        scoring = company["munger_scoring"]
        candidate = next(
            record["candidate"]["candidate_decision"]
            for record in records
            if record["ticker"] == company["ticker"]
            and record["investor_key"] == "munger"
        )
        main_gap = (
            scoring["evidence_gaps"][0]
            if scoring["evidence_gaps"]
            else "No material evidence gap recorded."
        )
        lines.append(
            f"| {company['ticker']} | "
            f"{scoring['overall_munger_quality_score']}/5 | "
            f"{scoring['hidden_stupidity_label']} | {main_gap} | {candidate} |"
        )

    lines.extend(
        [
            "",
            "## 10. Fisher Scuttlebutt Readiness Review",
            "",
            "| Ticker | Business Model Type | Readiness Label | Main Scuttlebutt Gap |",
            "| --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        checklist = company["fisher_checklist"]
        main_gap = (
            checklist["priority_items"][0]["evidence_area"]
            if checklist["priority_items"]
            else "No high-priority gap"
        )
        lines.append(
            f"| {company['ticker']} | {company['business_model_type']} | "
            f"{checklist['readiness_label']} | {main_gap} |"
        )

    lines.extend(
        [
            "",
            "## 11. Lynch Category Readiness Review",
            "",
            "| Ticker | Business Model Type | Primary Category | Secondary Category | Key Blocker | Required Evidence |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        scoring = company["lynch_scoring"]
        key_blocker = (
            scoring["evidence_gaps"][0]
            if scoring["evidence_gaps"]
            else "No category blocker recorded."
        )
        required = (
            scoring["evidence_gaps"][1]
            if len(scoring["evidence_gaps"]) > 1
            else key_blocker
        )
        lines.append(
            f"| {company['ticker']} | {scoring['business_model_type']} | "
            f"{scoring['primary_category']} | {scoring['secondary_category']} | "
            f"{key_blocker} | {required} |"
        )

    lines.extend(
        [
            "",
            "## 12. Bogle Index Overlap & Benchmark Risk Review",
            "",
            "| Ticker | Overlap Label | Concentration Risk | Limited-Weight Candidate | Main Benchmark Evidence Gap | Bogle Candidate |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        overlap = company["bogle_overlap"]
        risk = company["bogle_risk"]
        candidate = next(
            record["candidate"]["candidate_decision"]
            for record in records
            if record["ticker"] == company["ticker"]
            and record["investor_key"] == "bogle"
        )
        main_gap = (
            risk["missing_benchmark_evidence"][0]
            if risk["missing_benchmark_evidence"]
            else "No benchmark evidence gap recorded."
        )
        lines.append(
            f"| {company['ticker']} | {overlap['overlap_label']} | "
            f"{overlap['concentration_risk_label']} | "
            f"{'Yes' if overlap['limited_weight_candidate'] else 'No'} | "
            f"{main_gap} | {candidate} |"
        )

    lines.extend(
        [
            "",
            "## 13. Key Observations",
            "",
            "- Buffett candidates now incorporate the preliminary intrinsic value gap as well as owner earnings quality.",
            "- Bogle remains constrained because portfolio context is missing.",
            "- Fisher remains constrained because scuttlebutt and customer evidence are missing.",
            "- Munger remains constrained by inversion risks and incomplete evidence.",
            "",
            "## 14. Recommended Next Improvements",
            "",
            "- Add source-driven data ingestion.",
            "- Validate the Buffett intrinsic value range with normalized multi-year owner earnings.",
            "- Validate Munger incentives, capital allocation, and hidden-stupidity evidence.",
            "- Collect and verify the Fisher scuttlebutt checklist evidence by business model.",
            "- Collect and verify Lynch category scoring evidence by business model.",
            "- Add Bogle portfolio context form and index exposure calculation.",
            "- Add a rule for promoting candidate decisions to final decisions only after audit checks pass.",
            "",
        ]
    )
    return "\n".join(lines)
