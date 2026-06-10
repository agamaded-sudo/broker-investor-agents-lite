"""Basic backoffice data validation."""

REQUIRED_TOP_LEVEL_SECTIONS = [
    "metadata",
    "company_identity",
    "business_model",
    "financial_statements_summary",
    "calculated_financial_metrics",
    "sources_confidence_data_gaps",
]

REQUIRED_COMPANY_FIELDS = [
    "company_name",
    "ticker",
    "exchange",
    "market",
    "currency",
]


def validate_backoffice_pack(pack: dict) -> list[str]:
    """Return validation messages for a basic backoffice data pack."""
    messages: list[str] = []

    if not isinstance(pack, dict):
        return ["Backoffice pack must be a dictionary."]

    for section in REQUIRED_TOP_LEVEL_SECTIONS:
        if section not in pack:
            messages.append(f"Missing required top-level section: {section}")
        elif pack[section] in (None, "", [], {}):
            messages.append(f"Required top-level section is empty: {section}")

    company_identity = pack.get("company_identity")
    if not isinstance(company_identity, dict):
        messages.append("Missing or invalid company_identity section.")
        return messages

    for field in REQUIRED_COMPANY_FIELDS:
        if field not in company_identity:
            messages.append(f"Missing required company_identity field: {field}")
        elif company_identity[field] in (None, "", [], {}):
            messages.append(f"Required company_identity field is empty: {field}")

    return messages
