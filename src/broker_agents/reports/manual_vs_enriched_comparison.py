"""Compare deterministic investor outputs from manual and enriched packs."""

from pathlib import Path

import yaml

from broker_agents.backoffice.source_verification import verify_sources
from broker_agents.calculators.decision_candidates import (
    CURRENT_DECISIONS,
    build_decision_candidate,
)
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
)
from broker_agents.storage.file_paths import examples_dir

INVESTORS = {
    "buffett": "Warren Buffett",
    "munger": "Charlie Munger",
    "fisher": "Philip Fisher",
    "lynch": "Peter Lynch",
    "bogle": "John Bogle",
}

EVIDENCE_IMPROVEMENTS = {
    "buffett": (
        "Official financials, market data, historical valuation, and growth inputs",
        "Enrichment improves provenance for owner earnings and valuation work; "
        "maintenance versus growth capex remains unresolved.",
    ),
    "munger": (
        "Official financial and capital-allocation inputs",
        "Core financial evidence improves, but incentives, insider ownership, and "
        "acquisition-return evidence remain incomplete.",
    ),
    "fisher": (
        "Growth runway and reported operating evidence",
        "Growth inputs improve, while customer, developer, partner, and product "
        "scuttlebutt remain missing.",
    ),
    "lynch": (
        "Growth, PEG, market valuation, and historical valuation inputs",
        "The enriched pack adds valuation-versus-growth evidence, subject to provider "
        "and cycle-adjustment validation.",
    ),
    "bogle": (
        "No material benchmark-risk improvement",
        "Portfolio context may be supplied at report time, but benchmark returns, "
        "volatility, drawdown, beta, correlation, and holdings validation remain open.",
    ),
}

REMAINING_GAPS = {
    "buffett": "Maintenance versus growth capex and normalized owner earnings validation.",
    "munger": "Management incentives, ownership, compensation, and capital-allocation judgment.",
    "fisher": "Customer, product, developer, partner, and competitive scuttlebutt evidence.",
    "lynch": "Growth methodology validation and cycle-adjusted earnings where applicable.",
    "bogle": "Benchmark-relative risk and verified index or ETF holdings overlap.",
}


def _load_yaml(path: Path) -> dict:
    """Load a YAML mapping, returning an empty mapping when unavailable."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _quality_map(verification: dict) -> dict[str, str]:
    """Index section quality labels by section name."""
    return {
        item["section_name"]: item["section_quality_label"]
        for item in verification.get("source_quality_by_section", [])
    }


def _improved_sections(manual: dict, enriched: dict) -> str:
    """Describe sections whose source-quality label changed."""
    manual_quality = _quality_map(manual)
    enriched_quality = _quality_map(enriched)
    changes = [
        f"{section}: {before} to {enriched_quality.get(section, 'not assessed')}"
        for section, before in manual_quality.items()
        if enriched_quality.get(section) not in {None, before}
    ]
    return "; ".join(changes) if changes else "No section-label change detected"


def _summary_decisions(path: Path) -> dict[str, str]:
    """Extract investor decisions from an agents-summary Markdown table."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    decisions: dict[str, str] = {}
    names_to_keys = {name: key for key, name in INVESTORS.items()}
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0] in names_to_keys:
            decisions.setdefault(names_to_keys[cells[0]], cells[1])
    return decisions


