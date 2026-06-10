"""Independent investor agents summary report generation."""

from pathlib import Path

INVESTOR_NAMES = {
    "buffett": "Warren Buffett",
    "munger": "Charlie Munger",
    "fisher": "Philip Fisher",
    "lynch": "Peter Lynch",
    "bogle": "John Bogle",
}


def _extract_field(report_text: str, field_name: str) -> str:
    """Extract an inline field or the first non-empty line after a Markdown heading."""
    lines = report_text.splitlines()

    heading = f"## {field_name}"
    for index, line in enumerate(lines):
        if line.strip() == heading:
            for next_line in lines[index + 1 :]:
                stripped = next_line.strip()
                if stripped:
                    return stripped

    inline_prefix = f"{field_name}:"
    for line in lines:
        stripped = line.strip().lstrip("-").strip()
        if stripped.startswith(inline_prefix):
            return stripped[len(inline_prefix) :].strip() or "Not found"

    return "Not found"


def _extract_main_blocker(report_text: str) -> str:
    """Extract the first blocker from the decision candidate layer."""
    lines = report_text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "- Decision Blockers:":
            for next_line in lines[index + 1 :]:
                stripped = next_line.strip()
                if stripped.startswith("- "):
                    return stripped[2:].strip() or "Not found"
                if stripped.startswith("## ") or stripped.startswith("- Candidate Rationale:"):
                    break
    return "Not found"


def _decision_note(investor: str, decision: str, confidence: str) -> str:
    """Build a short independent note for one investor agent."""
    return f"{investor}: decision is {decision}; confidence is {confidence}."


def generate_agents_summary(
    company_name: str,
    ticker: str,
    report_paths: dict[str, Path],
) -> str:
    """Generate a Markdown summary of independent investor agent reports."""
    rows: list[dict[str, str]] = []

    for agent_name, report_path in report_paths.items():
        investor = INVESTOR_NAMES.get(agent_name, agent_name.title())
        path = Path(report_path)
        try:
            report_text = path.read_text(encoding="utf-8")
        except OSError:
            report_text = ""

        decision = _extract_field(report_text, "Decision")
        rationale = _extract_field(report_text, "Decision Rationale")
        confidence = _extract_field(report_text, "Confidence Level")
        if confidence == "Not found":
            confidence = _extract_field(report_text, "Confidence")
        candidate_decision = _extract_field(report_text, "Candidate Decision")
        candidate_confidence = _extract_field(report_text, "Candidate Confidence")
        main_blocker = _extract_main_blocker(report_text)

        rows.append(
            {
                "investor": investor,
                "decision": decision,
                "rationale": rationale,
                "confidence": confidence,
                "candidate_decision": candidate_decision,
                "candidate_confidence": candidate_confidence,
                "main_blocker": main_blocker,
                "report_file": str(path),
            }
        )

    lines = [
        f"# Independent Investor Agents Summary — {ticker}",
        "",
        f"- Company: {company_name}",
        f"- Ticker: {ticker}",
        "",
        "This is not a consensus recommendation. Each investor agent is independent.",
        "",
        "| Investor | Decision | Confidence | Report File |",
        "| --- | --- | --- | --- |",
    ]

    for row in rows:
        lines.append(
            f"| {row['investor']} | {row['decision']} | {row['confidence']} | {row['report_file']} |"
        )

    lines.extend(
        [
            "",
            "## Decision Candidate Snapshot",
            "",
            "| Investor | Decision Candidate | Candidate Confidence | Main Blocker |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['investor']} | {row['candidate_decision']} | "
            f"{row['candidate_confidence']} | {row['main_blocker']} |"
        )

    lines.extend(
        [
            "",
            "## How to read this summary",
            "",
            "Use this report as an index of separate investor-agent views. Do not average the decisions, treat them as votes, or infer a combined recommendation.",
            "",
            "## Independent Decision Rationale",
            "",
        ]
    )

    for row in rows:
        lines.append(f"- {row['investor']}: {row['rationale']}")

    lines.append("- Warren Buffett: Buffett upgrade/downgrade conditions available in the detailed report.")

    lines.extend(
        [
            "",
            "## Independent decision notes",
            "",
        ]
    )

    for row in rows:
        lines.append(f"- {_decision_note(row['investor'], row['decision'], row['confidence'])}")

    lines.append("")
    return "\n".join(lines)
