"""
错题本管理模块
负责错题的增删改查、掌握度更新、复习次数记录、签到系统、学习日志。
"""
import os
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

from utils.data_loader import REVIEW_FILE, STUDY_LOG_FILE, CHECKIN_FILE, load_question_banks


def _read_review_file() -> pd.DataFrame:
    """读取错题本，不存在则返回空 DataFrame"""
    if os.path.exists(REVIEW_FILE):
        df = pd.read_csv(REVIEW_FILE, encoding="utf-8-sig")
        for old, new in [("参考答案", "参考"), ("答案", "参考")]:
            if old in df.columns:
                df.rename(columns={old: new}, inplace=True)
        return df
    return pd.DataFrame(columns=["日期", "问题", "参考", "备注", "掌握度", "复习次数", "标签"])


def _write_review_file(df: pd.DataFrame):
    """写入错题本并清除缓存（带错误处理）"""
    try:
        df.to_csv(REVIEW_FILE, index=False, encoding="utf-8-sig")
        load_question_banks.clear()
    except PermissionError:
        st.error("文件被占用，请关闭其他打开此文件的程序后重试。")
    except Exception as e:
        st.error(f"保存失败: {e}")


def save_to_review_book(question: str, answer: str, note: str = "",
                        mastery: int = 0, tags: str = ""):
    """保存一道题到错题本。如果已存在则更新。"""
    mastery = max(0, min(5, int(mastery)))
    today_str = datetime.now().strftime("%Y-%m-%d")
    new_row = {
        "日期": today_str,
        "问题": question,
        "参考": answer,
        "备注": note,
        "掌握度": mastery,
        "复习次数": 0,
        "标签": tags,
    }

    df = _read_review_file()
    if not df.empty:
        df = df[df["问题"] != question]

    new_df = pd.DataFrame([new_row])
    updated = pd.concat([df, new_df], ignore_index=True)
    _write_review_file(updated)


def delete_from_review_book(question: str):
    """从错题本中删除指定题目"""
    df = _read_review_file()
    if df.empty:
        return
    df = df[df["问题"] != question]
    _write_review_file(df)


def update_mastery(question: str, mastery: int):
    """更新指定题目的掌握度（1-5），带范围校验"""
    mastery = max(0, min(5, int(mastery)))
    df = _read_review_file()
    if df.empty:
        return
    mask = df["问题"] == question
    if mask.any():
        df.loc[mask, "掌握度"] = mastery
        _write_review_file(df)


def update_note(question: str, note: str):
    """更新指定题目的备注"""
    df = _read_review_file()
    if df.empty:
        return
    mask = df["问题"] == question
    if mask.any():
        df.loc[mask, "备注"] = note
        _write_review_file(df)


def increment_review_count(question: str):
    """复习次数 +1"""
    df = _read_review_file()
    if df.empty:
        return
    mask = df["问题"] == question
    if mask.any():
        df.loc[mask, "复习次数"] = df.loc[mask, "复习次数"].fillna(0).astype(int) + 1
        _write_review_file(df)


def get_review_stats() -> dict:
    """返回错题本统计信息"""
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
# 签到系统
# ==========================================

def _read_checkin() -> pd.DataFrame:
    """读取签到记录"""
    if os.path.exists(CHECKIN_FILE):
        return pd.read_csv(CHECKIN_FILE, encoding="utf-8-sig")
    return pd.DataFrame(columns=["日期", "签到时间", "活动类型"])


def _write_checkin(df: pd.DataFrame):
    """写入签到记录"""
    try:
        df.to_csv(CHECKIN_FILE, index=False, encoding="utf-8-sig")
    except Exception:
        pass


def check_in(activity_type: str = "学习"):
    """
    记录一次签到。同一天可以多次签到（记录不同活动）。
    activity_type: "抽题" / "背题" / "错题复习" / "默写" / "签到"
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M:%S")

    df = _read_checkin()

    # 检查今天是否已经有同类型活动
    today_records = df[(df["日期"] == today_str) & (df["活动类型"] == activity_type)]
    if not today_records.empty:
        return  # 今天已经签到过这种活动了

    new_row = pd.DataFrame([{
        "日期": today_str,
        "签到时间": now_time,
        "活动类型": activity_type,
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    _write_checkin(df)


def get_checkin_stats() -> dict:
    """
    返回签到统计：
    - total_days: 总签到天数
    - streak: 连续签到天数（从今天往前）
    - this_month_days: 本月签到天数
    - checkin_dates: 所有签到日期列表（用于日历）
    - today_checked: 今天是否已签到
    """
    df = _read_checkin()
    if df.empty:
        return {
            "total_days": 0, "streak": 0, "this_month_days": 0,
            "checkin_dates": [], "today_checked": False,
        }

    # 所有唯一签到日期
    all_dates = sorted(df["日期"].dropna().unique().tolist())
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 连续签到天数
    streak = 0
    check_date = datetime.now().date()
    for d in reversed(all_dates):
        d_date = datetime.strptime(d, "%Y-%m-%d").date()
        if d_date == check_date:
            streak += 1
            check_date -= timedelta(days=1)
        elif d_date < check_date:
            break

    # 本月签到天数
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
# 学习日志管理
# ==========================================

def log_study_session(count: int, activity: str = "抽题",
                      categories: dict[str, int] | None = None):
    """
    记录一次学习会话到 study_log.csv
    activity: "抽题" / "背题" / "错题复习" / "默写"
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    new_row = {"日期": today_str, "刷题数": count, "活动类型": activity}

    if categories:
        for cat, cnt in categories.items():
            new_row[f"cat_{cat}"] = cnt

    if os.path.exists(STUDY_LOG_FILE):
        df = pd.read_csv(STUDY_LOG_FILE, encoding="utf-8-sig")
        # 兼容旧数据：没有活动类型列就加上
        if "活动类型" not in df.columns:
            df["活动类型"] = "抽题"
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        df = pd.DataFrame([new_row])

    df.to_csv(STUDY_LOG_FILE, index=False, encoding="utf-8-sig")

    # 同时记录签到
    check_in(activity)


def load_study_log() -> pd.DataFrame:
    """加载学习日志"""
    if os.path.exists(STUDY_LOG_FILE):
        df = pd.read_csv(STUDY_LOG_FILE, encoding="utf-8-sig")
        if "活动类型" not in df.columns:
            df["活动类型"] = "抽题"
        return df
    return pd.DataFrame(columns=["日期", "刷题数", "活动类型"])
