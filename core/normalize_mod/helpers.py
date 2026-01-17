from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional

import pandas as pd
from dateutil import parser


# -------------------------------
# Helpers
# -------------------------------
def _clean_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    return out


def _lower_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]
    return out


def _to_utc(series: pd.Series) -> pd.Series:
    """Parse mixed datetime strings -> timezone-aware UTC timestamps."""
    def parse_one(x):
        if pd.isna(x) or str(x).strip() == "":
            return pd.NaT
        try:
            dt = parser.parse(str(x))
            if dt.tzinfo is None:
                # assume already UTC if no tz given
                return pd.Timestamp(dt).tz_localize("UTC")
            return pd.Timestamp(dt).tz_convert("UTC")
        except Exception:
            return pd.NaT

    return series.apply(parse_one)


def _to_int(series: pd.Series, default: int = 0) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(default).astype(int)


def _to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _safe_str(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("").astype("string")


def _validation(errors: List[str]) -> Dict[str, Any]:
    return {"validation_errors": errors}


@dataclass(frozen=True)
class ColumnRule:
    name: str
    required: bool = True


def _require_cols(df: pd.DataFrame, rules: List[ColumnRule], table: str) -> List[str]:
    errs: List[str] = []
    cols = set(df.columns)
    for r in rules:
        if r.required and r.name not in cols:
            errs.append(f"[{table}] Missing required column: {r.name}")
    return errs
