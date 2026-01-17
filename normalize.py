"""Backwards-compatible normalization API (root level).

Prefer importing from `core.normalize` in new code.
This wrapper exists so older imports like `from normalize import normalize_orders`
continue to work.
"""

from __future__ import annotations

from core.normalize import (
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
