from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pandas as pd

from .helpers import ColumnRule, _clean_cols, _lower_cols, _require_cols, _safe_str, _to_int, _to_utc, _validation

def normalize_shipments(
    raw_shipments: pd.DataFrame,
    account_id: str,
    store_id: str,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Canonical Shipments output columns (one row per sku shipped):
      account_id, store_id, supplier_name, supplier_order_id,
      order_id, sku, quantity_shipped, ship_datetime_utc,
      carrier, tracking_number, ship_from_country, ship_to_country
    """
    errors: List[str] = []

    if raw_shipments is None or raw_shipments.empty:
        return pd.DataFrame(), _validation(["[shipments] Input shipments dataframe is empty."])

    df = _lower_cols(_clean_cols(raw_shipments))

    # Basic flexible renames (users will upload messy formats)
    rename_candidates = {
        "supplier": "supplier_name",
        "supplier name": "supplier_name",
        "vendor": "supplier_name",

        "supplier order id": "supplier_order_id",
        "supplier_order_id": "supplier_order_id",
        "po": "supplier_order_id",
        "purchase order": "supplier_order_id",

        "order id": "order_id",
        "order_id": "order_id",
        "shopify order id": "order_id",
        "name": "order_id",  # sometimes they paste Shopify order name

        "sku": "sku",
        "item sku": "sku",
        "lineitem sku": "sku",

        "quantity": "quantity_shipped",
        "qty": "quantity_shipped",
        "quantity shipped": "quantity_shipped",

        "ship date": "ship_datetime_utc",
        "shipped at": "ship_datetime_utc",
        "ship_datetime_utc": "ship_datetime_utc",
        "shipment date": "ship_datetime_utc",

        "carrier": "carrier",
        "tracking": "tracking_number",
        "tracking number": "tracking_number",
        "tracking_number": "tracking_number",

        "from country": "ship_from_country",
        "ship from country": "ship_from_country",
        "to country": "ship_to_country",
        "ship to country": "ship_to_country",
    }

    rename_map = {c: rename_candidates[c] for c in df.columns if c in rename_candidates}
    df = df.rename(columns=rename_map)

    # Ensure required columns exist
    required = [
        ColumnRule("supplier_name", True),
        ColumnRule("supplier_order_id", True),
        ColumnRule("sku", True),
        ColumnRule("quantity_shipped", True),
        ColumnRule("ship_datetime_utc", True),
    ]
    for col in [r.name for r in required]:
        if col not in df.columns:
            df[col] = pd.NA

    # Tenant
    df["account_id"] = account_id
    df["store_id"] = store_id

    # Clean types
    df["supplier_name"] = _safe_str(df["supplier_name"]).str.strip().replace("", "Unknown Supplier")
    df["supplier_order_id"] = _safe_str(df["supplier_order_id"]).str.strip()
    df["order_id"] = _safe_str(df.get("order_id", pd.Series([], dtype="string"))).str.strip()

    df["sku"] = _safe_str(df["sku"]).str.strip().str.upper()
    df["quantity_shipped"] = _to_int(df["quantity_shipped"], default=0)
    df["ship_datetime_utc"] = _to_utc(df["ship_datetime_utc"])

    df["carrier"] = _safe_str(df.get("carrier", pd.Series([], dtype="string"))).str.strip()
    df["tracking_number"] = _safe_str(df.get("tracking_number", pd.Series([], dtype="string"))).str.strip()

    df["ship_from_country"] = _safe_str(df.get("ship_from_country", pd.Series([], dtype="string"))).str.strip().str.upper().str[:2]
    df["ship_to_country"] = _safe_str(df.get("ship_to_country", pd.Series([], dtype="string"))).str.strip().str.upper().str[:2]

    # Validation
    errors.extend(_require_cols(df, required, "shipments"))

    # Drop empty criticals
    df = df[df["supplier_order_id"].str.len() > 0].copy()
    df = df[df["sku"].str.len() > 0].copy()

    out_cols = [
        "account_id",
        "store_id",
        "supplier_name",
        "supplier_order_id",
        "order_id",
        "sku",
        "quantity_shipped",
        "ship_datetime_utc",
        "carrier",
        "tracking_number",
        "ship_from_country",
        "ship_to_country",
    ]
    for c in out_cols:
        if c not in df.columns:
            df[c] = pd.NA

    return df[out_cols], _validation(errors)

