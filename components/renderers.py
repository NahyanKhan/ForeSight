"""
ForeSight — Component Renderers
Reusable Streamlit UI components for the dashboard.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd


def render_metric_card(label, value, sub="", variant="primary"):
    """Render a styled metric card."""
    st.markdown(f"""
    <div class="metric-card {variant}">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        <div class="sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def render_runway_gauge(median, ci_low, ci_high, distribution=None):
    """Render the animated survival runway display with gauge chart."""
    critical = median < 30
    days_class = "critical" if critical else ""

    st.markdown(f"""
    <div class="runway-display">
        <div class="runway-label">☰ Survival Runway</div>
        <div class="days {days_class}">{median}</div>
        <div style="font-size:1.2rem; color: #E2E8F0; font-weight:600; margin-top:0.2rem;">Days</div>
        <div class="ci">80% CI: {ci_low} – {ci_high} Days</div>
    </div>
    """, unsafe_allow_html=True)

    if distribution is not None:
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=distribution, nbinsx=50,
            marker_color="rgba(0, 212, 170, 0.4)",
            marker_line=dict(color="#00D4AA", width=1),
            name="Monte Carlo Simulations"
        ))
        fig.add_vline(x=median, line_dash="solid", line_color="#00D4AA", line_width=2,
                      annotation_text=f"Median: {median}d", annotation_font_color="#00D4AA")
        fig.add_vline(x=ci_low, line_dash="dash", line_color="#F59E0B", line_width=1,
                      annotation_text=f"P10: {ci_low}d", annotation_font_color="#F59E0B")
        fig.add_vline(x=ci_high, line_dash="dash", line_color="#F59E0B", line_width=1,
                      annotation_text=f"P90: {ci_high}d", annotation_font_color="#F59E0B")
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=220, margin=dict(l=20, r=20, t=30, b=20),
            title=dict(text="Runway Distribution (5,000 Monte Carlo Simulations)",
                       font=dict(size=12, color="#94A3B8")),
            xaxis_title="Days", yaxis_title="Frequency",
            xaxis=dict(gridcolor="#1E293B"), yaxis=dict(gridcolor="#1E293B"),
            showlegend=False,
        )
        st.plotly_chart(fig, width="stretch")


