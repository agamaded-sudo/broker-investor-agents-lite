"""Business-model-specific Fisher scuttlebutt checklists."""

from broker_agents.backoffice.company_signals import extract_company_signals

SOURCES = {
    "customer": ["Customer interviews", "Renewal data", "Customer surveys"],
    "product": ["Product reviews", "Usage metrics", "Product disclosures"],
    "developer": ["Developer surveys", "Ecosystem metrics", "Partner interviews"],
    "partner": ["Channel checks", "Partner interviews", "Supplier commentary"],
    "employee": ["Employee surveys", "Hiring trends", "Culture disclosures"],
    "competitive": ["Peer disclosures", "Industry research", "Customer comparisons"],
    "adoption": ["Operating KPIs", "Cohort data", "Usage and retention metrics"],
    "verification": ["Regulatory filings", "Official disclosures", "Primary-source checks"],
}


def _item(
    area: str,
    needed: str,
    evidence_type: str,
    priority: str,
    source_key: str,
    why: str,
    blocks: bool = True,
) -> dict:
    """Build one checklist item."""
    return {
        "evidence_area": area,
        "evidence_needed": needed,
        "evidence_type": evidence_type,
        "priority": priority,
        "suggested_sources": SOURCES[source_key],
        "why_it_matters": why,
        "blocks_fisher_upgrade": blocks,
    }


