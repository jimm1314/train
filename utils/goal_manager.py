"""
学习目标管理模块
负责设定和追踪用户的学习目标。
"""
import os
import json
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
from utils.data_loader import get_user_data_dir, ensure_user_data_dir

DEFAULT_GOALS = {
    "daily_questions": 20,
    "weekly_questions": 100,
    "daily_review": 5,
}


def _get_goals_file() -> str:
    return os.path.join(get_user_data_dir(), "goals.json")


def load_goals() -> dict:
    goals_file = _get_goals_file()
    if os.path.exists(goals_file):
        try:
            with open(goals_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = DEFAULT_GOALS.copy()
                merged.update(data)
                return merged
        except Exception:
            pass
    return DEFAULT_GOALS.copy()


def save_goals(goals: dict):
    ensure_user_data_dir()
    goals_file = _get_goals_file()
    with open(goals_file, "w", encoding="utf-8") as f:
        json.dump(goals, f, ensure_ascii=False, indent=2)


def get_today_progress() -> dict:
    from utils.review_manager import load_study_log
    study_log = load_study_log()
    today_str = datetime.now().strftime("%Y-%m-%d")

    if study_log.empty:
        return {"questions": 0}

    today_log = study_log[study_log["日期"] == today_str]
    questions = 0
    if not today_log.empty and "刷题数" in today_log.columns:
        questions = int(today_log["刷题数"].sum())

    return {"questions": questions}


def get_weekly_progress() -> dict:
    from utils.review_manager import load_study_log
    study_log = load_study_log()

    if study_log.empty:
        return {"questions": 0}

    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())

    if "日期" in study_log.columns:
        study_log = study_log.copy()
        study_log["日期_dt"] = pd.to_datetime(study_log["日期"], errors="coerce")
        week_log = study_log[study_log["日期_dt"].dt.date >= week_start]
        questions = 0
        if not week_log.empty and "刷题数" in week_log.columns:
            questions = int(week_log["刷题数"].sum())
    else:
        questions = 0

    return {"questions": questions}


def get_review_progress() -> int:
    from utils.review_manager import _read_review_file
    review_df = _read_review_file()
    if review_df.empty or "next_review" not in review_df.columns:
        return 0
    today_str = datetime.now().strftime("%Y-%m-%d")
    due = review_df[review_df["next_review"] <= today_str]
    return len(due)


def render_goal_progress():
    goals = load_goals()
    today = get_today_progress()
    weekly = get_weekly_progress()
    due_count = get_review_progress()

    daily_target = goals.get("daily_questions", 20)
    weekly_target = goals.get("weekly_questions", 100)
    review_target = goals.get("daily_review", 5)

    daily_pct = min(1.0, today["questions"] / daily_target) if daily_target > 0 else 0
    weekly_pct = min(1.0, weekly["questions"] / weekly_target) if weekly_target > 0 else 0
    review_done = min(due_count, review_target)
    review_pct = min(1.0, review_done / review_target) if review_target > 0 else 0

    st.markdown(
        '<div style="margin-bottom: 0.8rem;">'
        '<span style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0;">🎯 今日学习目标</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        _render_single_goal("📝 刷题", today["questions"], daily_target, daily_pct)
    with col2:
        _render_single_goal("📅 本周", weekly["questions"], weekly_target, weekly_pct)
    with col3:
        _render_single_goal("🔄 复习", review_done, review_target, review_pct)


def _render_single_goal(label: str, current: int, target: int, pct: float):
    color = "#10b981" if pct >= 1.0 else "#6366f1" if pct >= 0.5 else "#f59e0b"
    st.markdown(
        f'<div class="stat-card">'
        f'<div class="stat-card-value" style="font-size:1.4rem;">{current}/{target}</div>'
        f'<div class="stat-card-label">{label}</div>'
        f'<div style="margin-top:8px;height:4px;background:rgba(255,255,255,0.1);border-radius:2px;overflow:hidden;">'
        f'<div style="height:100%;width:{pct*100:.0f}%;background:{color};border-radius:2px;'
        f'transition:width 0.5s ease;"></div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
