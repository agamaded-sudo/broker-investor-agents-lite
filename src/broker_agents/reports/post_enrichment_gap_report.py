"""Post-enrichment evidence gap reporting."""

from pathlib import Path

import yaml

from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.backoffice.portfolio_context import (
    load_portfolio_context,
    merge_portfolio_context_into_pack,
)
from broker_agents.backoffice.source_verification import verify_sources
from broker_agents.backoffice.source_verification_matrix import (
    summarize_source_verification_matrix,
)
from broker_agents.calculators.decision_candidates import build_decision_candidate
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
)

INVESTORS = {
    "buffett": "Warren Buffett",
    "munger": "Charlie Munger",
    "fisher": "Philip Fisher",
    "lynch": "Peter Lynch",
    "bogle": "John Bogle",
}

IMPROVED_AREAS = [
    (
        "Official financials",
        "SEC / official filing fixture financial statements and high-confidence source logs.",
        "Buffett, Munger, Lynch",
    ),
    (
        "Market valuation",
        "Current price, market cap, multiples, and market-data provenance.",
        "Buffett, Lynch",
    ),
    (
        "Historical valuation",
        "5Y/10Y valuation medians and percentile fields with market-data provenance.",
        "Buffett, Lynch",
    ),
    (
        "Growth & PEG",
        "Revenue CAGR, EPS CAGR, FCF CAGR, forward growth, and PEG fixture evidence.",
        "Lynch, Fisher",
    ),
]

INVESTOR_GAPS = {
    "buffett": [
        (
            "maintenance vs growth capex split",
            "Still Missing Data",
            "Yes",
            "Build a capex normalization / owner earnings workflow.",
        ),
        (
            "source validation for normalized owner earnings",
            "Source Verification Needed",
            "Yes",
            "Validate 5-10 year FCF history and owner earnings methodology.",
        ),
        (
            "long-term owner earnings durability",
            "Methodology Validation",
            "Yes",
            "Normalize owner earnings across a longer history.",
        ),
        (
            "margin of safety assumption validation",
            "Human Review Needed",
            "Yes",
            "Review growth, discount-rate, and terminal multiple assumptions.",
        ),
    ],
    "munger": [
        (
            "management incentives",
            "Fetcher Needed",
            "Yes",
            "Add an incentives / ownership fetcher from proxy data.",
        ),
        (
            "insider ownership",
            "Fetcher Needed",
            "Yes",
            "Collect insider ownership and alignment data.",
        ),
        (
            "compensation structure",
            "Fetcher Needed",
            "Yes",
            "Collect compensation metrics, targets, and time horizons.",
        ),
        (
            "acquisition return evidence",
            "Methodology Validation",
            "Yes",
            "Analyze acquisition history, returns, and write-downs.",
        ),
        (
            "buyback discipline source evidence",
            "Source Verification Needed",
            "Yes",
            "Validate buyback timing, prices, and valuation context.",
        ),
        (
            "hidden-stupidity qualitative review",
            "Human Review Needed",
            "No",
            "Prepare evidence for later human judgment.",
        ),
    ],
    "fisher": [
        (
            "customer scuttlebutt",
            "Fetcher Needed",
            "Yes",
            "Collect customer interviews, usage evidence, and customer feedback.",
        ),
        (
            "product adoption evidence",
            "Fetcher Needed",
            "Yes",
            "Collect adoption, usage, retention, and product momentum evidence.",
        ),
        (
            "retention/churn",
            "Fetcher Needed",
            "Yes",
            "Collect retention, churn, expansion, and renewal indicators.",
        ),
        (
            "partner/developer feedback",
            "Fetcher Needed",
            "Yes",
            "Collect partner, developer, and ecosystem feedback.",
        ),
        (
            "competitive field checks",
            "Human Review Needed",
            "Yes",
            "Compare field evidence against relevant competitors.",
        ),
        (
            "management depth/customer obsession evidence",
            "Human Review Needed",
            "No",
            "Prepare leadership and culture evidence for Fisher review.",
        ),
    ],
    "lynch": [
        (
            "growth methodology validation",
            "Methodology Validation",
            "Yes",
            "Validate CAGR windows, adjustments, and provider methodology.",
        ),
        (
            "EPS growth source validation",
            "Source Verification Needed",
            "Yes",
            "Verify EPS growth series and forward estimate provenance.",
        ),
        (
            "PEG methodology validation",
            "Methodology Validation",
            "Yes",
            "Validate P/E, growth denominator, and forward estimate assumptions.",
        ),
        (
            "category-specific KPI validation",
            "Fetcher Needed",
            "Yes",
            "Collect KPIs specific to the detected business model.",
        ),
        (
            "cycle-adjusted growth for semiconductors",
            "Methodology Validation",
            "Yes",
            "Normalize growth against cycle-sensitive earnings where applicable.",
        ),
    ],
    "bogle": [
        (
            "benchmark-relative returns",
            "Fetcher Needed",
            "Yes",
            "Add stock-versus-benchmark total return history.",
        ),
        (
            "volatility",
            "Fetcher Needed",
            "Yes",
            "Calculate volatility against relevant benchmarks.",
        ),
        (
            "max drawdown",
            "Fetcher Needed",
            "Yes",
            "Calculate stock and benchmark max drawdowns.",
        ),
        (
            "beta",
            "Fetcher Needed",
            "Yes",
            "Calculate beta from verified return series.",
        ),
        (
            "correlation",
            "Fetcher Needed",
            "Yes",
            "Calculate correlation versus benchmark ETFs.",
        ),
        (
            "ETF/index holdings validation",
            "Fetcher Needed",
            "Yes",
            "Add benchmark risk and index holdings fetcher coverage.",
        ),
        (
            "proposed position size validation",
            "User Input Needed",
            "Yes",
            "Validate any proposed limited weight against portfolio constraints.",
        ),
    ],
}

