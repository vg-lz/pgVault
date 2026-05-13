"""Compatibility wrapper for legacy validator imports."""

from modules.pii_scanner.content_validators import (
    VALIDATORS,
    match_ratio,
    validate_card_number,
    validate_clabe,
    validate_content,
    validate_curp,
    validate_cvv,
    validate_email,
    validate_phone_mx,
    validate_rfc,
    validate_ssn,
    validate_token,
)

__all__ = [
    "VALIDATORS",
    "validate_curp",
    "validate_rfc",
    "validate_email",
    "validate_card_number",
    "validate_cvv",
    "validate_clabe",
    "validate_phone_mx",
    "validate_token",
    "validate_ssn",
    "validate_content",
    "match_ratio",
]
