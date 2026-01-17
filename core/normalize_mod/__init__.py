"""Normalization implementations.

This package contains the actual normalization functions.
Prefer importing the stable API from `core.normalize`.
"""

from .orders import SHOPIFY_COLUMN_MAP, detect_shopify_orders, normalize_orders
from .shipments import normalize_shipments
from .tracking import normalize_tracking

__all__ = [
    "SHOPIFY_COLUMN_MAP",
    "detect_shopify_orders",
    "normalize_orders",
    "normalize_shipments",
    "normalize_tracking",
]
