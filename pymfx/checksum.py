"""
pymfx.checksum — SHA-256 computation and verification for .mfx data[] blocks

Exact rules from spec v1.0 §7:
- Only data lines (not the `data[]:` header line)
- Each line stripped of leading and trailing whitespace
- Line endings normalized to \n (LF only)
- No trailing \n after the last line
"""
import hashlib


def compute_checksum(data_lines: list[str]) -> str:
    """
    Compute the SHA-256 checksum of a data[] block per spec rules.

    Args:
        data_lines: list of raw lines from the data[] block (excluding `data[]:`)

    Returns:
        String of the form "sha256:<hexdigest>"
    """
    trimmed = [line.strip() for line in data_lines]
    # Remove any trailing empty lines
    while trimmed and trimmed[-1] == "":
        trimmed.pop()
    content = "\n".join(trimmed)
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def verify_checksum(data_lines: list[str], declared: str) -> bool:
    """
    Verify that the declared checksum matches the data.

    Args:
        data_lines: raw lines from the data[] block
        declared: checksum value as declared in @checksum (e.g. "sha256:abc123...")

    Returns:
        True if the checksum matches, False otherwise
    """
    computed = compute_checksum(data_lines)
    return computed == declared
