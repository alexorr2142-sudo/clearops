"""Issue tracker UI facade.

Constraint: keep files small (<300 lines).

This facade adapts app_shell_render -> issue tracker panels without
changing panel implementations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import inspect
import hashlib

import pandas as pd
import streamlit as st

from ui.issue_tracker_ownership_ui import render_issue_ownership_panel
from ui.issue_tracker_panel_ui import render_issue_tracker_panel


def _call_with_accepted_kwargs(fn, *args, **kwargs):
    """Call helper that drops unexpected kwargs (keeps backward compat)."""
    sig = inspect.signature(fn)
    accepted = {k: v for k, v in kwargs.items() if k in sig.parameters}
    return fn(*args, **accepted)


def _stable_hash_id(parts: list[str]) -> str:
    s = "|".join([p.strip() for p in parts if str(p).strip()])
    if not s:
        s = "unknown"
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]


def _ensure_issue_id_column(followups: pd.DataFrame) -> pd.DataFrame:
    """
    Guarantee followups has `issue_id` (string) so the tracker panels can function.

    If missing, we create a deterministic id from the best available columns.
    This is intentionally UI-side so the app never hard-fails.
    """
    if not isinstance(followups, pd.DataFrame) or followups.empty:
        if isinstance(followups, pd.DataFrame) and "issue_id" not in followups.columns:
            followups = followups.copy()
            followups["issue_id"] = pd.Series(dtype="string")
        return followups

    if "issue_id" in followups.columns:
        # ensure string-ish
        out = followups.copy()
        out["issue_id"] = out["issue_id"].astype("string")
        return out

    out = followups.copy()

    # Try to build a good key from common columns across your pipeline versions
    candidate_cols = [
        "order_id",
        "order_name",
        "line_id",
        "sku",
        "supplier_name",
        "supplier",
        "exception_type",
        "exception_reason",
        "reason",
        "category",
        "status",
    ]
    cols = [c for c in candidate_cols if c in out.columns]

    def make_id(row) -> str:
        parts = []
        for c in cols:
            v = row.get(c, "")
            parts.append("" if pd.isna(v) else str(v))
        # If we found nothing useful, fall back to the row index
        if not any(p.strip() for p in parts):
            parts = [str(row.name)]
        return _stable_hash_id(parts)

    out["issue_id"] = out.apply(make_id, axis=1).astype("string")

    # Optional: if panels rely on a "status" column, keep a sane default
    if "status" not in out.columns:
        out["status"] = "Open"

    return out


def render_issue_tracker_ui(
    *,
    issue_tracker_path: Path,
    view: Optional[dict[str, Any]] = None,
    key_prefix: str = "it",
) -> None:
    """
    Follow-up Tracker tab entrypoint.

    - Main tracker panel (requires followups_full + issue_id)
    - Ownership panel (requires followups_df + issue_id)
    """
    if issue_tracker_path is None:
        st.caption("Issue tracker file not available.")
        return

    view = view or {}

    followups_full = view.get("followups_full", pd.DataFrame())
    if not isinstance(followups_full, pd.DataFrame):
        followups_full = pd.DataFrame()

    # ✅ Always guarantee issue_id exists (do NOT rely on apply_issue_tracker)
    followups_full = _ensure_issue_id_column(followups_full)

    # If still missing (shouldn’t happen), show a helpful message but continue safely
    if isinstance(followups_full, pd.DataFrame) and not followups_full.empty and "issue_id" not in followups_full.columns:
        st.warning("Issue Tracker requires `issue_id` in followups_full.")
        st.caption("Could not generate issue_id from available columns.")
        st.dataframe(followups_full.head(10), use_container_width=True)
        return

    # ----- Main panel -----
    _call_with_accepted_kwargs(
        render_issue_tracker_panel,
        followups_full,  # positional required
        issue_tracker_path=issue_tracker_path,
        key_prefix=f"{key_prefix}_panel",
    )

    st.divider()

    # ----- Ownership panel -----
    _call_with_accepted_kwargs(
        render_issue_ownership_panel,
        followups_full,  # positional followups_df (required by your current signature)
        issue_tracker_path=issue_tracker_path,
        key_prefix=f"{key_prefix}_own",
    )


# Back-compat alias (older imports)
render_issue_tracker = render_issue_tracker_ui

__all__ = ["render_issue_tracker_ui", "render_issue_tracker"]
