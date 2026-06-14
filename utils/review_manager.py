"""
错题本管理模块
负责错题的增删改查、掌握度更新、复习次数记录、签到系统、学习日志。
所有数据持久化通过数据库完成。
"""
import os
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

from utils import db
from utils.data_loader import (
    get_review_file, get_study_log_file, get_checkin_file,
    ensure_user_data_dir, load_question_banks,
)

REVIEW_COLUMNS = ["日期", "问题", "参考", "备注", "掌握度", "复习次数", "标签",
                  "归因", "next_review", "ease_factor", "interval", "repetitions"]

ATTRIBUTION_OPTIONS = ["知识盲区", "理解偏差", "表达问题", "粗心大意", "其他"]


def _get_username() -> str:
    return st.session_state.get("username", "")


def sm2(quality: int, repetitions: int, ease_factor: float, interval: int) -> tuple:
    quality = max(0, min(5, int(quality)))
    ease_factor = max(1.3, float(ease_factor))
    interval = max(1, int(interval))

    if quality >= 3:
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = round(interval * ease_factor)
        new_repetitions = repetitions + 1
        new_ease_factor = max(
            1.3,
            ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
        )
    else:
        new_repetitions = 0
        new_interval = 1
        new_ease_factor = max(1.3, ease_factor - 0.2)

    return new_repetitions, new_ease_factor, new_interval


# ==========================================
# 错题本（数据库）
# ==========================================

def _read_review_file() -> pd.DataFrame:
    """读取当前用户的错题本"""
    username = _get_username()
    if not username:
        return pd.DataFrame(columns=REVIEW_COLUMNS)

    try:
        db.init_tables()
        sql = (
            "SELECT date_str AS 日期, question AS 问题, answer AS 参考, "
            "note AS 备注, mastery AS 掌握度, review_count AS 复习次数, "
            "tags AS 标签, attribution AS 归因, next_review, "
            "ease_factor, review_interval AS `interval`, repetitions "
            "FROM review_book WHERE username = %s"
        )
        df = db.query_df(sql, (username,))
        if not df.empty:
            for col, default in [("归因", ""), ("next_review", datetime.now().strftime("%Y-%m-%d")),
                                  ("ease_factor", 2.5), ("interval", 1), ("repetitions", 0)]:
                if col not in df.columns:
                    df[col] = default
            return df
        return pd.DataFrame(columns=REVIEW_COLUMNS)
    except Exception:
        return pd.DataFrame(columns=REVIEW_COLUMNS)


