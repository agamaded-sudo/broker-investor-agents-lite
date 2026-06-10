"""Backoffice worklist generation for missing investor evidence."""

from pathlib import Path

import yaml

from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.backoffice.portfolio_context import merge_portfolio_context_into_pack
from broker_agents.backoffice.source_verification import verify_sources
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
from broker_agents.calculators.munger_inversion import build_munger_inversion_matrix
from broker_agents.calculators.munger_incentives import (
    score_munger_incentives_and_stupidity,
)
from broker_agents.calculators.owner_earnings import calculate_owner_earnings_snapshot
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
)
from broker_agents.calculators.valuation_guardrails import calculate_valuation_guardrails

INVESTORS = {
    "buffett": "Warren Buffett",
    "munger": "Charlie Munger",
    "fisher": "Philip Fisher",
    "lynch": "Peter Lynch",
    "bogle": "John Bogle",
}

INVESTOR_REQUESTS = {
    "buffett": [
        ("Intrinsic value range", "Calculation", "High", "Compute preliminary owner earnings valuation range.", "Yes"),
        ("Margin of safety validation", "Calculation", "High", "Validate the intrinsic value range against current market value.", "Yes"),
        ("Historical valuation source validation", "Source Verification", "High", "Validate the historical valuation provider and timestamped source lineage.", "Yes"),
        ("Provider methodology validation", "Source Verification", "High", "Review provider definitions, adjustments, and data coverage.", "Yes"),
        ("5Y/10Y median calculation methodology", "Source Verification", "High", "Validate P/E, P/FCF, and EV/EBITDA median calculation windows.", "Yes"),
        ("Percentile methodology validation", "Source Verification", "High", "Validate current P/FCF percentile methodology and observation history.", "Yes"),
        ("Normalized owner earnings history", "Calculation", "High", "Normalize FCF and owner earnings across 5-10 years.", "Yes"),
        ("Maintenance vs growth capex split", "Data Collection", "High", "Collect or estimate maintenance and growth capex separately.", "Yes"),
    ],
    "munger": [
        ("Inversion risk evidence", "Data Collection", "High", "Collect evidence related to the top inversion risk.", "Yes"),
        ("Management incentives", "Data Collection", "Medium", "Collect proxy statement compensation metrics and insider ownership.", "Yes"),
        ("Capital allocation rationality", "Calculation", "Medium", "Analyze buybacks, dividends, acquisitions, debt, and reinvestment.", "Yes"),
        ("Hidden-stupidity checks", "Human Judgment Later", "Medium", "Prepare evidence pack; final judgment remains human or investor-agent review.", "No"),
    ],
    "fisher": [
        ("Scuttlebutt / customer evidence", "Data Collection", "High", "Collect customer, developer, partner, employee, and product adoption evidence.", "Yes"),
        ("Product adoption / retention", "Data Collection", "High", "Collect retention, churn, installed base, customer expansion, or product usage metrics.", "Yes"),
        ("Innovation productivity", "Data Collection", "Medium", "Collect R&D history, new product contribution, and roadmap evidence.", "No"),
    ],
    "lynch": [
        ("PEG or valuation vs growth", "Calculation", "High", "Calculate EPS CAGR, forward growth assumptions, PEG, and valuation-vs-growth.", "Yes"),
        ("Category-specific growth proof", "Data Collection", "High", "Collect KPIs based on business model type.", "Yes"),
        ("Earnings durability", "Calculation", "Medium", "Analyze earnings, margins, and FCF consistency over 5-10 years.", "Yes"),
    ],
    "bogle": [
        ("Portfolio context", "User Input", "High", "Ask user for current holdings, index funds, target weights, and maximum single-stock limit.", "Yes"),
        ("Index overlap", "Data Collection", "High", "Collect index and ETF weights and indirect exposure.", "Yes"),
        ("Benchmark-relative risk", "Calculation", "Medium", "Calculate stock vs benchmark return, volatility, beta, drawdown, and correlation.", "Yes"),
    ],
}

