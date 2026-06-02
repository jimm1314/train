"""
管理员页面
查看和管理所有用户的信息与刷题记录。
仅管理员可访问。
"""
import streamlit as st
import pandas as pd
import os
import plotly.express as px
from datetime import datetime
from utils.session_state import init_session_state
from utils.styles import inject_global_styles
from utils.data_loader import DATA_DIR
from utils.auth import check_admin, get_all_users, delete_user

# 初始化
st.set_page_config(page_title="管理员面板", page_icon="👑", layout="wide")
check_admin()
init_session_state()
inject_global_styles()

st.title("👑 管理员面板")
st.markdown("---")

# ==========================================
# 用户数据目录
# ==========================================
USERS_DIR = os.path.join(DATA_DIR, "users")


def _read_user_csv(username: str, filename: str) -> pd.DataFrame:
    """读取指定用户的 CSV 文件"""
    fpath = os.path.join(USERS_DIR, username, filename)
    if os.path.exists(fpath):
        try:
            return pd.read_csv(fpath, encoding="utf-8-sig")
        except Exception:
            pass
    return pd.DataFrame()


def _get_user_data_size(username: str) -> str:
    """获取用户数据目录大小"""
    user_dir = os.path.join(USERS_DIR, username)
    if not os.path.exists(user_dir):
        return "0 B"
    total = 0
    for f in os.listdir(user_dir):
        fpath = os.path.join(user_dir, f)
        if os.path.isfile(fpath):
            total += os.path.getsize(fpath)
    if total < 1024:
        return f"{total} B"
    elif total < 1024 * 1024:
        return f"{total / 1024:.1f} KB"
    else:
        return f"{total / 1024 / 1024:.1f} MB"


def _get_user_stats(username: str) -> dict:
    """获取单个用户的统计数据"""
    review_df = _read_user_csv(username, "review_book.csv")
    study_log = _read_user_csv(username, "study_log.csv")
    checkin_df = _read_user_csv(username, "checkin_log.csv")

    total_drawn = 0
    if not study_log.empty and "刷题数" in study_log.columns:
        total_drawn = int(study_log["刷题数"].sum())

    avg_mastery = 0.0
    if not review_df.empty and "掌握度" in review_df.columns:
        avg_mastery = round(review_df["掌握度"].fillna(0).mean(), 1)

    streak = 0
    if not checkin_df.empty and "日期" in checkin_df.columns:
        from datetime import timedelta
        all_dates = sorted(checkin_df["日期"].dropna().unique().tolist())
        check_date = datetime.now().date()
        for d in reversed(all_dates):
            d_date = datetime.strptime(d, "%Y-%m-%d").date()
            if d_date == check_date:
                streak += 1
                check_date -= timedelta(days=1)
            elif d_date < check_date:
                break

    return {
        "错题数": len(review_df) if not review_df.empty else 0,
        "累计活动": total_drawn,
        "平均掌握度": avg_mastery,
        "连续签到": streak,
        "数据大小": _get_user_data_size(username),
    }


# ==========================================
# 顶部概览
# ==========================================
users = get_all_users()
col1, col2, col3 = st.columns(3)
col1.metric("👥 总用户数", f"{len(users)} 人")
admin_count = sum(1 for u in users if u["is_admin"])
col2.metric("👑 管理员", f"{admin_count} 人")
col3.metric("👤 普通用户", f"{len(users) - admin_count} 人")
st.markdown("---")

# ==========================================
# 用户列表 + 详情（使用 tabs 或 selectbox）
# ==========================================
st.markdown("### 👥 用户列表")

if not users:
    st.info("暂无用户注册。")
    st.stop()

# 构建用户选择列表
user_options = {}
for u in users:
    role_tag = "👑管理员" if u["is_admin"] else "👤用户"
    label = f"{role_tag}  {u['username']}  (注册于 {u['created_at']})"
    user_options[label] = u["username"]

selected_label = st.selectbox(
    "选择要查看的用户",
    list(user_options.keys()),
    key="admin_user_select",
)
selected_user = user_options[selected_label]

st.markdown("---")

# ==========================================
# 选中用户的详细信息
# ==========================================
st.markdown(f"### 📋 用户详情：`{selected_user}`")

user_stats = _get_user_stats(selected_user)

# 统计卡片
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("📝 错题数", f"{user_stats['错题数']} 道")
col2.metric("🔥 累计活动", f"{user_stats['累计活动']} 次")
col3.metric("⭐ 平均掌握度", user_stats["平均掌握度"])
col4.metric("🔥 连续签到", f"{user_stats['连续签到']} 天")
col5.metric("💾 数据大小", user_stats["数据大小"])

st.markdown("---")

# 数据详情 Tabs
tab_review, tab_study, tab_checkin, tab_dictation, tab_manage = st.tabs([
    "📝 错题本", "📊 学习日志", "📅 签到记录", "✍️ 默写记录", "⚙️ 用户管理"
])

