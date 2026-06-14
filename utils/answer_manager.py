"""
用户历史回答管理模块
负责保存、查询用户的历史回答记录。
"""
import streamlit as st
from utils import db


def _get_username() -> str:
    return st.session_state.get("username", "")


def save_answer(question: str, reference_answer: str, user_answer: str, score: int = 0) -> bool:
    """
    保存用户的回答到数据库。
    每次填写都保存一条新记录（不覆盖旧记录）。
    """
    username = _get_username()
    if not username or not user_answer.strip():
        return False

    try:
        db.init_tables()
        db.execute(
            "INSERT INTO user_answers (username, question, reference_answer, user_answer, score) "
            "VALUES (%s, %s, %s, %s, %s)",
            (username, question, reference_answer, user_answer.strip(), score),
        )
        return True
    except Exception as e:
        print(f"[AnswerManager] save_answer 失败: {e}")
        return False


def get_answer_history(question: str) -> list[dict]:
    """
    获取某道题目的所有历史回答，按时间倒序排列。
    返回: [{"id": 1, "user_answer": "...", "score": 80, "created_at": "2024-01-01 12:00:00"}, ...]
    """
    username = _get_username()
    if not username:
        return []

    try:
        db.init_tables()
        rows = db.execute(
            "SELECT id, user_answer, score, created_at "
            "FROM user_answers "
            "WHERE username = %s AND question = %s "
            "ORDER BY created_at DESC",
            (username, question),
            fetch=True,
        )
        # 格式化时间
        for row in rows:
            if row.get("created_at") and not isinstance(row["created_at"], str):
                row["created_at"] = row["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        return rows
    except Exception as e:
        print(f"[AnswerManager] get_answer_history 失败: {e}")
        return []


def get_latest_answer(question: str) -> str | None:
    """
    获取某道题目的最新一次回答内容。
    """
    history = get_answer_history(question)
    if history:
        return history[0]["user_answer"]
    return None


def get_answer_count(question: str) -> int:
    """
    获取某道题目的回答次数。
    """
    username = _get_username()
    if not username:
        return 0

    try:
        db.init_tables()
        rows = db.execute(
            "SELECT COUNT(*) AS cnt FROM user_answers WHERE username = %s AND question = %s",
            (username, question),
            fetch=True,
        )
        return rows[0]["cnt"] if rows else 0
    except Exception as e:
        print(f"[AnswerManager] get_answer_count 失败: {e}")
        return 0


def get_all_answered_questions() -> list[str]:
    """
    获取当前用户所有回答过的题目列表（去重）。
    """
    username = _get_username()
    if not username:
        return []

    try:
        db.init_tables()
        rows = db.execute(
            "SELECT question FROM user_answers WHERE username = %s GROUP BY question ORDER BY MAX(created_at) DESC",
            (username,),
            fetch=True,
        )
        return [row["question"] for row in rows]
    except Exception as e:
        print(f"[AnswerManager] get_all_answered_questions 失败: {e}")
        return []


def get_total_answers() -> int:
    """
    获取当前用户的总回答次数。
    """
    username = _get_username()
    if not username:
        return 0

    try:
        db.init_tables()
        rows = db.execute(
            "SELECT COUNT(*) AS cnt FROM user_answers WHERE username = %s",
            (username,),
            fetch=True,
        )
        return rows[0]["cnt"] if rows else 0
    except Exception as e:
        print(f"[AnswerManager] get_total_answers 失败: {e}")
        return 0
