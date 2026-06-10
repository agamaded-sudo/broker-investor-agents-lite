"""Basic research gap detection."""

KEY_GAPS = {
    "historical_valuation": {
        "description": "Historical valuation data is missing or empty.",
        "priority": "medium",
        "investor_relevance": "Needed to judge valuation against the company's own history.",
    },
    "peer_comparison": {
        "description": "Peer comparison data is missing or empty.",
        "priority": "medium",
        "investor_relevance": "Needed to compare quality, growth, risk, and valuation against alternatives.",
    },
    "scuttlebutt": {
        "description": "Qualitative scuttlebutt evidence is missing or empty.",
        "priority": "low",
        "investor_relevance": "Relevant for Fisher-style qualitative business assessment.",
    },
    "index_benchmark_alternative": {
        "description": "Index benchmark alternative data is missing or empty.",
        "priority": "high",
        "investor_relevance": "Needed to compare the stock against broad-market opportunity cost.",
    },
    "management_ownership_incentives": {
        "description": "Management ownership and incentive data is missing or empty.",
        "priority": "high",
        "investor_relevance": "Needed to assess alignment, stewardship, and capital allocation incentives.",
    },
    "capex_owner_earnings_proxy": {
        "description": "Capex and owner earnings proxy data is missing or empty.",
        "priority": "high",
        "investor_relevance": "Needed to estimate owner earnings and cash generation quality.",
    },
}


def detect_basic_gaps(pack: dict) -> list[dict]:
    """Detect missing or empty key fields in a backoffice data pack."""
    gaps: list[dict] = []

    if not isinstance(pack, dict):
        return [
            {
                "gap_name": "invalid_pack",
                "description": "Backoffice pack must be a dictionary.",
                "priority": "high",
                "investor_relevance": "Validation cannot proceed without a structured data pack.",
            }
        ]

    for gap_name, details in KEY_GAPS.items():
        if pack.get(gap_name) in (None, "", [], {}):
            gaps.append({"gap_name": gap_name, **details})

    return gaps
