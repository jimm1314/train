"""
错题本管理模块
负责错题的增删改查、掌握度更新、复习次数记录、签到系统、学习日志。
"""
import os
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

from utils.data_loader import (
    get_review_file, get_study_log_file, get_checkin_file,
    ensure_user_data_dir, load_question_banks,
)

REVIEW_COLUMNS = ["日期", "问题", "参考", "备注", "掌握度", "复习次数", "标签",
                  "归因", "next_review", "ease_factor", "interval", "repetitions"]

ATTRIBUTION_OPTIONS = ["知识盲区", "理解偏差", "表达问题", "粗心大意", "其他"]


def sm2(quality: int, repetitions: int, ease_factor: float, interval: int) -> tuple:
    """
    SM-2 间隔重复算法
    quality: 0-5 (掌握度评分)
    返回: (new_repetitions, new_ease_factor, new_interval)
    """
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


def _read_review_file() -> pd.DataFrame:
    """读取错题本，不存在则返回空 DataFrame。自动补全新列以保持向后兼容。"""
    review_file = get_review_file()
    today_str = datetime.now().strftime("%Y-%m-%d")

    if os.path.exists(review_file):
        df = pd.read_csv(review_file, encoding="utf-8-sig")
        for old, new in [("参考答案", "参考"), ("答案", "参考")]:
            if old in df.columns:
                df.rename(columns={old: new}, inplace=True)
    else:
        df = pd.DataFrame(columns=REVIEW_COLUMNS)

    new_col_defaults = {
        "归因": "",
        "next_review": today_str,
        "ease_factor": 2.5,
        "interval": 1,
        "repetitions": 0,
    }
    for col, default in new_col_defaults.items():
        if col not in df.columns:
            df[col] = default

    return df


def _write_review_file(df: pd.DataFrame):
    """写入错题本并清除缓存（带错误处理）"""
    try:
        ensure_user_data_dir()
        df.to_csv(get_review_file(), index=False, encoding="utf-8-sig")
        load_question_banks.clear()
    except PermissionError:
        st.error("文件被占用，请关闭其他打开此文件的程序后重试。")
    except Exception as e:
        st.error(f"保存失败: {e}")


def save_to_review_book(question: str, answer: str, note: str = "",
                        mastery: int = 0, tags: str = "",
                        attribution: str = ""):
    """保存一道题到错题本。如果已存在则更新。SM-2 字段自动初始化。"""
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
        "归因": attribution,
        "next_review": today_str,
        "ease_factor": 2.5,
        "interval": 1,
        "repetitions": 0,
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
    checkin_file = get_checkin_file()
    if os.path.exists(checkin_file):
        return pd.read_csv(checkin_file, encoding="utf-8-sig")
    return pd.DataFrame(columns=["日期", "签到时间", "活动类型"])


def _write_checkin(df: pd.DataFrame):
    """写入签到记录"""
    try:
        ensure_user_data_dir()
        df.to_csv(get_checkin_file(), index=False, encoding="utf-8-sig")
    except PermissionError:
        st.error("签到文件被占用，请关闭其他打开此文件的程序后重试。")
    except Exception as e:
        st.error(f"签到记录保存失败: {e}")


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

    study_log_file = get_study_log_file()
    if os.path.exists(study_log_file):
        df = pd.read_csv(study_log_file, encoding="utf-8-sig")
        # 兼容旧数据：没有活动类型列就加上
        if "活动类型" not in df.columns:
            df["活动类型"] = "抽题"
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        df = pd.DataFrame([new_row])

    ensure_user_data_dir()
    df.to_csv(study_log_file, index=False, encoding="utf-8-sig")

    # 同时记录签到
    check_in(activity)


def load_study_log() -> pd.DataFrame:
    """加载学习日志"""
    study_log_file = get_study_log_file()
    if os.path.exists(study_log_file):
        df = pd.read_csv(study_log_file, encoding="utf-8-sig")
        if "活动类型" not in df.columns:
            df["活动类型"] = "抽题"
        return df
    return pd.DataFrame(columns=["日期", "刷题数", "活动类型"])


# ==========================================
# SM-2 间隔重复扩展
# ==========================================

def update_sm2_after_review(question: str, quality: int):
    """复习后更新 SM-2 参数和下次复习日期"""
    df = _read_review_file()
    if df.empty:
        return
    mask = df["问题"] == question
    if not mask.any():
        return

    idx = df.index[mask][0]
    cur_rep = int(df.loc[idx, "repetitions"]) if pd.notna(df.loc[idx, "repetitions"]) else 0
    cur_ef = float(df.loc[idx, "ease_factor"]) if pd.notna(df.loc[idx, "ease_factor"]) else 2.5
    cur_iv = int(df.loc[idx, "interval"]) if pd.notna(df.loc[idx, "interval"]) else 1

    new_rep, new_ef, new_iv = sm2(quality, cur_rep, cur_ef, cur_iv)
    next_date = (datetime.now() + timedelta(days=new_iv)).strftime("%Y-%m-%d")

    df.loc[idx, "repetitions"] = new_rep
    df.loc[idx, "ease_factor"] = round(new_ef, 2)
    df.loc[idx, "interval"] = new_iv
    df.loc[idx, "next_review"] = next_date
    _write_review_file(df)


def get_due_reviews() -> pd.DataFrame:
    """获取今日待复习的题目（next_review <= 今天）"""
    df = _read_review_file()
    if df.empty or "next_review" not in df.columns:
        return pd.DataFrame(columns=REVIEW_COLUMNS)
    today_str = datetime.now().strftime("%Y-%m-%d")
    due = df[df["next_review"] <= today_str].copy()
    return due


def get_attribution_stats() -> dict:
    """返回错题归因统计"""
    df = _read_review_file()
    if df.empty or "归因" not in df.columns:
        return {}
    counts = df["归因"].replace("", "未分类").value_counts().to_dict()
    return counts


def update_attribution(question: str, attribution: str):
    """更新指定题目的归因分类"""
    df = _read_review_file()
    if df.empty:
        return
    mask = df["问题"] == question
    if mask.any():
        df.loc[mask, "归因"] = attribution
        _write_review_file(df)