MODEL_REQUESTS = {
    "software_cloud": [
        ("Charlie Munger", "Cloud margin durability", "Data Collection", "High", "Collect cloud segment margins and infrastructure cost trends.", "Yes"),
        ("Philip Fisher", "Retention / net revenue retention", "Data Collection", "High", "Collect retention, expansion, churn, and recurring revenue indicators.", "Yes"),
        ("Warren Buffett", "AI/cloud capex return evidence", "Calculation", "High", "Compare AI and cloud capex with incremental revenue, margins, and FCF.", "Yes"),
        ("Philip Fisher", "Developer/customer adoption", "Data Collection", "High", "Collect product usage, seat growth, developer activity, and customer adoption.", "Yes"),
    ],
    "consumer_ecosystem": [
        ("Philip Fisher", "Installed base evidence", "Data Collection", "High", "Collect installed base and active-device evidence.", "Yes"),
        ("Philip Fisher", "Services retention", "Data Collection", "High", "Collect services retention, subscriber, and renewal indicators.", "Yes"),
        ("Philip Fisher", "Customer loyalty", "Data Collection", "Medium", "Collect satisfaction, retention, switching, and ecosystem loyalty evidence.", "Yes"),
        ("Peter Lynch", "Product replacement cycle", "Data Collection", "High", "Collect replacement-cycle, unit, and product-mix trends.", "Yes"),
        ("Charlie Munger", "Services regulation exposure", "Source Verification", "Medium", "Verify platform-fee, antitrust, and services regulation exposure.", "Yes"),
    ],
    "semiconductor": [
        ("Philip Fisher", "Customer concentration", "Data Collection", "High", "Collect top-customer exposure and hyperscaler concentration.", "Yes"),
        ("Philip Fisher", "Demand durability", "Data Collection", "High", "Collect end-demand, order, backlog, and hyperscaler spending evidence.", "Yes"),
        ("Warren Buffett", "Cycle-normalized earnings", "Calculation", "High", "Normalize revenue, margins, earnings, and FCF across the semiconductor cycle.", "Yes"),
        ("Charlie Munger", "Inventory/capacity cycle", "Data Collection", "High", "Collect inventory, utilization, lead-time, and capacity evidence.", "Yes"),
        ("Charlie Munger", "Supply chain / foundry dependency", "Source Verification", "High", "Verify foundry, packaging, supplier, and geographic dependencies.", "Yes"),
    ],
    "retail": [
        ("Peter Lynch", "Same-store sales", "Data Collection", "High", "Collect comparable-store sales history.", "Yes"),
        ("Philip Fisher", "Store economics", "Calculation", "High", "Calculate unit economics, payback, and store-level returns.", "Yes"),
        ("Charlie Munger", "Inventory turnover", "Calculation", "Medium", "Calculate inventory turns, markdowns, and working-capital trends.", "Yes"),
        ("Philip Fisher", "Customer traffic", "Data Collection", "High", "Collect traffic, ticket, loyalty, and membership trends.", "Yes"),
    ],
    "payments_network": [
        ("Peter Lynch", "Payment volume", "Data Collection", "High", "Collect payment and transaction volume growth.", "Yes"),
        ("Peter Lynch", "Cross-border volume", "Data Collection", "High", "Collect cross-border transaction and revenue trends.", "Yes"),
        ("Warren Buffett", "Take rate", "Calculation", "Medium", "Calculate take-rate history and pricing durability.", "Yes"),
        ("Charlie Munger", "Regulatory fee pressure", "Source Verification", "High", "Verify fee regulation and network-pricing exposure.", "Yes"),
    ],
    "industrial": [
        ("Philip Fisher", "Backlog quality", "Data Collection", "High", "Collect backlog conversion, cancellations, and customer evidence.", "Yes"),
        ("Peter Lynch", "Capacity utilization", "Data Collection", "Medium", "Collect utilization and cycle-position indicators.", "Yes"),
        ("Charlie Munger", "Input cost exposure", "Data Collection", "Medium", "Collect commodity, labor, and energy cost exposure.", "Yes"),
        ("Warren Buffett", "Maintenance capex", "Calculation", "High", "Estimate maintenance versus growth capex.", "Yes"),
    ],
    "financial": [
        ("Charlie Munger", "Credit risk", "Data Collection", "High", "Collect loss, reserve, delinquency, and underwriting indicators.", "Yes"),
        ("Peter Lynch", "Funding cost", "Calculation", "High", "Calculate funding mix, cost, and spread trends.", "Yes"),
        ("Warren Buffett", "Book value quality", "Source Verification", "High", "Verify asset quality, marks, reserves, and tangible book value.", "Yes"),
        ("Warren Buffett", "Capital adequacy", "Data Collection", "High", "Collect regulatory capital and stress-test evidence.", "Yes"),
    ],
}


