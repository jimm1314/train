"""
面试题刷题系统 — 专业版
入口文件：展示欢迎页 + 学习概览
"""
import streamlit as st
from utils.session_state import init_session_state
from utils.styles import inject_global_styles
from utils.data_loader import get_filtered_questions
from utils.review_manager import _read_review_file, load_study_log, get_checkin_stats
from components.metrics import render_overview_cards

# ==========================================
# 页面配置
# ==========================================
st.set_page_config(
    page_title="面试题刷题系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 初始化
init_session_state()
inject_global_styles()

# ==========================================
# 侧边栏
# ==========================================
with st.sidebar:
    st.title("📚 面试题刷题系统")
    st.markdown("**专业版** — 系统化刷题，高效备战面试")
    st.markdown("---")
    st.markdown(
        "### 导航\n"
        "👈 使用左侧页面导航栏切换功能模块\n\n"
        "- 🎲 **抽题模式** — 随机抽题练习\n"
        "- ✍️ **默写模式** — 凭记忆默写，查漏补缺\n"
        "- 📖 **背题模式** — 沉浸式背诵\n"
        "- 📝 **错题复习** — 巩固薄弱点\n"
        "- 📊 **学习统计** — 数据分析\n"
        "- ⚙️ **设置** — 系统配置"
    )
    st.markdown("---")
    st.caption("v2.0 · 专业版")

# ==========================================
# 主页面：欢迎 + 概览
# ==========================================
st.title("📚 面试题刷题系统")
st.markdown("### 欢迎回来！今日也要加油 💪")
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

# 快速入口
st.markdown("### 🚀 快速开始")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.page_link("pages/1_🎲_抽题模式.py", label="🎲 开始抽题", icon="🎲")
    st.caption("随机抽取题目练习")
with col2:
    st.page_link("pages/6_✍️_默写模式.py", label="✍️ 默写模式", icon="✍️")
    st.caption("凭记忆默写答案")
with col3:
    st.page_link("pages/2_📖_背题模式.py", label="📖 背题模式", icon="📖")
    st.caption("沉浸式浏览题目")
with col4:
    st.page_link("pages/3_📝_错题复习.py", label="📝 错题复习", icon="📝")
    st.caption("复习已收藏错题")

# 知识点分布预览
if not df.empty and "知识点" in df.columns:
    st.markdown("---")
    st.markdown("### 📋 题库知识点分布")
    cat_counts = df["知识点"].value_counts()
    st.bar_chart(cat_counts)
