"""
学习统计页面
使用 Plotly 图表展示学习数据分析 + 签到日历。
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.session_state import init_session_state
from utils.styles import inject_global_styles
from utils.data_loader import get_filtered_questions
from utils.review_manager import _read_review_file, load_study_log, get_checkin_stats, check_in
from utils.auth import check_auth

# 初始化
st.set_page_config(page_title="学习统计", page_icon="📊", layout="wide")
check_auth()
init_session_state()
inject_global_styles()

st.title("📊 学习数据分析")

# ==========================================
# 加载数据
# ==========================================
df = get_filtered_questions(force_show_all=True)
review_df = _read_review_file()
study_log = load_study_log()
checkin = get_checkin_stats()

if df.empty:
    st.warning("题库为空，请先添加题目数据。")
    st.stop()

# 确保错题本列存在且类型安全
for col in ["掌握度", "复习次数", "知识点"]:
    if col not in review_df.columns:
        review_df[col] = 0 if col != "知识点" else "未分类"
review_df["掌握度"] = pd.to_numeric(review_df["掌握度"], errors="coerce").fillna(0).astype(int)
review_df["复习次数"] = pd.to_numeric(review_df["复习次数"], errors="coerce").fillna(0).astype(int)

# ==========================================
# 签到区域
# ==========================================
st.markdown("### 📅 今日签到")
col_checkin, col_streak, col_total = st.columns(3)

with col_checkin:
    if checkin["today_checked"]:
        st.success("✅ 今日已签到！继续保持！")
    else:
        st.info("❌ 今日尚未签到")
        if st.button("📌 一键签到", use_container_width=True, type="primary"):
            check_in("签到")
            st.toast("✅ 签到成功！")
            st.rerun()

with col_streak:
    streak = checkin["streak"]
    if streak > 0:
        st.markdown(
            '<div class="stat-card">'
            f'<div class="stat-card-value">🔥 {streak} 天</div>'
            '<div class="stat-card-label">连续签到</div>'
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.metric("🔥 连续签到", "0 天")

with col_total:
    st.metric("📅 总签到天数", f"{checkin['total_days']} 天")
    st.metric("📆 本月签到", f"{checkin['this_month_days']} 天")

st.markdown("---")

# ==========================================
# 签到热力图（GitHub 风格）
# ==========================================
st.markdown("### 🗓️ 签到日历")

from datetime import timedelta

checkin_dates_set = set(checkin["checkin_dates"]) if checkin["checkin_dates"] else set()
today = datetime.now().date()

# 最近 90 天
dates_range = [today - timedelta(days=i) for i in range(89, -1, -1)]

# 按周分组：周一=0 ... 周日=6
weeks = []
current_week = [None] * 7

for d in dates_range:
    weekday = d.weekday()
    current_week[weekday] = 1 if d.strftime("%Y-%m-%d") in checkin_dates_set else 0
    if weekday == 6:
        weeks.append(current_week)
        current_week = [None] * 7

# 补齐最后一周
if any(v is not None for v in current_week):
    for i in range(7):
        if current_week[i] is None:
            current_week[i] = 0
    weeks.append(current_week)

if weeks:
    # 转置：行=星期几(7)，列=第几周(N)
    matrix = list(zip(*weeks))
    matrix = [[v if v is not None else 0 for v in row] for row in matrix]
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    fig_cal = go.Figure(data=go.Heatmap(
        z=matrix,
        x=[f"第{i+1}周" for i in range(len(weeks))],
        y=weekday_names,
        colorscale=[[0, "rgba(255,255,255,0.04)"], [1, "#10b981"]],
        showscale=False,
        hovertemplate="%{y} %{x}<br>签到: %{z}<extra></extra>",
    ))
    fig_cal.update_layout(
        height=250,
        margin=dict(t=20, b=20, l=40, r=20),
        yaxis=dict(autorange="reversed", color="#94a3b8"),
        xaxis=dict(showticklabels=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"),
    )
    st.plotly_chart(fig_cal, use_container_width=True)
    st.caption("🟢 = 已签到  ⬜ = 未签到（最近 90 天）")
else:
    st.info("暂无签到记录，开始学习后自动签到。")

st.markdown("---")

# ==========================================
# 顶部概览卡片
# ==========================================
col1, col2, col3, col4 = st.columns(4)
col1.metric("📚 题库总量", f"{len(df)} 道")
col2.metric("📝 错题收录", f"{len(review_df)} 道")

total_drawn = int(study_log["刷题数"].sum()) if not study_log.empty and "刷题数" in study_log.columns else 0
col3.metric("🔥 累计活动", f"{total_drawn} 次")

avg_mastery = review_df["掌握度"].mean()
col4.metric("⭐ 平均掌握度", f"{avg_mastery:.1f}")
st.markdown("---")

# ==========================================
# 每日学习趋势（按活动类型分）
# ==========================================
st.markdown("### 📈 每日学习趋势")
if not study_log.empty and "日期" in study_log.columns:
    # 确保活动类型列存在
    if "活动类型" not in study_log.columns:
        study_log["活动类型"] = "抽题"

    daily = study_log.groupby(["日期", "活动类型"])["刷题数"].sum().reset_index()
    daily = daily.sort_values("日期")

    activity_colors = {
        "抽题": "#6366f1",
        "背题": "#22c55e",
        "错题复习": "#f59e0b",
        "默写": "#ec4899",
        "签到": "#6b7280",
    }

    fig_trend = px.line(
        daily, x="日期", y="刷题数", color="活动类型",
        markers=True, line_shape="spline",
        color_discrete_map=activity_colors,
    )
    fig_trend.update_layout(
        height=350,
        xaxis_title="日期",
        yaxis_title="活动次数",
        margin=dict(t=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("暂无学习记录。开始学习后会自动记录。")

st.markdown("---")

# ==========================================
# 图表区域
# ==========================================
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 📋 题库知识点分布")
    if "知识点" in df.columns:
        cat_counts = df["知识点"].value_counts().reset_index()
        cat_counts.columns = ["知识点", "题目数"]
        fig_cat = px.bar(
            cat_counts, x="知识点", y="题目数",
            color="题目数", color_continuous_scale="Blues", text="题目数",
        )
        fig_cat.update_layout(
            showlegend=False, xaxis_tickangle=-45, height=400, margin=dict(t=20, b=80),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        )
        st.plotly_chart(fig_cat, use_container_width=True)

with col_right:
    st.markdown("### 🎯 题库难度分布")
    if "难度" in df.columns:
        diff_counts = df["难度"].value_counts().reset_index()
        diff_counts.columns = ["难度", "题目数"]
        color_map = {"简单": "#22c55e", "中等": "#eab308", "困难": "#ef4444"}
        fig_diff = px.pie(
            diff_counts, values="题目数", names="难度",
            color="难度", color_discrete_map=color_map, hole=0.4,
        )
        fig_diff.update_layout(
            height=400, margin=dict(t=20),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8"),
        )
        st.plotly_chart(fig_diff, use_container_width=True)

st.markdown("---")

# ==========================================
# 错题分析
# ==========================================
col_left2, col_right2 = st.columns(2)

with col_left2:
    st.markdown("### 🔥 错题知识点分布")
    if not review_df.empty and "知识点" in review_df.columns:
        review_cat = review_df["知识点"].value_counts().reset_index()
        review_cat.columns = ["知识点", "错题数"]
        fig_heat = px.bar(
            review_cat, x="知识点", y="错题数",
            color="错题数", color_continuous_scale="Reds", text="错题数",
        )
        fig_heat.update_layout(
            showlegend=False, xaxis_tickangle=-45, height=350, margin=dict(t=20, b=80),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

with col_right2:
    st.markdown("### ⭐ 掌握度分布")
    if not review_df.empty:
        mastery_counts = review_df["掌握度"].value_counts().sort_index().reset_index()
        mastery_counts.columns = ["掌握度", "题目数"]
        fig_mastery = px.bar(
            mastery_counts, x="掌握度", y="题目数",
            color="掌握度", color_continuous_scale="YlGn", text="题目数",
        )
        fig_mastery.update_layout(
            showlegend=False, height=350,
            xaxis=dict(tickmode="linear", dtick=1, gridcolor="rgba(255,255,255,0.06)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            margin=dict(t=20),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8"),
        )
        st.plotly_chart(fig_mastery, use_container_width=True)

st.markdown("---")

# ==========================================
# 雷达图
# ==========================================
st.markdown("### 🕸️ 知识点掌握度雷达图")
if not review_df.empty and "知识点" in review_df.columns:
    radar_data = review_df.groupby("知识点")["掌握度"].mean().reset_index()
    radar_data.columns = ["知识点", "平均掌握度"]

    if len(radar_data) < 3:
        st.info("至少需要 3 个知识点分类才能生成雷达图（当前只有 {} 个）。".format(len(radar_data)))
    else:
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=radar_data["平均掌握度"].tolist() + [radar_data["平均掌握度"].iloc[0]],
            theta=radar_data["知识点"].tolist() + [radar_data["知识点"].iloc[0]],
            fill="toself",
            fillcolor="rgba(99, 102, 241, 0.2)",
            line_color="#6366f1",
            name="平均掌握度",
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 5], gridcolor="rgba(255,255,255,0.08)"),
                bgcolor="rgba(0,0,0,0)",
            ),
            height=450, margin=dict(t=40, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8"),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

st.markdown("---")

# ==========================================
# 详细数据表
# ==========================================
st.markdown("### 📋 详细数据")

tab1, tab2 = st.columns(2)
with tab1:
    st.markdown("#### 题库统计")
    if "知识点" in df.columns:
        summary = df.groupby("知识点").agg(题目数=("问题", "count")).reset_index()
        if "难度" in df.columns:
            diff_pivot = df.groupby(["知识点", "难度"]).size().unstack(fill_value=0)
            summary = summary.merge(diff_pivot.reset_index(), on="知识点", how="left")
        st.dataframe(summary, use_container_width=True, hide_index=True)

with tab2:
    st.markdown("#### 错题统计")
    if not review_df.empty and "知识点" in review_df.columns:
        review_summary = review_df.groupby("知识点").agg(
            错题数=("问题", "count"),
            平均掌握度=("掌握度", "mean"),
            总复习次数=("复习次数", "sum"),
        ).reset_index()
        review_summary["平均掌握度"] = review_summary["平均掌握度"].round(1)
        st.dataframe(review_summary, use_container_width=True, hide_index=True)