CHECKLISTS = {
    "software_cloud": [
        _item("Customer retention / churn", "Retention, churn, and renewal evidence.", "Adoption / Retention Data", "High", "adoption", "Tests recurring revenue durability."),
        _item("Net revenue retention / customer expansion", "Expansion, seat growth, and spend-per-customer evidence.", "Adoption / Retention Data", "High", "adoption", "Tests growth within the installed customer base."),
        _item("Developer/customer adoption", "Developer activity and customer adoption trends.", "Developer / Ecosystem Evidence", "High", "developer", "Tests ecosystem pull and product adoption."),
        _item("Product usage and mission criticality", "Usage depth, workflow dependence, and switching evidence.", "Product Evidence", "High", "product", "Tests product quality and switching costs."),
        _item("Partner ecosystem", "Partner economics, channel activity, and implementation demand.", "Partner Evidence", "Medium", "partner", "Tests distribution and ecosystem breadth.", False),
        _item("Enterprise customer feedback", "Direct feedback on value, reliability, and alternatives.", "Customer Evidence", "High", "customer", "Tests customer satisfaction and competitive position."),
        _item("Product/segment profitability", "Product or segment margins and unit economics.", "Source Verification", "Medium", "verification", "Tests the economic quality of growth."),
        _item("AI/cloud monetization", "AI and cloud adoption, pricing, revenue, and return evidence.", "Adoption / Retention Data", "High", "adoption", "Tests whether investment converts into durable growth."),
    ],
    "consumer_ecosystem": [
        _item("Installed base evidence", "Active installed base and engagement trends.", "Adoption / Retention Data", "High", "adoption", "Defines the ecosystem monetization base."),
        _item("Customer loyalty / repeat purchase", "Repeat purchase, switching, and loyalty evidence.", "Customer Evidence", "High", "customer", "Tests ecosystem durability."),
        _item("Services retention and adoption", "Subscriber, renewal, usage, and attach-rate evidence.", "Adoption / Retention Data", "High", "adoption", "Tests recurring services growth."),
        _item("Product satisfaction", "Satisfaction, quality, and customer review evidence.", "Product Evidence", "High", "product", "Tests product quality and brand delivery."),
        _item("Developer/app ecosystem", "Developer activity, app supply, and ecosystem economics.", "Developer / Ecosystem Evidence", "High", "developer", "Tests platform breadth and third-party commitment."),
        _item("Replacement cycle", "Upgrade timing, device age, and replacement behavior.", "Customer Evidence", "Medium", "customer", "Tests hardware growth durability."),
        _item("Services regulation pressure", "Regulatory exposure affecting platform and service economics.", "Source Verification", "Medium", "verification", "Tests sustainability of services monetization."),
        _item("Brand strength evidence", "Pricing power, preference, and brand survey evidence.", "Competitive Evidence", "Medium", "competitive", "Tests differentiation and pricing power.", False),
    ],
    "semiconductor": [
        _item("Customer concentration", "Top-customer exposure and concentration trends.", "Customer Evidence", "High", "customer", "Tests dependence on a small number of buyers."),
        _item("Demand durability", "Hyperscaler and customer demand durability evidence.", "Customer Evidence", "High", "customer", "Tests whether current demand can persist."),
        _item("Product roadmap credibility", "Roadmap delivery, performance, and transition evidence.", "Product Evidence", "High", "product", "Tests future product competitiveness."),
        _item("R&D productivity", "R&D history and product-output evidence.", "Product Evidence", "Medium", "product", "Tests innovation efficiency."),
        _item("Supply constraints / supply chain", "Foundry, packaging, and supplier availability evidence.", "Partner Evidence", "High", "partner", "Tests ability to meet demand."),
        _item("Inventory/capacity cycle", "Inventory, utilization, lead-time, and capacity evidence.", "Adoption / Retention Data", "High", "adoption", "Tests cycle and mismatch risk."),
        _item("Competitive positioning", "Customer and peer comparisons across performance and ecosystem.", "Competitive Evidence", "High", "competitive", "Tests relative platform strength."),
        _item("Demand normalization risk", "Evidence on orders, backlog, and normalized end demand.", "Customer Evidence", "High", "customer", "Tests peak-demand risk."),
    ],
    "retail": [
        _item("Customer traffic", "Traffic and visit-frequency evidence.", "Customer Evidence", "High", "customer", "Tests customer demand."),
        _item("Repeat purchase / loyalty", "Repeat purchase, membership, and loyalty evidence.", "Customer Evidence", "High", "customer", "Tests franchise durability."),
        _item("Same-store sales", "Comparable-store sales history and drivers.", "Adoption / Retention Data", "High", "adoption", "Tests organic growth."),
        _item("Store economics", "Unit economics, payback, and store returns.", "Product Evidence", "High", "product", "Tests expansion quality."),
        _item("Inventory discipline", "Turns, markdowns, and stock availability.", "Partner Evidence", "High", "partner", "Tests operating discipline."),
        _item("Customer reviews", "Satisfaction and review trends.", "Customer Evidence", "Medium", "customer", "Tests experience quality.", False),
        _item("Private label / differentiation", "Product differentiation and private-label economics.", "Competitive Evidence", "Medium", "competitive", "Tests moat and pricing power."),
    ],
    "payments_network": [
        _item("Payment volume quality", "Transaction volume mix and durability.", "Adoption / Retention Data", "High", "adoption", "Tests core network growth."),
        _item("Merchant acceptance", "Acceptance footprint and merchant feedback.", "Partner Evidence", "High", "partner", "Tests network breadth."),
        _item("Cross-border volume durability", "Cross-border mix and cycle evidence.", "Adoption / Retention Data", "High", "adoption", "Tests high-value volume durability."),
        _item("Take-rate pressure", "Pricing, incentives, and take-rate trends.", "Competitive Evidence", "High", "competitive", "Tests pricing power."),
        _item("Network effects", "Issuer, merchant, and consumer participation evidence.", "Competitive Evidence", "High", "competitive", "Tests network moat."),
        _item("Regulatory feedback", "Fee and competition regulation evidence.", "Source Verification", "Medium", "verification", "Tests regulatory durability."),
        _item("Partner/bank ecosystem", "Bank, fintech, and processor relationship evidence.", "Partner Evidence", "Medium", "partner", "Tests distribution resilience."),
    ],
    "industrial": [
        _item("Customer relationships", "Customer tenure, concentration, and renewal evidence.", "Customer Evidence", "High", "customer", "Tests franchise durability."),
        _item("Backlog quality", "Backlog conversion, cancellations, and profitability.", "Customer Evidence", "High", "customer", "Tests reported demand quality."),
        _item("Order durability", "Order trends and customer budget evidence.", "Adoption / Retention Data", "High", "adoption", "Tests cycle durability."),
        _item("Product quality", "Reliability, warranty, and customer satisfaction.", "Product Evidence", "High", "product", "Tests differentiation."),
        _item("Utilization", "Capacity and utilization evidence.", "Adoption / Retention Data", "Medium", "adoption", "Tests operating leverage."),
        _item("Aftersales/service revenue", "Installed base and recurring service evidence.", "Adoption / Retention Data", "Medium", "adoption", "Tests recurring economics."),
        _item("Innovation/engineering reputation", "Customer and employee evidence on engineering quality.", "Employee / Culture Evidence", "Medium", "employee", "Tests long-term product leadership."),
    ],
    "financial": [
        _item("Customer franchise", "Customer retention, satisfaction, and relationship depth.", "Customer Evidence", "High", "customer", "Tests franchise durability."),
        _item("Deposit/loan or AUM quality", "Mix, retention, concentration, and quality evidence.", "Adoption / Retention Data", "High", "adoption", "Tests funding or asset franchise quality."),
        _item("Underwriting quality", "Loss, reserve, and through-cycle underwriting evidence.", "Product Evidence", "High", "product", "Tests earnings quality."),
        _item("Distribution strength", "Advisor, branch, digital, and partner distribution evidence.", "Partner Evidence", "Medium", "partner", "Tests customer acquisition strength."),
        _item("Management risk culture", "Employee and governance evidence on risk behavior.", "Employee / Culture Evidence", "High", "employee", "Tests hidden balance-sheet risk."),
        _item("Funding stability", "Funding mix and customer behavior evidence.", "Adoption / Retention Data", "High", "adoption", "Tests liquidity resilience."),
        _item("Regulatory/compliance record", "Primary-source regulatory and compliance evidence.", "Source Verification", "Medium", "verification", "Tests operating and conduct risk."),
    ],
    "generic": [
        _item("Customer evidence", "Direct customer satisfaction and retention evidence.", "Customer Evidence", "High", "customer", "Tests demand durability."),
        _item("Product quality", "Product performance and satisfaction evidence.", "Product Evidence", "High", "product", "Tests differentiation."),
        _item("Growth durability", "Repeatable growth and adoption evidence.", "Adoption / Retention Data", "High", "adoption", "Tests runway quality."),
        _item("Management quality", "Employee, culture, and execution evidence.", "Employee / Culture Evidence", "Medium", "employee", "Tests organizational quality."),
        _item("Competitive position", "Customer and peer comparison evidence.", "Competitive Evidence", "High", "competitive", "Tests moat durability."),
        _item("Retention / repeat purchase", "Retention or repeat-purchase evidence.", "Adoption / Retention Data", "High", "adoption", "Tests recurring demand."),
    ],
}


