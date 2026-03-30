def format_peso(value: float, decimals: int = 2) -> str:
    """
    Format a raw peso value into a human-readable string.
    1,500,000,000 -> PHP 1.50B
    """
    if value is None:
        return "N/A"
    if value >= 1_000_000_000_000:
        return f"PHP {value / 1_000_000_000_000:.{decimals}f}T"
    if value >= 1_000_000_000:
        return f"PHP {value / 1_000_000_000:.{decimals}f}B"
    if value >= 1_000_000:
        return f"PHP {value / 1_000_000:.{decimals}f}M"
    return f"PHP {value:,.{decimals}f}"


def format_number(value: float) -> str:
    """Format large integers with comma separators."""
    if value is None:
        return "N/A"
    return f"{int(value):,}"


def truncate_label(label: str, max_len: int = 40) -> str:
    """Truncate long agency or program names for chart labels."""
    if not label:
        return ""
    return label if len(label) <= max_len else label[:max_len] + "..."