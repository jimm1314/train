"""
模拟面试模式页面
模拟真实面试场景：限时作答、逐题推进、结束后 AI 评分。
"""
import streamlit as st

st.set_page_config(page_title="模拟面试", page_icon="🎤", layout="wide")

import random
from datetime import datetime
from utils.session_state import init_session_state
from utils.styles import inject_global_styles, render_difficulty_tag, render_knowledge_tag
from utils.data_loader import get_filtered_questions, get_knowledge_categories
from utils.review_manager import save_to_review_book, log_study_session, get_due_reviews
from utils.auth import check_auth
from utils.ai_scorer import score_answer, render_score_result
from components.question_card import safe_format

check_auth()
init_session_state()
inject_global_styles()

st.title("🎤 模拟面试")

st.markdown("""
<div style="background: linear-gradient(135deg, rgba(236,72,153,0.1), rgba(99,102,241,0.1));
            border: 1px solid rgba(236,72,153,0.2); border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
    <div style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0; margin-bottom: 0.8rem;">
        🎤 模拟真实面试，限时作答
    </div>
    <div style="color: #94a3b8; font-size: 0.9rem; line-height: 1.6;">
        <p>⏱️ <strong>限时作答</strong>：每题设定时间限制，模拟面试压力</p>
        <p>📝 <strong>逐题推进</strong>：一道一道作答，不可回头修改</p>
        <p>🤖 <strong>AI 评分</strong>：答完后自动对比参考答案给出评分</p>
        <p>📊 <strong>综合报告</strong>：面试结束后生成详细分析报告</p>
    </div>
</div>
""", unsafe_allow_html=True)

INTERVIEW_STATES = {"setup": "setup", "active": "active", "done": "done"}

if "interview_state" not in st.session_state:
    st.session_state.interview_state = INTERVIEW_STATES["setup"]
if "interview_questions" not in st.session_state:
    st.session_state.interview_questions = []
if "interview_current" not in st.session_state:
    st.session_state.interview_current = 0
if "interview_answers" not in st.session_state:
    st.session_state.interview_answers = []
if "interview_scores" not in st.session_state:
    st.session_state.interview_scores = []
if "interview_feedbacks" not in st.session_state:
    st.session_state.interview_feedbacks = []
if "interview_methods" not in st.session_state:
    st.session_state.interview_methods = []
if "interview_time_limit" not in st.session_state:
    st.session_state.interview_time_limit = 5


def reset_interview():
    st.session_state.interview_state = INTERVIEW_STATES["setup"]
    st.session_state.interview_questions = []
    st.session_state.interview_current = 0
    st.session_state.interview_answers = []
    st.session_state.interview_scores = []
    st.session_state.interview_feedbacks = []
    st.session_state.interview_methods = []
    if "interview_answer_input" in st.session_state:
        del st.session_state["interview_answer_input"]