def _present_types(pack: dict) -> set[str]:
    """Infer broad evidence categories present in the scuttlebutt section."""
    scuttlebutt = pack.get("scuttlebutt", {})
    status = str(scuttlebutt.get("status", "")).lower()
    if status in {"weak_unavailable", "unavailable", "missing", ""}:
        return set()
    if status in {"ready", "complete", "strong"}:
        return {
            "Customer Evidence",
            "Product Evidence",
            "Developer / Ecosystem Evidence",
            "Partner Evidence",
            "Employee / Culture Evidence",
            "Competitive Evidence",
            "Adoption / Retention Data",
            "Source Verification",
        }
    evidence = scuttlebutt.get("evidence", {})
    present: set[str] = set()
    if isinstance(evidence, dict):
        for evidence_type, value in evidence.items():
            if value not in (None, "", [], {}, "unavailable", "missing"):
                present.add(str(evidence_type))
    if not present and scuttlebutt.get("observations"):
        present.update({"Customer Evidence", "Product Evidence"})
    return present


def build_fisher_scuttlebutt_checklist(pack: dict) -> dict:
    """Build a Fisher checklist and readiness assessment from a Backoffice pack."""
    model = extract_company_signals(pack)["business_model_type"]
    items = [dict(item) for item in CHECKLISTS[model]]
    present_types = _present_types(pack)
    gaps = [
        item
        for item in items
        if item["evidence_type"] not in present_types
    ]
    priority_items = [
        item for item in gaps if item["priority"] == "High"
    ]
    has_customer = "Customer Evidence" in present_types or "Adoption / Retention Data" in present_types
    has_product = "Product Evidence" in present_types
    has_ecosystem = bool(
        present_types
        & {
            "Developer / Ecosystem Evidence",
            "Partner Evidence",
            "Competitive Evidence",
        }
    )
    if has_customer and has_product and has_ecosystem:
        readiness_label = "Ready for Fisher Review"
    elif has_customer or has_product:
        readiness_label = "Partially Ready"
    else:
        readiness_label = "Not Ready"
    return {
        "business_model_type": model,
        "checklist_items": items,
        "priority_items": priority_items,
        "evidence_gaps": gaps,
        "scuttlebutt_readiness": {
            "customer_evidence_present": has_customer,
            "product_evidence_present": has_product,
            "ecosystem_or_competitive_evidence_present": has_ecosystem,
            "present_evidence_types": sorted(present_types),
        },
        "readiness_label": readiness_label,
        "notes": [
            "Readiness is based only on structured evidence present in the current pack.",
            "The checklist does not replace Fisher-style human review.",
        ],
    }
