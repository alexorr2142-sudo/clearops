"""Issue tracker UI facade.

Constraint: keep files small (<300 lines).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import streamlit as st

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

    This is intentionally a thin facade:
      - main tracker panel
      - ownership panel
    """
    if issue_tracker_path is None:
        st.caption("Issue tracker file not available.")
        return

    render_issue_tracker_panel(
        issue_tracker_path=issue_tracker_path,
        key_prefix=f"{key_prefix}_panel",
        view=view or {},
    )

    st.divider()

    render_issue_ownership_panel(
        issue_tracker_path=issue_tracker_path,
        key_prefix=f"{key_prefix}_own",
        view=view or {},
    )


# Back-compat alias (older imports)
render_issue_tracker = render_issue_tracker_ui

__all__ = ["render_issue_tracker_ui", "render_issue_tracker"]
