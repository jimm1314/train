"""
数据加载模块
负责从 data/ 目录读取所有 Excel/CSV 文件，合并、清洗、返回 DataFrame。
"""
import os
import glob
import pandas as pd
import streamlit as st

# 数据目录：相对于本文件向上一级的 data/ 文件夹
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def get_user_data_dir() -> str:
    """获取当前用户的数据目录路径"""
    username = st.session_state.get("username", "")
    if not username:
        return DATA_DIR
    return os.path.join(DATA_DIR, "users", username)


def ensure_user_data_dir():
    """确保当前用户的数据目录存在"""
    user_dir = get_user_data_dir()
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def get_review_file() -> str:
    """获取当前用户的错题本文件路径"""
    return os.path.join(get_user_data_dir(), "review_book.csv")


def get_study_log_file() -> str:
    """获取当前用户的学习日志文件路径"""
    return os.path.join(get_user_data_dir(), "study_log.csv")


def get_checkin_file() -> str:
    """获取当前用户的签到记录文件路径"""
    return os.path.join(get_user_data_dir(), "checkin_log.csv")


def get_dictation_file() -> str:
    """获取当前用户的默写记录文件路径"""
    return os.path.join(get_user_data_dir(), "dictation_log.csv")


def _resolve_data_folder():
    """解析数据文件夹的绝对路径"""
    return os.path.abspath(DATA_DIR)


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """统一列名：参考答案/答案 → 参考"""
    rename_map = {}
    if "参考答案" in df.columns:
        rename_map["参考答案"] = "参考"
    if "答案" in df.columns:
        rename_map["答案"] = "参考"
    if rename_map:
        df.rename(columns=rename_map, inplace=True)
    return df


def _read_single_file(filepath: str) -> pd.DataFrame | None:
    """读取单个文件，返回 DataFrame 或 None（读取失败时）"""
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
        st.warning(f"读取文件 {os.path.basename(filepath)} 时出错: {e}")
        return None


@st.cache_data(ttl=300)
def load_question_banks() -> pd.DataFrame:
    """
    加载所有题库文件（xlsx/csv），合并返回。
    缓存 5 分钟，避免每次交互都重新读取磁盘。
    """
    data_folder = _resolve_data_folder()
    all_files = glob.glob(os.path.join(data_folder, "*.xlsx")) + \
                glob.glob(os.path.join(data_folder, "*.csv"))

    # 排除 review_book.csv 和 study_log.csv（它们不是题库）
    all_files = [f for f in all_files
                 if os.path.basename(f) not in ("review_book.csv", "study_log.csv")]

    df_list = []
    for f in all_files:
        result = _read_single_file(f)
        if result is not None:
            df_list.append(result)

    if not df_list:
        return pd.DataFrame()

    df = pd.concat(df_list, ignore_index=True)

    # 确保必要列存在
    if "问题" not in df.columns or "参考" not in df.columns:
        st.error("表格中必须包含『问题』和『参考』两列！")
        return pd.DataFrame()

    # 填充可选列的默认值
    for col, default in [("知识点", "未分类"), ("难度", "中等"), ("来源", "")]:
        if col not in df.columns:
            df[col] = default

    # 清洗
    df = df.dropna(subset=["问题", "参考"])
    df = df.drop_duplicates(subset=["问题"])

    return df


def get_filtered_questions(force_show_all: bool = False) -> pd.DataFrame:
    """
    获取题目数据，可选是否强制显示全部（忽略「是否显示」列）。
    """
    df = load_question_banks()
    if df.empty:
        return df

    if not force_show_all and "是否显示" in df.columns:
        df = df.copy()
        df["是否显示"] = pd.to_numeric(df["是否显示"], errors="coerce").fillna(1)
        df = df[df["是否显示"] == 1]

    return df


def get_knowledge_categories(df: pd.DataFrame) -> list[str]:
    """获取所有知识点分类列表"""
    if df.empty or "知识点" not in df.columns:
        return []
    return sorted(df["知识点"].dropna().unique().tolist())


def get_difficulty_levels() -> list[str]:
    """返回难度等级列表"""
    return ["简单", "中等", "困难"]
