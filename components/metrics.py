"""
指标展示组件
玻璃拟态风格的统计卡片和指标行。
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
    渲染首页概览统计卡片（玻璃拟态风格）。
    参数:
        stats: {
            "total_questions": int,
            "total_reviewed": int,
            "total_drawn": int,
            "avg_mastery": float,
            "streak_days": int,
        }
    """
    col1, col2, col3, col4, col5 = st.columns(5)

    cards = [
        (col1, stats.get("total_questions", 0), "📚 题库总量"),
        (col2, stats.get("total_reviewed", 0), "📝 错题收录"),
        (col3, stats.get("total_drawn", 0), "🔥 累计刷题"),
        (col4, stats.get("avg_mastery", 0), "⭐ 平均掌握度"),
    ]

    for col, value, label in cards:
        with col:
            st.markdown(
                '<div class="stat-card">'
                f'<div class="stat-card-value">{value}</div>'
                f'<div class="stat-card-label">{label}</div>'
                "</div>",
                unsafe_allow_html=True,
            )

    with col5:
        streak = stats.get("streak_days", 0)
        badge = ' <span class="streak-badge">🔥 连续</span>' if streak > 0 else ""
        st.markdown(
            '<div class="stat-card">'
            f'<div class="stat-card-value">{streak} 天{badge}</div>'
            '<div class="stat-card-label">🔥 连续学习</div>'
            "</div>",
            unsafe_allow_html=True,
        )
