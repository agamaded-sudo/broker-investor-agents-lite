"""Comparison report for independent investor agent summaries."""

from pathlib import Path

INVESTORS = [
    "Warren Buffett",
    "Charlie Munger",
    "Philip Fisher",
    "Peter Lynch",
    "John Bogle",
]


def _read_text(path: Path) -> str:
    """Read a Markdown file, returning an empty string when unavailable."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""


def _extract_summary_rows(summary_text: str) -> dict[str, dict[str, str]]:
    """Extract investor decisions and confidence from a summary Markdown table."""
    rows: dict[str, dict[str, str]] = {}
    in_decision_table = False
    for line in summary_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("| Investor | Decision | Confidence |"):
            in_decision_table = True
            continue
        if in_decision_table and stripped.startswith("## "):
            break
        if not in_decision_table:
            continue
        if not stripped.startswith("|"):
            continue
        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if len(parts) < 4 or parts[0] == "---":
            continue
        investor, decision, confidence = parts[0], parts[1], parts[2]
        if investor in INVESTORS:
            rows[investor] = {
                "decision": decision or "Not found",
                "confidence": confidence or "Not found",
            }

    return rows


def _extract_candidate_rows(summary_text: str) -> dict[str, dict[str, str]]:
    """Extract candidate decisions, confidence, and blockers from a summary."""
    rows: dict[str, dict[str, str]] = {}
    in_candidate_section = False
    for line in summary_text.splitlines():
        stripped = line.strip()
        if stripped == "## Decision Candidate Snapshot":
            in_candidate_section = True
            continue
        if in_candidate_section and stripped.startswith("## "):
            break
        if not in_candidate_section or not stripped.startswith("|"):
            continue
        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if len(parts) < 4 or parts[0] in ("Investor", "---"):
            continue
        if parts[0] in INVESTORS:
            rows[parts[0]] = {
                "candidate": parts[1] or "Not found",
                "confidence": parts[2] or "Not found",
                "blocker": parts[3] or "Not found",
            }
    return rows


def _extract_bullet_value(text: str, label: str) -> str:
    """Extract a '- Label: value' bullet from Markdown."""
    prefix = f"- {label}:"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped.split(":", 1)[1].strip() or "Not found"
    return "Not found"


def _extract_company_signal_summary(summary_path: Path, ticker: str) -> dict[str, str]:
    """Extract company signal fields from the sibling Backoffice report."""
    backoffice_path = Path(summary_path).parent / f"{ticker.lower()}_backoffice_data_pack.md"
    text = _read_text(backoffice_path)
    return {
        "business_model_type": _extract_bullet_value(text, "Business Model Type"),
        "primary_growth_engine": _extract_bullet_value(text, "Primary growth engine"),
        "dominant_revenue_stream": _extract_bullet_value(text, "Dominant revenue stream"),
        "capex_profile": _extract_bullet_value(text, "Capex Profile"),
        "major_capex_issue": _extract_bullet_value(text, "Major capex issue"),
        "fisher_angle": _extract_bullet_value(text, "Fisher angle"),
        "lynch_angle": _extract_bullet_value(text, "Lynch angle"),
        "bogle_angle": _extract_bullet_value(text, "Bogle angle"),
    }


def _extract_owner_earnings_summary(summary_path: Path, ticker: str) -> dict[str, str]:
    """Extract owner earnings fields from the sibling Backoffice report."""
    backoffice_path = Path(summary_path).parent / f"{ticker.lower()}_backoffice_data_pack.md"
    text = _read_text(backoffice_path)
    return {
        "fcf_margin": _extract_bullet_value(text, "FCF Margin"),
        "capex_to_ocf": _extract_bullet_value(text, "Capex / OCF"),
        "capex_intensity_label": _extract_bullet_value(text, "Capex Intensity Label"),
        "owner_earnings_quality_label": _extract_bullet_value(
            text,
            "Owner Earnings Quality Label",
        ),
    }


def _extract_valuation_guardrails(summary_path: Path, ticker: str) -> dict[str, str]:
    """Extract valuation guardrail fields from the sibling Backoffice report."""
    backoffice_path = Path(summary_path).parent / f"{ticker.lower()}_backoffice_data_pack.md"
    text = _read_text(backoffice_path)
    return {
        "p_fcf": _extract_bullet_value(text, "P/FCF"),
        "fcf_yield": _extract_bullet_value(text, "FCF Yield"),
        "valuation_status": _extract_bullet_value(text, "Valuation Status"),
        "valuation_confidence": _extract_bullet_value(text, "Valuation Confidence"),
    }


def _extract_report_rationales(summary_path: Path, ticker: str) -> dict[str, str]:
    """Extract decision rationales from sibling investor reports."""
    agent_by_investor = {
        "Warren Buffett": "buffett",
        "Charlie Munger": "munger",
        "Philip Fisher": "fisher",
        "Peter Lynch": "lynch",
        "John Bogle": "bogle",
    }
    rationales: dict[str, str] = {}
    for investor, agent in agent_by_investor.items():
        report_path = Path(summary_path).parent / f"{ticker.lower()}_{agent}_report.md"
        text = _read_text(report_path)
        rationales[investor] = _extract_heading_value(text, "Decision Rationale")
    return rationales


def _extract_bullet_after_label(text: str, label: str) -> str:
    """Extract the first bullet after an exact label line."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == label:
            for next_line in lines[index + 1 :]:
                stripped = next_line.strip()
                if stripped.startswith("- "):
                    return stripped[2:]
                if stripped.startswith("## "):
                    break
    return "Not found"