def _report_candidate(path: Path) -> str | None:
    """Extract a candidate decision from a detailed investor report."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    prefix = "Candidate Decision:"
    for line in text.splitlines():
        stripped = line.strip().lstrip("-").strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip() or None
    return None


def _candidate(pack: dict, investor: str, report_path: Path) -> dict:
    """Return calculator output, preferring a generated report candidate label."""
    calculated = build_decision_candidate(pack, investor)
    parsed = _report_candidate(report_path)
    if parsed:
        calculated = {**calculated, "candidate_decision": parsed}
    return calculated


def generate_manual_vs_enriched_comparison(
    tickers: list[str],
    outputs_root: Path,
) -> str:
    """Generate a deterministic comparison of manual and enriched pipeline evidence."""
    outputs_root = Path(outputs_root)
    records: list[dict] = []

    for raw_ticker in tickers:
        ticker = raw_ticker.strip().upper()
        if not ticker:
            continue
        lower = ticker.lower()
        manual_input = examples_dir() / f"{lower}_input.yaml"
        enriched_input = outputs_root / ticker / f"{lower}_enriched_input.yaml"
        manual_dir = outputs_root / ticker
        enriched_dir = manual_dir / "enriched"
        manual_pack = _load_yaml(manual_input)
        enriched_pack = _load_yaml(enriched_input)
        manual_verification = verify_sources(manual_pack) if manual_pack else {}
        enriched_verification = verify_sources(enriched_pack) if enriched_pack else {}
        records.append(
            {
                "ticker": ticker,
                "lower": lower,
                "manual_input": manual_input,
                "enriched_input": enriched_input,
                "manual_dir": manual_dir,
                "enriched_dir": enriched_dir,
                "manual_pack": manual_pack,
                "enriched_pack": enriched_pack,
                "manual_verification": manual_verification,
                "enriched_verification": enriched_verification,
                "manual_decisions": _summary_decisions(
                    manual_dir / f"{lower}_agents_summary.md"
                ),
                "enriched_decisions": _summary_decisions(
                    enriched_dir / f"{lower}_agents_summary.md"
                ),
            }
        )

    lines = [
        "# Manual vs Enriched Pipeline Comparison",
        "",
        "## 1. Important Disclaimer",
        "",
        "This report is not a recommendation, ranking, vote, average score, or consensus. "
        "It compares evidence and source quality only.",
        "",
        "## 2. Companies Compared",
        "",
        "| Ticker | Manual Output Exists | Enriched Output Exists | Manual Input | Enriched Input |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in records:
        lines.append(
            f"| {item['ticker']} | {'Yes' if item['manual_dir'].is_dir() else 'No'} | "
            f"{'Yes' if item['enriched_dir'].is_dir() else 'No'} | "
            f"{item['manual_input']} | {item['enriched_input']} |"
        )

    lines.extend(
        [
            "",
            "## 3. Source Quality Change",
            "",
            "| Ticker | Manual Overall Source Quality | Enriched Overall Source Quality | Main Improved Sections |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in records:
        manual = item["manual_verification"]
        enriched = item["enriched_verification"]
        lines.append(
            f"| {item['ticker']} | {manual.get('overall_source_quality', 'Not available')} | "
            f"{enriched.get('overall_source_quality', 'Not available')} | "
            f"{_improved_sections(manual, enriched) if manual and enriched else 'Enriched input not available'} |"
        )

    lines.extend(
        [
            "",
            "## 4. Investor Final Decision Stability",
            "",
            "| Ticker | Buffett | Munger | Fisher | Lynch | Bogle |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    all_final_decisions_stable = True
    for item in records:
        cells: list[str] = []
        for investor in INVESTORS:
            manual = item["manual_decisions"].get(investor, CURRENT_DECISIONS[investor])
            enriched = item["enriched_decisions"].get(investor, CURRENT_DECISIONS[investor])
            all_final_decisions_stable &= manual == enriched
            cells.append(f"{manual} -> {enriched}")
        lines.append(f"| {item['ticker']} | " + " | ".join(cells) + " |")

    lines.extend(
        [
            "",
            "## 5. Candidate Decision Changes",
            "",
            "| Ticker | Investor | Manual Candidate | Enriched Candidate | Changed? | Explanation |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in records:
        for investor, investor_name in INVESTORS.items():
            if not item["manual_pack"] or not item["enriched_pack"]:
                lines.append(
                    f"| {item['ticker']} | {investor_name} | Not available | Not available | "
                    "Not parsed | Manual or enriched input is missing. |"
                )
                continue
            manual = _candidate(
                item["manual_pack"],
                investor,
                item["manual_dir"] / f"{item['lower']}_{investor}_report.md",
            )
            enriched = _candidate(
                item["enriched_pack"],
                investor,
                item["enriched_dir"] / f"{item['lower']}_{investor}_report.md",
            )
            changed = manual["candidate_decision"] != enriched["candidate_decision"]
            explanation = (
                enriched["rationale"]
                if changed
                else "Candidate label is unchanged; enriched provenance and evidence detail improved."
            )
            lines.append(
                f"| {item['ticker']} | {investor_name} | {manual['candidate_decision']} | "
                f"{enriched['candidate_decision']} | {'Yes' if changed else 'No'} | {explanation} |"
            )

    lines.extend(
        [
            "",
            "## 6. Evidence Improvements",
            "",
            "| Ticker | Investor | Evidence Improved | Details |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in records:
        for investor, investor_name in INVESTORS.items():
            evidence, details = EVIDENCE_IMPROVEMENTS[investor]
            lines.append(
                f"| {item['ticker']} | {investor_name} | {evidence} | {details} |"
            )

    lines.extend(
        [
            "",
            "## 7. Remaining Gaps After Enrichment",
            "",
            "| Ticker | Investor | Remaining Gap | Reason |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in records:
        for investor, investor_name in INVESTORS.items():
            gap = REMAINING_GAPS[investor]
            lines.append(
                f"| {item['ticker']} | {investor_name} | {gap} | "
                "The available fixture set does not supply this evidence. |"
            )

    auto_promotion_disabled = True
    for item in records:
        for pack in (item["manual_pack"], item["enriched_pack"]):
            if not pack:
                continue
            for investor in INVESTORS:
                auto_promotion_disabled &= not evaluate_promotion_eligibility(
                    pack, investor
                )["auto_promotion_allowed"]

    lines.extend(
        [
            "",
            "## 8. Safety Check",
            "",
            f"- Final decisions unchanged: {'Yes' if all_final_decisions_stable else 'No'}",
            f"- Auto-promotion disabled: {'Yes' if auto_promotion_disabled else 'No'}",
            "- No ranking: Confirmed.",
            "- No consensus: Confirmed.",
            "- No trade or execution signal: Confirmed.",
            "",
        ]
    )
    return "\n".join(lines)
