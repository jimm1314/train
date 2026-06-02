"""
Session State 统一管理模块
所有 session_state 的初始化都在这里完成，避免各页面重复代码。
"""
import streamlit as st


def init_session_state():
    """初始化所有 session state 变量（仅在不存在时设置默认值）"""
    defaults = {
        # 抽题模式
        "drawn_questions": [],
        "drawn_answers": [],
        "drawn_meta": [],
        "total_drawn_count": 0,
        "seen_questions": set(),
        "history_log": [],
        "countdown_trigger": 0,
        "last_page": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