def render_buyer_card(buyer, on_click_key=None):
    """Render a single buyer reliability card."""
    score = buyer.get("reliability_score")
    if score is None:
        score_display = "N/A"
        score_class = "score-mid"
        score = 0
    elif score >= 75:
        score_display = str(score)
        score_class = "score-high"
    elif score >= 50:
        score_display = str(score)
        score_class = "score-mid"
    else:
        score_display = str(score)
        score_class = "score-low"

    trend_map = {"up": "↑ Improving", "down": "↓ Declining", "stable": "→ Stable", "unknown": "? New Buyer"}
    trend_text = trend_map.get(buyer.get("trend", "stable"), "→ Stable")
    trend_color = {"up": "#10B981", "down": "#EF4444", "stable": "#F59E0B", "unknown": "#94A3B8"}
    t_color = trend_color.get(buyer.get("trend", "stable"), "#94A3B8")

    outstanding = buyer.get("total_outstanding", 0)
    retaliation = "🚨 RETALIATION DETECTED" if buyer.get("retaliation_flag") else ""

    st.markdown(f"""
    <div class="buyer-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div class="buyer-name">{buyer['name']}</div>
                <div style="font-size:0.75rem; color:#64748B; margin-top:2px;">
                    {buyer.get('sector', '').replace('_', ' ').title()} · GSTIN: {buyer.get('gstin', 'N/A')[:8]}...
                </div>
                <div style="font-size:0.8rem; color:{t_color}; margin-top:4px;" class="buyer-trend">{trend_text}</div>
                <div style="font-size:0.75rem; color:#EF4444; margin-top:2px; font-weight:700;">{retaliation}</div>
            </div>
            <div style="text-align:right;">
                <div class="buyer-score {score_class}">{score_display}</div>
                <div style="font-size:0.7rem; color:#64748B;">Reliability</div>
                <div style="font-size:0.8rem; color:#94A3B8; margin-top:4px; font-family:'JetBrains Mono',monospace;">
                    ₹{outstanding:,.0f}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_concentration_chart(concentration_data):
    """Render concentration risk as a donut chart."""
    if not concentration_data:
        return

    labels = [c["buyer"] for c in concentration_data]
    values = [c["amount"] for c in concentration_data]
    colors = ["#EF4444", "#F59E0B", "#6366F1", "#10B981", "#3B82F6", "#8B5CF6", "#EC4899", "#14B8A6"]

    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=0.6,
        marker=dict(colors=colors[:len(labels)], line=dict(color="#0A0E17", width=2)),
        textinfo="percent", textfont=dict(size=11, color="#E2E8F0"),
        hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>"
    )])
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=300, margin=dict(l=10, r=10, t=30, b=10),
        title=dict(text="Revenue Concentration Risk", font=dict(size=13, color="#94A3B8")),
        legend=dict(font=dict(size=10, color="#94A3B8"), orientation="v"),
        annotations=[dict(text="Concentration", x=0.5, y=0.5, font_size=12,
                          font_color="#94A3B8", showarrow=False)],
    )
    st.plotly_chart(fig, width="stretch")


def render_shap_waterfall(buyer_name, feature_importances):
    """Render a SHAP-style waterfall chart for buyer score explanation."""
    features = list(feature_importances.keys())
    values = list(feature_importances.values())
    colors = ["#10B981" if v > 0 else "#EF4444" for v in values]

    fig = go.Figure(go.Waterfall(
        name="SHAP", orientation="h",
        y=features, x=values,
        connector=dict(line=dict(color="#1E293B", width=1)),
        increasing=dict(marker=dict(color="#10B981")),
        decreasing=dict(marker=dict(color="#EF4444")),
        totals=dict(marker=dict(color="#6366F1")),
        textposition="outside",
        text=[f"{v:+.1f}" for v in values],
        textfont=dict(size=10, color="#E2E8F0"),
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=280, margin=dict(l=10, r=40, t=35, b=10),
        title=dict(text=f"Score Breakdown — {buyer_name}", font=dict(size=13, color="#94A3B8")),
        xaxis=dict(gridcolor="#1E293B", title="Impact on Score"),
        yaxis=dict(gridcolor="#1E293B"),
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch")


def render_retaliation_chart(orders_df):
    """Render order volume chart showing retaliation pattern."""
    fig = go.Figure()

    pre = orders_df[orders_df["period"] == "pre_notice"]
    post = orders_df[orders_df["period"] == "post_notice"]

    fig.add_trace(go.Scatter(
        x=pre["date"], y=pre["order_volume"],
        mode="lines", name="Pre-Notice",
        line=dict(color="#10B981", width=2),
        fill="tozeroy", fillcolor="rgba(16,185,129,0.1)"
    ))
    fig.add_trace(go.Scatter(
        x=post["date"], y=post["order_volume"],
        mode="lines", name="Post-Notice",
        line=dict(color="#EF4444", width=2),
        fill="tozeroy", fillcolor="rgba(239,68,68,0.1)"
    ))
    fig.add_shape(
        type="line", x0="2025-09-15", x1="2025-09-15", y0=0, y1=1,
        yref="paper", line=dict(color="#F59E0B", width=2, dash="dash")
    )
    fig.add_annotation(
        x="2025-09-15", y=1, yref="paper",
        text="Legal Notice Sent", font=dict(color="#F59E0B", size=11),
        showarrow=False, yanchor="bottom"
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=300, margin=dict(l=20, r=20, t=40, b=30),
        title=dict(text="Order Volume — Retaliation Detection", font=dict(size=13, color="#94A3B8")),
        xaxis=dict(gridcolor="#1E293B", title="Date"),
        yaxis=dict(gridcolor="#1E293B", title="Daily Order Volume"),
        legend=dict(font=dict(size=10, color="#94A3B8")),
    )
    st.plotly_chart(fig, width="stretch")


def render_fhe_panel(arch_data):
    """Render the FHE Architecture Panel."""
    st.markdown('<div class="section-header">🔐 FHE Architecture Panel</div>', unsafe_allow_html=True)

    for step in arch_data["pipeline_steps"]:
        st.markdown(f"""
        <div class="fhe-step">
            <span style="font-size:1.1rem;">{step['status']}</span>
            <span style="color:#E2E8F0; font-weight:600;">{step['step']}</span>
            <span style="color:#64748B; margin-left:auto; font-size:0.75rem;">{step['detail']}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Security Properties**")
        for prop, val in arch_data["security_properties"].items():
            st.markdown(f"<div style='font-size:0.8rem; padding:2px 0; color:#94A3B8;'>"
                        f"<span style='color:#E2E8F0;'>{prop}:</span> {val}</div>",
                        unsafe_allow_html=True)

    with col2:
        st.markdown("**Performance**")
        for prop, val in arch_data["performance"].items():
            st.markdown(f"<div style='font-size:0.8rem; padding:2px 0; color:#94A3B8;'>"
                        f"<span style='color:#E2E8F0;'>{prop}:</span> {val}</div>",
                        unsafe_allow_html=True)


def render_cash_ledger(transactions):
    """Render the cash transaction ledger with pending approvals."""
    pending = [t for t in transactions if t["status"] == "pending"]
    approved = [t for t in transactions if t["status"] == "approved"]

    if pending:
        st.markdown(f"""
        <div class="alert-warning" style="border-radius:12px; padding:0.8rem 1rem; margin-bottom:1rem;">
            ⏳ <strong>{len(pending)} transactions</strong> awaiting Maker-Checker approval
            (excluded from runway calculation)
        </div>
        """, unsafe_allow_html=True)

        for tx in pending[:5]:
            st.markdown(f"""
            <div class="tx-pending">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-weight:600; color:#FDBA74;">₹{tx['amount']:,}</span>
                        <span style="color:#94A3B8; margin-left:8px;">{tx['vendor']} · {tx['category']}</span>
                    </div>
                    <div style="font-size:0.75rem; color:#64748B;">{tx['logged_by']} · {tx['date']}</div>
                </div>
                <div style="font-size:0.75rem; color:#64748B; margin-top:3px; font-style:italic;">
                    💬 "{tx['raw_message']}"
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f'<div class="section-header">✅ Approved Transactions ({len(approved)})</div>',
                unsafe_allow_html=True)

    df = pd.DataFrame(approved[:20])
    if not df.empty:
        display_df = df[["date", "vendor", "category", "amount", "logged_by"]].copy()
        display_df["amount"] = display_df["amount"].apply(lambda x: f"₹{x:,}")
        display_df.columns = ["Date", "Vendor", "Category", "Amount", "Logged By"]
        st.dataframe(display_df, width="stretch", hide_index=True)


def render_what_if_result(original, modified, buyer_name, delay_days):
    """Render the what-if simulation comparison."""
    delta = modified["median"] - original["median"]
    delta_color = "#10B981" if delta >= 0 else "#EF4444"
    delta_sign = "+" if delta >= 0 else ""

    col1, col2, col3 = st.columns(3)
    with col1:
        render_metric_card("Original Runway", f"{original['median']}d",
                           f"CI: {original['ci_low']}–{original['ci_high']}d", "success")
    with col2:
        render_metric_card("Simulated Runway", f"{modified['median']}d",
                           f"CI: {modified['ci_low']}–{modified['ci_high']}d",
                           "danger" if modified["median"] < 30 else "warning")
    with col3:
        render_metric_card("Impact", f"{delta_sign}{delta}d",
                           f"If {buyer_name} delays +{delay_days}d", "danger" if delta < 0 else "success")
