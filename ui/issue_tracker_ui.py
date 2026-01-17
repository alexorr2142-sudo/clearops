"""Issue tracker UI facade.

Constraint: keep files small (<300 lines).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import streamlit as st

from core.issue_tracker_apply import apply_issue_tracker
from ui.issue_tracker_maintenance_ui import render_issue_tracker_maintenance
from ui.issue_tracker_ownership_ui import render_issue_ownership_panel
from ui.issue_tracker_panel_ui import render_issue_tracker_panel


def render_issue_tracker_ui(
    *,
    issue_tracker_path: Path,
    view: Optional[dict[str, Any]] = None,
    key_prefix: str = "it",
) -> None:
    """
    Follow-up Tracker tab entrypoint.

    - Shows the main tracker panel (open/waiting/resolved, notes, follow-up+1, etc.)
    - Shows ownership panel (assign owner / accountability)
    - Keeps maintenance in its own UI elsewhere (sidebar), but safe to call if needed
    """
    if issue_tracker_path is None:
        st.caption("Issue tracker file not available.")
        return

    # Main panel (this is the core UI)
    render_issue_tracker_panel(
        issue_tracker_path=issue_tracker_path,
        key_prefix=f"{key_prefix}_panel",
        view=view or {},
    )

    st.divider()

    # Ownership / accountability
    render_issue_ownership_panel(
        issue_tracker_path=issue_tracker_path,
        key_prefix=f"{key_prefix}_own",
        view=view or {},
    )


# Back-compat alias (if any older code imports this name)
render_issue_tracker = render_issue_tracker_ui

__all__ = [
    "apply_issue_tracker",
    "render_issue_tracker_maintenance",
    "render_issue_tracker_panel",
    "render_issue_ownership_panel",
    "render_issue_tracker_ui",
    "render_issue_tracker",
]
