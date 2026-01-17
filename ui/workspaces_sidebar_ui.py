"""Compatibility wrapper for legacy imports.

Do not duplicate workspace sidebar logic here.
Canonical implementation lives in ui/workspaces_ui.py.
"""

from __future__ import annotations

from ui.workspaces_ui import WorkspacesResult, render_workspaces_sidebar

__all__ = ["render_workspaces_sidebar", "WorkspacesResult"]
