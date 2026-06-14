"""
背题模式页面
沉浸式浏览所有题目，支持分页、筛选、搜索、收藏到错题本。
"""
import streamlit as st
import math
import pandas as pd
from utils.session_state import init_session_state
from utils.styles import inject_global_styles, render_difficulty_tag, render_knowledge_tag
from utils.data_loader import get_filtered_questions, get_knowledge_categories
from utils.review_manager import save_to_review_book, log_study_session
from utils.auth import check_auth
from components.question_card import safe_format

# 初始化
try:
    st.set_page_config(page_title="背题模式", page_icon="📖", layout="wide")
except Exception:
    pass
check_auth()
init_session_state()
inject_global_styles()

st.title("📖 沉浸式背题模式")

# 页面介绍
st.markdown("""
<div style="background: linear-gradient(135deg, rgba(16,185,129,0.1), rgba(6,182,212,0.1));
            border: 1px solid rgba(16,185,129,0.2); border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
    <div style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0; margin-bottom: 0.8rem;">
        📖 沉浸式背题，系统学习
    </div>
    <div style="color: #94a3b8; font-size: 0.9rem; line-height: 1.6;">
        <p>📚 <strong>系统浏览</strong>：分页浏览所有题目，全面掌握知识点</p>
        <p>🔍 <strong>智能搜索</strong>：支持关键词搜索，快速定位目标题目</p>
        <p>📌 <strong>收藏功能</strong>：一键收藏难题到错题本，方便复习</p>
        <p>📊 <strong>进度追踪</strong>：实时显示浏览进度，掌控学习节奏</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 侧边栏设置
# ==========================================
with st.sidebar:
    st.subheader("⚙️ 背题设置")
    force_load = True
    per_page = st.number_input("每页显示题数", min_value=5, max_value=50, value=10)

    st.markdown("---")
    st.subheader("🔍 关键词搜索")
    search_keyword = st.text_input("搜索题目或答案", placeholder="输入关键词...", key="背题_search")

    st.markdown("---")
    st.subheader("🎯 题目分类筛选")

    df = get_filtered_questions(force_show_all=force_load)

    # 题目分类筛选（使用数据库的category字段）
    categories = get_knowledge_categories(df)
    selected_cat = st.selectbox("📋 选择题目大类", ["全部"] + categories)

    # 难度筛选
    if not df.empty and "难度" in df.columns:
        diff_list = ["全部"] + sorted(df["难度"].dropna().unique().tolist())
        selected_diff = st.selectbox("🎯 选择难度", diff_list)
    else:
        selected_diff = "全部"

# ==========================================
# 数据筛选 + 分页重置
# ==========================================
display_df = df.copy()
if df.empty:
    st.error("当前数据文件夹为空！请检查 data/ 目录。")
    st.stop()

if search_keyword:
    kw = search_keyword.lower()
    mask = (
        display_df["问题"].str.lower().str.contains(kw, na=False) |
        display_df["参考"].astype(str).str.lower().str.contains(kw, na=False)
    )
    display_df = display_df[mask]
if selected_cat != "全部":
    display_df = display_df[display_df["知识点"] == selected_cat]
if selected_diff != "全部":
    display_df = display_df[display_df["难度"] == selected_diff]

# 分页重置：用筛选条件的 hash 来检测变化
filter_key = f"{search_keyword}|{selected_cat}|{selected_diff}|{per_page}"
if st.session_state.get("背题_filter_key") != filter_key:
    st.session_state.背题_filter_key = filter_key
    st.session_state.背题_page = 1

# ==========================================
# 指标
# ==========================================
col1, col2, col3 = st.columns(3)
col1.metric("📋 当前筛选结果", f"{len(display_df)} 道")
col2.metric("📂 总题库", f"{len(df)} 道")
if "知识点" in display_df.columns:
    col3.metric("📋 涉及知识点", f"{display_df['知识点'].nunique()} 个")
st.markdown("---")

# ==========================================
# 分页 + 跳页
# ==========================================
total_pages = max(1, math.ceil(len(display_df) / per_page))

if "背题_page" not in st.session_state:
    st.session_state.背题_page = 1

# 确保页码不越界
st.session_state.背题_page = max(1, min(st.session_state.背题_page, total_pages))

col_prev, col_jump, col_next = st.columns([1, 2, 1])
with col_prev:
    if st.button("⬅️ 上一页", use_container_width=True, disabled=(st.session_state.背题_page <= 1)):
        st.session_state.背题_page -= 1
        st.rerun()
with col_jump:
    jump_page = st.number_input(
        "跳转到第几页", min_value=1, max_value=total_pages,
        value=st.session_state.背题_page, key="jump_page_input",
        label_visibility="collapsed",
    )
    if jump_page != st.session_state.背题_page:
        st.session_state.背题_page = jump_page
        st.rerun()
with col_next:
    if st.button("下一页 ➡️", use_container_width=True, disabled=(st.session_state.背题_page >= total_pages)):
        st.session_state.背题_page += 1
        st.rerun()

st.markdown(
    f'<div class="pagination-info">第 {st.session_state.背题_page} / {total_pages} 页 · '
    f'共 {len(display_df)} 道题</div>',
    unsafe_allow_html=True,
)

# 进度条
progress = st.session_state.背题_page / total_pages
st.progress(progress)

# ==========================================
# 渲染当前页的题目
# ==========================================
start_idx = (st.session_state.背题_page - 1) * per_page
end_idx = min(start_idx + per_page, len(display_df))
page_df = display_df.iloc[start_idx:end_idx]

# 记录背题学习活动（仅在翻页时记录，防止每次交互重复记录）
_page_log_key = f"背题_logged_page_{st.session_state.背题_page}"
if len(page_df) > 0 and not st.session_state.get(_page_log_key, False):
    log_study_session(len(page_df), activity="背题")
    st.session_state[_page_log_key] = True

for idx, (_, row) in enumerate(page_df.iterrows()):
    global_idx = start_idx + idx + 1

    # 标题行
    tag_html = ""
    if "难度" in row and not (isinstance(row["难度"], float) and math.isnan(row["难度"])):
        tag_html += render_difficulty_tag(str(row["难度"])) + " "
    if "知识点" in row and not (isinstance(row["知识点"], float) and math.isnan(row["知识点"])) and row["知识点"] != "未分类":
        tag_html += render_knowledge_tag(str(row["知识点"]))

    st.markdown(
        f'<div class="question-title">Q{global_idx}: {safe_format(row["问题"])}</div>'
        f'<div style="margin-bottom: 6px;">{tag_html}</div>',
        unsafe_allow_html=True,
    )

    st.info(safe_format(row["参考"]))

    # 收藏到错题本按钮
    with st.expander(f"📌 收藏此题", expanded=False):
        note = st.text_area("备注（选填）", key=f"背题_note_{global_idx}", height=60)
        mastery = st.selectbox(
            "掌握度", options=[0, 1, 2, 3, 4, 5],
            format_func=lambda x: ["未评分", "⭐1", "⭐⭐2", "⭐⭐⭐3", "⭐⭐⭐⭐4", "⭐⭐⭐⭐⭐5"][x],
            key=f"背题_mastery_{global_idx}",
        )
        if st.button("🚩 保存至错题本", key=f"背题_save_{global_idx}", use_container_width=True):
            save_to_review_book(row["问题"], row["参考"], note, mastery)
            st.toast("✅ 已保存至错题本！")

    st.write("")

# 底部分页
st.markdown("---")
col_prev2, col_info2, col_next2 = st.columns([1, 2, 1])
with col_prev2:
    if st.button("⬅️ 上一页 ", use_container_width=True, disabled=(st.session_state.背题_page <= 1),
                 key="prev_bottom"):
        st.session_state.背题_page -= 1
        st.rerun()
with col_info2:
    st.markdown(
        f'<div class="pagination-info">第 {st.session_state.背题_page} / {total_pages} 页</div>',
        unsafe_allow_html=True,
    )
with col_next2:
    if st.button("下一页  ➡️", use_container_width=True, disabled=(st.session_state.背题_page >= total_pages),
                 key="next_bottom"):
        st.session_state.背题_page += 1
        st.rerun()
