"""
数据加载模块
负责从数据库（TiDB/MySQL/SQLite）读取题库数据。
不可用时 fallback 到本地 Excel/CSV 文件。
"""
import os
import glob
import pandas as pd
import streamlit as st
from utils import db

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def get_user_data_dir() -> str:
    username = st.session_state.get("username", "")
    if not username:
        return DATA_DIR
    return os.path.join(DATA_DIR, "users", username)


def ensure_user_data_dir():
    user_dir = get_user_data_dir()
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def get_review_file() -> str:
    return os.path.join(get_user_data_dir(), "review_book.csv")


def get_study_log_file() -> str:
    return os.path.join(get_user_data_dir(), "study_log.csv")


def get_checkin_file() -> str:
    return os.path.join(get_user_data_dir(), "checkin_log.csv")


def get_dictation_file() -> str:
    return os.path.join(get_user_data_dir(), "dictation_log.csv")


def _resolve_data_folder():
    return os.path.abspath(DATA_DIR)


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {}
    if "参考答案" in df.columns:
        rename_map["参考答案"] = "参考"
    if "答案" in df.columns:
        rename_map["答案"] = "参考"
    if rename_map:
        df.rename(columns=rename_map, inplace=True)
    return df


def _read_single_file(filepath: str) -> pd.DataFrame | None:
    try:
        if filepath.endswith(".csv"):
            try:
                df = pd.read_csv(filepath, encoding="utf-8-sig")
            except UnicodeDecodeError:
                df = pd.read_csv(filepath, encoding="gbk")
        else:
            df = pd.read_excel(filepath, engine="calamine")

        df = _normalize_columns(df)
        df["来源文件"] = os.path.basename(filepath)
        return df
    except Exception as e:
        st.warning(f"读取文件 {os.path.basename(filepath)} 时出出错: {e}")
        return None


def _load_from_files() -> pd.DataFrame:
    """从本地文件加载题库（fallback）"""
    data_folder = _resolve_data_folder()
    all_files = glob.glob(os.path.join(data_folder, "*.xlsx")) + \
                glob.glob(os.path.join(data_folder, "*.csv"))
    all_files = [f for f in all_files
                 if os.path.basename(f) not in ("review_book.csv", "study_log.csv",
                                                 "checkin_log.csv", "dictation_log.csv")]

    df_list = []
    for f in all_files:
        result = _read_single_file(f)
        if result is not None:
            df_list.append(result)

    if not df_list:
        return pd.DataFrame()

    df = pd.concat(df_list, ignore_index=True)

    if "问题" not in df.columns or "参考" not in df.columns:
        return pd.DataFrame()

    for col, default in [("知识点", "未分类"), ("难度", "中等"), ("来源", "")]:
        if col not in df.columns:
            df[col] = default

    df = df.dropna(subset=["问题", "参考"])
    df = df.drop_duplicates(subset=["问题"])
    return df


@st.cache_data(ttl=300)
def load_question_banks() -> pd.DataFrame:
    """
    加载所有题库。从数据库读取（MySQL 优先，SQLite 兜底）。
    缓存 5 分钟，避免每次交互都重新读取。
    """
    sql = """SELECT id, question AS 问题, answer AS 参考, 
                    category AS 知识点, difficulty AS 难度, 
                    source AS 来源, is_visible AS 是否显示 
             FROM interview_questions"""
    
    # 尝试 MySQL
    if db.is_mysql():
        try:
            df = db.query_df(sql)
            if not df.empty:
                df["来源文件"] = "database"
                return df
        except Exception:
            pass

    # 尝试 SQLite
    try:
        db.init_tables()
        df = db.query_df(sql)
        if not df.empty:
            df["来源文件"] = "database"
            return df
    except Exception:
        pass

    # 数据库不可用或为空时，回退到本地 Excel/CSV 文件
    return _load_from_files()


def get_filtered_questions(force_show_all: bool = False) -> pd.DataFrame:
    df = load_question_banks()
    if df.empty:
        return df

    if not force_show_all and "是否显示" in df.columns:
        df = df.copy()
        df["是否显示"] = pd.to_numeric(df["是否显示"], errors="coerce").fillna(1)
        df = df[df["是否显示"] == 1]

    return df


def get_knowledge_categories(df: pd.DataFrame) -> list[str]:
    """获取所有知识点分类（从数据库的category字段）"""
    if df.empty or "知识点" not in df.columns:
        return []
    return sorted(df["知识点"].dropna().unique().tolist())


def get_difficulty_levels() -> list[str]:
    return ["简单", "中等", "困难"]


def get_categories_from_db() -> list[str]:
    """直接从数据库获取所有分类（不依赖DataFrame）"""
    try:
        db.init_tables()
        rows = db.execute("SELECT DISTINCT category FROM interview_questions ORDER BY category", fetch=True)
        return [r["category"] for r in rows] if rows else []
    except Exception:
        return []
