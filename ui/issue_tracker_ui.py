"""Issue tracker UI facade.

Constraint: keep files small (<300 lines).

This facade adapts app_shell_render -> issue tracker panels without
changing panel implementations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import inspect

import pandas as pd
import streamlit as st

from ui.issue_tracker_ownership_ui import render_issue_ownership_panel
from ui.issue_tracker_panel_ui import render_issue_tracker_panel


def _call_with_accepted_kwargs(fn, *args, **kwargs):
    """Call helper that drops unexpected kwargs (keeps backward compat)."""
    try:
        sig = inspect.signature(fn)
        accepted = {k: v for k, v in kwargs.items() if k in sig.parameters}
        return fn(*args, **accepted)
    except TypeError as e:
        # If this still fails, re-raise; caller will handle.
        raise e


def _ensure_issue_ids(
    *,
    followups_full: pd.DataFrame,
    issue_tracker_path: Path,
    ws_root: Optional[Path],
) -> pd.DataFrame:
    """
    Ensure followups_full has issue_id by (best-effort) applying issue tracker.
    """
    if not isinstance(followups_full, pd.DataFrame) or followups_full.empty:
        return followups_full

    if "issue_id" in followups_full.columns:
        return followups_full

    # Best-effort: apply_issue_tracker should add issue_id and statuses.
    try:
        from core.issue_tracker_apply import apply_issue_tracker  # type: ignore
    except Exception:
        apply_issue_tracker = None  # type: ignore

    if not callable(apply_issue_tracker):
        return followups_full

    # Prefer ws_root from view; otherwise derive from issue_tracker_path parent.
    root = ws_root if isinstance(ws_root, Path) else issue_tracker_path.parent

    try:
        res = apply_issue_tracker(ws_root=root, followups_full=followups_full)
        if isinstance(res, dict) and isinstance(res.get("followups_full"), pd.DataFrame):
            return res["followups_full"]
    except Exception:
        # Never fatal here; just return original.
        return followups_full

    return followups_full


def render_issue_tracker_ui(
    *,
    issue_tracker_path: Path,
    view: Optional[dict[str, Any]] = None,
    key_prefix: str = "it",
) -> None:
    """
    Follow-up Tracker tab entrypoint.

    - Main tracker panel (requires followups_full)
    - Ownership panel (requires followups_df)
    """
    if issue_tracker_path is None:
        st.caption("Issue tracker file not available.")
        return

    view = view or {}

    followups_full = view.get("followups_full", pd.DataFrame())
    if not isinstance(followups_full, pd.DataFrame):
        followups_full = pd.DataFrame()

    ws_root = view.get("ws_root", None)
    if isinstance(ws_root, str) and ws_root:
        ws_root = Path(ws_root)

    # Ensure issue_id exists (best-effort)
    followups_full = _ensure_issue_ids(
        followups_full=followups_full,
        issue_tracker_path=issue_tracker_path,
        ws_root=ws_root if isinstance(ws_root, Path) else None,
    )

    # If still missing, show a helpful message but do not crash the app
    if isinstance(followups_full, pd.DataFrame) and not followups_full.empty and "issue_id" not in followups_full.columns:
        st.warning("Issue Tracker requires `issue_id` in followups_full. (Issue tracker apply step did not run.)")

    # ----- Main panel -----
    # Some versions want: render_issue_tracker_panel(followups_full, issue_tracker_path=..., key_prefix=...)
    _call_with_accepted_kwargs(
        render_issue_tracker_panel,
        followups_full,
        issue_tracker_path=issue_tracker_path,
        key_prefix=f"{key_prefix}_panel",
    )

    st.divider()

    # ----- Ownership panel -----
    # Your current panel requires positional followups_df
    try:
        _call_with_accepted_kwargs(
            render_issue_ownership_panel,
            followups_full,  # positional followups_df
            issue_tracker_path=issue_tracker_path,
            key_prefix=f"{key_prefix}_own",
        )
    except TypeError:
        # Fallback for older signature: (issue_tracker_path, ...)
        _call_with_accepted_kwargs(
            render_issue_ownership_panel,
            issue_tracker_path=issue_tracker_path,
            key_prefix=f"{key_prefix}_own",
        )


# Back-compat alias (older imports)
render_issue_tracker = render_issue_tracker_ui

__all__ = ["render_issue_tracker_ui", "render_issue_tracker"]
