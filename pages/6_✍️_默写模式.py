"""
默写模式页面
看到题目后先凭记忆默写答案，再对照参考答案。
所有默写内容自动保存，方便回顾和对比。
"""
import streamlit as st

try:
    st.set_page_config(page_title="默写模式", page_icon="✍️", layout="wide")
except Exception:
    pass

import pandas as pd
from datetime import datetime
from utils.session_state import init_session_state
from utils.styles import inject_global_styles, render_difficulty_tag, render_knowledge_tag
from utils.data_loader import get_filtered_questions, get_knowledge_categories
from utils import db
from utils.review_manager import save_to_review_book, log_study_session
from utils.auth import check_auth
from utils.ai_scorer import score_answer, render_score_result
from components.question_card import safe_format

check_auth()
init_session_state()
inject_global_styles()

st.title("✍️ 默写模式")

# 页面介绍
st.markdown("""
<div style="background: linear-gradient(135deg, rgba(168,85,247,0.1), rgba(236,72,153,0.1));
            border: 1px solid rgba(168,85,247,0.2); border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
    <div style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0; margin-bottom: 0.8rem;">
        ✍️ 默写练习，强化记忆
    </div>
    <div style="color: #94a3b8; font-size: 0.9rem; line-height: 1.6;">
        <p>🧠 <strong>主动回忆</strong>：先凭记忆默写，再对照答案，加深理解</p>
        <p>💾 <strong>即时保存</strong>：每答一题可单独保存，刷新页面也不会丢失</p>
        <p>📊 <strong>历史记录</strong>：查看历史默写记录，追踪学习进步</p>
        <p>📥 <strong>导出功能</strong>：支持导出默写记录，便于整理复习</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("看到题目后**先凭记忆默写**，再点击「💾 保存」按钮保存，刷新页面也不会丢失！")


# ==========================================
# 数据库操作函数
# ==========================================

def save_dictation(question: str, reference: str, my_answer: str):
    """保存单条默写记录到数据库"""
    username = st.session_state.get("username", "")
    if not username:
        return False
    today_str = datetime.now().strftime("%Y-%m-%d")
    try:
        db.init_tables()
        db.execute(
            "INSERT INTO dictation_log (username, date_str, question, reference_answer, my_answer) VALUES (%s, %s, %s, %s, %s)",
            (username, today_str, question, reference, my_answer),
        )
        return True
    except Exception as e:
        st.warning(f"保存默写记录失败: {e}")
        return False


def save_dictation_draft(question: str, reference: str, my_answer: str, draft_key: str):
    """保存/更新默写草稿（同一个draft_key会覆盖）"""
    username = st.session_state.get("username", "")
    if not username:
        return False
    today_str = datetime.now().strftime("%Y-%m-%d")
    try:
        db.init_tables()
        # 先检查是否已存在该草稿
        existing = db.execute(
            "SELECT id FROM dictation_drafts WHERE username = %s AND draft_key = %s",
            (username, draft_key), fetch=True,
        )
        if existing:
            # 更新已有草稿
            db.execute(
                "UPDATE dictation_drafts SET my_answer = %s, updated_at = %s WHERE username = %s AND draft_key = %s",
                (my_answer, today_str, username, draft_key),
            )
        else:
            # 插入新草稿
            db.execute(
                "INSERT INTO dictation_drafts (username, date_str, question, reference_answer, my_answer, draft_key) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (username, today_str, question, reference, my_answer, draft_key),
            )
        return True
    except Exception as e:
        print(f"[Dictation] save_dictation_draft 失败: {e}")
        return False


def load_dictation_drafts() -> dict:
    """加载当前用户的所有草稿，返回 {draft_key: {question, reference, answer}}"""
    username = st.session_state.get("username", "")
    if not username:
        return {}
    try:
        db.init_tables()
        rows = db.execute(
            "SELECT draft_key, question, reference_answer, my_answer FROM dictation_drafts WHERE username = %s",
            (username,), fetch=True,
        )
        return {r["draft_key"]: {"question": r["question"], "reference": r["reference_answer"], "answer": r["my_answer"]} for r in rows} if rows else {}
    except Exception:
        return {}


def delete_dictation_drafts(draft_keys: list):
    """删除指定的草稿"""
    username = st.session_state.get("username", "")
    if not username or not draft_keys:
        return
    try:
        operations = []
        for key in draft_keys:
            operations.append((
                "DELETE FROM dictation_drafts WHERE username = %s AND draft_key = %s",
                (username, key),
            ))
        db.execute_transaction(operations)
    except Exception as e:
        print(f"[Dictation] delete_dictation_drafts 失败: {e}")


def load_dictation_log() -> pd.DataFrame:
    """加载默写历史记录"""
    username = st.session_state.get("username", "")
    if not username:
        return pd.DataFrame(columns=["日期", "问题", "参考答案", "我的默写"])
    try:
        db.init_tables()
        sql = "SELECT date_str AS 日期, question AS 问题, reference_answer AS 参考答案, my_answer AS 我的默写 FROM dictation_log WHERE username = %s"
        df = db.query_df(sql, (username,))
        if df.empty:
            return pd.DataFrame(columns=["日期", "问题", "参考答案", "我的默写"])
        return df
    except Exception:
        return pd.DataFrame(columns=["日期", "问题", "参考答案", "我的默写"])


def ensure_drafts_table():
    """确保草稿表存在"""
    try:
        db.init_tables()
        # 检查 dictation_drafts 表是否存在
        if db.is_mysql():
            db.execute("""
                CREATE TABLE IF NOT EXISTS dictation_drafts (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(100) NOT NULL,
                    date_str VARCHAR(20) NOT NULL,
                    question TEXT NOT NULL,
                    reference_answer TEXT,
                    my_answer TEXT,
                    draft_key VARCHAR(200) NOT NULL,
                    updated_at VARCHAR(20),
                    UNIQUE KEY uk_user_key (username, draft_key)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        else:
            db.execute("""
                CREATE TABLE IF NOT EXISTS dictation_drafts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    date_str TEXT NOT NULL,
                    question TEXT NOT NULL,
                    reference_answer TEXT,
                    my_answer TEXT,
                    draft_key TEXT NOT NULL,
                    updated_at TEXT,
                    UNIQUE(username, draft_key)
                )
            """)
    except Exception as e:
        print(f"[Dictation] ensure_drafts_table: {e}")


# 初始化草稿表
ensure_drafts_table()


# ==========================================
# Session State
# ==========================================
defaults = {
    "dictation_questions": [],
    "dictation_answers": [],
    "dictation_meta": [],
    "dictation_submitted": [],
    "dictation_show_answer": [],
    "dictation_scores": [],
    "dictation_feedbacks": [],
    "dictation_methods": [],
    "dictation_saved_flags": [],  # 记录每题是否已保存
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

    # 草稿统计
    drafts = load_dictation_drafts()
    if drafts:
        st.metric("未提交草稿", f"{len(drafts)} 条")
        if st.button("📥 恢复上次草稿", use_container_width=True):
            st.session_state.dictation_questions = [drafts[k]["question"] for k in drafts]
            st.session_state.dictation_answers = [drafts[k]["reference"] for k in drafts]
            st.session_state.dictation_meta = [{} for _ in drafts]
            st.session_state.dictation_submitted = [False] * len(drafts)
            st.session_state.dictation_show_answer = [False] * len(drafts)
            st.session_state.dictation_scores = []
            st.session_state.dictation_feedbacks = []
            st.session_state.dictation_methods = []
            st.session_state.dictation_saved_flags = [False] * len(drafts)
            # 恢复草稿中的答案到输入框
            for i, k in enumerate(drafts):
                st.session_state[f"dictation_input_{i}"] = drafts[k]["answer"]
            st.rerun()


# ==========================================
# 开始新一轮
# ==========================================
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    if st.button("🚀 开始新一轮默写", use_container_width=True, type="primary"):
        if filtered.empty:
            st.error("当前筛选条件下题库为空！")
        else:
            # 先保存当前未保存的答案为草稿
            if st.session_state.dictation_questions:
                for i in range(len(st.session_state.dictation_questions)):
                    key = f"dictation_input_{i}"
                    val = st.session_state.get(key, "")
                    if val and val.strip():
                        q = st.session_state.dictation_questions[i]
                        ans = st.session_state.dictation_answers[i]
                        today = datetime.now().strftime("%Y-%m-%d")
                        draft_key = f"{today}_{q[:50]}"
                        save_dictation_draft(q, ans, val, draft_key)

            sample_size = min(num_questions, len(filtered))
            sampled = filtered.sample(n=sample_size)
            st.session_state.dictation_questions = sampled["问题"].tolist()
            st.session_state.dictation_answers = sampled["参考"].tolist()
            st.session_state.dictation_meta = sampled.to_dict("records")
            # 记录默写学习活动
            log_study_session(sample_size, activity="默写")
            st.session_state.dictation_submitted = [False] * sample_size
            st.session_state.dictation_show_answer = [False] * sample_size
            st.session_state.dictation_scores = []
            st.session_state.dictation_feedbacks = []
            st.session_state.dictation_methods = []
            st.session_state.dictation_saved_flags = [False] * sample_size
            # 清空输入框
            for i in range(sample_size):
                if f"dictation_input_{i}" in st.session_state:
                    del st.session_state[f"dictation_input_{i}"]
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

    # 已保存标记
    saved_indicator = ""
    if i < len(st.session_state.dictation_saved_flags) and st.session_state.dictation_saved_flags[i]:
        saved_indicator = ' <span style="color: #10b981; font-size: 0.85rem;">✅ 已保存</span>'

    st.markdown(
        f'<div class="question-title">【第 {i + 1} 题】 {safe_format(q)}{saved_indicator}</div>'
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

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        if st.button("💡 查看参考答案", key=f"show_{i}", use_container_width=True):
            st.session_state.dictation_show_answer[i] = True

    with col2:
        if st.button("💾 保存此题", key=f"save_{i}", use_container_width=True):
            if my_answer.strip():
                save_dictation(q, ans, my_answer)
                # 同时删除草稿（已正式保存）
                today = datetime.now().strftime("%Y-%m-%d")
                draft_key = f"{today}_{q[:50]}"
                delete_dictation_drafts([draft_key])
                # 标记已保存
                while len(st.session_state.dictation_saved_flags) <= i:
                    st.session_state.dictation_saved_flags.append(False)
                st.session_state.dictation_saved_flags[i] = True
                st.session_state.dictation_submitted[i] = True
                st.toast(f"✅ 第 {i + 1} 题已保存到默写记录！刷新页面也不会丢失~")
                st.rerun()
            else:
                st.warning("请先写下你的答案再保存哦~")

    with col3:
        # 自动保存草稿按钮
        if st.button("📝 存为草稿", key=f"draft_{i}", use_container_width=True):
            if my_answer.strip():
                today = datetime.now().strftime("%Y-%m-%d")
                draft_key = f"{today}_{q[:50]}"
                save_dictation_draft(q, ans, my_answer, draft_key)
                st.toast(f"📝 第 {i + 1} 题已存为草稿，可从侧边栏恢复")
            else:
                st.warning("请先写下你的答案~")

    with col4:
        if st.button("🚩 收藏此题", key=f"collect_{i}", use_container_width=True):
            save_to_review_book(q, ans, my_answer, mastery=0)
            st.toast("✅ 已收藏至错题本！")

    if st.session_state.dictation_show_answer[i]:
        st.markdown('<div class="note-box">✅ <b>参考答案：</b></div>', unsafe_allow_html=True)
        st.info(safe_format(ans))

        if st.session_state.dictation_submitted[i]:
            st.markdown('<div class="note-box">📝 <b>我的默写：</b></div>', unsafe_allow_html=True)
            st.text_area("", value=my_answer, height=100, disabled=True, key=f"my_saved_{i}")

        if st.button("🤖 AI 评分", key=f"ai_score_{i}", use_container_width=True):
            if my_answer.strip():
                with st.spinner("正在评分..."):
                    s, f, m = score_answer(q, ans, my_answer)
                while len(st.session_state.dictation_scores) <= i:
                    st.session_state.dictation_scores.append(None)
                    st.session_state.dictation_feedbacks.append("")
                    st.session_state.dictation_methods.append("local")
                st.session_state.dictation_scores[i] = s
                st.session_state.dictation_feedbacks[i] = f
                st.session_state.dictation_methods[i] = m
                if m == "local":
                    st.warning("AI 接口调用失败，已使用本地算法评分。")
                st.rerun()
            else:
                st.warning("请先写下你的答案再评分~")

        if i < len(st.session_state.dictation_scores) and st.session_state.dictation_scores[i] is not None:
            render_score_result(
                st.session_state.dictation_scores[i],
                st.session_state.dictation_feedbacks[i],
                st.session_state.dictation_methods[i],
            )

    st.markdown("---")

# ==========================================
# 批量操作
# ==========================================
st.markdown("### 📦 批量操作")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("💡 全部显示答案", use_container_width=True):
        st.session_state.dictation_show_answer = [True] * len(st.session_state.dictation_questions)
        st.rerun()
with col2:
    if st.button("💾 全部保存到记录", use_container_width=True, type="primary"):
        saved_count = 0
        draft_keys_to_delete = []
        for i in range(len(st.session_state.dictation_questions)):
            key = f"dictation_input_{i}"
            val = st.session_state.get(key, "")
            if val and val.strip():
                save_dictation(
                    st.session_state.dictation_questions[i],
                    st.session_state.dictation_answers[i],
                    val,
                )
                # 标记已保存
                while len(st.session_state.dictation_saved_flags) <= i:
                    st.session_state.dictation_saved_flags.append(False)
                st.session_state.dictation_saved_flags[i] = True
                st.session_state.dictation_submitted[i] = True
                # 记录要删除的草稿key
                today = datetime.now().strftime("%Y-%m-%d")
                draft_key = f"{today}_{st.session_state.dictation_questions[i][:50]}"
                draft_keys_to_delete.append(draft_key)
                saved_count += 1
        if saved_count > 0:
            delete_dictation_drafts(draft_keys_to_delete)
            st.toast(f"✅ 已保存 {saved_count} 条默写记录！刷新不会丢失~")
            st.rerun()
        else:
            st.warning("没有找到已填写的默写内容。")
with col3:
    if st.button("📝 全部存为草稿", use_container_width=True):
        saved_count = 0
        for i in range(len(st.session_state.dictation_questions)):
            key = f"dictation_input_{i}"
            val = st.session_state.get(key, "")
            if val and val.strip():
                today = datetime.now().strftime("%Y-%m-%d")
                draft_key = f"{today}_{st.session_state.dictation_questions[i][:50]}"
                save_dictation_draft(
                    st.session_state.dictation_questions[i],
                    st.session_state.dictation_answers[i],
                    val,
                    draft_key,
                )
                saved_count += 1
        if saved_count > 0:
            st.toast(f"📝 已将 {saved_count} 条答案存为草稿！")
        else:
            st.warning("没有找到已填写的默写内容。")