def _load_pack(path: Path) -> dict:
    """Load a YAML pack, returning an empty dictionary when unavailable."""
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _action_owner(evidence_type: str) -> str:
    """Map evidence type to the owner used by the high-priority worklist."""
    if evidence_type == "User Input":
        return "User"
    if evidence_type == "Human Judgment Later":
        return "Human Review Later"
    return "Backoffice"


def _company_audit_status(eligibility_results: list[dict]) -> str:
    """Summarize promotion evidence status for one company."""
    statuses = {item["promotion_eligibility"] for item in eligibility_results}
    if statuses == {"Needs More Evidence"}:
        return "Needs More Evidence"
    if "Conditionally Eligible" in statuses:
        return "Mixed: Conditional / Needs More Evidence"
    return ", ".join(sorted(statuses)) or "Not established"


def _request(
    ticker: str,
    investor: str,
    evidence_needed: str,
    evidence_type: str,
    priority: str,
    action: str,
    blocks: str,
) -> dict:
    """Build one normalized evidence request."""
    return {
        "ticker": ticker,
        "investor": investor,
        "evidence_needed": evidence_needed,
        "evidence_type": evidence_type,
        "priority": priority,
        "backoffice_action": action,
        "blocks_promotion": blocks,
        "action_owner": _action_owner(evidence_type),
    }


