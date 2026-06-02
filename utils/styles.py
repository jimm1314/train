"""
全局 CSS 样式模块
集中管理所有自定义样式，自动适配亮色/暗色主题。
"""
import streamlit as st


def inject_global_styles():
    """注入全局 CSS 样式到 Streamlit 页面，自动适配暗色主题"""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


GLOBAL_CSS = """
<style>
    /* ========== 题目卡片（亮色） ========== */
    .question-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e3a8a;
        line-height: 1.6;
        margin-bottom: 8px;
    }

    /* ========== 笔记盒子 ========== */
    .note-box {
        background-color: #f0f2f6;
        color: #1f1f1f;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        margin: 10px 0;
    }

    /* ========== 历史记录标题 ========== */
    .history-header {
        color: #ff4b4b;
        font-size: 1.4rem;
        font-weight: bold;
        margin-top: 40px;
        border-bottom: 2px solid #ff4b4b;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }

    /* ========== 难度标签 ========== */
    .difficulty-easy {
        background-color: #dcfce7;
        color: #166534;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .difficulty-medium {
        background-color: #fef9c3;
        color: #854d0e;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .difficulty-hard {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* ========== 知识点标签 ========== */
    .knowledge-tag {
        background-color: #dbeafe;
        color: #1e40af;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-right: 6px;
    }

    /* ========== 统计卡片 ========== */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 16px;
    }
    .stat-card-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .stat-card-label {
        font-size: 0.9rem;
        opacity: 0.85;
    }

    /* ========== 分页导航 ========== */
    .pagination-info {
        text-align: center;
        color: #6b7280;
        font-size: 0.9rem;
        margin: 10px 0;
    }

    /* ========== 掌握度星星 ========== */
    .mastery-stars {
        color: #f59e0b;
        font-size: 1rem;
        letter-spacing: 2px;
    }

    /* ========== 连续学习天数 ========== */
    .streak-badge {
        display: inline-block;
        background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    /* ========== 暗色主题适配 ========== */
    [data-theme="dark"] .question-title {
        color: #93c5fd;
    }
    [data-theme="dark"] .note-box {
        background-color: #1e293b;
        color: #e2e8f0;
    }
    [data-theme="dark"] .knowledge-tag {
        background-color: #1e3a5f;
        color: #93c5fd;
    }
    [data-theme="dark"] .difficulty-easy {
        background-color: #14532d;
        color: #86efac;
    }
    [data-theme="dark"] .difficulty-medium {
        background-color: #713f12;
        color: #fde047;
    }
    [data-theme="dark"] .difficulty-hard {
        background-color: #7f1d1d;
        color: #fca5a5;
    }
    [data-theme="dark"] .pagination-info {
        color: #9ca3af;
    }
</style>
"""


def render_difficulty_tag(difficulty: str) -> str:
    """渲染难度标签的 HTML"""
    class_map = {
        "简单": "difficulty-easy",
        "中等": "difficulty-medium",
        "困难": "difficulty-hard",
    }
    css_class = class_map.get(difficulty, "difficulty-medium")
    return f'<span class="{css_class}">{difficulty}</span>'


def render_knowledge_tag(tag: str) -> str:
    """渲染知识点标签的 HTML"""
    return f'<span class="knowledge-tag">{tag}</span>'


def render_mastery_stars(level: int) -> str:
    """渲染掌握度星星（1-5）"""
    level = max(0, min(5, level))
    filled = "★" * level
    empty = "☆" * (5 - level)
    return f'<span class="mastery-stars">{filled}{empty}</span>'
