"""Deterministic readiness dashboard for the investor-agent system."""

from pathlib import Path

import yaml

from broker_agents.backoffice.company_signals import extract_company_signals
from broker_agents.backoffice.source_verification import verify_sources

AGENT_READINESS = [
    {
        "agent": "Buffett",
        "layers": [
            "Owner Earnings Snapshot",
            "Valuation Guardrails",
            "Intrinsic Value Range",
            "Valuation History Evidence",
            "Normalized Owner Earnings Evidence",
            "Upgrade/Downgrade Conditions",
            "Promotion Eligibility",
        ],
        "level": "Partially Ready",
        "short": "Partial",
        "missing": [
            "historical valuation provider validation",
            "normalized owner earnings validation",
            "maintenance vs growth capex",
            "margin of safety validation",
        ],
        "priority": "Validate valuation history and source-backed owner earnings normalization.",
    },
    {
        "agent": "Munger",
        "layers": [
            "Inversion Risk Matrix",
            "Incentives Score",
            "Capital Allocation Score",
            "Hidden-Stupidity Score",
            "Promotion Eligibility",
        ],
        "level": "Partially Ready",
        "short": "Partial",
        "missing": [
            "management incentives source data",
            "insider ownership",
            "compensation structure",
            "acquisition return evidence",
            "buyback discipline evidence",
        ],
        "priority": "Add source-driven incentives and capital allocation evidence.",
    },
    {
        "agent": "Fisher",
        "layers": [
            "Business-Model Scuttlebutt Checklist",
            "Scuttlebutt Readiness",
            "Promotion Eligibility",
        ],
        "level": "Needs Evidence",
        "short": "Needs Evidence",
        "missing": [
            "customer evidence",
            "product adoption",
            "retention/churn",
            "developer/partner feedback",
            "competitive scuttlebutt",
        ],
        "priority": "Build a scuttlebutt data collection workflow.",
    },
    {
        "agent": "Lynch",
        "layers": [
            "Category Scoring",
            "Story Score",
            "Growth Score",
            "Valuation vs Growth Score",
            "Cyclicality Score",
            "Promotion Eligibility",
        ],
        "level": "Partially Ready",
        "short": "Partial",
        "missing": [
            "growth/PEG provider validation",
            "EPS growth methodology validation",
            "cycle-adjusted growth validation",
            "historical valuation methodology validation",
            "earnings durability",
        ],
        "priority": "Validate growth/PEG providers, methodology, and cycle-adjusted growth.",
    },
    {
        "agent": "Bogle",
        "layers": [
            "Portfolio Context",
            "Index Overlap",
            "Indirect Exposure",
            "Concentration Risk",
            "Benchmark Risk",
            "Limited-Weight Guardrails",
        ],
        "level": "Partially Ready",
        "short": "Partial",
        "missing": [
            "benchmark-relative returns",
            "volatility",
            "max drawdown",
            "beta",
            "correlation",
            "ETF/index holdings validation",
        ],
        "priority": "Add benchmark risk and index holdings fetchers.",
    },
]