# ---- 错题本 Tab ----
with tab_review:
    review_df = _read_user_csv(selected_user, "review_book.csv")
    if review_df.empty:
        st.info("该用户暂无错题记录。")
    else:
        st.markdown(f"共 **{len(review_df)}** 条错题记录")
        # 筛选
        if "知识点" in review_df.columns:
            cats = ["全部"] + sorted(review_df["知识点"].dropna().unique().tolist())
            sel_cat = st.selectbox("按知识点筛选", cats, key="admin_review_cat")
            if sel_cat != "全部":
                review_df = review_df[review_df["知识点"] == sel_cat]

        if "掌握度" in review_df.columns:
            mastery_opt = st.selectbox(
                "按掌握度筛选", ["全部", "未掌握 (0-2)", "已掌握 (3-5)"],
                key="admin_review_mastery",
            )
            if mastery_opt == "未掌握 (0-2)":
                review_df = review_df[review_df["掌握度"].fillna(0).astype(int) <= 2]
            elif mastery_opt == "已掌握 (3-5)":
                review_df = review_df[review_df["掌握度"].fillna(0).astype(int) >= 3]

        st.dataframe(review_df, use_container_width=True, hide_index=True)

        # 掌握度分布图
        if "掌握度" in review_df.columns:
            mastery_counts = review_df["掌握度"].fillna(0).astype(int).value_counts().sort_index().reset_index()
            mastery_counts.columns = ["掌握度", "题目数"]
            fig = px.bar(mastery_counts, x="掌握度", y="题目数",
                         color="掌握度", color_continuous_scale="YlGn", text="题目数")
            fig.update_layout(
                height=300, showlegend=False,
                xaxis=dict(tickmode="linear", dtick=1, gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                margin=dict(t=20),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8"),
            )
            st.plotly_chart(fig, use_container_width=True)

        # 导出
        csv_data = review_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "📥 导出该用户错题本",
            data=csv_data,
            file_name=f"review_book_{selected_user}.csv",
            mime="text/csv",
        )

# ---- 学习日志 Tab ----
with tab_study:
    study_log = _read_user_csv(selected_user, "study_log.csv")
    if study_log.empty:
        st.info("该用户暂无学习记录。")
    else:
        st.markdown(f"共 **{len(study_log)}** 条学习记录")

        # 每日趋势
        if "日期" in study_log.columns and "刷题数" in study_log.columns:
            if "活动类型" not in study_log.columns:
                study_log["活动类型"] = "抽题"
            daily = study_log.groupby(["日期", "活动类型"])["刷题数"].sum().reset_index()
            daily = daily.sort_values("日期")
            fig = px.line(daily, x="日期", y="刷题数", color="活动类型",
                          markers=True, line_shape="spline")
            fig.update_layout(
                height=300, margin=dict(t=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            )
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(study_log, use_container_width=True, hide_index=True)

        csv_data = study_log.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "📥 导出该用户学习日志",
            data=csv_data,
            file_name=f"study_log_{selected_user}.csv",
            mime="text/csv",
        )

# ---- 签到记录 Tab ----
with tab_checkin:
    checkin_df = _read_user_csv(selected_user, "checkin_log.csv")
    if checkin_df.empty:
        st.info("该用户暂无签到记录。")
    else:
        st.markdown(f"共 **{len(checkin_df)}** 条签到记录")

        # 签到统计
        if "日期" in checkin_df.columns:
            unique_dates = checkin_df["日期"].dropna().unique()
            st.metric("总签到天数", f"{len(unique_dates)} 天")

        st.dataframe(checkin_df, use_container_width=True, hide_index=True)

        csv_data = checkin_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "📥 导出该用户签到记录",
            data=csv_data,
            file_name=f"checkin_log_{selected_user}.csv",
            mime="text/csv",
        )

# ---- 默写记录 Tab ----
with tab_dictation:
    dictation_df = _read_user_csv(selected_user, "dictation_log.csv")
    if dictation_df.empty:
        st.info("该用户暂无默写记录。")
    else:
        st.markdown(f"共 **{len(dictation_df)}** 条默写记录")

        # 日期筛选
        if "日期" in dictation_df.columns:
            dates = ["全部"] + sorted(dictation_df["日期"].dropna().unique().tolist(), reverse=True)
            sel_date = st.selectbox("按日期筛选", dates, key="admin_dict_date")
            if sel_date != "全部":
                dictation_df = dictation_df[dictation_df["日期"] == sel_date]

        for idx, row in dictation_df.iterrows():
            st.markdown(f"**📌 {row.get('问题', '')}**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**📝 用户默写：**")
                st.text_area("", value=str(row.get("我的默写", "")), height=80,
                             disabled=True, key=f"admin_dict_my_{idx}")
            with col_b:
                st.markdown("**✅ 参考答案：**")
                st.text_area("", value=str(row.get("参考答案", "")), height=80,
                             disabled=True, key=f"admin_dict_ref_{idx}")
            st.caption(f"📅 {row.get('日期', '')}")
            st.markdown("---")

        csv_data = dictation_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "📥 导出该用户默写记录",
            data=csv_data,
            file_name=f"dictation_log_{selected_user}.csv",
            mime="text/csv",
        )

# ---- 用户管理 Tab ----
with tab_manage:
    st.markdown("#### ⚠️ 危险操作")

    if selected_user == "admin":
        st.warning("管理员账户不可删除。")
    else:
        st.markdown(f"当前选中用户：**`{selected_user}`**")
        st.warning("删除用户将**永久移除**该用户的所有数据（错题本、学习日志、签到记录、默写记录），且无法恢复！")

        confirm_text = st.text_input(
            f"请输入用户名 `{selected_user}` 以确认删除：",
            key="admin_delete_confirm",
        )
        if st.button(
            "🗑️ 永久删除该用户",
            type="primary",
            disabled=(confirm_text != selected_user),
        ):
            success, msg = delete_user(selected_user)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