def _extract_buffett_conditions(summary_path: Path, ticker: str) -> dict[str, str]:
    """Extract top Buffett upgrade, downgrade, and watch items."""
    report_path = Path(summary_path).parent / f"{ticker.lower()}_buffett_report.md"
    text = _read_text(report_path)
    return {
        "main_upgrade_condition": _extract_bullet_after_label(
            text,
            "Conditions that could improve the decision:",
        ),
        "main_downgrade_condition": _extract_bullet_after_label(
            text,
            "Conditions that could worsen the decision:",
        ),
        "key_watch_item": _extract_bullet_after_label(text, "Watch items:"),
    }


def _extract_munger_top_inversion(summary_path: Path, ticker: str) -> dict[str, str]:
    """Extract the first high-severity Munger inversion matrix row."""
    report_path = Path(summary_path).parent / f"{ticker.lower()}_munger_report.md"
    text = _read_text(report_path)
    fallback: dict[str, str] | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped or "Failure Mode" in stripped:
            continue
        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if len(parts) < 4:
            continue
        row = {
            "failure_mode": parts[0],
            "evidence": parts[1],
            "severity": parts[2],
            "risk_reduction": parts[3],
        }
        fallback = fallback or row
        if row["severity"].lower() == "high":
            return row
    return fallback or {
        "failure_mode": "Not found",
        "evidence": "Not found",
        "severity": "Not found",
        "risk_reduction": "Not found",
    }


