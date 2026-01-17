from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pandas as pd

from .helpers import ColumnRule, _clean_cols, _lower_cols, _require_cols, _safe_str, _to_float, _to_int, _to_utc, _validation

# -------------------------------
# Shopify detection + mapping
# -------------------------------
def detect_shopify_orders(raw_df: pd.DataFrame) -> bool:
    df = _lower_cols(_clean_cols(raw_df))
    cols = set(df.columns)

    shopify_signals = {
        "name",
        "created at",
        "lineitem sku",
        "lineitem quantity",
        "variant sku",
        "shipping country",
        "shipping province",
        "financial status",
        "fulfillment status",
    }
    score = len(shopify_signals.intersection(cols))
    return score >= 3


SHOPIFY_COLUMN_MAP = {
    # IDs
    "name": "order_id",
    "order id": "order_id",

    # time
    "created at": "order_datetime_utc",

    # sku options
    "lineitem sku": "sku",
    "variant sku": "sku",
    "lineitem name": "sku",  # fallback if no SKU

    # quantity
    "lineitem quantity": "quantity_ordered",
    "quantity": "quantity_ordered",

    # geo
    "shipping country": "customer_country",
    "shipping province": "customer_state",

    # financials
    "total": "order_revenue",
    "subtotal": "order_revenue",
    "currency": "currency",

    # shipping
    "shipping method": "shipping_method",
    "shipping line title": "shipping_method",
}


# -------------------------------
# Public API
# -------------------------------
def normalize_orders(
    raw_orders: pd.DataFrame,
    account_id: str,
    store_id: str,
    platform_hint: str = "shopify",
    default_currency: str = "USD",
    default_promised_ship_days: int = 3,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Canonical Orders output columns (one row per order line / sku):
      account_id, store_id, platform, order_id, order_datetime_utc,
      sku, quantity_ordered, customer_country, customer_state,
      order_revenue, currency, shipping_method, promised_ship_days

    Returns: (df, meta) where meta['validation_errors'] is a list
    """
    errors: List[str] = []

    if raw_orders is None or raw_orders.empty:
        return pd.DataFrame(), _validation(["[orders] Input orders dataframe is empty."])

    df = _lower_cols(_clean_cols(raw_orders))

    # Detect Shopify & map columns
    is_shopify = detect_shopify_orders(raw_orders) or (platform_hint.lower() == "shopify")

    if is_shopify:
        rename_map = {c: SHOPIFY_COLUMN_MAP[c] for c in df.columns if c in SHOPIFY_COLUMN_MAP}
        df = df.rename(columns=rename_map)

    # Ensure required columns exist
    required = [
        ColumnRule("order_id", True),
        ColumnRule("order_datetime_utc", True),
        ColumnRule("sku", True),
        ColumnRule("quantity_ordered", True),
        ColumnRule("customer_country", True),
    ]
    for col in [r.name for r in required]:
        if col not in df.columns:
            df[col] = pd.NA

    # Tenant columns
    df["account_id"] = account_id
    df["store_id"] = store_id
    df["platform"] = "shopify" if is_shopify else (platform_hint or "other")

    # Clean fields
    df["order_id"] = _safe_str(df["order_id"]).str.strip()
    df["sku"] = _safe_str(df["sku"]).str.strip().str.upper()

    # Datetime
    df["order_datetime_utc"] = _to_utc(df["order_datetime_utc"])

    # Quantity
    df["quantity_ordered"] = _to_int(df["quantity_ordered"], default=1)
    df.loc[df["quantity_ordered"] <= 0, "quantity_ordered"] = 1

    # Country/state
    df["customer_country"] = _safe_str(df["customer_country"]).str.strip().str.upper()
    # if someone gives full country names, we keep as-is for MVP; later can ISO-map
    df["customer_country"] = df["customer_country"].str[:2].where(df["customer_country"].str.len() >= 2, df["customer_country"])
    df["customer_state"] = _safe_str(df.get("customer_state", pd.Series([], dtype="string"))).str.strip()

    # Optional financial/shipping
    if "order_revenue" in df.columns:
        df["order_revenue"] = _to_float(df["order_revenue"])
    else:
        df["order_revenue"] = pd.NA

    if "currency" in df.columns:
        df["currency"] = _safe_str(df["currency"]).str.strip().str.upper()
    else:
        df["currency"] = default_currency

    if "shipping_method" in df.columns:
        df["shipping_method"] = _safe_str(df["shipping_method"]).str.strip()
    else:
        df["shipping_method"] = ""

    df["promised_ship_days"] = int(default_promised_ship_days)

    # Validation errors
    errors.extend(_require_cols(df, required, "orders"))

    # Drop obvious empties
    df = df[df["order_id"].str.len() > 0].copy()
    df = df[df["sku"].str.len() > 0].copy()

    out_cols = [
        "account_id",
        "store_id",
        "platform",
        "order_id",
        "order_datetime_utc",
        "sku",
        "quantity_ordered",
        "customer_country",
        "customer_state",
        "order_revenue",
        "currency",
        "shipping_method",
        "promised_ship_days",
    ]

    # keep any missing columns safe
    for c in out_cols:
        if c not in df.columns:
            df[c] = pd.NA

    return df[out_cols], _validation(errors)

