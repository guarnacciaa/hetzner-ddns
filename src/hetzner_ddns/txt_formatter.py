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


def format_txt_records(value: str) -> list:
    """
    Format a TXT record value for the Hetzner Cloud API.
    
    Returns a list with a single record dictionary containing the properly
    formatted TXT value. For values longer than 255 characters, the value
    is split into multiple quoted strings within the same value field.
    
    Args:
        value: The raw TXT record value
        
    Returns:
        List with one record dictionary: [{"value": "..."}]
        
    Examples:
        >>> format_txt_records("v=spf1 mx ~all")
        [{"value": '"v=spf1 mx ~all"'}]
        
        >>> format_txt_records("v=DKIM1; k=rsa; p=MIIB...")  # Long key > 255 chars
        [{"value": '"v=DKIM1; k=rsa; p=MII..." "...rest..."'}]
    """
    # Check if the value is already in the pre-formatted quoted format
    # (for backwards compatibility with manually formatted values)
    if _is_preformatted(value):
        logger.debug("TXT value is pre-formatted, passing through as-is")
        return [{"value": value}]
    
    # Clean the value (remove any surrounding quotes if present)
    clean_value = value.strip()
    if clean_value.startswith('"') and clean_value.endswith('"') and '" "' not in clean_value:
        # Single quoted string - remove quotes for processing
        clean_value = clean_value[1:-1]
    
    # If the value fits in a single string, just quote it
    if len(clean_value) <= MAX_TXT_LENGTH:
        formatted = f'"{clean_value}"'
        return [{"value": formatted}]
    
    # Split into chunks of MAX_TXT_LENGTH characters
    chunks = _split_into_chunks(clean_value, MAX_TXT_LENGTH)
    
    # Format as: "chunk1" "chunk2" "chunk3"
    formatted = " ".join(f'"{chunk}"' for chunk in chunks)
    
    logger.info(f"Split long TXT record into {len(chunks)} parts ({len(clean_value)} chars)")
    
    return [{"value": formatted}]


def _is_preformatted(value: str) -> bool:
    """
    Check if a TXT value is already in the pre-formatted quoted format.
    
    Pre-formatted values look like: "part1" "part2"
    These are typically manually formatted DKIM keys.
    """
    value = value.strip()
    
    if not value:
        return False
    
    # Check for the multi-part quoted format: "..." "..."
    if value.startswith('"') and value.endswith('"') and '" "' in value:
        return True
    
    return False


def _split_into_chunks(value: str, chunk_size: int) -> list:
    """
    Split a string into chunks of specified size.
    """
    return [value[i:i + chunk_size] for i in range(0, len(value), chunk_size)]
