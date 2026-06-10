"""Deterministic quality review for generated Markdown reports."""

from pathlib import Path

INVESTOR_LABELS = {
    "buffett": "Warren Buffett",
    "munger": "Charlie Munger",
    "fisher": "Philip Fisher",
    "lynch": "Peter Lynch",
    "bogle": "John Bogle",
}

EXPECTED_DECISIONS = {
    "buffett": "Wait for Better Price / Complete Intrinsic Value Work",
    "munger": "Buy Gradually / Wait for Better Evidence on AI Capex Returns",
    "fisher": "Needs More Scuttlebutt / Watch Closely",
    "lynch": "Follow / Watch",
    "bogle": "Prefer Broad Index",
}

FORBIDDEN_INDEPENDENCE_TERMS = [
    "committee",
    "consensus",
    "vote",
    "average score",
    "combined recommendation",
]


def _read_report(path: Path) -> str:
    """Read a report, returning an empty string when unavailable."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""


def _contains_any(text: str, phrases: list[str]) -> bool:
    """Return whether text contains any phrase, case-insensitively."""
    lower_text = text.lower()
    return any(phrase.lower() in lower_text for phrase in phrases)


def _yes_no(value: bool) -> str:
    """Render a boolean as a Markdown-friendly status."""
    return "Yes" if value else "No"


def _extract_heading_value(text: str, heading: str) -> str:
    """Extract the first non-empty line after a Markdown heading."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == f"## {heading}" or stripped == f"### {heading}":
            for next_line in lines[index + 1 :]:
                value = next_line.strip()
                if value:
                    return value
    return "Not found"


def _extract_field(text: str, field_name: str) -> str:
    """Extract a field from inline syntax or a Markdown heading."""
    prefix = f"{field_name}:"
    for line in text.splitlines():
        stripped = line.strip()
        if prefix in stripped:
            return stripped.split(prefix, 1)[1].strip() or "Not found"
    return _extract_heading_value(text, field_name)


def _infer_ticker(report_paths: dict[str, Path]) -> str:
    """Infer ticker from report filenames such as msft_buffett_report.md."""
    for path in report_paths.values():
        stem = Path(path).stem
        if "_" in stem:
            return stem.split("_", 1)[0].upper()
    return "MSFT"


def _check_investor_report(text: str) -> dict[str, bool]:
    """Run structural checks for one investor report."""
    return {
        "Investor identity present": "## Investor Identity" in text,
        "Company and ticker present": "## Company Under Review" in text and "MSFT" in text,
        "Core question present": "## Core Question" in text,
        "Completed investor analysis present": "## Completed Investor Analysis" in text,
        "Missing Backoffice data present": "## Missing Backoffice Data" in text,
        "Pending investor analysis present": "## Pending Investor Analysis" in text,
        "Decision present": "## Decision" in text or "Decision:" in text,
        "Confidence present": "## Confidence Level" in text or "Confidence:" in text,
        "Final statement present": "Final" in text and "Statement" in text,
    }


def review_generated_reports(report_paths: dict[str, Path]) -> str:
    """Generate a deterministic Markdown quality review for generated reports."""
    loaded = {name: _read_report(path) for name, path in report_paths.items()}
    issues: list[str] = []
    ticker = _infer_ticker(report_paths)

    lines = [
        f"# {ticker} Reports Quality Review",
        "",
        "## 1. Files Reviewed",
        "",
        "| Report | File | Exists |",
        "| --- | --- | --- |",
    ]

    for name, path in report_paths.items():
        exists = Path(path).exists()
        lines.append(f"| {name} | {path} | {_yes_no(exists)} |")
        if not exists:
            issues.append(f"Missing report file: {path}")

    backoffice = loaded.get("backoffice", "")
    backoffice_checks = {
        "Avoids recommendation language": not _contains_any(
            backoffice,
            ["## Decision", "Buy ", "Sell ", "Prefer Broad Index", "Follow / Watch"],
        ),
        "Includes sources": "Sources" in backoffice,
        "Includes data gaps": "Data Gaps" in backoffice or "Gaps" in backoffice,
        "Uses neutral language": "recommendation" in backoffice.lower()
        and "does not include an investment recommendation" in backoffice.lower(),
        "Clearly separates data from analysis": "Financial Highlights" in backoffice
        and "Sources and Data Gaps" in backoffice,
    }

    lines.extend(
        [
            "",
            "## 2. Backoffice Report Review",
            "",
            "| Check | Result |",
            "| --- | --- |",
        ]
    )
    for check, passed in backoffice_checks.items():
        lines.append(f"| {check} | {_yes_no(passed)} |")
        if not passed:
            issues.append(f"Backoffice report issue: {check}")

    lines.extend(
        [
            "",
            "## 3. Investor Reports Review",
            "",
        ]
    )

    for agent_name, investor_name in INVESTOR_LABELS.items():
        text = loaded.get(agent_name, "")
        checks = _check_investor_report(text)
        lines.extend(
            [
                f"### {investor_name}",
                "",
                "| Check | Result |",
                "| --- | --- |",
            ]
        )
        for check, passed in checks.items():
            lines.append(f"| {check} | {_yes_no(passed)} |")
            if not passed:
                issues.append(f"{investor_name} report issue: {check}")
        lines.append("")

    lines.extend(
        [
            "## 4. Investor Independence Review",
            "",
            "| Term | Present in investor reports |",
            "| --- | --- |",
        ]
    )

    investor_text = "\n".join(loaded.get(agent, "") for agent in INVESTOR_LABELS)
    for term in FORBIDDEN_INDEPENDENCE_TERMS:
        present = term.lower() in investor_text.lower()
        lines.append(f"| {term} | {_yes_no(present)} |")
        if present:
            issues.append(f"Investor independence issue: found '{term}' in investor reports.")

    summary_text = loaded.get("agents_summary", "")
    if "consensus recommendation" in summary_text.lower():
        allowed_disclaimer = "not a consensus recommendation" in summary_text.lower()
        if not allowed_disclaimer:
            issues.append("Summary may imply consensus recommendation.")

    lines.extend(
        [
            "",
            "## 5. Decision Consistency Review",
            "",
            "| Investor | Decision | Expected Decision | Confidence |",
            "| --- | --- | --- | --- |",
        ]
    )

    for agent_name, investor_name in INVESTOR_LABELS.items():
        text = loaded.get(agent_name, "")
        decision = _extract_field(text, "Decision")
        confidence = _extract_field(text, "Confidence Level")
        expected = EXPECTED_DECISIONS[agent_name]
        lines.append(f"| {investor_name} | {decision} | {expected} | {confidence} |")
        if decision != expected:
            issues.append(f"{investor_name} decision differs from expected MSFT decision.")
        if confidence == "Not found":
            issues.append(f"{investor_name} confidence not found.")

    lines.extend(
        [
            "",
            "## 6. Quality Issues Found",
            "",
        ]
    )
    if issues:
        lines.extend(f"- {issue}" for issue in issues)
    else:
        lines.append("- No structural quality issues found by deterministic checks.")

    lines.extend(
        [
            "",
            "## 7. Recommended Improvements for v0.2",
            "",
            "- Add stronger source citations and source IDs next to each major metric.",
            "- Add richer numeric formatting for millions, percentages, and per-share values.",
            "- Add explicit section-level data quality ratings.",
            "- Add deterministic checks for repeated phrasing across investor reports.",
            "- Add benchmark and portfolio context fields before expanding Bogle analysis.",
            "- Add investor-specific evidence maps that link report claims to Backoffice sections.",
            "",
        ]
    )

    return "\n".join(lines)
