"""
默写模式页面
看到题目后先凭记忆默写答案，再对照参考答案。
所有默写内容自动保存，方便回顾和对比。
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils.session_state import init_session_state
from utils.styles import inject_global_styles, render_difficulty_tag, render_knowledge_tag
from utils.data_loader import get_filtered_questions, get_knowledge_categories, get_dictation_file, ensure_user_data_dir
from utils.review_manager import save_to_review_book, log_study_session
from utils.auth import check_auth
from components.question_card import safe_format

# 初始化
st.set_page_config(page_title="默写模式", page_icon="✍️", layout="wide")
check_auth()
init_session_state()
inject_global_styles()

st.title("✍️ 默写模式")
st.markdown("看到题目后**先凭记忆默写**，再对照参考答案查漏补缺。所有默写内容自动保存！")

# 默写记录文件（动态获取当前用户路径）


def save_dictation(question: str, reference: str, my_answer: str):
    """保存一条默写记录"""
    dictation_file = get_dictation_file()
    today_str = datetime.now().strftime("%Y-%m-%d")
    new_row = pd.DataFrame([{
        "日期": today_str,
        "问题": question,
        "参考答案": reference,
        "我的默写": my_answer,
    }])

    if os.path.exists(dictation_file):
        exist_df = pd.read_csv(dictation_file, encoding="utf-8-sig")
        updated = pd.concat([exist_df, new_row], ignore_index=True)
    else:
        updated = new_row

    ensure_user_data_dir()
    updated.to_csv(dictation_file, index=False, encoding="utf-8-sig")


def load_dictation_log() -> pd.DataFrame:
    """加载默写记录"""
    dictation_file = get_dictation_file()
    if os.path.exists(dictation_file):
        return pd.read_csv(dictation_file, encoding="utf-8-sig")
    return pd.DataFrame(columns=["日期", "问题", "参考答案", "我的默写"])


# ==========================================
# Session State
# ==========================================
defaults = {
    "dictation_questions": [],
    "dictation_answers": [],
    "dictation_meta": [],
    "dictation_submitted": [],
    "dictation_show_answer": [],
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)


# ==========================================
# 侧边栏
# ==========================================
with st.sidebar:
    st.subheader("⚙️ 默写设置")
    num_questions = st.number_input("每次默写题数", min_value=1, max_value=20, value=3)

    st.markdown("---")
    st.subheader("🔍 关键词搜索")
    search_kw = st.text_input("搜索题目", placeholder="输入关键词...", key="dictation_search")

    st.markdown("---")
    st.subheader("🎯 筛选条件")

    df = get_filtered_questions(force_show_all=False)

    categories = get_knowledge_categories(df)
    selected_cats = st.multiselect("按知识点筛选", categories, default=[])

    if not df.empty and "难度" in df.columns:
        difficulties = df["难度"].dropna().unique().tolist()
        selected_diff = st.multiselect("按难度筛选", difficulties, default=[])
    else:
        selected_diff = []

    # 筛选
    filtered = df.copy()
    if search_kw:
        kw = search_kw.lower()
        mask = (
            filtered["问题"].str.lower().str.contains(kw, na=False) |
            filtered["参考"].astype(str).str.lower().str.contains(kw, na=False)
        )
        filtered = filtered[mask]
    if selected_cats:
        filtered = filtered[filtered["知识点"].isin(selected_cats)]
    if selected_diff:
        filtered = filtered[filtered["难度"].isin(selected_diff)]

    st.markdown("---")
    st.metric("当前题库", f"{len(filtered)} 道")

    # 历史统计
    dict_log = load_dictation_log()
    st.metric("累计默写", f"{len(dict_log)} 次")

# ==========================================
# 开始新一轮
# ==========================================
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    if st.button("🚀 开始新一轮默写", use_container_width=True, type="primary"):
        if filtered.empty:
            st.error("当前筛选条件下题库为空！")
        else:
            sample_size = min(num_questions, len(filtered))
            sampled = filtered.sample(n=sample_size)
            st.session_state.dictation_questions = sampled["问题"].tolist()
            st.session_state.dictation_answers = sampled["参考"].tolist()
            st.session_state.dictation_meta = sampled.to_dict("records")
            # 记录默写学习活动
            log_study_session(sample_size, activity="默写")
            st.session_state.dictation_submitted = [False] * sample_size
            st.session_state.dictation_show_answer = [False] * sample_size
            st.rerun()
with col2:
    if st.button("📋 查看历史默写", use_container_width=True):
        st.session_state._show_dictation_history = not st.session_state.get("_show_dictation_history", False)
with col3:
    if st.button("🗑️ 清空当前", use_container_width=True):
        st.session_state.dictation_questions = []
        st.rerun()

st.markdown("---")

# ==========================================
# 展示历史默写
# ==========================================
if st.session_state.get("_show_dictation_history", False):
    st.markdown("### 📋 我的默写历史")
    dict_log = load_dictation_log()
    if dict_log.empty:
        st.info("暂无默写记录。")
    else:
        # 按日期倒序
        dict_log = dict_log.sort_values("日期", ascending=False)

        # 日期筛选
        dates = ["全部"] + sorted(dict_log["日期"].dropna().unique().tolist(), reverse=True)
        sel_date = st.selectbox("按日期筛选", dates, key="dict_hist_date")
        if sel_date != "全部":
            dict_log = dict_log[dict_log["日期"] == sel_date]

        for idx, row in dict_log.iterrows():
            st.markdown(f'<div class="question-title">📌 {safe_format(row["问题"])}</div>',
                        unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**📝 我的默写：**")
                st.text_area("", value=str(row.get("我的默写", "")), height=100,
                             disabled=True, key=f"hist_my_{idx}")
            with col_b:
                st.markdown("**✅ 参考答案：**")
                st.text_area("", value=str(row.get("参考答案", "")), height=100,
                             disabled=True, key=f"hist_ref_{idx}")

            st.markdown(f'<span style="color: #94a3b8; font-size: 0.85rem;">📅 {row["日期"]}</span>',
                        unsafe_allow_html=True)
            st.markdown("---")

        # 导出功能
        csv_data = dict_log.to_csv(index=False, encoding="utf-8-sig")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            "📥 导出默写记录",
            data=csv_data,
            file_name=f"dictation_log_{timestamp}.csv",
            mime="text/csv",
        )

    st.markdown("---")

# ==========================================
# 默写题目
# ==========================================
if not st.session_state.dictation_questions:
    st.info("👈 点击「开始新一轮默写」开始练习！")
    st.stop()

st.markdown(f"### ✍️ 本轮默写（共 {len(st.session_state.dictation_questions)} 题）")

for i in range(len(st.session_state.dictation_questions)):
    q = st.session_state.dictation_questions[i]
    ans = st.session_state.dictation_answers[i]
    meta = st.session_state.dictation_meta[i] if i < len(st.session_state.dictation_meta) else {}

    # 标题 + 标签
    tag_html = ""
    if "难度" in meta and pd.notna(meta.get("难度")):
        tag_html += render_difficulty_tag(str(meta["难度"])) + " "
    if "知识点" in meta and pd.notna(meta.get("知识点")) and meta.get("知识点") != "未分类":
        tag_html += render_knowledge_tag(str(meta["知识点"]))

    st.markdown(
        f'<div class="question-title">【第 {i + 1} 题】 {safe_format(q)}</div>'
        f'<div style="margin-bottom: 8px;">{tag_html}</div>',
        unsafe_allow_html=True,
    )

    # 默写输入框
    my_answer = st.text_area(
        "📝 在这里默写你的答案...",
        key=f"dictation_input_{i}",
        height=150,
        placeholder="闭上眼睛回忆一下，然后在这里写下来...",
    )

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("💡 查看参考答案", key=f"show_{i}", use_container_width=True):
            st.session_state.dictation_show_answer[i] = True

    with col2:
        if st.button("💾 保存默写", key=f"save_{i}", use_container_width=True):
            if my_answer.strip():
                save_dictation(q, ans, my_answer)
                st.session_state.dictation_submitted[i] = True
                st.toast(f"✅ 第 {i + 1} 题默写已保存！")
            else:
                st.warning("请先写下你的答案再保存哦~")

    with col3:
        if st.button("🚩 收藏此题", key=f"collect_{i}", use_container_width=True):
            save_to_review_book(q, ans, my_answer, mastery=0)
            st.toast("✅ 已收藏至错题本！")

    # 展示参考答案（折叠）
    if st.session_state.dictation_show_answer[i]:
        st.markdown('<div class="note-box">✅ <b>参考答案：</b></div>', unsafe_allow_html=True)
        st.info(safe_format(ans))

        # 展示我的默写（如果有）
        if st.session_state.dictation_submitted[i]:
            st.markdown('<div class="note-box">📝 <b>我的默写：</b></div>', unsafe_allow_html=True)
            st.text_area("", value=my_answer, height=100, disabled=True, key=f"my_saved_{i}")

    st.markdown("---")

# ==========================================
# 批量操作
# ==========================================
st.markdown("### 📦 批量操作")
col1, col2 = st.columns(2)
with col1:
    if st.button("💡 全部显示答案", use_container_width=True):
        st.session_state.dictation_show_answer = [True] * len(st.session_state.dictation_questions)
        st.rerun()
with col2:
    if st.button("💾 全部保存默写", use_container_width=True):
        saved_count = 0
        for i in range(len(st.session_state.dictation_questions)):
            key = f"dictation_input_{i}"
            val = st.session_state.get(key, "")
            if val and val.strip():
                save_dictation(
                    st.session_state.dictation_questions[i],
                    st.session_state.dictation_answers[i],
                    val,
                )
                saved_count += 1
        if saved_count > 0:
            st.toast(f"✅ 已保存 {saved_count} 条默写记录！")
        else:
            st.warning("没有找到已填写的默写内容。")
