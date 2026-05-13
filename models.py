"""Compatibility re-export for older module imports.

New PgVault code should import shared contracts from ``pgvault.models``.
The existing PII scanner can migrate gradually without breaking root imports.
"""

from pgvault.models import *  # noqa: F401,F403