# ==================== 设置阶段 ====================
if st.session_state.interview_state == INTERVIEW_STATES["setup"]:

    col_setup1, col_setup2 = st.columns([2, 1])

    with col_setup1:
        st.markdown("### ⚙️ 面试设置")

        df = get_filtered_questions(force_show_all=False)

        if df.empty:
            st.error("题库为空，请先添加题目。")
            st.stop()

        available_files = sorted(df["来源文件"].dropna().unique().tolist()) if "来源文件" in df.columns else []
        selected_files = []

        source_mode = st.radio(
            "题目来源",
            ["随机抽题", "优先复习错题"],
            horizontal=True,
        )

        st.markdown("---")
        st.markdown("#### 📁 题库文件筛选")

        if available_files:
            selected_files = st.multiselect(
                "选择题库文件（不选则使用全部）",
                available_files,
                default=[],
                help="可以针对特定文件的题目进行模拟面试",
            )
            if selected_files:
                df = df[df["来源文件"].isin(selected_files)]
        else:
            st.caption("当前题库没有来源文件信息")

        st.markdown("---")
        st.markdown("#### ⚙️ 面试参数")

        num_questions = st.slider("题目数量", min_value=3, max_value=20, value=5)
        time_per_question = st.slider("每题限时（分钟）", min_value=1, max_value=15, value=5)
        st.session_state.interview_time_limit = time_per_question

        categories = get_knowledge_categories(df)
        selected_cats = st.multiselect("按知识点筛选（不选则随机）", categories, default=[])

        if not df.empty and "难度" in df.columns:
            difficulties = df["难度"].dropna().unique().tolist()
            selected_diff = st.multiselect("按难度筛选", difficulties, default=[])
        else:
            selected_diff = []

    with col_setup2:
        st.markdown("### 📋 面试概览")
        filtered = df.copy()
        if selected_cats:
            filtered = filtered[filtered["知识点"].isin(selected_cats)]
        if selected_diff:
            filtered = filtered[filtered["难度"].isin(selected_diff)]

        st.metric("可用题库", f"{len(filtered)} 道")
        actual_count = min(num_questions, len(filtered))
        st.metric("面试题数", f"{actual_count} 道")
        st.metric("每题限时", f"{time_per_question} 分钟")
        est_total = actual_count * time_per_question
        st.metric("预计时长", f"约 {est_total} 分钟")

        if selected_files:
            st.markdown("---")
            st.markdown("**📁 已选文件：**")
            for fname in selected_files:
                file_count = len(df[df["来源文件"] == fname]) if "来源文件" in df.columns else 0
                st.markdown(f"- `{fname}` ({file_count} 题)")

    st.markdown("---")

    if st.button("🚀 开始面试", type="primary", use_container_width=True):
        if filtered.empty:
            st.error("当前筛选条件下没有可用题目！")
        else:
            sample_size = min(num_questions, len(filtered))

            if source_mode == "优先复习错题":
                due = get_due_reviews()
                if not due.empty:
                    if selected_cats:
                        due = due[due["知识点"].isin(selected_cats)] if "知识点" in due.columns else due
                    due_sample = due.head(sample_size)
                    remaining = sample_size - len(due_sample)
                    if remaining > 0:
                        extra = filtered[~filtered["问题"].isin(due_sample["问题"])].sample(n=min(remaining, len(filtered)))
                        import pandas as pd
                        sampled = pd.concat([due_sample[["问题", "参考"]], extra[["问题", "参考"]]], ignore_index=True)
                    else:
                        sampled = due_sample[["问题", "参考"]].reset_index(drop=True)
                else:
                    sampled = filtered.sample(n=sample_size)
            else:
                sampled = filtered.sample(n=sample_size)

            st.session_state.interview_questions = sampled.to_dict("records")
            st.session_state.interview_current = 0
            st.session_state.interview_answers = []
            st.session_state.interview_scores = []
            st.session_state.interview_feedbacks = []
            st.session_state.interview_methods = []
            st.session_state.interview_state = INTERVIEW_STATES["active"]
            st.rerun()


