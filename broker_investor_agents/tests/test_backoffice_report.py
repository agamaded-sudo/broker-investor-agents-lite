"""Tests for Backoffice Markdown report generation."""

from broker_agents.reports.backoffice_report import generate_backoffice_report


def test_generate_backoffice_report_contains_core_markdown_terms() -> None:
    pack = {
        "metadata": {
            "schema_name": "backoffice_data_pack_v2",
            "schema_version": 2,
            "analysis_date": "2026-06-05",
            "latest_annual_period": "FY2025",
        },
        "company_identity": {
            "company_name": "Microsoft Corporation",
            "ticker": "MSFT",
            "exchange": "NASDAQ",
            "market": "USA",
            "currency": "USD",
        },
        "business_model": {"summary": "Software and cloud services."},
        "financial_statements_summary": {
            "annual": {"revenue": 281700},
            "quarterly": {"period": "FY26 Q3"},
        },
        "products_customers_revenue_segments": {"segments": []},
        "calculated_financial_metrics": {},
        "sources_confidence_data_gaps": {"source_log": [], "known_gaps": []},
    }

    markdown = generate_backoffice_report(pack)

    assert "Microsoft Corporation" in markdown
    assert "MSFT" in markdown
    assert "Backoffice Data Pack" in markdown
    assert "Revenue" in markdown
    assert "Sources" in markdown
    assert "Data Quality Summary" in markdown
    assert "Company Signal Summary" in markdown
