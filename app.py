"""
面试题刷题系统 — 专业版
入口文件：展示欢迎页 + 学习概览
"""
import streamlit as st

st.set_page_config(
    page_title="面试题刷题系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd
import plotly.express as px
from utils.session_state import init_session_state
from utils.styles import inject_global_styles
from utils.data_loader import get_filtered_questions
from utils.review_manager import _read_review_file, load_study_log, get_checkin_stats
from utils.auth import get_current_user, is_admin, logout
from components.metrics import render_overview_cards
from utils.goal_manager import render_goal_progress, get_review_progress
from utils.review_manager import get_due_reviews

# 初始化
init_session_state()
inject_global_styles()

# 检查登录状态，未登录则跳转到登录页面
from utils.auth import is_authenticated
if not is_authenticated():
    st.switch_page("pages/0_🔐_登录注册.py")

# ==========================================
# 侧边栏
# ==========================================
with st.sidebar:
    st.markdown(
        '<div style="text-align:center; padding: 0.5rem 0 1rem 0;">'
        '<span style="font-size: 1.5rem; font-weight: 800; '
        'background: linear-gradient(135deg, #818cf8, #f472b6); '
        '-webkit-background-clip: text; -webkit-text-fill-color: transparent; '
        'background-clip: text;">📚 面试题刷题系统</span>'
        '<br><span style="color: #64748b; font-size: 0.8rem;">系统化刷题，高效备战面试</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # 用户信息卡片
    current_user = get_current_user()
    if current_user:
        st.markdown(
            f'<div style="display:flex; align-items:center; gap:10px; '
            f'padding: 0.6rem 0.8rem; background: rgba(99,102,241,0.08); '
            f'border: 1px solid rgba(99,102,241,0.15); border-radius: 10px; margin-bottom: 0.8rem;">'
            f'<span style="font-size:1.2rem;">👤</span>'
            f'<div><div style="font-weight:600; color:#e2e8f0; font-size:0.9rem;">{current_user}</div>'
            f'<div style="color:#64748b; font-size:0.72rem;">当前在线</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("🚪 退出登录", use_container_width=True):
            logout()
            st.switch_page("pages/0_🔐_登录注册.py")
        st.markdown("---")

    if is_admin():
        st.page_link("pages/7_👑_管理员.py", label="👑 管理员面板", icon="👑")
        st.page_link("pages/8_✏️_题库编辑.py", label="✏️ 题库编辑", icon="✏️")
        st.markdown("---")

    st.caption("v3.0 · 专业版")

# ==========================================
# 主页面
# ==========================================
st.markdown(
    '<div style="padding: 0.8rem 0 0.3rem 0;">'
    '<h1 style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0.2rem; '
    'background: linear-gradient(135deg, #818cf8, #f472b6); '
    '-webkit-background-clip: text; -webkit-text-fill-color: transparent; '
    'background-clip: text;">📚 面试题刷题系统</h1>'
    '<p style="color: #94a3b8; font-size: 0.95rem;">欢迎回来！今日也要加油 💪</p>'
    '</div>',
    unsafe_allow_html=True,
)
st.markdown("---")

# 加载统计数据
df = get_filtered_questions(force_show_all=True)
review_df = _read_review_file()
study_log = load_study_log()

stats = {
    "total_questions": len(df) if not df.empty else 0,
    "total_reviewed": len(review_df) if not review_df.empty else 0,
    "total_drawn": int(study_log["刷题数"].sum()) if not study_log.empty and "刷题数" in study_log.columns else 0,
    "avg_mastery": round(review_df["掌握度"].mean(), 1) if not review_df.empty and "掌握度" in review_df.columns else 0,
    "streak_days": get_checkin_stats()["streak"],
}

render_overview_cards(stats)

st.markdown("---")

render_goal_progress()

due_count = get_review_progress()
if due_count > 0:
    st.markdown("---")
    due_df = get_due_reviews()
    st.markdown(
        f'<div style="margin-bottom: 0.8rem;">'
        f'<span style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0;">⏰ 今日待复习 '
        f'<span style="background:#ef4444;color:white;padding:2px 8px;border-radius:10px;'
        f'font-size:0.8rem;">{due_count} 题</span></span></div>',
        unsafe_allow_html=True,
    )
    for _, row in due_df.head(5).iterrows():
        q = str(row.get("问题", ""))[:80]
        mastery = int(row.get("掌握度", 0)) if pd.notna(row.get("掌握度", 0)) else 0
        stars = "★" * mastery + "☆" * (5 - mastery)
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;">'
            f'<span style="color:#f59e0b;">{stars}</span>'
            f'<span style="color:#cbd5e1;font-size:0.9rem;">{q}</span></div>',
            unsafe_allow_html=True,
        )
    if due_count > 5:
        st.caption(f"... 还有 {due_count - 5} 道待复习")
    st.page_link("pages/3_📝_错题复习.py", label="📝 前往错题复习", icon="📝")

st.markdown("---")

st.markdown(
    '<div style="margin-bottom: 0.8rem;">'
    '<span style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0;">🚀 快速开始</span>'
    '</div>',
    unsafe_allow_html=True,
)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.page_link("pages/1_🎲_抽题模式.py", label="🎲 开始抽题", icon="🎲")
    st.caption("随机抽取题目练习")
with col2:
    st.page_link("pages/9_🎤_模拟面试.py", label="🎤 模拟面试", icon="🎤")
    st.caption("限时模拟面试")
with col3:
    st.page_link("pages/6_✍️_默写模式.py", label="✍️ 默写模式", icon="✍️")
    st.caption("凭记忆默写答案")
with col4:
    st.page_link("pages/2_📖_背题模式.py", label="📖 背题模式", icon="📖")
    st.caption("沉浸式浏览题目")
with col5:
    st.page_link("pages/3_📝_错题复习.py", label="📝 错题复习", icon="📝")
    st.caption("复习已收藏错题")

# 知识点分布预览（Plotly 版，适配暗色主题）
if not df.empty and "知识点" in df.columns:
    st.markdown("---")
    st.markdown(
        '<div style="margin-bottom: 0.8rem;">'
        '<span style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0;">📋 题库知识点分布</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    cat_counts = df["知识点"].value_counts().reset_index()
    cat_counts.columns = ["知识点", "题目数"]
    fig = px.bar(
        cat_counts, x="知识点", y="题目数",
        color="题目数", color_continuous_scale="Blues", text="题目数",
    )
    fig.update_layout(
        height=350,
        margin=dict(t=20, b=60),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickangle=-30),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True)