def generate_backoffice_missing_evidence_report(
    tickers: list[str],
    outputs_root: Path,
    examples_root: Path,
    portfolio_context: dict | None = None,
) -> str:
    """Generate a practical Backoffice worklist from candidate evidence gaps."""
    companies: list[dict] = []
    requests: list[dict] = []
    source_results: list[dict] = []

    for raw_ticker in tickers:
        ticker = raw_ticker.strip().upper()
        if not ticker:
            continue
        input_path = Path(examples_root) / f"{ticker.lower()}_input.yaml"
        output_dir = Path(outputs_root) / ticker
        pack = merge_portfolio_context_into_pack(
            _load_pack(input_path),
            portfolio_context or {},
        )
        signals = extract_company_signals(pack)
        owner = calculate_owner_earnings_snapshot(pack)
        valuation = calculate_valuation_guardrails(pack)
        inversion_matrix = build_munger_inversion_matrix(pack)
        top_inversion = next(
            (
                row
                for row in inversion_matrix
                if str(row.get("severity", "")).lower() == "high"
            ),
            inversion_matrix[0],
        )
        eligibility_results: list[dict] = []
        portfolio_provided = pack.get("portfolio_context_form", {}).get("provided") is True
        fisher_checklist = build_fisher_scuttlebutt_checklist(pack)
        intrinsic_value = calculate_buffett_intrinsic_value_range(pack)
        munger_scoring = score_munger_incentives_and_stupidity(pack)
        bogle_overlap = calculate_bogle_index_overlap(pack)
        bogle_risk = calculate_bogle_benchmark_risk(pack)
        source_results.append(verify_sources(pack))

        for investor_key, investor_name in INVESTORS.items():
            build_decision_candidate(pack, investor_key)
            eligibility = evaluate_promotion_eligibility(pack, investor_key)
            eligibility_results.append(eligibility)
            for evidence, evidence_type, priority, action, blocks in INVESTOR_REQUESTS[
                investor_key
            ]:
                if investor_key == "fisher":
                    continue
                if investor_key == "lynch":
                    continue
                if investor_key == "munger":
                    continue
                if investor_key == "bogle":
                    continue
                if (
                    investor_key == "buffett"
                    and evidence == "Intrinsic value range"
                    and intrinsic_value["intrinsic_value_mid"] is not None
                ):
                    continue
                contextual_action = action
                if investor_key == "buffett" and evidence == "Intrinsic value range":
                    contextual_action += (
                        f" Current valuation status: {valuation['valuation_status']}; "
                        f"owner earnings quality: {owner['owner_earnings_quality_label']}."
                    )
                if investor_key == "munger" and evidence == "Inversion risk evidence":
                    contextual_action += f" Top risk: {top_inversion['failure_mode']}."
                requests.append(
                    _request(
                        ticker,
                        investor_name,
                        evidence,
                        evidence_type,
                        priority,
                        contextual_action,
                        blocks,
                    )
                )
            if (
                investor_key == "buffett"
                and intrinsic_value["intrinsic_value_mid"] is not None
            ):
                requests.append(
                    _request(
                        ticker,
                        investor_name,
                        "Preliminary intrinsic value source verification",
                        "Source Verification",
                        "High",
                        "Verify owner earnings inputs, market cap, growth assumptions, and terminal multiples.",
                        "Yes",
                    )
                )
                if signals["business_model_type"] in {
                    "semiconductor",
                    "industrial",
                    "financial",
                }:
                    requests.append(
                        _request(
                            ticker,
                            investor_name,
                            "Cycle-normalized earnings",
                            "Calculation",
                            "High",
                            "Normalize earnings and free cash flow across a full business cycle.",
                            "Yes",
                        )
                    )
            if investor_key == "munger":
                munger_requests = [
                    (
                        "Management compensation metrics",
                        "Data Collection",
                        "High",
                        "Collect proxy-statement compensation metrics and performance periods.",
                    ),
                    (
                        "Insider ownership",
                        "Data Collection",
                        "High",
                        "Collect insider ownership, holding requirements, and alignment evidence.",
                    ),
                    (
                        "Share-based compensation trend",
                        "Calculation",
                        "Medium",
                        "Calculate share-based compensation and dilution trends over 5-10 years.",
                    ),
                    (
                        "Buyback price discipline",
                        "Calculation",
                        "High",
                        "Compare repurchase prices and share-count changes with intrinsic value.",
                    ),
                    (
                        "Acquisition history and returns",
                        "Data Collection",
                        "Medium",
                        "Collect acquisition prices, strategic rationale, write-downs, and realized returns.",
                    ),
                    (
                        "Debt discipline",
                        "Source Verification",
                        "Medium",
                        "Verify debt purpose, maturities, leverage policy, and acquisition funding.",
                    ),
                    (
                        "Inversion risk evidence / top hidden-stupidity risk",
                        "Data Collection",
                        "High",
                        (
                            "Collect evidence addressing: "
                            f"{top_inversion['failure_mode']}."
                        ),
                    ),
                ]
                for evidence, evidence_type, priority, action in munger_requests:
                    requests.append(
                        _request(
                            ticker,
                            investor_name,
                            evidence,
                            evidence_type,
                            priority,
                            action,
                            "Yes",
                        )
                    )
                for gap in munger_scoring["evidence_gaps"]:
                    if not any(
                        request["ticker"] == ticker
                        and request["investor"] == investor_name
                        and request["evidence_needed"].lower() in gap.lower()
                        for request in requests
                    ):
                        requests.append(
                            _request(
                                ticker,
                                investor_name,
                                gap.rstrip("."),
                                "Data Collection",
                                "Medium",
                                f"Collect and verify {gap.lower()}",
                                "Yes",
                            )
                        )
            if investor_key == "fisher":
                for item in fisher_checklist["evidence_gaps"]:
                    evidence_type = (
                        "Source Verification"
                        if item["evidence_type"] == "Source Verification"
                        else "Data Collection"
                    )
                    action = (
                        f"Collect {item['evidence_needed'].lower()} Suggested sources: "
                        f"{', '.join(item['suggested_sources'])}."
                    )
                    requests.append(
                        _request(
                            ticker,
                            investor_name,
                            item["evidence_area"],
                            evidence_type,
                            item["priority"],
                            action,
                            "Yes" if item["blocks_fisher_upgrade"] else "No",
                        )
                    )
            if investor_key == "lynch":
                lynch_requests = [
                    ("Growth / PEG source validation", "Source Verification", "High", "Validate provider lineage for historical and forward growth data."),
                    ("EPS CAGR methodology validation", "Source Verification", "High", "Validate EPS definitions, adjustments, and 3Y/5Y calculation windows."),
                    ("Revenue CAGR methodology validation", "Source Verification", "High", "Validate revenue history and 3Y/5Y calculation windows."),
                    ("FCF CAGR validation", "Source Verification", "Medium", "Validate free-cash-flow definitions and CAGR calculation inputs."),
                    ("Forward estimate source validation", "Source Verification", "High", "Validate forward revenue and EPS estimates against timestamped sources."),
                ]
                if signals["business_model_type"] == "semiconductor":
                    lynch_requests.append(
                        (
                            "Cycle-adjusted growth validation",
                            "Calculation",
                            "High",
                            "Normalize revenue, EPS, and FCF growth across the semiconductor cycle.",
                        )
                    )
                for evidence, evidence_type, priority, action in lynch_requests:
                    requests.append(
                        _request(
                            ticker,
                            investor_name,
                            evidence,
                            evidence_type,
                            priority,
                            action,
                            "Yes",
                        )
                    )
            if investor_key == "bogle":
                if not portfolio_provided:
                    requests.append(
                        _request(
                            ticker,
                            investor_name,
                            "Portfolio context",
                            "User Input",
                            "High",
                            "Ask user for current holdings, index funds, target weights, and maximum single-stock limit.",
                            "Yes",
                        )
                    )
                bogle_requests = [
                    (
                        "Benchmark-relative return",
                        "Calculation",
                        "High",
                        (
                            "Calculate stock and "
                            f"{bogle_risk['benchmark_etf']} benchmark total returns "
                            "over 1Y, 3Y, 5Y, and 10Y."
                        ),
                    ),
                    (
                        "Stock and benchmark volatility",
                        "Calculation",
                        "Medium",
                        "Calculate annualized stock and benchmark volatility.",
                    ),
                    (
                        "Stock and benchmark max drawdown",
                        "Calculation",
                        "Medium",
                        "Calculate maximum drawdown over matched periods.",
                    ),
                    (
                        "Beta",
                        "Calculation",
                        "Medium",
                        "Calculate beta against the selected benchmark.",
                    ),
                    (
                        "Correlation",
                        "Calculation",
                        "Medium",
                        "Calculate stock correlation with the selected benchmark.",
                    ),
                    (
                        "Index and ETF holdings validation",
                        "Source Verification",
                        "High",
                        "Verify current ETF holdings and indirect company exposure.",
                    ),
                ]
                direct_stocks = pack.get("portfolio_context_form", {}).get(
                    "current_holdings",
                    {},
                ).get("direct_stocks", [])
                proposed_defined = any(
                    isinstance(item, dict)
                    and str(item.get("ticker", "")).upper() == ticker
                    and item.get("proposed_weight") is not None
                    for item in direct_stocks
                )
                if not proposed_defined:
                    bogle_requests.append(
                        (
                            "Proposed position size",
                            "User Input",
                            "High",
                            (
                                "Ask user to define a proposed direct weight within the "
                                f"{bogle_overlap['maximum_single_stock_weight']:.1%} limit."
                                if bogle_overlap["maximum_single_stock_weight"] is not None
                                else "Ask user to define a proposed direct-stock weight."
                            ),
                        )
                    )
                for evidence, evidence_type, priority, action in bogle_requests:
                    requests.append(
                        _request(
                            ticker,
                            investor_name,
                            evidence,
                            evidence_type,
                            priority,
                            action,
                            "Yes",
                        )
                    )

        for spec in MODEL_REQUESTS.get(signals["business_model_type"], []):
            if spec[0] not in {"Charlie Munger", "Philip Fisher", "Peter Lynch"}:
                requests.append(_request(ticker, *spec))

        companies.append(
            {
                "ticker": ticker,
                "company_name": signals["company_name"],
                "business_model_type": signals["business_model_type"],
                "audit_status": _company_audit_status(eligibility_results),
                "output_dir": output_dir,
                "exists": input_path.exists() and output_dir.exists(),
            }
        )

    lines = [
        "# Backoffice Missing Evidence Request Report",
        "",
        "## 1. Important Disclaimer",
        "",
        "This report is not a recommendation, ranking, vote, average score, or consensus. It is a Backoffice worklist for missing evidence.",
        "",
        "## 2. Companies Covered",
        "",
        "| Ticker | Company | Business Model Type | Candidate Audit Status | Output Directory | Exists |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for company in companies:
        lines.append(
            f"| {company['ticker']} | {company['company_name']} | "
            f"{company['business_model_type']} | {company['audit_status']} | "
            f"{company['output_dir']} | {'Yes' if company['exists'] else 'No'} |"
        )

    lines.extend(
        [
            "",
            "## 3. Evidence Request Summary",
            "",
            "| Ticker | Investor | Evidence Needed | Evidence Type | Priority | Backoffice Action | Blocks Promotion? |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in requests:
        lines.append(
            f"| {item['ticker']} | {item['investor']} | {item['evidence_needed']} | "
            f"{item['evidence_type']} | {item['priority']} | "
            f"{item['backoffice_action']} | {item['blocks_promotion']} |"
        )

    high_priority = [item for item in requests if item["priority"] == "High"]
    lines.extend(
        [
            "",
            "## 4. High Priority Backoffice Worklist",
            "",
            "| Priority | Ticker | Investor | Evidence Needed | Action Owner | Suggested Next Step |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in high_priority:
        lines.append(
            f"| High | {item['ticker']} | {item['investor']} | "
            f"{item['evidence_needed']} | {item['action_owner']} | "
            f"{item['backoffice_action']} |"
        )

    user_inputs = [item for item in requests if item["evidence_type"] == "User Input"]
    lines.extend(
        [
            "",
            "## 5. User Input Requests",
            "",
            "| Ticker | Investor | Evidence Needed | Backoffice Action | Blocks Promotion? |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in user_inputs:
        lines.append(
            f"| {item['ticker']} | {item['investor']} | {item['evidence_needed']} | "
            f"{item['backoffice_action']} | {item['blocks_promotion']} |"
        )

    human_items = [
        item for item in requests if item["evidence_type"] == "Human Judgment Later"
    ]
    lines.extend(
        [
            "",
            "## 6. Human Judgment Later",
            "",
            "These items are not ready for decision until Backoffice has prepared the supporting evidence pack.",
            "",
            "| Ticker | Investor | Evidence Needed | Backoffice Preparation |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in human_items:
        lines.append(
            f"| {item['ticker']} | {item['investor']} | {item['evidence_needed']} | "
            f"{item['backoffice_action']} |"
        )

    lines.extend(
        [
            "",
            "## 7. Suggested Backoffice Execution Order",
            "",
            (
                "1. Confirm proposed position size for Bogle."
                if companies
                and all(
                    not any(
                        item["ticker"] == company["ticker"]
                        and item["evidence_needed"] == "Portfolio context"
                        for item in requests
                    )
                    for company in companies
                )
                else "1. Portfolio context form for Bogle."
            ),
            "2. Buffett valuation and owner earnings work.",
            "3. Fisher scuttlebutt and customer evidence.",
            "4. Lynch PEG and category growth proof.",
            "5. Munger incentives and inversion evidence.",
            "6. Benchmark and index overlap data.",
            "",
            "## 8. Source Verification Dependencies",
            "",
            "Calculated outputs remain dependent on verified underlying inputs. Placeholder and missing source areas must be resolved before automated promotion or final-decision changes.",
            "",
            "| Ticker | Dependency | Current Source Quality | Required Backoffice Action |",
            "| --- | --- | --- | --- |",
        ]
    )
    for result in source_results:
        quality = {
            item["section_name"]: item["section_quality_label"]
            for item in result["source_quality_by_section"]
        }
        dependencies = [
            (
                "Valuation history placeholders",
                quality["historical_valuation"],
                "Validate provider lineage, 5Y/10Y median calculations, and percentile methodology.",
            ),
            (
                "Market data placeholders",
                quality["valuation_snapshot"],
                "Verify market cap, price, and valuation multiples against a timestamped provider.",
            ),
            (
                "Calculated outputs",
                quality["calculated_outputs"],
                "Verify source inputs and retain calculation lineage.",
            ),
            (
                "Scuttlebutt evidence",
                quality["scuttlebutt"],
                "Collect customer, product, developer, partner, and culture evidence.",
            ),
            (
                "Benchmark risk evidence",
                quality["index_benchmark_alternative"],
                "Collect and verify benchmark returns, volatility, drawdown, beta, correlation, and index holdings.",
            ),
        ]
        for dependency, label, action in dependencies:
            lines.append(
                f"| {result['ticker']} | {dependency} | {label} | {action} |"
            )
    lines.append("")
    return "\n".join(lines)
