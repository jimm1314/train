"""
错题复习页面
查看已收藏的错题，支持按日期/知识点/掌握度筛选和排序。
"""
import streamlit as st
from utils.session_state import init_session_state
from utils.styles import inject_global_styles
from utils.review_manager import _read_review_file, delete_from_review_book, update_note, log_study_session
from components.question_card import render_review_card, safe_format

# 初始化
st.set_page_config(page_title="错题复习", page_icon="📝", layout="wide")
init_session_state()
inject_global_styles()

st.title("📝 我的错题与笔记")

# ==========================================
# 加载数据
# ==========================================
df = _read_review_file()

if df.empty:
    st.info("还没有收藏任何题目哦！快去 **🎲 抽题模式** 刷两道吧~")
    st.stop()

# 确保列存在
for col in ["掌握度", "复习次数", "标签"]:
    if col not in df.columns:
        df[col] = 0 if col != "标签" else ""

df["掌握度"] = df["掌握度"].fillna(0).astype(int)
df["复习次数"] = df["复习次数"].fillna(0).astype(int)

# ==========================================
# 侧边栏筛选
# ==========================================
with st.sidebar:
    st.subheader("🔍 筛选条件")

    # 日期筛选
    dates = ["全部"] + sorted(df["日期"].dropna().unique().tolist(), reverse=True)
    selected_date = st.selectbox("📅 选择日期", dates)

    # 知识点筛选（如果错题本有知识点列）
    if "知识点" in df.columns:
        cats = ["全部"] + sorted(df["知识点"].dropna().unique().tolist())
        selected_cat = st.selectbox("📋 知识点", cats)
    else:
        selected_cat = "全部"

    # 掌握度筛选
    mastery_filter = st.selectbox("⭐ 掌握度筛选", ["全部", "未掌握 (0-2)", "已掌握 (3-5)"])

    # 排序方式
    sort_by = st.selectbox("📊 排序方式", ["日期（最新）", "掌握度（低→高）", "复习次数（少→多）"])

    st.markdown("---")
    st.subheader("📈 快速统计")
    st.metric("错题总数", f"{len(df)} 道")
    avg_m = df["掌握度"].mean()
    st.metric("平均掌握度", f"{avg_m:.1f} ⭐")
    total_reviews = df["复习次数"].sum()
    st.metric("累计复习次数", f"{total_reviews} 次")

# ==========================================
# 应用筛选
# ==========================================
filtered = df.copy()

if selected_date != "全部":
    filtered = filtered[filtered["日期"] == selected_date]
if selected_cat != "全部" and "知识点" in filtered.columns:
    filtered = filtered[filtered["知识点"] == selected_cat]
if mastery_filter == "未掌握 (0-2)":
    filtered = filtered[filtered["掌握度"] <= 2]
elif mastery_filter == "已掌握 (3-5)":
    filtered = filtered[filtered["掌握度"] >= 3]

# 排序
if sort_by == "掌握度（低→高）":
    filtered = filtered.sort_values("掌握度", ascending=True)
elif sort_by == "复习次数（少→多）":
    filtered = filtered.sort_values("复习次数", ascending=True)
else:
    filtered = filtered.sort_values("日期", ascending=False)

# ==========================================
# 展示错题
# ==========================================
st.metric("当前筛选结果", f"{len(filtered)} 道")
st.markdown("---")

if filtered.empty:
    st.info("当前筛选条件下没有错题记录。")
else:
    # 记录错题复习活动
    log_study_session(len(filtered), activity="错题复习")
    for idx, (_, row) in enumerate(filtered.iterrows()):
        render_review_card(idx + 1, row)

        # 删除按钮（放在每道题下方）
        with st.expander(f"🗑️ 管理此题", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ 从错题本删除", key=f"del_{idx}",
                             use_container_width=True):
                    delete_from_review_book(row["问题"])
                    st.toast("✅ 已删除！")
                    st.rerun()
            with col2:
                new_note = st.text_area(
                    "✏️ 编辑备注",
                    value=str(row.get("备注", "")),
                    key=f"edit_note_{idx}",
                    height=68,
                )
                if st.button("💾 保存备注", key=f"save_note_{idx}",
                             use_container_width=True):
                    update_note(row["问题"], new_note)
                    st.toast("✅ 备注已更新！")
                    st.rerun()
