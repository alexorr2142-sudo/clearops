from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pandas as pd

from .helpers import ColumnRule, _clean_cols, _lower_cols, _require_cols, _safe_str, _to_utc, _validation

def normalize_tracking(
    raw_tracking: pd.DataFrame,
    account_id: str,
    store_id: str,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Canonical Tracking output columns:
      account_id, store_id, carrier, tracking_number,
      order_id, supplier_order_id, tracking_status_raw,
      tracking_status_normalized, last_update_utc,
      delivery_date_utc, delivery_exception
    """
    errors: List[str] = []

    if raw_tracking is None or raw_tracking.empty:
        return pd.DataFrame(), _validation([])

    df = _lower_cols(_clean_cols(raw_tracking))

    rename_candidates = {
        "carrier": "carrier",
        "tracking number": "tracking_number",
        "tracking": "tracking_number",
        "tracking_number": "tracking_number",

        "order id": "order_id",
        "supplier order id": "supplier_order_id",

        "status": "tracking_status_raw",
        "tracking status": "tracking_status_raw",
        "tracking_status_raw": "tracking_status_raw",

        "last update": "last_update_utc",
        "last updated": "last_update_utc",
        "last_update_utc": "last_update_utc",

        "delivered at": "delivery_date_utc",
        "delivered": "delivery_date_utc",
        "delivery date": "delivery_date_utc",
        "delivery_date_utc": "delivery_date_utc",

        "exception": "delivery_exception",
        "delivery exception": "delivery_exception",
    }

    rename_map = {c: rename_candidates[c] for c in df.columns if c in rename_candidates}
    df = df.rename(columns=rename_map)

    required = [
        ColumnRule("tracking_number", True),
    ]
    for col in [r.name for r in required]:
        if col not in df.columns:
            df[col] = pd.NA

    df["account_id"] = account_id
    df["store_id"] = store_id

    df["carrier"] = _safe_str(df.get("carrier", pd.Series([], dtype="string"))).str.strip()
    df["tracking_number"] = _safe_str(df["tracking_number"]).str.strip()

    df["order_id"] = _safe_str(df.get("order_id", pd.Series([], dtype="string"))).str.strip()
    df["supplier_order_id"] = _safe_str(df.get("supplier_order_id", pd.Series([], dtype="string"))).str.strip()

    df["tracking_status_raw"] = _safe_str(df.get("tracking_status_raw", pd.Series([], dtype="string"))).str.strip()
    df["tracking_status_normalized"] = _safe_str(df.get("tracking_status_normalized", pd.Series([], dtype="string"))).str.strip()

    # Date fields
    if "last_update_utc" in df.columns:
        df["last_update_utc"] = _to_utc(df["last_update_utc"])
    else:
        df["last_update_utc"] = pd.NaT

    if "delivery_date_utc" in df.columns:
        df["delivery_date_utc"] = _to_utc(df["delivery_date_utc"])
    else:
        df["delivery_date_utc"] = pd.NaT

    df["delivery_exception"] = _safe_str(df.get("delivery_exception", pd.Series([], dtype="string"))).str.strip()

    errors.extend(_require_cols(df, required, "tracking"))

    # Drop empty tracking numbers
    df = df[df["tracking_number"].str.len() > 0].copy()

    out_cols = [
        "account_id",
        "store_id",
        "carrier",
        "tracking_number",
        "order_id",
        "supplier_order_id",
        "tracking_status_raw",
        "tracking_status_normalized",
        "last_update_utc",
        "delivery_date_utc",
        "delivery_exception",
    ]
    for c in out_cols:
        if c not in df.columns:
            df[c] = pd.NA

    return df[out_cols], _validation(errors)
