"""
Compatibility wrapper.

This repo has a canonical Workspaces sidebar implementation in ui/workspaces_ui.py.

To prevent duplicate logic (and signature mismatches like save_run kwargs),
this module re-exports the canonical functions/types so legacy imports keep working.
"""

from __future__ import annotations

from ui.workspaces_ui import WorkspacesResult, render_workspaces_sidebar

__all__ = ["render_workspaces_sidebar", "WorkspacesResult"]
