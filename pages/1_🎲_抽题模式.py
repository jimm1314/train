"""
抽题模式页面
随机抽取题目进行练习，支持知识点/难度筛选。
"""
import streamlit as st
import random
import pandas as pd
from utils.session_state import init_session_state
from utils.styles import inject_global_styles
from utils.data_loader import get_filtered_questions, get_knowledge_categories
from utils.review_manager import log_study_session
from utils.auth import check_auth
from components.timer import render_timer
from components.question_card import render_question_card
from components.metrics import render_metric_row

# 初始化
try:
    st.set_page_config(page_title="抽题模式", page_icon="🎲", layout="wide")
except Exception:
    pass
check_auth()
init_session_state()
inject_global_styles()

st.title("🎲 抽题模式")

# 页面介绍
st.markdown("""
<div style="background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(236,72,153,0.1));
            border: 1px solid rgba(99,102,241,0.2); border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
    <div style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0; margin-bottom: 0.8rem;">
        🎯 随机抽题，高效练习
    </div>
    <div style="color: #94a3b8; font-size: 0.9rem; line-height: 1.6;">
        <p>✨ <strong>随机抽取</strong>：系统从题库中随机抽取题目，避免重复练习</p>
        <p>🎯 <strong>精准筛选</strong>：支持按知识点、难度筛选，针对性练习</p>
        <p>⏱️ <strong>计时练习</strong>：内置倒计时功能，模拟真实面试场景</p>
        <p>📊 <strong>学习记录</strong>：自动记录刷题数量，追踪学习进度</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 侧边栏设置
# ==========================================
with st.sidebar:
    st.subheader("⚙️ 抽题设置")
    num_to_draw = st.number_input("每次抽取题目数量", min_value=1, max_value=20, value=3)
    force_load = st.checkbox("强制加载所有题目（无视是否显示）", value=False)

    st.markdown("---")
    st.subheader("🔍 关键词搜索")
    search_keyword = st.text_input("搜索题目或答案", placeholder="输入关键词...", key="search_kw")

    st.markdown("---")
    st.subheader("🎯 筛选条件")

    df = get_filtered_questions(force_show_all=force_load)

    # 知识点筛选
    categories = get_knowledge_categories(df)
    selected_cats = st.multiselect("按知识点筛选", categories, default=[])

    # 难度筛选
    if not df.empty and "难度" in df.columns:
        difficulties = df["难度"].dropna().unique().tolist()
        selected_diff = st.multiselect("按难度筛选", difficulties, default=[])
    else:
        selected_diff = []

    # 应用筛选
    filtered_df = df.copy()
    if search_keyword:
        kw = search_keyword.lower()
        mask = (
            filtered_df["问题"].str.lower().str.contains(kw, na=False) |
            filtered_df["参考"].astype(str).str.lower().str.contains(kw, na=False)
        )
        filtered_df = filtered_df[mask]
    if selected_cats:
        filtered_df = filtered_df[filtered_df["知识点"].isin(selected_cats)]
    if selected_diff:
        filtered_df = filtered_df[filtered_df["难度"].isin(selected_diff)]

    st.markdown("---")
    st.subheader("⏱️ 倒计时工具")
    timer_minutes = st.number_input("设置答题时间（分钟）", min_value=1, max_value=60, value=5)
    if st.button("▶️ 启动倒计时", use_container_width=True):
        st.session_state.countdown_trigger += 1

    st.markdown("---")
    if st.button("♻️ 重置抽题记忆（重新洗牌）", use_container_width=True):
        st.session_state.seen_questions = set()
        st.session_state.history_log = []
        st.success("洗牌完成！")

# ==========================================
# 指标行
# ==========================================
render_metric_row([
    {"label": "📚 当前可用题库", "value": f"{len(filtered_df)} 道"},
    {"label": "🔥 累计刷题", "value": f"{st.session_state.total_drawn_count} 道"},
    {"label": "🧠 已抽过（记忆中）", "value": f"{len(st.session_state.seen_questions)} 道"},
])
st.markdown("---")

# 倒计时
if st.session_state.countdown_trigger > 0:
    render_timer(timer_minutes, st.session_state.countdown_trigger)

# ==========================================
# 抽题按钮
# ==========================================
if st.button(f"🚀 抽取 {num_to_draw} 道新题目", use_container_width=True, type="primary"):
    if not filtered_df.empty:
        # 把旧题目归入历史
        if st.session_state.drawn_questions:
            for old_q, old_a in zip(st.session_state.drawn_questions, st.session_state.drawn_answers):
                if not any(item["q"] == old_q for item in st.session_state.history_log):
                    st.session_state.history_log.insert(0, {"q": old_q, "a": old_a})

        # 去重 + 洗牌
        available_df = filtered_df[~filtered_df["问题"].isin(st.session_state.seen_questions)]
        if len(available_df) < num_to_draw:
            st.warning("🔄 题库已抽完一轮，正在为您重新洗牌...")
            st.session_state.seen_questions = set()
            available_df = filtered_df

        sample_size = min(num_to_draw, len(available_df))
        random_rows = available_df.sample(n=sample_size)

        st.session_state.drawn_questions = random_rows["问题"].tolist()
        st.session_state.drawn_answers = random_rows["参考"].tolist()
        st.session_state.drawn_meta = random_rows.to_dict("records")  # 保存完整元数据

        st.session_state.seen_questions.update(st.session_state.drawn_questions)
        st.session_state.total_drawn_count += sample_size

        # 记录学习日志
        if "知识点" in random_rows.columns:
            cat_counts = random_rows["知识点"].value_counts().to_dict()
            log_study_session(sample_size, activity="抽题", categories=cat_counts)
        else:
            log_study_session(sample_size, activity="抽题")
    else:
        st.error("当前筛选条件下题库为空！请调整筛选条件。")

# ==========================================
# 展示题目
# ==========================================
if st.session_state.drawn_questions:
    st.success("👇 最新抽取的题目已就绪！")
    meta_list = st.session_state.get("drawn_meta", [])

    for i in range(len(st.session_state.drawn_questions)):
        q = st.session_state.drawn_questions[i]
        ans = st.session_state.drawn_answers[i]

        # 构建 row Series
        if i < len(meta_list):
            row_data = meta_list[i]
        else:
            row_data = {"问题": q, "参考": ans}

        row = pd.Series(row_data)

        render_question_card(
            index=i + 1,
            row=row,
            show_tags=True,
            show_save_button=True,
            total_key=st.session_state.total_drawn_count,
        )

# ==========================================
# 历史记录
# ==========================================
if st.session_state.history_log:
    st.markdown('<div class="history-header">📜 本次会话历史记录</div>', unsafe_allow_html=True)

    for idx, item in enumerate(st.session_state.history_log):
        preview = item['q'][:100] + ("..." if len(item['q']) > 100 else "")
        st.markdown(f"**🔄 历史回顾 {idx + 1}：** {preview}")
        with st.expander("查看完整题目与参考答案"):
            st.markdown(f"**题目：** {item['q']}")
            st.markdown(f"**参考答案：** {item['a']}")
        st.write("---")
