"""Markdown rendering for broker deal intake readiness."""

from broker_agents.deals.deal_intake import DealIntakeStatus


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def _add_list(lines: list[str], values: list[str], empty: str) -> None:
    if values:
        lines.extend(f"- {value}" for value in values)
    else:
        lines.append(f"- {empty}")


def generate_deal_intake_report(status: DealIntakeStatus) -> str:
    """Render one deterministic deal intake report."""
    files = [
        (
            "Manual Input Pack",
            status.manual_input_path,
            status.manual_input_exists,
            "Yes",
        ),
        (
            "SEC Fixture",
            status.sec_fixture_path,
            status.sec_fixture_exists,
            "No",
        ),
        (
            "Market Data Fixture",
            status.market_fixture_path,
            status.market_fixture_exists,
            "No",
        ),
        (
            "Historical Valuation Fixture",
            status.historical_valuation_fixture_path,
            status.historical_valuation_fixture_exists,
            "No",
        ),
        (
            "Growth & PEG Fixture",
            status.growth_peg_fixture_path,
            status.growth_peg_fixture_exists,
            "No",
        ),
        (
            "Portfolio Context",
            status.portfolio_context_path,
            status.portfolio_context_exists,
            "No (Bogle context)",
        ),
    ]
    display_ticker = status.normalized_ticker or "UNSPECIFIED"
    lines = [
        f"# Deal Intake Report — {display_ticker}",
        "",
        "## 1. Important Disclaimer",
        "",
        "This intake report is not a recommendation, ranking, vote, average score, consensus, allocation instruction, or trade signal. It only checks whether the ticker is ready for the Backoffice + Investor Agent deal workflow.",
        "",
        "## 2. Intake Summary",
        "",
        "| Ticker | Market | Company | Intake Status | Can Run Deal |",
        "| --- | --- | --- | --- | --- |",
        (
            f"| {display_ticker} | {status.market} | {status.company_name} | "
            f"{status.intake_status} | {_yes_no(status.can_run_deal)} |"
        ),
        "",
        "## 3. Required Files",
        "",
        "| File Type | Expected Path | Exists | Required? |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| {label} | {path} | {_yes_no(exists)} | {required} |"
        for label, path, exists, required in files
    )
    lines.extend(["", "## 4. Missing Requirements", ""])
    _add_list(lines, status.missing_requirements, "No required files are missing.")
    lines.extend(["", "## 5. Optional Missing Sources", ""])
    _add_list(
        lines,
        status.optional_missing_sources,
        "All optional enrichment fixtures are available.",
    )
    lines.extend(["", "## 6. Backoffice Next Actions", ""])
    _add_list(lines, status.backoffice_next_actions, "No next action established.")
    if status.warnings:
        lines.extend(["", "### Warnings", ""])
        _add_list(lines, status.warnings, "None.")
    lines.extend(
        [
            "",
            "## 7. Safety Check",
            "",
            "- Intake only",
            "- No investor decision",
            "- No recommendation",
            "- No ranking",
            "- No consensus",
            "- No allocation",
            "- No trade signal",
            "- Auto-promotion disabled",
            "",
        ]
    )
    return "\n".join(lines)