def _extract_heading_value(text: str, heading: str) -> str:
    """Extract the first non-empty line after a Markdown heading."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == f"## {heading}":
            for next_line in lines[index + 1 :]:
                stripped = next_line.strip()
                if stripped:
                    return stripped
    return "Not found"


def generate_agents_comparison(
    left_ticker: str,
    right_ticker: str,
    left_summary_path: Path,
    right_summary_path: Path,
) -> str:
    """Generate a comparison of two independent investor-agent summaries."""
    left_ticker = left_ticker.upper()
    right_ticker = right_ticker.upper()
    left_path = Path(left_summary_path)
    right_path = Path(right_summary_path)
    left_text = _read_text(left_path)
    right_text = _read_text(right_path)
    left_rows = _extract_summary_rows(left_text)
    right_rows = _extract_summary_rows(right_text)
    left_candidates = _extract_candidate_rows(left_text)
    right_candidates = _extract_candidate_rows(right_text)
    left_signals = _extract_company_signal_summary(left_path, left_ticker)
    right_signals = _extract_company_signal_summary(right_path, right_ticker)
    left_owner_earnings = _extract_owner_earnings_summary(left_path, left_ticker)
    right_owner_earnings = _extract_owner_earnings_summary(right_path, right_ticker)
    left_valuation = _extract_valuation_guardrails(left_path, left_ticker)
    right_valuation = _extract_valuation_guardrails(right_path, right_ticker)
    left_rationales = _extract_report_rationales(left_path, left_ticker)
    right_rationales = _extract_report_rationales(right_path, right_ticker)
    left_conditions = _extract_buffett_conditions(left_path, left_ticker)
    right_conditions = _extract_buffett_conditions(right_path, right_ticker)
    left_munger_inversion = _extract_munger_top_inversion(left_path, left_ticker)
    right_munger_inversion = _extract_munger_top_inversion(right_path, right_ticker)

    comparison_rows: list[dict[str, str]] = []
    same_count = 0
    different_count = 0

    for investor in INVESTORS:
        left_decision = left_rows.get(investor, {}).get("decision", "Not found")
        left_confidence = left_rows.get(investor, {}).get("confidence", "Not found")
        right_decision = right_rows.get(investor, {}).get("decision", "Not found")
        right_confidence = right_rows.get(investor, {}).get("confidence", "Not found")
        same_or_different = "Same" if left_decision == right_decision else "Different"
        same_count += same_or_different == "Same"
        different_count += same_or_different == "Different"
        comparison_rows.append(
            {
                "investor": investor,
                "left_decision": left_decision,
                "left_confidence": left_confidence,
                "right_decision": right_decision,
                "right_confidence": right_confidence,
                "same_or_different": same_or_different,
            }
        )

    lines = [
        f"# Independent Investor Agents Comparison — {left_ticker} vs {right_ticker}",
        "",
        "## 1. Files Compared",
        "",
        "| Ticker | Summary File | Exists |",
        "| --- | --- | --- |",
        f"| {left_ticker} | {left_path} | {'Yes' if left_path.exists() else 'No'} |",
        f"| {right_ticker} | {right_path} | {'Yes' if right_path.exists() else 'No'} |",
        "",
        "## 2. Important Disclaimer",
        "",
        "This is not a recommendation, ranking, vote, or consensus. It compares independent agent outputs only.",
        "",
        "## 3. Side-by-Side Decision Table",
        "",
        f"| Investor | {left_ticker} Decision | {left_ticker} Confidence | {right_ticker} Decision | {right_ticker} Confidence | Same or Different |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for row in comparison_rows:
        lines.append(
            f"| {row['investor']} | {row['left_decision']} | {row['left_confidence']} | "
            f"{row['right_decision']} | {row['right_confidence']} | {row['same_or_different']} |"
        )

    lines.extend(
        [
            "",
            "## Decision Candidate Comparison",
            "",
            f"| Investor | {left_ticker} Candidate | {right_ticker} Candidate | Key Differentiation |",
            "| --- | --- | --- | --- |",
        ]
    )
    for investor in INVESTORS:
        left_candidate = left_candidates.get(
            investor,
            {"candidate": "Not found", "blocker": "Not found"},
        )
        right_candidate = right_candidates.get(
            investor,
            {"candidate": "Not found", "blocker": "Not found"},
        )
        lines.append(
            f"| {investor} | {left_candidate['candidate']} | "
            f"{right_candidate['candidate']} | {left_ticker}: {left_candidate['blocker']}; "
            f"{right_ticker}: {right_candidate['blocker']} |"
        )

    lines.extend(
        [
            "",
            "## 4. Company-Specific Signal Comparison",
            "",
            f"| Signal | {left_ticker} | {right_ticker} |",
            "| --- | --- | --- |",
            f"| Business Model Type | {left_signals['business_model_type']} | {right_signals['business_model_type']} |",
            f"| Primary growth engine | {left_signals['primary_growth_engine']} | {right_signals['primary_growth_engine']} |",
            f"| Dominant revenue stream | {left_signals['dominant_revenue_stream']} | {right_signals['dominant_revenue_stream']} |",
            f"| Capex Profile | {left_signals['capex_profile']} | {right_signals['capex_profile']} |",
            f"| Major capex issue | {left_signals['major_capex_issue']} | {right_signals['major_capex_issue']} |",
            f"| Fisher angle | {left_signals['fisher_angle']} | {right_signals['fisher_angle']} |",
            f"| Lynch angle | {left_signals['lynch_angle']} | {right_signals['lynch_angle']} |",
            f"| Bogle angle | {left_signals['bogle_angle']} | {right_signals['bogle_angle']} |",
            "",
            "## 5. Buffett Owner Earnings Comparison",
            "",
            f"| Metric | {left_ticker} | {right_ticker} |",
            "| --- | --- | --- |",
            f"| FCF Margin | {left_owner_earnings['fcf_margin']} | {right_owner_earnings['fcf_margin']} |",
            f"| Capex / OCF | {left_owner_earnings['capex_to_ocf']} | {right_owner_earnings['capex_to_ocf']} |",
            f"| Capex Intensity Label | {left_owner_earnings['capex_intensity_label']} | {right_owner_earnings['capex_intensity_label']} |",
            f"| Owner Earnings Quality Label | {left_owner_earnings['owner_earnings_quality_label']} | {right_owner_earnings['owner_earnings_quality_label']} |",
            "",
            "## 6. Buffett Valuation Guardrails Comparison",
            "",
            f"| Metric | {left_ticker} | {right_ticker} |",
            "| --- | --- | --- |",
            f"| P/FCF | {left_valuation['p_fcf']} | {right_valuation['p_fcf']} |",
            f"| FCF Yield | {left_valuation['fcf_yield']} | {right_valuation['fcf_yield']} |",
            f"| Valuation Status | {left_valuation['valuation_status']} | {right_valuation['valuation_status']} |",
            f"| Valuation Confidence | {left_valuation['valuation_confidence']} | {right_valuation['valuation_confidence']} |",
            "",
            "## 7. Buffett Upgrade/Downgrade Conditions Comparison",
            "",
            f"| Condition Type | {left_ticker} | {right_ticker} |",
            "| --- | --- | --- |",
            f"| Main upgrade condition | {left_conditions['main_upgrade_condition']} | {right_conditions['main_upgrade_condition']} |",
            f"| Main downgrade condition | {left_conditions['main_downgrade_condition']} | {right_conditions['main_downgrade_condition']} |",
            f"| Key watch item | {left_conditions['key_watch_item']} | {right_conditions['key_watch_item']} |",
            "",
            "## 8. Munger Inversion Risk Comparison",
            "",
            f"| Field | {left_ticker} | {right_ticker} |",
            "| --- | --- | --- |",
            f"| Top failure mode | {left_munger_inversion['failure_mode']} | {right_munger_inversion['failure_mode']} |",
            f"| Severity | {left_munger_inversion['severity']} | {right_munger_inversion['severity']} |",
            f"| Risk-reduction evidence needed | {left_munger_inversion['risk_reduction']} | {right_munger_inversion['risk_reduction']} |",
            "",
            "## 9. Rationale Differences",
            "",
            f"| Investor | {left_ticker} Rationale | {right_ticker} Rationale |",
            "| --- | --- | --- |",
        ]
    )

    for investor in INVESTORS:
        lines.append(
            f"| {investor} | {left_rationales.get(investor, 'Not found')} | "
            f"{right_rationales.get(investor, 'Not found')} |"
        )

    lines.extend(
        [
            "",
            "## 10. Similarities",
            "",
            f"- The detected business models are {left_signals['business_model_type']} for {left_ticker} and {right_signals['business_model_type']} for {right_ticker}.",
            "- Both summaries preserve independent investor-agent decisions rather than a combined view.",
            "- Both companies show Medium confidence across the current generated summaries when extracted from the summary tables.",
            "- Both may reflect incomplete valuation history, benchmark context, scuttlebutt, or portfolio context from the manual data packs.",
            "",
            "## 11. Differences",
            "",
        ]
    )

    if different_count:
        for row in comparison_rows:
            if row["same_or_different"] == "Different":
                lines.append(
                    f"- {row['investor']}: {left_ticker} decision is {row['left_decision']}; "
                    f"{right_ticker} decision is {row['right_decision']}."
                )
    else:
        lines.append(
            "- No investor decision differences were detected from the extracted summary tables."
        )

    if same_count >= len(INVESTORS) - 1:
        lines.append(
            "- Current deterministic rules may be too coarse to create meaningful differentiation."
        )

    lines.extend(
        [
            "",
            "## 12. Interpretation Risk",
            "",
            "- Similar decisions may reflect similar large-cap quality profiles.",
            "- Similar decisions may reflect incomplete manual input data.",
            "- Similar decisions may reflect early deterministic rules.",
            "- Similar decisions may reflect the need for richer company-specific logic in v0.2.",
            "",
            "## 13. Recommended Improvements",
            "",
            "- Add investor-specific scoring/rubrics internally while keeping outputs non-consensus.",
            "- Improve company-specific metrics extraction.",
            "- Add valuation history.",
            "- Add product/segment-specific logic.",
            "- Add Bogle benchmark weights and portfolio context.",
            "- Add Fisher scuttlebutt data.",
            "- Add Lynch category-specific logic.",
            "- Add Buffett preliminary intrinsic value model.",
            "- Add Munger incentive and hidden-stupidity checks.",
            "",
        ]
    )

    return "\n".join(lines)
