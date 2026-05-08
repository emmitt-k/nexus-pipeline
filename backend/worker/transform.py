"""
Transform data.

Applies:
1. Column mapping (schema_mapping) - rename columns
2. Value transformations (transform_spec) - convert values
"""

from datetime import datetime


def transform_data(data, schema_mapping, transform_spec):
    """
    Apply column mapping and transformations to data.

    Args:
        data: List of dictionaries from CSV/JSON
        schema_mapping: {"source_col": "target_col"}
        transform_spec: {"target_col": {"transform": "..."}}

    Returns:
        Transformed list of dictionaries
    """

    if not data:
        return data

    # Apply mapping + transforms to each row
    transformed = []

    for row in data:
        new_row = {}

        # Apply column mapping
        for source_col, value in row.items():
            # Get target column name
            target_col = schema_mapping.get(source_col, source_col)

            # Get transform rules for this column
            rules = transform_spec.get(target_col, {})

            # Apply transformations
            new_row[target_col] = apply_transforms(value, rules)

        transformed.append(new_row)

    return transformed


def apply_transforms(value, rules):
    """
    Apply transformation rules to a single value.

    Supported rules:
    - transform: "uppercase" | "lowercase" | "titlecase"
    - type: "number" | "boolean" | "date"
    - format: date format (e.g., "YYYY-MM-DD")
    - mask: mask pattern (e.g., "###-####")
    - default: default value if null/empty

    Args:
        value: The cell value
        rules: Dict of transformation rules

    Returns:
        Transformed value
    """

    # Handle null/empty - but allow boolean to handle empty string
    type_rule = rules.get("type", "")
    if (value is None or value == "") and type_rule != "boolean":
        return rules.get("default", value)

    # Apply string transforms
    transform = rules.get("transform", "")
    if transform == "uppercase":
        value = str(value).upper()
    elif transform == "lowercase":
        value = str(value).lower()
    elif transform == "titlecase":
        value = str(value).title()

    # Apply type conversion
    type_rule = rules.get("type", "")
    if type_rule == "number":
        try:
            value = float(value)
            if rules.get("integer"):
                value = int(value)
        except (ValueError, TypeError):
            value = None
    elif type_rule == "boolean":
        value = parse_boolean(value)
    elif type_rule == "date":
        value = parse_date(value, rules.get("format"))

    # Apply masking
    if "mask" in rules:
        value = apply_mask(str(value), rules["mask"])

    return value


def parse_boolean(value):
    """Convert to boolean."""

    if isinstance(value, bool):
        return value

    value_lower = str(value).lower().strip()

    # Truthy
    if value_lower in ("true", "yes", "1", "on", "enabled"):
        return True
    # Falsy
    if value_lower in ("false", "no", "0", "off", "disabled", ""):
        return False

    return None


def parse_date(value, format_str=None):
    """Parse date string to ISO format."""

    if not value:
        return None

    # Common formats
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%b %d, %Y",
        "%B %d, %Y",
        "%d-%m-%Y",
        "%m-%d-%Y",
    ]

    # Add custom format if provided
    if format_str:
        # Handle MMM month abbreviation
        fmt = format_str.replace("YYYY", "%Y").replace("MMM", "%b").replace("MM", "%m").replace("DD", "%d")
        formats.insert(0, fmt)

    for fmt in formats:
        try:
            dt = datetime.strptime(str(value), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Return original if parsing fails
    return value


def apply_mask(value, mask_pattern):
    """
    Apply masking.

    Example: "5551234" with "###-####" -> "555-1234"
    """

    result = []
    value = str(value)
    value_idx = 0

    for char in mask_pattern:
        if char == "#":
            # Use character from value if available
            if value_idx < len(value):
                result.append(value[value_idx])
                value_idx += 1
            else:
                result.append("#")
        else:
            result.append(char)

    return "".join(result)