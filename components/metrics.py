"""
指标展示组件
提供统计卡片和指标行的渲染。
"""
import streamlit as st


def render_metric_row(metrics: list[dict]):
    """
    渲染一行指标卡片。

    参数:
        metrics: [{"label": "xxx", "value": "123", "delta": "+3"}, ...]
    """
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        col.metric(
            label=m["label"],
            value=m["value"],
            delta=m.get("delta"),
        )


def render_overview_cards(stats: dict):
    """
    渲染首页概览统计卡片。

    参数:
        stats: {
            "total_questions": int,
            "total_reviewed": int,
            "total_drawn": int,
            "avg_mastery": float,
            "streak_days": int,
        }
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            '<div class="stat-card">'
            f'<div class="stat-card-value">{stats.get("total_questions", 0)}</div>'
            '<div class="stat-card-label">📚 题库总量</div>'
            "</div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            '<div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">'
            f'<div class="stat-card-value">{stats.get("total_reviewed", 0)}</div>'
            '<div class="stat-card-label">📝 错题收录</div>'
            "</div>",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            '<div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">'
            f'<div class="stat-card-value">{stats.get("total_drawn", 0)}</div>'
            '<div class="stat-card-label">🔥 累计刷题</div>'
            "</div>",
            unsafe_allow_html=True,
        )
    with col4:
        streak = stats.get("streak_days", 0)
        badge = ' <span class="streak-badge">🔥 连续</span>' if streak > 0 else ""
        st.markdown(
            '<div class="stat-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">'
            f'<div class="stat-card-value">{streak} 天{badge}</div>'
            '<div class="stat-card-label">🔥 连续学习天数</div>'
            "</div>",
            unsafe_allow_html=True,
        )