def _load_pack(path: Path) -> dict:
    """Load a YAML company pack, returning an empty mapping on failure."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def generate_investor_agent_readiness_dashboard(
    tickers: list[str],
    outputs_root: Path,
    examples_root: Path,
) -> str:
    """Generate a non-ranking dashboard of agent maturity and evidence gaps."""
    companies: list[dict] = []
    for raw_ticker in tickers:
        ticker = raw_ticker.strip().upper()
        if not ticker:
            continue
        input_path = Path(examples_root) / f"{ticker.lower()}_input.yaml"
        output_dir = Path(outputs_root) / ticker
        pack = _load_pack(input_path)
        signals = extract_company_signals(pack)
        source_quality = verify_sources(pack)
        companies.append(
            {
                "ticker": ticker,
                "company": signals["company_name"],
                "business_model_type": signals["business_model_type"],
                "output_dir": output_dir,
                "exists": input_path.exists() and output_dir.exists(),
                "source_quality": source_quality,
            }
        )

    covered_tickers = ", ".join(company["ticker"] for company in companies) or "None"
    lines = [
        "# Investor Agent Readiness Dashboard",
        "",
        "## 1. Important Disclaimer",
        "",
        "This dashboard is not a recommendation, ranking, vote, average score, or consensus. It evaluates agent readiness and missing evidence only.",
        "",
        "## 2. Companies Covered",
        "",
        "| Ticker | Company | Business Model Type | Output Directory | Exists |",
        "| --- | --- | --- | --- | --- |",
    ]
    for company in companies:
        lines.append(
            f"| {company['ticker']} | {company['company']} | "
            f"{company['business_model_type']} | {company['output_dir']} | "
            f"{'Yes' if company['exists'] else 'No'} |"
        )

    lines.extend(
        [
            "",
            "## 3. Agent Readiness Summary",
            "",
            "| Investor Agent | Current Analytical Layers | Readiness Level | Main Missing Evidence | Next Development Priority |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for agent in AGENT_READINESS:
        lines.append(
            f"| {agent['agent']} | {', '.join(agent['layers'])} | "
            f"{agent['level']} | {', '.join(agent['missing'])} | "
            f"{agent['priority']} |"
        )

    lines.extend(
        [
            "",
            "## 4. Source Quality Dependencies by Agent",
            "",
            "| Investor Agent | Required Source Quality | Current Source Status |",
            "| --- | --- | --- |",
        ]
    )
    agent_dependencies = [
        (
            "Buffett",
            "Verified financials, valuation history, and owner earnings inputs.",
            "Financials are generally stronger; historical valuation still needs provider and methodology validation, while normalized owner earnings needs source validation.",
        ),
        (
            "Munger",
            "Verified incentives, ownership, capital allocation, and acquisition evidence.",
            "Management and incentives source quality is weak across the current manual packs.",
        ),
        (
            "Fisher",
            "Verified customer, product, developer, partner, and culture evidence.",
            "Scuttlebutt source quality is weak or missing.",
        ),
        (
            "Lynch",
            "Verified growth history, PEG methodology, category KPIs, earnings durability, and valuation data.",
            "Growth/PEG provider and methodology validation remains incomplete, including cycle adjustment where relevant.",
        ),
        (
            "Bogle",
            "Verified benchmark, index holdings, risk series, and user portfolio context.",
            "Benchmark and index source quality is weak; portfolio context is user-provided when supplied.",
        ),
    ]
    for agent, dependency, status in agent_dependencies:
        lines.append(f"| {agent} | {dependency} | {status} |")

    lines.extend(
        [
            "",
            "## 5. Agent Readiness by Company",
            "",
            "| Ticker | Buffett | Munger | Fisher | Lynch | Bogle |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    readiness_by_agent = {agent["agent"]: agent["short"] for agent in AGENT_READINESS}
    for company in companies:
        lines.append(
            f"| {company['ticker']} | {readiness_by_agent['Buffett']} | "
            f"{readiness_by_agent['Munger']} | {readiness_by_agent['Fisher']} | "
            f"{readiness_by_agent['Lynch']} | {readiness_by_agent['Bogle']} |"
        )

    bottlenecks = [
        (
            "Valuation history",
            "Buffett, Lynch",
            "High",
            "Validate provider lineage, 5Y/10Y median calculations, and percentile methodology.",
        ),
        (
            "Normalized owner earnings",
            "Buffett",
            "High",
            "Normalize operating cash flow, capex, and owner earnings over 5-10 years.",
        ),
        (
            "Incentives and ownership",
            "Munger",
            "High",
            "Collect proxy compensation, insider ownership, and alignment evidence.",
        ),
        (
            "Scuttlebutt/customer evidence",
            "Fisher",
            "High",
            "Build customer, product, developer, partner, and competitive evidence workflows.",
        ),
        (
            "PEG and EPS growth",
            "Lynch",
            "High",
            "Validate growth/PEG provider data, CAGR methodology, and cycle-adjusted growth.",
        ),
        (
            "Benchmark risk",
            "Bogle",
            "High",
            "Calculate benchmark-relative returns, volatility, drawdown, beta, and correlation.",
        ),
        (
            "Index holdings and overlap validation",
            "Bogle",
            "High",
            "Verify ETF holdings, index weights, and indirect exposure estimates.",
        ),
    ]
    lines.extend(
        [
            "",
            "## 6. Evidence Bottlenecks",
            "",
            "| Evidence Area | Affected Agents | Affected Tickers | Priority | Backoffice Action |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for area, agents, priority, action in bottlenecks:
        lines.append(
            f"| {area} | {agents} | {covered_tickers} | {priority} | {action} |"
        )

    lines.extend(
        [
            "",
            "## 7. Recommended Development Sequence",
            "",
            "1. Validate valuation history and normalized owner earnings for Buffett.",
            "2. Add incentives / ownership / compensation evidence for Munger.",
            "3. Add Fisher scuttlebutt collection workflow.",
            "4. Add Lynch PEG and category KPI calculations.",
            "5. Add Bogle benchmark risk and index holdings validation.",
            "6. Add source-driven data fetchers.",
            "7. Add human review queue after evidence coverage improves.",
            "",
            "## 8. Not Yet Ready For",
            "",
            "- Automatic final decision changes.",
            "- Auto-promotion; it remains disabled.",
            "- Ranking companies.",
            "- Portfolio allocation recommendations.",
            "- Live trading or execution.",
            "- Replacing human review.",
            "",
        ]
    )
    return "\n".join(lines)
