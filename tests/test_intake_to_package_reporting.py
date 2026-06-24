from broker_agents.intake_to_package import (
    PackageReadinessLabel,
    build_package_readiness_report,
    render_package_readiness_markdown,
)


def test_build_package_readiness_report_ready_payload() -> None:
    report = build_package_readiness_report(_complete_payload())

    assert report.title == "Intake-to-Package Readiness Report"
    assert report.company_name == "Microsoft Corporation"
    assert report.readiness_label == PackageReadinessLabel.READY_FOR_HUMAN_REVIEW.value
    assert report.allowed_next_step == "human_review"
    assert report.human_review_required is True
    assert report.blocker_count == 0


def test_build_package_readiness_report_includes_blockers() -> None:
    report = build_package_readiness_report(
        {
            "ticker": "MSFT",
            "exchange": "NASDAQ",
            "as_of_date": "2026-06-24",
            "requested_output": "intake_summary",
        }
    )

    assert report.readiness_label == PackageReadinessLabel.NOT_READY.value
    assert report.blocker_count > 0
    assert any(
        blocker["related_field"] == "company_name"
        for blocker in report.blockers
    )


def test_build_package_readiness_report_includes_warnings() -> None:
    payload = _complete_payload()
    payload["financial_statement_sources"] = [
        {
            "title": "Secondary financial summary",
            "reliability_label": "trusted_secondary",
            "publication_date": "2026-01-01",
        }
    ]

    report = build_package_readiness_report(payload)

    assert report.readiness_label == PackageReadinessLabel.PARTIAL.value
    assert report.warning_count > 0
    assert report.blocker_count == 0


def test_render_package_readiness_markdown_contains_safe_sections() -> None:
    markdown = render_package_readiness_markdown(_complete_payload())

    assert "# Intake-to-Package Readiness Report" in markdown
    assert "## Status" in markdown
    assert "## Blockers" in markdown
    assert "## Warnings" in markdown
    assert "## Blocked Next Steps" in markdown
    assert "## Safety Boundary" in markdown


def test_render_package_readiness_markdown_keeps_safety_boundary() -> None:
    markdown = render_package_readiness_markdown(_complete_payload())

    assert "No investor-agent execution" in markdown
    assert "recommendation" in markdown
    assert "trade signal" in markdown
    assert "auto-promotion" in markdown


def test_report_blocks_investment_next_steps() -> None:
    report = build_package_readiness_report(_complete_payload())

    assert "investor_agent_execution" in report.blocked_next_steps
    assert "recommendation" in report.blocked_next_steps
    assert "ranking" in report.blocked_next_steps
    assert "allocation" in report.blocked_next_steps
    assert "trade_signal" in report.blocked_next_steps


def _complete_payload() -> dict[str, object]:
    official_source = {
        "title": "Official annual report",
        "url_or_path": "https://example.com/annual-report",
        "source_type": "annual_report",
        "publication_date": "2026-01-01",
        "access_date": "2026-06-24",
        "reliability_label": "official",
    }
    return {
        "company_name": "Microsoft Corporation",
        "ticker": "MSFT",
        "exchange": "NASDAQ",
        "listing_country": "United States",
        "as_of_date": "2026-06-24",
        "requested_output": ["package_readiness"],
        "official_filings": [official_source],
        "financial_statement_sources": [official_source],
    }