def _write_review_file(df: pd.DataFrame):
    """写入错题本（通过数据库 upsert，使用事务保护）"""
    username = _get_username()
    if not username:
        return

    try:
        sql = (
            "INSERT INTO review_book "
            "(username, date_str, question, answer, note, mastery, review_count, "
            "tags, attribution, next_review, ease_factor, review_interval, repetitions) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        today_str = datetime.now().strftime("%Y-%m-%d")
        operations = [
            ("DELETE FROM review_book WHERE username = %s", (username,)),
        ]
        for _, row in df.iterrows():
            operations.append((sql, (
                username,
                str(row.get("日期", today_str)),
                str(row.get("问题", "")),
                str(row.get("参考", "")),
                str(row.get("备注", "")),
                int(row.get("掌握度", 0)) if pd.notna(row.get("掌握度", 0)) else 0,
                int(row.get("复习次数", 0)) if pd.notna(row.get("复习次数", 0)) else 0,
                str(row.get("标签", "")),
                str(row.get("归因", "")),
                str(row.get("next_review", today_str)),
                float(row.get("ease_factor", 2.5)) if pd.notna(row.get("ease_factor", 2.5)) else 2.5,
                int(row.get("interval", 1)) if pd.notna(row.get("interval", 1)) else 1,
                int(row.get("repetitions", 0)) if pd.notna(row.get("repetitions", 0)) else 0,
            )))
        db.execute_transaction(operations)
    except Exception as e:
        st.error(f"保存错题本失败: {e}")


def save_to_review_book(question: str, answer: str, note: str = "",
                        mastery: int = 0, tags: str = "",
                        attribution: str = ""):
    mastery = max(0, min(5, int(mastery)))
    today_str = datetime.now().strftime("%Y-%m-%d")

    df = _read_review_file()
    if not df.empty:
        df = df[df["问题"] != question]

    new_row = pd.DataFrame([{
        "日期": today_str, "问题": question, "参考": answer, "备注": note,
        "掌握度": mastery, "复习次数": 0, "标签": tags, "归因": attribution,
        "next_review": today_str, "ease_factor": 2.5, "interval": 1, "repetitions": 0,
    }])
    updated = pd.concat([df, new_row], ignore_index=True)
    _write_review_file(updated)


def delete_from_review_book(question: str):
    df = _read_review_file()
    if df.empty:
        return
    df = df[df["问题"] != question]
    _write_review_file(df)


def update_mastery(question: str, mastery: int):
    mastery = max(0, min(5, int(mastery)))
    username = _get_username()
    if not username:
        return
    try:
        db.execute(
            "UPDATE review_book SET mastery = %s WHERE username = %s AND question = %s",
            (mastery, username, question),
        )
    except Exception as e:
        print(f"[ReviewManager] update_mastery 失败: {e}")


def update_note(question: str, note: str):
    username = _get_username()
    if not username:
        return
    try:
        db.execute(
            "UPDATE review_book SET note = %s WHERE username = %s AND question = %s",
            (note, username, question),
        )
    except Exception as e:
        print(f"[ReviewManager] update_note 失败: {e}")


def increment_review_count(question: str):
    username = _get_username()
    if not username:
        return
    try:
        db.execute(
            "UPDATE review_book SET review_count = review_count + 1 WHERE username = %s AND question = %s",
            (username, question),
        )
    except Exception as e:
        print(f"[ReviewManager] increment_review_count 失败: {e}")


def get_review_stats() -> dict:
    df = _read_review_file()
    if df.empty:
        return {"total": 0, "avg_mastery": 0, "by_date": {}, "by_tag": {}}
    return {
        "total": len(df),
        "avg_mastery": round(df["掌握度"].fillna(0).mean(), 1),
        "by_date": df.groupby("日期").size().to_dict(),
        "by_tag": df["标签"].dropna().value_counts().to_dict() if "标签" in df.columns else {},
    }


# ==========================================
# 签到系统（数据库）
# ==========================================

def _read_checkin() -> pd.DataFrame:
    username = _get_username()
    if not username:
        return pd.DataFrame(columns=["日期", "签到时间", "活动类型"])
    try:
        db.init_tables()
        sql = "SELECT date_str AS 日期, checkin_time AS 签到时间, activity_type AS 活动类型 FROM checkin_log WHERE username = %s"
        df = db.query_df(sql, (username,))
        if df.empty:
            return pd.DataFrame(columns=["日期", "签到时间", "活动类型"])
        return df
    except Exception:
        return pd.DataFrame(columns=["日期", "签到时间", "活动类型"])


def _write_checkin(df: pd.DataFrame):
    pass


def check_in(activity_type: str = "学习"):
    today_str = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M:%S")
    username = _get_username()
    if not username:
        return

    try:
        db.init_tables()
        existing = db.execute(
            "SELECT id FROM checkin_log WHERE username = %s AND date_str = %s AND activity_type = %s",
            (username, today_str, activity_type), fetch=True,
        )
        if existing:
            return
        db.execute(
            "INSERT INTO checkin_log (username, date_str, checkin_time, activity_type) VALUES (%s, %s, %s, %s)",
            (username, today_str, now_time, activity_type),
        )
    except Exception as e:
        print(f"[ReviewManager] check_in 失败: {e}")


def get_checkin_stats() -> dict:
    username = _get_username()
    if not username:
        return {"total_days": 0, "streak": 0, "this_month_days": 0,
                "checkin_dates": [], "today_checked": False}

    try:
        db.init_tables()
        sql = "SELECT DISTINCT date_str FROM checkin_log WHERE username = %s ORDER BY date_str"
        rows = db.execute(sql, (username,), fetch=True)
    except Exception:
        rows = []

    if not rows:
        return {"total_days": 0, "streak": 0, "this_month_days": 0,
                "checkin_dates": [], "today_checked": False}

    all_dates = sorted([r["date_str"] for r in rows])
    today_str = datetime.now().strftime("%Y-%m-%d")

    streak = 0
    check_date = datetime.now().date()
    for d in reversed(all_dates):
        d_date = datetime.strptime(d, "%Y-%m-%d").date()
        if d_date == check_date:
            streak += 1
            check_date -= timedelta(days=1)
        elif d_date < check_date:
            break

    this_month = datetime.now().strftime("%Y-%m")
    this_month_dates = [d for d in all_dates if d.startswith(this_month)]

    return {
        "total_days": len(all_dates),
        "streak": streak,
        "this_month_days": len(set(this_month_dates)),
        "checkin_dates": all_dates,
        "today_checked": today_str in all_dates,
    }


# ==========================================
# 学习日志管理（数据库）
# ==========================================

def log_study_session(count: int, activity: str = "抽题",
                      categories: dict[str, int] | None = None):
    username = _get_username()
    if not username:
        return
    today_str = datetime.now().strftime("%Y-%m-%d")

    try:
        db.init_tables()
        db.execute(
            "INSERT INTO study_log (username, date_str, count, activity_type) VALUES (%s, %s, %s, %s)",
            (username, today_str, count, activity),
        )
    except Exception as e:
        print(f"[ReviewManager] log_study_session 失败: {e}")

    check_in(activity)


def load_study_log() -> pd.DataFrame:
    username = _get_username()
    if not username:
        return pd.DataFrame(columns=["日期", "刷题数", "活动类型"])
    try:
        db.init_tables()
        sql = "SELECT date_str AS 日期, count AS 刷题数, activity_type AS 活动类型 FROM study_log WHERE username = %s"
        df = db.query_df(sql, (username,))
        if df.empty:
            return pd.DataFrame(columns=["日期", "刷题数", "活动类型"])
        return df
    except Exception:
        return pd.DataFrame(columns=["日期", "刷题数", "活动类型"])


# ==========================================
# SM-2 间隔重复扩展（数据库）
# ==========================================

def update_sm2_after_review(question: str, quality: int):
    username = _get_username()
    if not username:
        return

    try:
        rows = db.execute(
            "SELECT repetitions, ease_factor, review_interval FROM review_book WHERE username = %s AND question = %s",
            (username, question), fetch=True,
        )
        if not rows:
            return

        row = rows[0]
        cur_rep = int(row["repetitions"]) if row["repetitions"] is not None else 0
        cur_ef = float(row["ease_factor"]) if row["ease_factor"] is not None else 2.5
        cur_iv = int(row["review_interval"]) if row["review_interval"] is not None else 1

        new_rep, new_ef, new_iv = sm2(quality, cur_rep, cur_ef, cur_iv)
        next_date = (datetime.now() + timedelta(days=new_iv)).strftime("%Y-%m-%d")

        db.execute(
            "UPDATE review_book SET repetitions = %s, ease_factor = %s, review_interval = %s, next_review = %s "
            "WHERE username = %s AND question = %s",
            (new_rep, round(new_ef, 2), new_iv, next_date, username, question),
        )
    except Exception as e:
        print(f"[ReviewManager] update_sm2_after_review 失败: {e}")


def get_due_reviews() -> pd.DataFrame:
    username = _get_username()
    if not username:
        return pd.DataFrame(columns=REVIEW_COLUMNS)
    try:
        db.init_tables()
        today_str = datetime.now().strftime("%Y-%m-%d")
        sql = (
            "SELECT date_str AS 日期, question AS 问题, answer AS 参考, "
            "note AS 备注, mastery AS 掌握度, review_count AS 复习次数, "
            "tags AS 标签, attribution AS 归因, next_review, "
            "ease_factor, review_interval AS `interval`, repetitions "
            "FROM review_book WHERE username = %s AND next_review <= %s"
        )
        df = db.query_df(sql, (username, today_str))
        if df.empty:
            return pd.DataFrame(columns=REVIEW_COLUMNS)
        return df
    except Exception:
        return pd.DataFrame(columns=REVIEW_COLUMNS)


def get_attribution_stats() -> dict:
    df = _read_review_file()
    if df.empty or "归因" not in df.columns:
        return {}
    counts = df["归因"].replace("", "未分类").value_counts().to_dict()
    return counts


def update_attribution(question: str, attribution: str):
    username = _get_username()
    if not username:
        return
    try:
        db.execute(
            "UPDATE review_book SET attribution = %s WHERE username = %s AND question = %s",
            (attribution, username, question),
        )
    except Exception as e:
        print(f"[ReviewManager] update_attribution 失败: {e}")
