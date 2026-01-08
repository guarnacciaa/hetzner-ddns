"""
TXT record formatter for DNS.

Handles automatic quoting and splitting of long TXT records (like DKIM).
DNS TXT records have a 255 character limit per string, so longer values
must be split into multiple quoted strings.
"""

import logging

logger = logging.getLogger(__name__)

# Maximum length for a single TXT string (DNS limit)
MAX_TXT_LENGTH = 255


def format_txt_value(value: str) -> str:
    """
    Format a TXT record value for DNS.
    
    - Adds quotes around the value if not already quoted
    - Splits values longer than 255 characters into multiple quoted strings
    - Handles DKIM keys and other long TXT records automatically
    
    Args:
        value: The raw TXT record value
        
    Returns:
        Properly formatted TXT value with quotes and splits
        
    Examples:
        >>> format_txt_value("v=spf1 mx ~all")
        '"v=spf1 mx ~all"'
        
        >>> format_txt_value("v=DKIM1; k=rsa; p=MIIB...")  # Long key
        '"v=DKIM1; k=rsa; p=MII..." "...rest of key..."'
    """
    # If value is already properly formatted (starts and ends with quotes),
    # check if it needs reformatting
    if _is_already_formatted(value):
        logger.debug("TXT value already formatted, keeping as-is")
        return value
    
    # Remove any existing quotes for processing
    clean_value = _strip_quotes(value)
    
    # If the value fits in a single string, just quote it
    if len(clean_value) <= MAX_TXT_LENGTH:
        return f'"{clean_value}"'
    
    # Split into chunks of MAX_TXT_LENGTH characters
    chunks = _split_into_chunks(clean_value, MAX_TXT_LENGTH)
    
    # Quote each chunk and join with space
    formatted = " ".join(f'"{chunk}"' for chunk in chunks)
    
    logger.debug(f"Split TXT record into {len(chunks)} chunks")
    return formatted


def _is_already_formatted(value: str) -> bool:
    """
    Check if a TXT value is already properly formatted.
    
    A properly formatted value:
    - Starts with a quote
    - Ends with a quote
    - Has balanced quotes (for multi-part values like "part1" "part2")
    """
    value = value.strip()
    
    if not value:
        return False
    
    # Check if it starts and ends with quotes
    if not (value.startswith('"') and value.endswith('"')):
        return False
    
    # Count quotes - should be even for balanced quotes
    quote_count = value.count('"')
    if quote_count % 2 != 0:
        return False
    
    # Check for the pattern "..." "..." (multi-part TXT)
    # This is valid formatted output
    if '" "' in value:
        return True
    
    # Single quoted string
    if quote_count == 2:
        return True
    
    return False


def _strip_quotes(value: str) -> str:
    """
    Remove quotes from a TXT value for processing.
    
    Handles both single-part and multi-part quoted strings.
    """
    value = value.strip()
    
    # Handle multi-part values: "part1" "part2" -> part1part2
    if '" "' in value:
        # Split by '" "' and strip outer quotes
        parts = value.split('" "')
        # Clean up first and last parts
        if parts:
            parts[0] = parts[0].lstrip('"')
            parts[-1] = parts[-1].rstrip('"')
        return "".join(parts)
    
    # Handle single quoted string
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    
    return value


def _split_into_chunks(value: str, chunk_size: int) -> list:
    """
    Split a string into chunks of specified size.
    """
    return [value[i:i + chunk_size] for i in range(0, len(value), chunk_size)]