FETCHER_ROADMAP = [
    (
        "1",
        "Benchmark Risk & Index Holdings Fetcher",
        "Benchmark-relative return, volatility, max drawdown, beta, correlation, ETF/index weights.",
        "John Bogle",
        "Bogle remains blocked by benchmark risk and verified index-overlap evidence.",
    ),
    (
        "2",
        "Incentives / Ownership Fetcher",
        "Management incentives, insider ownership, compensation structure.",
        "Charlie Munger",
        "Munger needs source-backed alignment evidence before promotion review.",
    ),
    (
        "3",
        "Capital Allocation History Fetcher",
        "Buyback discipline, acquisition returns, debt and dividend history.",
        "Charlie Munger, Warren Buffett",
        "Capital allocation quality still needs longer verified history.",
    ),
    (
        "4",
        "Scuttlebutt Collection Workflow",
        "Customer feedback, product adoption, retention, partner and developer evidence.",
        "Philip Fisher",
        "Fisher remains evidence-constrained after quantitative enrichment.",
    ),
    (
        "5",
        "Capex Normalization / Owner Earnings Workflow",
        "Maintenance vs growth capex and normalized owner earnings durability.",
        "Warren Buffett",
        "Buffett still needs validated owner earnings assumptions.",
    ),
    (
        "6",
        "Category KPI Fetchers by Business Model",
        "Business-model KPIs for software, ecosystems, semiconductors, retail, payments, industrials, and financials.",
        "Peter Lynch, Philip Fisher",
        "Lynch and Fisher need category-specific operating proof.",
    ),
]

HUMAN_REVIEW_QUESTIONS = {
    "buffett": "Are owner earnings truly durable after capex normalization?",
    "munger": "Are management incentives rational and aligned?",
    "fisher": "Is the company's product/customer feedback strong enough?",
    "lynch": "Is the growth story simple, durable, and not overpaid?",
    "bogle": "Is a separate satellite position justified despite index overlap?",
}


