"""Business-model-driven company signal extraction from Backoffice packs."""

from typing import Any

from broker_agents.calculators.owner_earnings import calculate_owner_earnings_snapshot

BUSINESS_MODEL_TYPES = {
    "software_cloud",
    "consumer_ecosystem",
    "semiconductor",
    "retail",
    "payments_network",
    "industrial",
    "financial",
    "generic",
}


def _text_from_values(value: Any) -> str:
    """Return a lowercase text blob from nested dictionaries and lists."""
    if isinstance(value, dict):
        return " ".join(_text_from_values(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_text_from_values(item) for item in value)
    return str(value).lower()


def _pack_text(pack: dict) -> str:
    """Return searchable business, product, KPI, sector, and industry text."""
    company_identity = pack.get("company_identity", {})
    return _text_from_values(
        {
            "sector": company_identity.get("sector"),
            "industry": company_identity.get("industry"),
            "business_model": pack.get("business_model", {}),
            "products": pack.get("products_customers_revenue_segments", {}),
            "product_service_mix": pack.get("product_service_mix", {}),
            "operating_kpis": pack.get("sector_specific_operating_kpis", {}),
        }
    )


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    """Return whether any term occurs in text."""
    return any(term in text for term in terms)


def _is_large_cap_or_index_constituent(pack: dict) -> bool:
    """Infer whether concentration and index overlap are likely relevant."""
    market_cap = pack.get("valuation_snapshot", {}).get("market_cap")
    try:
        return float(market_cap) >= 200_000
    except (TypeError, ValueError):
        return _contains_any(_pack_text(pack), ("large-cap", "mega-cap", "index constituent"))


def detect_business_model_type(pack: dict) -> str:
    """Classify the company into a supported business model type."""
    text = _pack_text(pack)
    company_identity = pack.get("company_identity", {})
    industry = str(company_identity.get("industry", "")).lower()
    kpis = pack.get("sector_specific_operating_kpis", {})
    kpi_keys = _text_from_values(list(kpis.keys()))

    if _contains_any(industry, ("semiconductor", "chips", "gpu", "foundry")):
        return "semiconductor"
    if "consumer electronics" in industry:
        return "consumer_ecosystem"
    if _contains_any(industry, ("software", "cloud", "enterprise software")):
        return "software_cloud"
    if _contains_any(industry, ("payments", "financial network", "card network")):
        return "payments_network"
    if "retail" in industry:
        return "retail"
    if _contains_any(industry, ("industrial", "manufacturing", "machinery", "materials")):
        return "industrial"
    if _contains_any(industry, ("bank", "insurance", "asset management", "financial")):
        return "financial"

    if _contains_any(
        text,
        ("semiconductor", "chips", "chip ", "gpu", "foundry", "wafer", "data center accelerator"),
    ):
        return "semiconductor"
    if _contains_any(
        text,
        ("consumer electronics", "iphone", "wearables", "hardware ecosystem", "installed base"),
    ) or (
        "services" in text
        and _contains_any(text, ("devices", "hardware", "smartphone", "tablet", "personal computer"))
    ):
        return "consumer_ecosystem"
    if _contains_any(
        text,
        ("software", "cloud", "saas", "azure", "microsoft 365", "enterprise software", "ai platform"),
    ) or _contains_any(kpi_keys, ("software_cloud", "cloud")):
        return "software_cloud"
    if _contains_any(
        text,
        ("payment volume", "card network", "financial network", "take rate", "cross-border volume"),
    ):
        return "payments_network"
    if _contains_any(text, ("retail", "same-store sales", "same store sales", "average ticket")) or _contains_any(
        kpi_keys,
        ("store_count", "same_store_sales", "average_ticket", "inventory_turnover"),
    ):
        return "retail"
    if _contains_any(
        text,
        ("industrial", "manufacturing", "machinery", "materials"),
    ) or _contains_any(kpi_keys, ("capacity", "utilization", "backlog", "orders", "input_cost_exposure")):
        return "industrial"
    if _contains_any(
        text,
        ("bank", "insurance", "asset management", "financial services"),
    ) or _contains_any(kpi_keys, ("loan_growth", "deposits", "nim", "npl", "capital_adequacy")):
        return "financial"
    return "generic"


def detect_revenue_pattern(pack: dict) -> dict:
    """Detect dominant revenue and product patterns."""
    text = _pack_text(pack)
    segments = pack.get("products_customers_revenue_segments", {}).get("segments", [])
    numeric_segments: list[tuple[str, float]] = []
    for segment in segments if isinstance(segments, list) else []:
        if not isinstance(segment, dict):
            continue
        try:
            numeric_segments.append((str(segment.get("name", "Unknown")), float(segment["revenue"])))
        except (KeyError, TypeError, ValueError):
            continue
    numeric_segments.sort(key=lambda item: item[1], reverse=True)

    recurring_terms = _contains_any(
        text,
        ("subscription", "subscriptions", "saas", "services", "recurring", "membership"),
    )
    hardware_terms = _contains_any(
        text,
        ("iphone", "hardware", "devices", "smartphones", "wearables", "chips", "equipment"),
    )
    dominant_segment = numeric_segments[0][0] if numeric_segments else "Not established"

    return {
        "dominant_segment": dominant_segment,
        "segment_count": len(numeric_segments),
        "has_recurring_revenue_signals": recurring_terms,
        "has_hardware_revenue_signals": hardware_terms,
        "revenue_model_text": _text_from_values(pack.get("business_model", {}).get("revenue_model", [])),
    }


def detect_capex_profile(pack: dict) -> str:
    """Classify capex intensity from the owner earnings snapshot."""
    capex_to_ocf = calculate_owner_earnings_snapshot(pack).get("capex_to_ocf")
    if capex_to_ocf is None:
        return "unknown"
    if capex_to_ocf < 0.15:
        return "low_capex_intensity"
    if capex_to_ocf < 0.35:
        return "moderate_capex_intensity"
    return "high_capex_intensity"


def detect_growth_engine(pack: dict) -> str:
    """Detect the primary growth engine from business model and operating evidence."""
    business_model_type = detect_business_model_type(pack)
    text = _pack_text(pack)

    if business_model_type == "software_cloud":
        if _contains_any(text, ("ai", "copilot", "data center", "azure")):
            return "Cloud and AI infrastructure adoption"
        return "Cloud, enterprise software, and subscription adoption"
    if business_model_type == "consumer_ecosystem":
        if "iphone" in text:
            return "iPhone ecosystem and services monetization"
        return "Installed base, ecosystem monetization, and services expansion"
    if business_model_type == "semiconductor":
        return "Data center, AI compute, and semiconductor demand cycle"
    if business_model_type == "retail":
        if _contains_any(text, ("membership", "renewal rate", "paid households", "cardholders")):
            return (
                "Membership renewal, comparable sales, store expansion, "
                "and pricing discipline"
            )
        return "Same-store sales, store expansion, and customer traffic"
    if business_model_type == "payments_network":
        return "Payment volume, cross-border growth, and network effects"
    if business_model_type == "industrial":
        return "Orders, backlog, capacity utilization, and pricing cycle"
    if business_model_type == "financial":
        return "Balance sheet growth, fees, and underwriting or investment spread"
    return "Not established from current pack"


def detect_major_data_gaps(pack: dict) -> list[str]:
    """Collect known and section-level data gaps without duplicates."""
    gaps: list[str] = []
    sources = pack.get("sources_confidence_data_gaps", {})
    candidates: list[Any] = list(sources.get("known_gaps", [])) if isinstance(sources, dict) else []
    for section_name in (
        "quality_of_earnings",
        "sector_specific_operating_kpis",
        "management_ownership_incentives",
        "capex_owner_earnings_proxy",
        "historical_valuation",
        "peer_comparison",
        "scuttlebutt",
        "index_benchmark_alternative",
        "portfolio_context_form",
    ):
        section = pack.get(section_name, {})
        if isinstance(section, dict):
            candidates.extend(section.get("gaps", []))
    for gap in candidates:
        text = str(gap)
        if text and text not in gaps:
            gaps.append(text)
    return gaps


def _dominant_revenue_stream(pack: dict, business_model_type: str, revenue_pattern: dict) -> str:
    """Build a business-model-aware dominant revenue stream description."""
    mapping = {
        "software_cloud": "Software, cloud, subscriptions, and enterprise productivity",
        "consumer_ecosystem": "Hardware-led ecosystem with services growth",
        "semiconductor": "Chips, platforms, and semiconductor components",
        "retail": "Retail sales with recurring membership economics",
        "payments_network": "Transaction fees and network revenue",
        "industrial": "Industrial production, equipment, or materials",
        "financial": "Interest income, fees, premiums, or assets under management",
    }
    if business_model_type == "consumer_ecosystem" and "iphone" in _pack_text(pack):
        return "iPhone-led hardware ecosystem with services expansion"
    if business_model_type == "software_cloud" and _contains_any(
        _pack_text(pack),
        ("enterprise software", "productivity", "microsoft 365"),
    ):
        return "Enterprise software, cloud, and productivity ecosystem"
    if business_model_type in mapping:
        return mapping[business_model_type]
    revenue_model = pack.get("business_model", {}).get("revenue_model")
    summary = pack.get("business_model", {}).get("summary") or pack.get("business_model", {}).get(
        "business_summary"
    )
    if revenue_model:
        return "; ".join(str(item) for item in revenue_model) if isinstance(revenue_model, list) else str(revenue_model)
    if revenue_pattern.get("dominant_segment") != "Not established":
        return f"Dominant reported segment: {revenue_pattern['dominant_segment']}"
    return str(summary or "Not established from current pack")


def _major_capex_issue(pack: dict, business_model_type: str, capex_profile: str) -> str:
    """Build a business-model-aware capex issue."""
    text = _pack_text(pack)
    if business_model_type == "software_cloud":
        if capex_profile == "high_capex_intensity" and _contains_any(text, ("ai", "azure", "data center")):
            return "AI and data center infrastructure capex"
        return "Cloud and data infrastructure investment"
    if business_model_type == "consumer_ecosystem":
        if capex_profile == "low_capex_intensity":
            return "Lower direct capex intensity than cloud infrastructure businesses"
        return "Product tooling, supply chain, and ecosystem investment"
    if business_model_type == "semiconductor":
        return "Manufacturing, foundry, capacity, and inventory cycle"
    if business_model_type == "retail":
        return "Store expansion and inventory working capital"
    if business_model_type == "payments_network":
        return "Low physical capex; regulatory and technology investment matter"
    if business_model_type == "industrial":
        return "Maintenance capex, capacity expansion, and energy or input costs"
    if business_model_type == "financial":
        return "Capital adequacy, credit risk, and reserves rather than physical capex"
    if capex_profile == "high_capex_intensity":
        return "High capex intensity requires return-on-investment evidence"
    if capex_profile == "moderate_capex_intensity":
        return "Moderate capex intensity requires maintenance versus growth clarification"
    if capex_profile == "low_capex_intensity":
        return "Low direct capex intensity"
    return "Capex profile not established"


def _major_margin_issue(business_model_type: str) -> str:
    """Return the primary margin issue for a business model."""
    return {
        "software_cloud": "Cloud infrastructure costs, competition, and AI margin pressure",
        "consumer_ecosystem": "Services mix, hardware product mix, and replacement-cycle sensitivity",
        "semiconductor": "Cycle pricing, utilization, inventory, and product-mix volatility",
        "retail": "Merchandise mix, labor, shrink, occupancy, and inventory markdowns",
        "payments_network": "Take-rate pressure, regulation, and technology investment",
        "industrial": "Utilization, pricing, energy, and input-cost exposure",
        "financial": "Credit costs, spread compression, reserves, and leverage",
        "generic": "Margin durability not established from current pack",
    }[business_model_type]


def build_investor_specific_angles(pack: dict, detected: dict) -> dict:
    """Build investor-specific angles from detected company patterns."""
    model = detected["business_model_type"]
    text = _pack_text(pack)
    large_cap_note = (
        "Large index constituent; individual ownership likely increases concentration"
        if _is_large_cap_or_index_constituent(pack)
        else "Needs benchmark overlap and portfolio concentration context"
    )

    angles = {
        "software_cloud": {
            "buffett": "Owner earnings depend on cloud infrastructure capex, retention, and pricing power.",
            "munger": "Assess whether infrastructure investment is rational and whether competition creates hidden fragility.",
            "fisher": "Needs customer retention, net revenue retention, developer/customer adoption, and product usage evidence",
            "lynch": "Cloud/software growth story needs retention, EPS/FCF growth, and valuation-vs-growth checks",
            "bogle": large_cap_note,
        },
        "consumer_ecosystem": {
            "buffett": "Needs owner earnings, ecosystem durability, and valuation evidence beyond reported cash generation.",
            "munger": "Assess product dependence, ecosystem durability, capital allocation discipline, and incentives.",
            "fisher": "Needs loyalty, installed base, services retention, developer ecosystem, and product satisfaction evidence",
            "lynch": "Ecosystem + services monetization story needs replacement-cycle, PEG, and growth-durability checks",
            "bogle": large_cap_note,
        },
        "semiconductor": {
            "buffett": "Needs normalized cycle earnings, capital intensity, and durable platform economics.",
            "munger": "Focus on cycle risk, customer concentration, capital intensity, and hidden fragility.",
            "fisher": "Needs customer concentration, product roadmap, R&D, ecosystem, and supply-constraint evidence",
            "lynch": "Cyclicality, inventory, sustainable earnings, and valuation versus cycle are central",
            "bogle": large_cap_note,
        },
        "retail": {
            "buffett": "Needs durable membership economics, store returns, inventory discipline, and valuation evidence.",
            "munger": "Focus on membership loyalty, operating discipline, inventory mistakes, and avoiding overpayment.",
            "fisher": "Needs customer loyalty, membership renewal, store economics, and product differentiation evidence",
            "lynch": "Membership renewal, comparable sales, unit economics, store growth, and valuation drive the story",
            "bogle": large_cap_note,
        },
        "payments_network": {
            "buffett": "Needs durable network economics, pricing power, and regulatory resilience.",
            "munger": "Focus on network durability, regulation, incentives, and technology disruption.",
            "fisher": "Needs network effects, acceptance, volume growth, and innovation evidence",
            "lynch": "Payment volume and earnings growth story must be tested against valuation",
            "bogle": large_cap_note,
        },
        "industrial": {
            "buffett": "Needs normalized cycle earnings, maintenance capex, and pricing-power evidence.",
            "munger": "Focus on cyclicality, capital intensity, and commodity or input-cost fragility.",
            "fisher": "Needs customer relationships, product quality, backlog, and innovation evidence",
            "lynch": "Cyclicality, backlog, margins, and peak-earnings risk drive the story",
            "bogle": large_cap_note,
        },
        "financial": {
            "buffett": "Needs underwriting quality, normalized earnings, leverage, and capital adequacy evidence.",
            "munger": "Focus on leverage, hidden balance-sheet risk, reserves, and incentives.",
            "fisher": "Needs customer franchise, distribution, and long-term relationship evidence",
            "lynch": "Credit cycle, book value, and earnings quality drive the story",
            "bogle": large_cap_note,
        },
        "generic": {
            "buffett": "Needs durable economics, owner earnings, and valuation evidence.",
            "munger": "Needs incentive, culture, and avoidable-error evidence.",
            "fisher": "Needs customer, product, management, and growth-quality evidence.",
            "lynch": "Needs a simple story, category fit, growth, and valuation evidence.",
            "bogle": large_cap_note,
        },
    }[model]

    if model == "software_cloud":
        products: list[str] = []
        for term, label in (
            ("azure", "Azure"),
            ("microsoft 365", "Microsoft 365"),
            ("copilot", "Copilot"),
        ):
            if term in text:
                products.append(label)
        if products:
            angles["fisher"] = f"Needs customer/developer scuttlebutt for {', '.join(products)}"
        if _contains_any(text, ("productivity", "microsoft 365")) and "ai" in text:
            angles["lynch"] = "Cloud + AI + productivity ecosystem story"
    if model == "consumer_ecosystem" and "iphone" in text:
        angles["fisher"] = (
            "Needs installed base, retention, customer loyalty, services adoption, "
            "developer ecosystem, and product satisfaction evidence"
        )
        angles["lynch"] = "Ecosystem + services monetization story"
    return angles


def build_decision_rationales(pack: dict, detected: dict) -> dict:
    """Build generalized investor decision rationales."""
    model = detected["business_model_type"]
    capex_profile = detected["capex_profile"]
    growth_engine = detected["primary_growth_engine"]
    text = _pack_text(pack)

    rationales = {
        "buffett": (
            f"Owner earnings and margin of safety require confirmation for a {model} business; "
            f"the current capex profile is {capex_profile}."
        ),
        "munger": (
            f"The main inversion risks arise from {detected['major_capex_issue'].lower()}, "
            "business durability, incentives, and capital allocation."
        ),
        "fisher": f"The growth case depends on stronger qualitative evidence around {growth_engine.lower()}.",
        "lynch": f"The story centers on {growth_engine.lower()}, but growth durability and valuation need confirmation.",
        "bogle": (
            "Separate ownership requires benchmark-overlap and portfolio-concentration evidence."
        ),
    }

    if model == "software_cloud":
        rationales["buffett"] = (
            "Owner earnings and margin of safety need better clarity because AI/data-center capex "
            "may affect normalized owner earnings."
            if _contains_any(text, ("ai", "data center", "azure"))
            else "Owner earnings and margin of safety need clearer cloud infrastructure capex and retention evidence."
        )
        rationales["munger"] = (
            "AI infrastructure could be a rational growth investment or an expensive arms race; "
            "incentive and capex quality need more evidence."
        )
        rationales["fisher"] = (
            "Growth case depends on customer/developer adoption of Azure, Microsoft 365, and Copilot."
            if _contains_any(text, ("azure", "microsoft 365", "copilot"))
            else "Growth case depends on customer retention, product usage, and developer adoption."
        )
        rationales["lynch"] = (
            "Story is Cloud + AI + productivity ecosystem, but PEG and expectations need confirmation."
        )
    elif model == "consumer_ecosystem":
        rationales["buffett"] = (
            "Strong cash generation and lower capex intensity are attractive, but valuation history "
            "and normalized growth still need confirmation."
            if capex_profile == "low_capex_intensity"
            else "Ecosystem cash generation is attractive, but owner earnings, valuation, and growth durability need confirmation."
        )
        rationales["munger"] = (
            "Key risks include product dependence, ecosystem durability, capital allocation discipline, and incentives."
        )
        rationales["fisher"] = (
            "Growth case depends on installed base loyalty, services adoption, customer retention, and product innovation."
        )
        rationales["lynch"] = (
            "Story is ecosystem + services monetization, but growth rate and PEG need confirmation."
        )
    elif model == "retail" and "membership" in text:
        rationales["buffett"] = (
            "Recurring membership economics and customer loyalty support business quality, "
            "but normalized owner earnings and valuation discipline remain decisive."
        )
        rationales["munger"] = (
            "The membership franchise may be high quality, but inventory discipline, "
            "capital allocation, and overpayment risk require evidence."
        )
        rationales["fisher"] = (
            "The growth case depends on membership renewal, customer loyalty, "
            "store economics, and field evidence on the customer experience."
        )
        rationales["lynch"] = (
            "The story is understandable membership-led retail growth, but comparable sales, "
            "store economics, and valuation versus growth need confirmation."
        )

    if _is_large_cap_or_index_constituent(pack):
        ticker = str(pack.get("company_identity", {}).get("ticker") or "The company").upper()
        rationales["bogle"] = (
            f"{ticker} is already a major index constituent; separate ownership likely increases concentration."
        )
    return rationales


def extract_company_signals(pack: dict) -> dict:
    """Extract generalized company-specific signals from a Backoffice pack."""
    company_identity = pack.get("company_identity", {})
    metadata = pack.get("metadata", {})
    ticker = str(company_identity.get("ticker") or metadata.get("ticker") or "").upper()
    company_name = str(
        company_identity.get("company_name") or metadata.get("company_name") or "Unknown company"
    )
    business_model_type = detect_business_model_type(pack)
    revenue_pattern = detect_revenue_pattern(pack)
    capex_profile = detect_capex_profile(pack)
    detected = {
        "business_model_type": business_model_type,
        "revenue_pattern": revenue_pattern,
        "primary_growth_engine": detect_growth_engine(pack),
        "capex_profile": capex_profile,
        "major_data_gaps": detect_major_data_gaps(pack),
    }
    detected["dominant_revenue_stream"] = _dominant_revenue_stream(
        pack,
        business_model_type,
        revenue_pattern,
    )
    detected["major_capex_issue"] = _major_capex_issue(
        pack,
        business_model_type,
        capex_profile,
    )
    detected["major_margin_issue"] = _major_margin_issue(business_model_type)

    business_type_labels = {
        "software_cloud": "Software, cloud, and AI platform company",
        "consumer_ecosystem": "Consumer hardware, services, and software ecosystem company",
        "semiconductor": "Semiconductor and compute platform company",
        "retail": "Retail company",
        "payments_network": "Payments network company",
        "industrial": "Industrial or manufacturing company",
        "financial": "Financial services company",
        "generic": "Business model not yet classified",
    }

    return {
        "ticker": ticker,
        "company_name": company_name,
        "business_model_type": business_model_type,
        "business_type": business_type_labels[business_model_type],
        "primary_growth_engine": detected["primary_growth_engine"],
        "secondary_growth_engine": revenue_pattern.get("dominant_segment", "Not established"),
        "dominant_revenue_stream": detected["dominant_revenue_stream"],
        "capex_profile": capex_profile,
        "major_capex_issue": detected["major_capex_issue"],
        "major_margin_issue": detected["major_margin_issue"],
        "major_data_gaps": detected["major_data_gaps"],
        "revenue_pattern": revenue_pattern,
        "investor_specific_angles": build_investor_specific_angles(pack, detected),
        "decision_rationales": build_decision_rationales(pack, detected),
    }
