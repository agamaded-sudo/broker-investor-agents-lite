"""Merge normalized official financial facts into a Backoffice data pack."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from broker_agents.fetchers.sec_financials_fetcher import (
    SecFinancialFacts,
    SecFinancialsFetcher,
)


def _present_values(values: dict[str, Any]) -> dict[str, Any]:
    """Return fields whose official value is available."""
    return {key: value for key, value in values.items() if value is not None}


def _update_first_row(section: dict, key: str, values: dict) -> None:
    """Update or create the latest statement row without deleting history."""
    rows = section.get(key)
    if not isinstance(rows, list):
        rows = []
        section[key] = rows
    if rows and isinstance(rows[0], dict):
        rows[0].update(values)
    else:
        rows.insert(0, values)


def merge_official_financials_into_pack(
    pack: dict,
    financials: SecFinancialFacts,
) -> dict:
    """Return a copy of a pack with official annual financials and provenance."""
    merged = deepcopy(pack)
    source_id = (
        f"sec_company_facts_{financials.ticker.lower()}_{financials.fiscal_year}"
    )
    financial_section = merged.setdefault("financial_statements_summary", {})

    common = {
        "period": financials.period,
        "fiscal_year": financials.fiscal_year,
        "source_id": source_id,
        "confidence": "high",
    }
    income_values = {
        **common,
        **_present_values(
            {
                "revenue": financials.revenue,
                "gross_profit": financials.gross_profit,
                "operating_income": financials.operating_income,
                "operating_income_ebit": financials.operating_income,
                "net_income": financials.net_income,
            }
        ),
    }
    balance_values = {
        **common,
        **_present_values(
            {
                "cash_and_equivalents": financials.cash_and_equivalents,
                "cash_and_short_term_investments": financials.cash_and_equivalents,
                "long_term_debt": financials.long_term_debt,
                "shareholders_equity": financials.shareholders_equity,
            }
        ),
    }
    cash_flow_values = {
        **common,
        **_present_values(
            {
                "operating_cash_flow": financials.operating_cash_flow,
                "capital_expenditure": financials.capital_expenditure,
                "capital_expenditures": financials.capital_expenditure,
                "capex": financials.capital_expenditure,
                "free_cash_flow": financials.free_cash_flow,
            }
        ),
    }
    _update_first_row(financial_section, "income_statement", income_values)
    _update_first_row(financial_section, "balance_sheet", balance_values)
    _update_first_row(financial_section, "cash_flow_statement", cash_flow_values)

    annual = financial_section.setdefault("annual", {})
    annual.update(
        {
            **common,
            **_present_values(
                {
                    "revenue": financials.revenue,
                    "gross_profit": financials.gross_profit,
                    "operating_income": financials.operating_income,
                    "net_income": financials.net_income,
                    "operating_cash_flow": financials.operating_cash_flow,
                    "capital_expenditure": financials.capital_expenditure,
                    "capex": financials.capital_expenditure,
                    "free_cash_flow": financials.free_cash_flow,
                    "cash_and_equivalents": financials.cash_and_equivalents,
                    "cash_and_short_term_investments": financials.cash_and_equivalents,
                    "long_term_debt": financials.long_term_debt,
                    "shareholders_equity": financials.shareholders_equity,
                }
            ),
        }
    )

    notes = financial_section.setdefault("notes", [])
    note = "Official financials merged from SEC fixture/source."
    if note not in notes:
        notes.append(note)

    source_section = merged.setdefault("sources_confidence_data_gaps", {})
    source_log = source_section.setdefault("source_log", [])
    source_record = SecFinancialsFetcher().build_source_log(financials)[0]
    existing_index = next(
        (
            index
            for index, item in enumerate(source_log)
            if isinstance(item, dict) and item.get("source_id") == source_id
        ),
        None,
    )
    if existing_index is None:
        source_log.append(source_record)
    else:
        source_log[existing_index] = source_record

    return merged
