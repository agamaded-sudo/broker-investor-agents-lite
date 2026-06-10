"""Deterministic source-quality classification for manual backoffice packs."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from broker_agents.backoffice.source_tracker import collect_source_log
from broker_agents.calculators.owner_earnings import calculate_owner_earnings_snapshot
from broker_agents.calculators.valuation_guardrails import calculate_valuation_guardrails

SOURCE_STATUSES = {
    "official_verified",
    "market_data_verified",
    "manual_placeholder",
    "calculated",
    "missing",
    "needs_verification",
    "not_applicable",
}

CRITICAL_SECTIONS = (
    "financial_statements_summary",
    "valuation_snapshot",
    "historical_valuation",
    "capital_allocation",
    "management_ownership_incentives",
    "sector_specific_operating_kpis",
    "index_benchmark_alternative",
    "portfolio_context_form",
    "scuttlebutt",
    "growth_peg_analysis",
)

FIELD_SPECS: dict[str, list[tuple[str, tuple[str, ...], str, str]]] = {
    "financial_statements_summary": [
        ("revenue", ("income_statement.0.revenue", "annual.revenue"), "investor financial analysis", "Official annual filing"),
        ("gross_profit", ("income_statement.0.gross_profit", "annual.gross_profit"), "margin analysis", "Official annual filing"),
        ("operating_income_ebit", ("income_statement.0.operating_income_ebit", "income_statement.0.operating_income", "annual.operating_income_ebit", "annual.operating_income"), "business quality analysis", "Official annual filing"),
        ("net_income", ("income_statement.0.net_income", "annual.net_income"), "earnings analysis", "Official annual filing"),
        ("operating_cash_flow", ("cash_flow_statement.0.operating_cash_flow", "annual.operating_cash_flow"), "owner earnings analysis", "Official annual filing"),
        ("capital_expenditure", ("cash_flow_statement.0.capital_expenditure", "cash_flow_statement.0.capex", "annual.capital_expenditure", "annual.capex"), "owner earnings normalization", "Official annual filing"),
        ("free_cash_flow", ("cash_flow_statement.0.free_cash_flow", "annual.free_cash_flow"), "cash conversion analysis", "Official annual filing or verified calculation"),
        ("cash_and_equivalents", ("balance_sheet.0.cash_and_equivalents", "annual.cash_and_equivalents", "annual.cash_and_short_term_investments"), "balance sheet analysis", "Official annual filing"),
        ("long_term_debt", ("balance_sheet.0.long_term_debt", "annual.long_term_debt"), "balance sheet analysis", "Official annual filing"),
        ("shareholders_equity", ("balance_sheet.0.shareholders_equity", "annual.shareholders_equity"), "capital and return analysis", "Official annual filing"),
    ],
    "valuation_snapshot": [
        ("market_cap", ("market_cap",), "valuation guardrails", "Timestamped market-data provider"),
        ("current_price", ("current_price",), "current valuation", "Timestamped market-data provider"),
        ("pe", ("pe",), "valuation guardrails", "Timestamped market-data provider"),
        ("p_fcf", ("p_fcf",), "valuation guardrails", "Timestamped market-data provider"),
    ],
    "historical_valuation": [
        ("pe_5y_median", ("pe_5y_median",), "historical valuation comparison", "Verified 5Y valuation dataset"),
        ("pe_10y_median", ("pe_10y_median",), "historical valuation comparison", "Verified 10Y valuation dataset"),
        ("p_fcf_5y_median", ("p_fcf_5y_median",), "historical valuation comparison", "Verified 5Y valuation dataset"),
        ("p_fcf_10y_median", ("p_fcf_10y_median",), "historical valuation comparison", "Verified 10Y valuation dataset"),
        ("ev_ebitda_5y_median", ("ev_ebitda_5y_median",), "historical valuation comparison", "Verified 5Y valuation dataset"),
        ("ev_ebitda_10y_median", ("ev_ebitda_10y_median",), "historical valuation comparison", "Verified 10Y valuation dataset"),
        ("current_vs_5y_p_fcf_percentile", ("current_vs_5y_p_fcf_percentile",), "relative valuation context", "Verified historical market dataset"),
        ("current_vs_10y_p_fcf_percentile", ("current_vs_10y_p_fcf_percentile",), "relative valuation context", "Verified historical market dataset"),
    ],
    "capital_allocation": [
        ("dividends_paid", ("dividends_paid",), "capital allocation analysis", "Official cash-flow statement"),
        ("share_repurchases", ("share_repurchases",), "buyback discipline analysis", "Official cash-flow statement"),
        ("stock_based_compensation", ("stock_based_compensation",), "dilution analysis", "Official filing or proxy statement"),
        ("share_count_change", ("share_count_change",), "buyback effectiveness analysis", "Official share-count history"),
    ],
    "management_ownership_incentives": [
        ("compensation_metrics", ("compensation_metrics",), "incentive alignment analysis", "Official proxy statement"),
        ("insider_ownership", ("insider_ownership",), "management alignment analysis", "Official proxy statement"),
        ("management_tenure", ("management_tenure",), "management quality analysis", "Official proxy or company filing"),
        ("related_party_transactions", ("related_party_transactions",), "governance risk analysis", "Official filing"),
    ],
    "index_benchmark_alternative": [
        ("index_weights", ("index_weights",), "index overlap analysis", "Official index or ETF holdings"),
        ("etf_holdings", ("etf_holdings",), "indirect exposure analysis", "Official ETF holdings"),
        ("beta", ("beta",), "benchmark-relative risk", "Verified market return series"),
        ("volatility", ("volatility",), "benchmark-relative risk", "Verified market return series"),
        ("max_drawdown", ("max_drawdown",), "benchmark-relative risk", "Verified market return series"),
        ("correlation", ("correlation",), "benchmark-relative risk", "Verified market return series"),
    ],
    "portfolio_context_form": [
        ("provided", ("provided",), "portfolio suitability context", "User-provided portfolio context"),
        ("current_holdings", ("current_holdings",), "portfolio overlap analysis", "User-provided portfolio context"),
        ("constraints", ("constraints",), "position guardrails", "User-provided portfolio context"),
        ("indirect_exposure_estimates", ("indirect_exposure_estimates",), "index overlap analysis", "User input plus verified ETF holdings"),
    ],
    "scuttlebutt": [
        ("customer_evidence", ("customer_evidence",), "Fisher customer validation", "Customer interviews or verified adoption data"),
        ("product_evidence", ("product_evidence",), "Fisher product validation", "Product usage and satisfaction evidence"),
        ("developer_ecosystem", ("developer_ecosystem",), "ecosystem durability analysis", "Developer activity and ecosystem sources"),
        ("partner_evidence", ("partner_evidence",), "distribution and ecosystem analysis", "Partner or channel evidence"),
        ("employee_culture_evidence", ("employee_culture_evidence",), "culture analysis", "Employee and culture evidence"),
    ],
    "growth_peg_analysis": [
        ("revenue_cagr_3y", ("revenue_cagr_3y",), "Lynch and Fisher growth evidence", "Verified historical financial series"),
        ("revenue_cagr_5y", ("revenue_cagr_5y",), "growth durability analysis", "Verified historical financial series"),
        ("eps_cagr_3y", ("eps_cagr_3y",), "Lynch earnings growth analysis", "Verified EPS history"),
        ("eps_cagr_5y", ("eps_cagr_5y",), "earnings durability analysis", "Verified EPS history"),
        ("fcf_cagr_3y", ("fcf_cagr_3y",), "cash growth analysis", "Verified cash-flow history"),
        ("fcf_cagr_5y", ("fcf_cagr_5y",), "cash growth durability analysis", "Verified cash-flow history"),
        ("forward_revenue_growth", ("forward_revenue_growth",), "forward growth expectations", "Timestamped analyst estimate source"),
        ("forward_eps_growth", ("forward_eps_growth",), "forward earnings expectations", "Timestamped analyst estimate source"),
        ("current_pe", ("current_pe",), "PEG validation", "Timestamped market-data provider"),
        ("peg_ratio", ("peg_ratio",), "valuation-versus-growth analysis", "Verified PEG methodology"),
    ],
}


def _is_missing(value: Any) -> bool:
    """Return whether a value represents unavailable evidence."""
    if value is None or value == "" or value == [] or value == {}:
        return True
    if isinstance(value, str):
        normalized = value.strip().lower().replace("_", " ")
        return normalized in {
            "missing",
            "not available",
            "unavailable",
            "unknown",
            "not established",
            "weak unavailable",
        }
    return False


def _get_path(data: dict, paths: Iterable[str]) -> tuple[Any, str | None, str | None]:
    """Return the first available path, unwrapping provenance-aware values."""
    for path in paths:
        current: Any = data
        inherited_source_id: str | None = None
        inherited_confidence: str | None = None
        for part in path.split("."):
            if isinstance(current, dict):
                inherited_source_id = current.get("source_id") or inherited_source_id
                inherited_confidence = (
                    current.get("confidence") or inherited_confidence
                )
                if part not in current:
                    current = None
                    break
                current = current[part]
                continue
            if isinstance(current, list) and part.isdigit():
                index = int(part)
                if index >= len(current):
                    current = None
                    break
                current = current[index]
                continue
            else:
                current = None
                break
        if current is None:
            continue
        if isinstance(current, dict) and "value" in current:
            return (
                current.get("value"),
                current.get("source_id") or inherited_source_id,
                current.get("confidence") or inherited_confidence,
            )
        if isinstance(current, dict):
            inherited_source_id = current.get("source_id") or inherited_source_id
            inherited_confidence = current.get("confidence") or inherited_confidence
        return current, inherited_source_id, inherited_confidence
    return None, None, None


def _source_map(pack: dict) -> dict[str, dict]:
    """Index normalized source-log records by source id."""
    return {
        str(item.get("source_id")): item
        for item in collect_source_log(pack)
        if isinstance(item, dict) and item.get("source_id")
    }


def _pick_source(source_map: dict[str, dict], kind: str) -> str | None:
    """Select a conservative section-level source when scalar links are absent."""
    candidates = list(source_map.items())
    if kind == "official":
        for source_id, record in candidates:
            text = f"{source_id} {record.get('source_name', '')} {record.get('notes', '')}".lower()
            if record.get("source_type") == "company" and any(
                term in text for term in ("annual", "10-k", "10k")
            ):
                return source_id
    if kind == "quarterly":
        for source_id, record in candidates:
            text = f"{source_id} {record.get('source_name', '')}".lower()
            if record.get("source_type") == "company" and any(
                term in text for term in ("quarter", "q2", "q3")
            ):
                return source_id
    if kind == "market":
        for source_id, record in candidates:
            if record.get("source_type") in {
                "vendor",
                "market_data_provider",
                "historical_market_data_provider",
                "growth_market_data_provider",
            } or "market" in source_id.lower():
                return source_id
    return None


def _has_placeholder_marker(*values: Any) -> bool:
    """Return whether any provenance marker explicitly denotes a placeholder."""
    return any("placeholder" in str(value).lower() for value in values if value is not None)


def _classify(
    value: Any,
    source_id: str | None,
    confidence: str | None,
    source_map: dict[str, dict],
    section_marker: str,
    calculated: bool = False,
) -> tuple[str, str]:
    """Classify one field into a source status and confidence."""
    if calculated:
        return "calculated", "calculated"
    if _is_missing(value):
        return "missing", "missing"

    source = source_map.get(source_id or "", {})
    source_confidence = str(confidence or source.get("confidence") or "").lower()
    if _has_placeholder_marker(source_id, confidence, section_marker, source.get("source_name"), source.get("notes")):
        return "manual_placeholder", "placeholder"
    if source_id and source:
        if source_confidence == "high" and source.get("source_type") == "company":
            return "official_verified", "high"
        if source_confidence in {"high", "medium"} and source.get("source_type") in {
            "vendor",
            "market_data_provider",
            "historical_market_data_provider",
            "growth_market_data_provider",
        }:
            return "market_data_verified", "medium"
    return "needs_verification", source_confidence or "low"


def _section_source_id(section: str, source_map: dict[str, dict]) -> str | None:
    """Infer the most relevant logged source for a critical section."""
    if section in {"financial_statements_summary", "capital_allocation"}:
        return _pick_source(source_map, "official")
    if section == "sector_specific_operating_kpis":
        return _pick_source(source_map, "quarterly")
    if section in {
        "valuation_snapshot",
        "historical_valuation",
        "index_benchmark_alternative",
        "growth_peg_analysis",
    }:
        return _pick_source(source_map, "market")
    return None


def _record(
    *,
    section: str,
    field: str,
    value: Any,
    source_id: str | None,
    confidence: str | None,
    source_map: dict[str, dict],
    section_marker: str,
    required_for: str,
    suggested_source: str,
    calculated: bool = False,
) -> dict:
    """Build one normalized source-verification record."""
    status, normalized_confidence = _classify(
        value,
        source_id,
        confidence,
        source_map,
        section_marker,
        calculated,
    )
    return {
        "section": section,
        "field": field,
        "field_path": f"{section}.{field}",
        "value": value,
        "status": status,
        "confidence": normalized_confidence,
        "source_id": source_id,
        "required_for": required_for,
        "suggested_source": suggested_source,
    }


def _sector_kpi_records(pack: dict, source_map: dict[str, dict]) -> list[dict]:
    """Classify actual scalar operating KPIs while ignoring narrative gap lists."""
    section = pack.get("sector_specific_operating_kpis", {})
    source_id = _section_source_id("sector_specific_operating_kpis", source_map)
    marker = str(section.get("status", "")) if isinstance(section, dict) else ""
    records: list[dict] = []

    def visit(value: Any, prefix: str) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"gaps", "notes", "observations", "source_id", "confidence"}:
                    continue
                visit(item, f"{prefix}.{key}" if prefix else key)
        elif not isinstance(value, list):
            records.append(
                _record(
                    section="sector_specific_operating_kpis",
                    field=prefix,
                    value=value,
                    source_id=source_id,
                    confidence=None,
                    source_map=source_map,
                    section_marker=marker,
                    required_for="business-model operating evidence",
                    suggested_source="Official filing, earnings release, or verified KPI dataset",
                )
            )

    visit(section, "")
    if not records:
        records.append(
            _record(
                section="sector_specific_operating_kpis",
                field="business_model_kpis",
                value=None,
                source_id=None,
                confidence=None,
                source_map=source_map,
                section_marker=marker,
                required_for="business-model operating evidence",
                suggested_source="Official filing or earnings release",
            )
        )
    return records


def _quality_label(records: list[dict]) -> str:
    """Summarize section quality from field-level statuses."""
    if not records:
        return "weak"
    counts = {status: 0 for status in SOURCE_STATUSES}
    for item in records:
        counts[item["status"]] += 1
    total = len(records)
    verified = counts["official_verified"] + counts["market_data_verified"]
    if counts["calculated"] >= max(1, total - counts["missing"]):
        return "calculated-only"
    if counts["manual_placeholder"] >= max(1, total / 2):
        return "placeholder-heavy"
    if verified > total / 2:
        return "strong" if counts["missing"] + counts["needs_verification"] == 0 else "mixed"
    if verified and counts["missing"] + counts["needs_verification"] + counts["manual_placeholder"]:
        return "mixed"
    return "weak"


def _source_quality_by_section(records: list[dict]) -> list[dict]:
    """Aggregate verification counts for each critical section."""
    summaries: list[dict] = []
    section_names = list(CRITICAL_SECTIONS) + ["calculated_outputs"]
    for section in section_names:
        section_records = [item for item in records if item["section"] == section]
        summaries.append(
            {
                "section_name": section,
                "verified_count": sum(
                    item["status"] in {"official_verified", "market_data_verified"}
                    for item in section_records
                ),
                "placeholder_count": sum(
                    item["status"] == "manual_placeholder" for item in section_records
                ),
                "missing_count": sum(
                    item["status"] == "missing" for item in section_records
                ),
                "needs_verification_count": sum(
                    item["status"] == "needs_verification" for item in section_records
                ),
                "calculated_count": sum(
                    item["status"] == "calculated" for item in section_records
                ),
                "section_quality_label": _quality_label(section_records),
            }
        )
    return summaries


def verify_sources(pack: dict) -> dict:
    """Classify critical fields and summarize source-verification readiness."""
    identity = pack.get("company_identity", {}) if isinstance(pack, dict) else {}
    metadata = pack.get("metadata", {}) if isinstance(pack, dict) else {}
    ticker = str(identity.get("ticker") or metadata.get("ticker") or "UNKNOWN")
    company_name = str(
        identity.get("company_name") or metadata.get("company_name") or "Unknown company"
    )
    source_map = _source_map(pack)
    records: list[dict] = []

    for section, specs in FIELD_SPECS.items():
        section_data = pack.get(section, {})
        if not isinstance(section_data, dict):
            section_data = {}
        inferred_source_id = _section_source_id(section, source_map)
        marker = " ".join(
            str(section_data.get(key, ""))
            for key in ("status", "valuation_history_confidence", "data_entry_mode")
        )
        for field, paths, required_for, suggested_source in specs:
            value, explicit_source_id, confidence = _get_path(section_data, paths)
            records.append(
                _record(
                    section=section,
                    field=field,
                    value=value,
                    source_id=explicit_source_id or inferred_source_id,
                    confidence=confidence,
                    source_map=source_map,
                    section_marker=marker,
                    required_for=required_for,
                    suggested_source=suggested_source,
                )
            )

    records.extend(_sector_kpi_records(pack, source_map))

    owner = calculate_owner_earnings_snapshot(pack)
    valuation = calculate_valuation_guardrails(pack)
    calculated_fields = {
        "owner_earnings_proxy": owner.get("owner_earnings_proxy"),
        "fcf_margin": owner.get("fcf_margin"),
        "capex_to_ocf": owner.get("capex_to_ocf"),
        "p_fcf_calculated": valuation.get("p_fcf"),
        "fcf_yield": valuation.get("fcf_yield"),
        "earnings_yield": valuation.get("earnings_yield"),
    }
    for field, value in calculated_fields.items():
        records.append(
            _record(
                section="calculated_outputs",
                field=field,
                value=value,
                source_id=None,
                confidence="calculated",
                source_map=source_map,
                section_marker="",
                required_for="deterministic investor calculations",
                suggested_source="Verify underlying source inputs and calculation method",
                calculated=not _is_missing(value),
            )
        )

    section_quality = _source_quality_by_section(records)
    quality_map = {
        item["section_name"]: item["section_quality_label"] for item in section_quality
    }
    financial_quality = quality_map["financial_statements_summary"]
    placeholder_sections = sum(
        item["section_quality_label"] == "placeholder-heavy" for item in section_quality
    )
    strong_sections = sum(
        item["section_quality_label"] == "strong" for item in section_quality
    )
    mixed_sections = sum(
        item["section_quality_label"] == "mixed" for item in section_quality
    )
    if financial_quality == "weak":
        overall_quality = "weak"
    elif (
        quality_map["historical_valuation"] == "placeholder-heavy"
        or quality_map["valuation_snapshot"] == "placeholder-heavy"
        or placeholder_sections >= 2
    ):
        overall_quality = "placeholder-heavy"
    elif strong_sections >= len(CRITICAL_SECTIONS) / 2:
        overall_quality = "strong"
    elif mixed_sections or strong_sections:
        overall_quality = "mixed"
    else:
        overall_quality = "weak"

    critical_gaps = [
        {
            "field_or_section": item["field_path"],
            "current_status": item["status"],
            "why_it_matters": item["required_for"],
            "backoffice_action": (
                f"Collect or verify against: {item['suggested_source']}."
            ),
        }
        for item in records
        if item["section"] != "calculated_outputs"
        and item["status"] in {"manual_placeholder", "missing", "needs_verification"}
    ]
    actions: list[dict] = []
    for gap in critical_gaps:
        status = gap["current_status"]
        evidence_type = (
            "Source Verification"
            if status in {"manual_placeholder", "needs_verification"}
            else "Data Collection"
        )
        priority = "High" if any(
            term in gap["field_or_section"]
            for term in (
                "financial_statements_summary",
                "valuation_snapshot",
                "historical_valuation",
                "management_ownership_incentives",
            )
        ) else "Medium"
        actions.append(
            {
                "priority": priority,
                "action": gap["backoffice_action"],
                "evidence_type": evidence_type,
                "suggested_source": gap["backoffice_action"].removeprefix(
                    "Collect or verify against: "
                ).removesuffix("."),
            }
        )

    verified_count = sum(
        item["status"] in {"official_verified", "market_data_verified"}
        for item in records
    )
    placeholder_count = sum(
        item["status"] == "manual_placeholder" for item in records
    )
    calculated_count = sum(item["status"] == "calculated" for item in records)
    missing_count = sum(item["status"] == "missing" for item in records)
    needs_count = sum(item["status"] == "needs_verification" for item in records)
    if not critical_gaps:
        verification_status = "verified"
    elif verified_count:
        verification_status = "partially verified"
    else:
        verification_status = "verification required"

    return {
        "ticker": ticker,
        "company_name": company_name,
        "overall_source_quality": overall_quality,
        "source_verification_status": verification_status,
        "verified_fields_count": verified_count,
        "placeholder_fields_count": placeholder_count,
        "calculated_fields_count": calculated_count,
        "missing_fields_count": missing_count,
        "fields_needing_verification_count": needs_count,
        "critical_source_gaps": critical_gaps,
        "source_quality_by_section": section_quality,
        "source_verification_records": records,
        "recommended_backoffice_actions": actions,
    }
