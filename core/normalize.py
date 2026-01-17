"""Stable normalization API.

The rest of the app should import normalization functions from this module.
The underlying implementations live in `core.normalize_mod`.
"""

from core.normalize_mod import (
    SHOPIFY_COLUMN_MAP,
    detect_shopify_orders,
    normalize_orders,
    normalize_shipments,
    normalize_tracking,
)

__all__ = [
    "SHOPIFY_COLUMN_MAP",
    "detect_shopify_orders",
    "normalize_orders",
    "normalize_shipments",
    "normalize_tracking",
]
