from pathlib import Path


KNOWLEDGE_ROOT = Path(__file__).resolve().parents[2] / "knowledge_base"
INTENT_DIRECTORIES = {
    "DELIVERED_NOT_RECEIVED": {"delivery_policies"},
    "FAILED_DELIVERY": {"delivery_policies"},
    "LATE_DELIVERY": {"delivery_policies"},
    "ORDER_STATUS": {"delivery_policies"},
    "DELIVERY_PARTNER": {"delivery_policies"},
    "DAMAGED_ITEM": {"damaged_order_policies"},
    "WRONG_ITEM": {"damaged_order_policies", "replacement_policies"},
    "MISSING_ITEM": {"damaged_order_policies", "replacement_policies"},
    "REFUND": {"refund_policies"},
    "CANCELLATION": {"cancellation_policies"},
    "REPLACEMENT": {"replacement_policies"},
}


def retrieve_policy(query: str, limit: int = 2) -> list[dict[str, str]]:
    """Small lexical local retriever with source-grounded snippets and stable citations."""
    terms = {term.lower().strip(".,!?;:#") for term in query.split() if len(term) > 3}
    normalized_query = query.upper()
    allowed_directories = next(
        (directories for intent, directories in INTENT_DIRECTORIES.items() if intent in normalized_query),
        None,
    )
    matches: list[tuple[int, dict[str, str]]] = []
    for path in sorted(KNOWLEDGE_ROOT.rglob("*.md")):
        if allowed_directories and path.parent.name not in allowed_directories:
            continue
        content = path.read_text(encoding="utf-8")
        score = sum(content.lower().count(term) for term in terms)
        if score:
            matches.append((score, {"source": path.name, "excerpt": content[:1600]}))
    matches.sort(key=lambda item: item[0], reverse=True)
    return [entry for _, entry in matches[:limit]]