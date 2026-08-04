from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


def sanitize_external_url(value: object) -> str | None:
    if not value:
        return None
    try:
        parsed = urlparse(str(value))
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            return None
        try:
            address = ipaddress.ip_address(parsed.hostname)
            if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
                return None
        except ValueError:
            pass
        return parsed.geturl()
    except (TypeError, ValueError):
        return None


def is_safe_cors_regex(pattern: str | None) -> bool:
    if not pattern:
        return True
    return pattern.startswith("^https://") and pattern.endswith("$") and ".*" not in pattern