def _load_pack(path: Path) -> dict:
    """Load a YAML pack, returning an empty mapping when unavailable."""
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _section_quality(verification: dict, section: str) -> str:
    """Return one section quality label from a source verification result."""
    for item in verification.get("source_quality_by_section", []):
        if item["section_name"] == section:
            return item["section_quality_label"]
    return "not available"


def _main_blocker(eligibility: dict) -> str:
    """Return the most useful promotion blocker from an eligibility result."""
    for item in eligibility.get("blocking_conditions", []):
        if item:
            return str(item)
    for item in eligibility.get("required_evidence", []):
        if item:
            return str(item)
    return "No blocker parsed."


def _source_quality_for_area(verification: dict, area: str) -> str:
    """Map improved area names to source-quality labels."""
    section_by_area = {
        "Official financials": "financial_statements_summary",
        "Market valuation": "valuation_snapshot",
        "Historical valuation": "historical_valuation",
        "Growth & PEG": "growth_peg_analysis",
    }
    return _section_quality(verification, section_by_area[area])


def generate_post_enrichment_gap_report(
    tickers: list[str],
    outputs_root: Path,
    examples_root: Path,
) -> str:
    """Generate a Markdown report of remaining evidence gaps after enrichment."""
    outputs_root = Path(outputs_root)
    examples_root = Path(examples_root)
    companies: list[dict] = []
    warnings: list[str] = []
    portfolio_context: dict = {}
    portfolio_context_path = examples_root / "portfolio_context.yaml"
    if portfolio_context_path.is_file():
        try:
            portfolio_context = load_portfolio_context(portfolio_context_path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            warnings.append(
                f"Could not load shared portfolio context {portfolio_context_path}: {exc}"
            )

    for raw_ticker in tickers:
        ticker = raw_ticker.strip().upper()
        if not ticker:
            continue
        lower = ticker.lower()
        enriched_input = outputs_root / ticker / f"{lower}_enriched_input.yaml"
        enriched_output = outputs_root / ticker / "enriched"
        summary_path = enriched_output / f"{lower}_agents_summary.md"
        pack = _load_pack(enriched_input)
        if not pack:
            warnings.append(f"Could not parse enriched input for {ticker}: {enriched_input}")
        verification = verify_sources(pack) if pack else {}
        analysis_pack = merge_portfolio_context_into_pack(pack, portfolio_context)
        verification_matrix = (
            summarize_source_verification_matrix(analysis_pack).to_dict()
            if analysis_pack
            else {}
        )
        signals = extract_company_signals(analysis_pack) if analysis_pack else {}
        candidates: dict[str, dict] = {}
        eligibility: dict[str, dict] = {}
        for investor in INVESTORS:
            if not analysis_pack:
                continue
            try:
                candidates[investor] = build_decision_candidate(analysis_pack, investor)
                eligibility[investor] = evaluate_promotion_eligibility(
                    analysis_pack, investor
                )
            except (KeyError, ValueError, TypeError) as exc:
                warnings.append(f"Could not evaluate {ticker} {investor}: {exc}")
        companies.append(
            {
                "ticker": ticker,
                "lower": lower,
                "enriched_input": enriched_input,
                "enriched_output": enriched_output,
                "summary_path": summary_path,
                "pack": pack,
                "verification": verification,
                "verification_matrix": verification_matrix,
                "business_model_type": signals.get("business_model_type", "generic"),
                "candidates": candidates,
                "eligibility": eligibility,
                "manual_input": examples_root / f"{lower}_input.yaml",
            }
        )

    lines = [
        "# Post-Enrichment Evidence Gap Report",
        "",
        "## 1. Important Disclaimer",
        "",
        "This report is not a recommendation, ranking, vote, average score, or consensus. "
        "It identifies evidence gaps after enrichment only.",
        "",
        "## 2. Companies Reviewed",
        "",
        "| Ticker | Enriched Input Exists | Enriched Output Exists | Enriched Summary Exists | Source Quality |",
        "| --- | --- | --- | --- | --- |",
    ]
    for company in companies:
        source_quality = company["verification"].get(
            "overall_source_quality", "Not available"
        )
        lines.append(
            f"| {company['ticker']} | {'Yes' if company['enriched_input'].is_file() else 'No'} | "
            f"{'Yes' if company['enriched_output'].is_dir() else 'No'} | "
            f"{'Yes' if company['summary_path'].is_file() else 'No'} | {source_quality} |"
        )

    lines.extend(
        [
            "",
            "## 3. What Improved After Enrichment",
            "",
            "| Ticker | Improved Area | Evidence Added | Source Quality After Enrichment | Affected Investors |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        for area, evidence, affected in IMPROVED_AREAS:
            quality = _source_quality_for_area(company["verification"], area)
            lines.append(
                f"| {company['ticker']} | {area} | {evidence} | {quality} | {affected} |"
            )

    lines.extend(
        [
            "",
            "## 4. Source Verification Matrix After Enrichment",
            "",
            "| Ticker | Category | Status | Broker Action | Blocks Promotion? |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        for category in company["verification_matrix"].get("categories", []):
            lines.append(
                f"| {company['ticker']} | {category['category']} | "
                f"{category['status']} | {category['broker_action']} | "
                f"{'Yes' if category['blocks_promotion'] else 'No'} |"
            )

    lines.extend(
        [
            "",
            "## 5. Remaining Evidence Gaps by Investor",
            "",
            "| Ticker | Investor | Remaining Gap | Gap Type | Blocks Promotion? | Suggested Next Step |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        for investor_key, investor_name in INVESTORS.items():
            for gap, gap_type, blocks, next_step in INVESTOR_GAPS[investor_key]:
                if (
                    gap == "cycle-adjusted growth for semiconductors"
                    and company["business_model_type"] != "semiconductor"
                ):
                    continue
                lines.append(
                    f"| {company['ticker']} | {investor_name} | {gap} | {gap_type} | "
                    f"{blocks} | {next_step} |"
                )

    lines.extend(
        [
            "",
            "## 6. Promotion Blockers After Enrichment",
            "",
            "| Ticker | Investor | Candidate Decision | Promotion Status | Main Blocker | Auto-Promotion |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        for investor_key, investor_name in INVESTORS.items():
            candidate = company["candidates"].get(investor_key, {})
            eligibility = company["eligibility"].get(investor_key, {})
            auto_promotion = eligibility.get("auto_promotion_allowed", False)
            lines.append(
                f"| {company['ticker']} | {investor_name} | "
                f"{candidate.get('candidate_decision', 'Not available')} | "
                f"{eligibility.get('promotion_eligibility', 'Not available')} | "
                f"{_main_blocker(eligibility)} | "
                f"{'disabled / false' if not auto_promotion else 'enabled'} |"
            )

    lines.extend(
        [
            "",
            "## 7. Fetcher Roadmap From Remaining Gaps",
            "",
            "| Priority | Fetcher / Workflow | Evidence Covered | Affected Investors | Why Next |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for priority, workflow, evidence, affected, why_next in FETCHER_ROADMAP:
        lines.append(
            f"| {priority} | {workflow} | {evidence} | {affected} | {why_next} |"
        )

    lines.extend(
        [
            "",
            "## 8. Human Review Queue Candidates",
            "",
            "| Priority | Ticker | Investor | Review Question | Why Human Review Is Needed |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for company in companies:
        for priority, (investor_key, investor_name) in enumerate(INVESTORS.items(), start=1):
            lines.append(
                f"| {priority} | {company['ticker']} | {investor_name} | "
                f"{HUMAN_REVIEW_QUESTIONS[investor_key]} | "
                "The enriched pipeline still leaves judgment-heavy evidence unresolved. |"
            )

    lines.extend(
        [
            "",
            "## 9. Safety Check",
            "",
            "- Final decisions unchanged.",
            "- Auto-promotion disabled.",
            "- No ranking.",
            "- No consensus.",
            "- No portfolio allocation recommendation.",
            "- No trade or execution signal.",
            "- Human review required before any promotion.",
        ]
    )
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
    lines.append("")
    return "\n".join(lines)
