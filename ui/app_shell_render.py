from __future__ import annotations

import inspect
from pathlib import Path

import pandas as pd
import streamlit as st

from ui.app_shell_boot import _safe_imports


def _call_with_accepted_kwargs(fn, /, **kwargs):
    """
    Call fn(**kwargs) but only pass parameters the function accepts.
    This prevents UI breakage when modules evolve independently.
    """
    if fn is None:
        raise TypeError("Attempted to call a None function.")
    sig = inspect.signature(fn)
    accepted = {k: v for k, v in kwargs.items() if k in sig.parameters}
    return fn(**accepted)


def render_app() -> None:
    """
    The main app body AFTER access gates.
    """
    deps = _safe_imports()

    # Paths
    base_dir = Path(__file__).resolve().parent.parent

    if not hasattr(deps, "init_paths") or not callable(deps.init_paths):
        st.error("Boot error: deps.init_paths is missing. (_safe_imports did not load expected functions.)")
        st.stop()

    _base_dir, data_dir, workspaces_dir, suppliers_dir = deps.init_paths(base_dir)

    # Sidebar context (tenant/defaults/demo/suppliers)
    if not hasattr(deps, "render_sidebar_context") or not callable(deps.render_sidebar_context):
        st.error("Boot error: deps.render_sidebar_context is missing.")
        st.stop()

    sb = deps.render_sidebar_context(
        data_dir=data_dir,
        workspaces_dir=workspaces_dir,
        suppliers_dir=suppliers_dir,
        key_prefix="sb",
    )

    account_id = str(sb.get("account_id", "") or "")
    store_id = str(sb.get("store_id", "") or "")
    platform_hint = str(sb.get("platform_hint", "other") or "other")
    default_currency = str(sb.get("default_currency", "USD") or "USD")
    promised_days = int(sb.get("default_promised_ship_days", 3) or 3)
    suppliers_df = sb.get("suppliers_df", pd.DataFrame())
    demo_mode = bool(sb.get("demo_mode", False))

    # Optional: onboarding checklist
    if callable(getattr(deps, "render_onboarding_checklist", None)):
        try:
            deps.render_onboarding_checklist(expanded=True)
        except Exception:
            st.warning("Onboarding checklist failed to render (non-critical).")

    # Uploads + templates (fail-safe)
    uploads = None
    if callable(getattr(deps, "render_upload_and_templates", None)):
        try:
            uploads = _call_with_accepted_kwargs(deps.render_upload_and_templates)
        except Exception as e:
            st.warning("Uploads / templates UI failed; proceeding without uploads (non-critical).")
            st.code(str(e))

    # Raw inputs (demo-safe)
    if not callable(getattr(deps, "resolve_raw_inputs", None)):
        st.error("Boot error: deps.resolve_raw_inputs is missing.")
        st.stop()

    raw_orders, raw_shipments, raw_tracking = _call_with_accepted_kwargs(
        deps.resolve_raw_inputs,
        demo_mode_active=demo_mode,
        data_dir=data_dir,
        uploads=uploads,
    )

    # Stop if required inputs are missing (unless demo)
    if callable(getattr(deps, "stop_if_missing_required_inputs", None)):
        _call_with_accepted_kwargs(
            deps.stop_if_missing_required_inputs,
            raw_orders=raw_orders,
            raw_shipments=raw_shipments,
            raw_tracking=raw_tracking,
        )

    # Run pipeline
    if not callable(getattr(deps, "run_pipeline", None)):
        st.error("Boot error: deps.run_pipeline is missing.")
        st.stop()

    pipe = deps.run_pipeline(
        raw_orders=raw_orders,
        raw_shipments=raw_shipments,
        raw_tracking=raw_tracking,
        account_id=account_id,
        store_id=store_id,
        platform_hint=platform_hint,
        default_currency=default_currency,
        default_promised_ship_days=promised_days,
        suppliers_df=suppliers_df,
        workspaces_dir=workspaces_dir,
        normalize_orders=getattr(deps, "normalize_orders", None),
        normalize_shipments=getattr(deps, "normalize_shipments", None),
        normalize_tracking=getattr(deps, "normalize_tracking", None),
        reconcile_all=getattr(deps, "reconcile_all", None),
        enhance_explanations=getattr(deps, "enhance_explanations", None),
        enrich_followups_with_suppliers=getattr(deps, "enrich_followups_with_suppliers", None),
        add_missing_supplier_contact_exceptions=getattr(deps, "add_missing_supplier_contact_exceptions", None),
        add_urgency_column=getattr(deps, "add_urgency_column", None),
        build_supplier_scorecard_from_run=getattr(deps, "build_supplier_scorecard_from_run", None),
        make_daily_ops_pack_bytes=getattr(deps, "make_daily_ops_pack_bytes", None),
        workspace_root=getattr(deps, "workspace_root", None),
        render_sla_escalations=getattr(deps, "render_sla_escalations", None),
        apply_issue_tracker=getattr(deps, "apply_issue_tracker", None),
        render_issue_tracker_maintenance=getattr(deps, "render_issue_tracker_maintenance", None),
        IssueTrackerStore=getattr(deps, "IssueTrackerStore", None),
        build_customer_impact_view=getattr(deps, "build_customer_impact_view", None),
        mailto_link=getattr(deps, "mailto_link", None),
        render_workspaces_sidebar_and_maybe_override_outputs=getattr(
            deps, "render_workspaces_sidebar_and_maybe_override_outputs", None
        ),
    )

    view = dict(pipe) if isinstance(pipe, dict) else {}

    # Backward-compat mapping
    if "supplier_scorecards" not in view and "scorecard" in view:
        view["supplier_scorecards"] = view.get("scorecard", pd.DataFrame())

    # ---------- Main tabs ----------
    tabs = st.tabs(
        [
            "Dashboard",
            "Ops Triage",
            "Exceptions Queue",
            "Supplier Scorecards",
            "Ops Outreach (Comms)",
            "SLA Escalations",
            "Follow-up Tracker",
            "KPI Trends",
        ]
    )

    with tabs[0]:
        try:
            if callable(getattr(deps, "render_dashboard", None)):
                _call_with_accepted_kwargs(
                    deps.render_dashboard,
                    kpis=view.get("kpis", {}),
                    run_history_df=view.get("run_history_df", pd.DataFrame()),
                    view=view,
                )
            else:
                st.caption("Dashboard UI not available.")
        except Exception as e:
            st.warning("Dashboard failed to render (non-critical).")
            st.code(str(e))

    with tabs[1]:
        try:
            if callable(getattr(deps, "render_ops_triage", None)):
                _call_with_accepted_kwargs(
                    deps.render_ops_triage,
                    exceptions=view.get("exceptions", pd.DataFrame()),
                    followups_open=view.get("followups_open", pd.DataFrame()),
                    view=view,
                )
            else:
                st.caption("Ops triage UI not available.")
        except Exception as e:
            st.warning("Ops triage failed to render (non-critical).")
            st.code(str(e))

    with tabs[2]:
        try:
            if callable(getattr(deps, "render_exceptions_queue_section", None)):
                _call_with_accepted_kwargs(
                    deps.render_exceptions_queue_section,
                    exceptions=view.get("exceptions", pd.DataFrame()),
                    view=view,
                )
            else:
                st.caption("Exceptions queue UI not available.")
        except Exception as e:
            st.warning("Exceptions queue failed to render (non-critical).")
            st.code(str(e))

    with tabs[3]:
        try:
            if callable(getattr(deps, "render_supplier_scorecards", None)):
                _call_with_accepted_kwargs(
                    deps.render_supplier_scorecards,
                    supplier_scorecards=view.get("supplier_scorecards", pd.DataFrame()),
                    scorecard=view.get("scorecard", pd.DataFrame()),
                    view=view,
                )
            else:
                st.caption("Supplier scorecards UI not available.")
        except Exception as e:
            st.warning("Supplier scorecards failed to render (non-critical).")
            st.code(str(e))

    with tabs[4]:
        try:
            if callable(getattr(deps, "render_ops_outreach_comms", None)):
                _call_with_accepted_kwargs(
                    deps.render_ops_outreach_comms,
                    followups_open=view.get("followups_open", pd.DataFrame()),
                    customer_impact=view.get("customer_impact", pd.DataFrame()),
                    mailto_link=view.get("mailto_link", ""),
                    view=view,
                )
            else:
                st.caption("Ops outreach UI not available.")
        except Exception as e:
            st.warning("Ops outreach failed to render (non-critical).")
            st.code(str(e))

    with tabs[5]:
        try:
            if callable(getattr(deps, "render_sla_escalations_panel", None)):
                _call_with_accepted_kwargs(
                    deps.render_sla_escalations_panel,
                    escalations_df=view.get("escalations_df", pd.DataFrame()),
                    view=view,
                )
            else:
                df = view.get("escalations_df", pd.DataFrame())
                if isinstance(df, pd.DataFrame) and not df.empty:
                    st.dataframe(df, use_container_width=True)
                else:
                    st.caption("SLA escalations UI not available.")
        except Exception as e:
            st.warning("SLA escalations failed to render (non-critical).")
            st.code(str(e))

    with tabs[6]:
        try:
            issue_tracker_path = view.get("issue_tracker_path", None)
            if callable(getattr(deps, "render_issue_tracker_ui", None)) and issue_tracker_path:
                _call_with_accepted_kwargs(
                    deps.render_issue_tracker_ui,
                    issue_tracker_path=issue_tracker_path,
                    view=view,
                )
            else:
                st.caption("Follow-up tracker UI not available.")
        except Exception as e:
            st.warning("Follow-up tracker failed to render (non-critical).")
            st.code(str(e))

    with tabs[7]:
        if callable(getattr(deps, "render_kpi_trends", None)):
            try:
                _call_with_accepted_kwargs(
                    deps.render_kpi_trends,
                    workspaces_dir=workspaces_dir,
                    account_id=account_id,
                    store_id=store_id,
                    view=view,
                )
            except Exception as e:
                st.warning("KPI trends UI failed to render (non-critical).")
                st.code(str(e))
        else:
            st.caption("KPI trends UI not available.")
