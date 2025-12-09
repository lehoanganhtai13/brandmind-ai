import re
from typing import Any, Dict


def build_properties_string(properties: Dict[str, Any]) -> str:
    """
    Build a Cypher properties string from a dictionary.

    Example:
        >>> build_properties_string({"name": "Nike", "type": "Brand"})
        "{name: $name, type: $type}"
    """
    if not properties:
        return ""
    props = ", ".join([f"{k}: ${k}" for k in properties.keys()])
    return f"{{{props}}}"


def sanitize_relation_type(relation_type: str) -> str:
    """
    Sanitize and normalize relation type for use in Cypher query.

    Converts camelCase to UPPER_SNAKE_CASE and handles special characters.

    Examples:
        >>> sanitize_relation_type("employsStrategy")
        "EMPLOYS_STRATEGY"
        >>> sanitize_relation_type("createsSynergyWith")
        "CREATES_SYNERGY_WITH"
        >>> sanitize_relation_type("isUnitFor")
        "IS_UNIT_FOR"
        >>> sanitize_relation_type("employs strategy")  # with space
        "EMPLOYS_STRATEGY"
    """
    # Step 1: Insert underscore before uppercase letters (camelCase -> snake_case)
    # "employsStrategy" -> "employs_Strategy" -> "employs_strategy"
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", relation_type)

    # Step 2: Replace any non-alphanumeric chars with underscore
    s = re.sub(r"[^a-zA-Z0-9_]", "_", s)

    # Step 3: Collapse multiple underscores
    s = re.sub(r"_+", "_", s)

    # Step 4: Strip leading/trailing underscores and convert to uppercase
    return s.strip("_").upper()