# ==================== 面试进行中 ====================
elif st.session_state.interview_state == INTERVIEW_STATES["active"]:
    questions = st.session_state.interview_questions
    current = st.session_state.interview_current
    total = len(questions)
    time_limit = st.session_state.interview_time_limit

    if current >= total:
        st.session_state.interview_state = INTERVIEW_STATES["done"]
        st.rerun()

    q_data = questions[current]
    question = q_data.get("问题", "")
    answer = q_data.get("参考", "")

    progress_pct = current / total
    st.progress(progress_pct)
    st.markdown(
        f'<div style="text-align:center;color:#94a3b8;margin-bottom:1rem;">'
        f'第 <b style="color:#e2e8f0;">{current + 1}</b> / {total} 题 · '
        f'每题限时 {time_limit} 分钟</div>',
        unsafe_allow_html=True,
    )

    tag_html = ""
    if "难度" in q_data and q_data.get("难度"):
        tag_html += render_difficulty_tag(str(q_data["难度"])) + " "
    if "知识点" in q_data and q_data.get("知识点") and q_data.get("知识点") != "未分类":
        tag_html += render_knowledge_tag(str(q_data["知识点"]))

    st.markdown(
        f'<div class="question-card">'
        f'<div class="question-title">📌 第 {current + 1} 题</div>'
        f'<div style="margin-bottom: 6px;">{tag_html}</div>'
        f'<div style="color: #cbd5e1; line-height: 1.7; font-size: 0.95rem;">{safe_format(question)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.components.v1.html(
        f"""<div id="interview_timer" style="
            font-size: 20px; font-weight: bold; color: #6366f1;
            background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.2);
            padding: 10px; border-radius: 10px; text-align: center;">
            ⏱️ 剩余时间: {time_limit}:00
        </div>
        <script>
        var t = {time_limit} * 60;
        var el = document.getElementById("interview_timer");
        var iv = setInterval(function(){{
            var m = Math.floor(t/60); var s = t%60;
            m = m<10?"0"+m:m; s = s<10?"0"+s:s;
            el.innerHTML = "⏱️ 剩余时间: "+m+":"+s;
            t--;
            if(t<0){{ clearInterval(iv);
                el.innerHTML="⏰ 时间到！";
                el.style.color="white"; el.style.background="#ef4444";
            }}
        }}, 1000);
        </script>""",
        height=55,
    )

    user_answer = st.text_area(
        "📝 请作答（像真实面试一样口述你的答案）",
        key=f"interview_answer_input",
        height=180,
        placeholder="请在此输入你的回答...",
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("➡️ 提交并下一题", type="primary", use_container_width=True):
            score, feedback, method = score_answer(question, answer, user_answer)
            st.session_state.interview_answers.append(user_answer)
            st.session_state.interview_scores.append(score)
            st.session_state.interview_feedbacks.append(feedback)
            st.session_state.interview_methods.append(method)

            if current + 1 >= total:
                st.session_state.interview_state = INTERVIEW_STATES["done"]
            else:
                st.session_state.interview_current = current + 1
            st.rerun()
    with col2:
        if st.button("🏳️ 放弃本题", use_container_width=True):
            st.session_state.interview_answers.append("")
            st.session_state.interview_scores.append(0)
            st.session_state.interview_feedbacks.append("未作答")
            st.session_state.interview_methods.append("local")

            if current + 1 >= total:
                st.session_state.interview_state = INTERVIEW_STATES["done"]
            else:
                st.session_state.interview_current = current + 1
            st.rerun()
    with col3:
        if st.button("❌ 终止面试", use_container_width=True):
            st.session_state.interview_state = INTERVIEW_STATES["done"]
            st.rerun()


# ==================== 面试结果 ====================
elif st.session_state.interview_state == INTERVIEW_STATES["done"]:
    questions = st.session_state.interview_questions
    answers = st.session_state.interview_answers
    scores = st.session_state.interview_scores
    feedbacks = st.session_state.interview_feedbacks
    methods = st.session_state.interview_methods

    total_answered = len(scores)
    if total_answered == 0:
        st.info("本次面试没有作答记录。")
        if st.button("🔄 重新开始"):
            reset_interview()
            st.rerun()
        st.stop()

    avg_score = sum(scores) / total_answered
    max_score = max(scores)
    min_score = min(scores)
    pass_count = sum(1 for s in scores if s >= 60)

    log_study_session(total_answered, activity="模拟面试")

    st.markdown("### 📊 面试报告")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f'<div class="stat-card"><div class="stat-card-value">{total_answered}</div>'
            f'<div class="stat-card-label">答题数</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        color = "#10b981" if avg_score >= 70 else "#f59e0b" if avg_score >= 50 else "#ef4444"
        st.markdown(
            f'<div class="stat-card"><div class="stat-card-value" style="color:{color};-webkit-text-fill-color:{color};">{avg_score:.0f}</div>'
            f'<div class="stat-card-label">平均分</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f'<div class="stat-card"><div class="stat-card-value">{pass_count}/{total_answered}</div>'
            f'<div class="stat-card-label">及格率</div></div>',
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f'<div class="stat-card"><div class="stat-card-value">{max_score}</div>'
            f'<div class="stat-card-label">最高分</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### 📋 逐题回顾")

    for i in range(min(len(questions), total_answered)):
        q_data = questions[i]
        question = q_data.get("问题", "")
        ref_answer = q_data.get("参考", "")
        user_ans = answers[i] if i < len(answers) else ""
        score = scores[i] if i < len(scores) else 0
        feedback = feedbacks[i] if i < len(feedbacks) else ""
        method = methods[i] if i < len(methods) else "local"

        with st.expander(f"第 {i+1} 题 — 得分: {score} 分 {'✅' if score >= 60 else '❌'}"):
            st.markdown(f"**题目：** {safe_format(question)}")

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**📝 你的回答：**")
                st.info(user_ans if user_ans else "（未作答）")
            with col_b:
                st.markdown("**✅ 参考答案：**")
                st.info(safe_format(ref_answer))

            render_score_result(score, feedback, method)

            if st.button("🚩 收藏到错题本", key=f"interview_save_{i}", use_container_width=True):
                save_to_review_book(question, ref_answer, note=user_ans, mastery=max(1, score // 20))
                st.toast("✅ 已收藏！")

    st.markdown("---")

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("🔄 重新面试", type="primary", use_container_width=True):
            reset_interview()
            st.rerun()
    with col_r2:
        if st.button("🏠 返回首页", use_container_width=True):
            reset_interview()
            st.switch_page("app.py")
