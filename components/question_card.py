"""
题目卡片组件
统一的题目展示组件，支持难度标签、知识点标签、Markdown 渲染。
"""
import html as html_mod
import streamlit as st
import pandas as pd
from utils.styles import render_difficulty_tag, render_knowledge_tag, render_mastery_stars
from utils.review_manager import save_to_review_book, update_mastery, increment_review_count


def safe_format(text) -> str:
    """安全格式化文本，处理 NaN、换行和 HTML 转义（防 XSS）"""
    if pd.isna(text):
        return ""
    return html_mod.escape(str(text)).replace("\n", "\n\n")


def render_question_card(index: int, row: pd.Series, show_tags: bool = True,
                         show_save_button: bool = True, total_key: int = 0):
    """
    渲染一道题目的卡片。

    参数:
        index: 题目序号（从 1 开始）
        row: 包含 问题/参考/知识点/难度 等列的 Series
        show_tags: 是否显示难度和知识点标签
        show_save_button: 是否显示保存到错题本的按钮
        total_key: 用于生成唯一 key 的计数器
    """
    question = row["问题"]
    answer = row["参考"]

    # 标题行：序号 + 难度标签 + 知识点标签
    tag_html = ""
    if show_tags:
        if "难度" in row and pd.notna(row["难度"]):
            tag_html += render_difficulty_tag(str(row["难度"])) + " "
        if "知识点" in row and pd.notna(row["知识点"]) and row["知识点"] != "未分类":
            tag_html += render_knowledge_tag(str(row["知识点"]))

    st.markdown(
        f'<div class="question-title">【第 {index} 题】 {safe_format(question)}</div>'
        f'<div style="margin-bottom: 8px;">{tag_html}</div>',
        unsafe_allow_html=True,
    )

    # 答案区域（折叠）
    with st.expander("💡 点击查看参考答案及做笔记"):
        st.markdown(safe_format(answer))

        if show_save_button:
            st.markdown("---")

            # 掌握度评分
            mastery = st.selectbox(
                "⭐ 掌握度评分",
                options=[1, 2, 3, 4, 5],
                index=2,  # 默认选中"基本掌握"
                format_func=lambda x: ["⭐ 1分 - 完全不会", "⭐⭐ 2分 - 勉强记得",
                                        "⭐⭐⭐ 3分 - 基本掌握", "⭐⭐⭐⭐ 4分 - 熟练", "⭐⭐⭐⭐⭐ 5分 - 完全掌握"][x - 1],
                key=f"mastery_{index}_{total_key}",
            )

            user_note = st.text_area(
                "✍️ 记录我的理解和总结（选填）",
                key=f"note_{index}_{total_key}",
                height=80,
            )

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🚩 保存至错题本", key=f"save_{index}_{total_key}",
                             use_container_width=True):
                    save_to_review_book(
                        question, answer, user_note,
                        mastery=mastery,
                    )
                    st.toast("✅ 已保存至错题本！")
            with col2:
                if st.button("✅ 已掌握，不保存", key=f"skip_{index}_{total_key}",
                             use_container_width=True):
                    st.toast("👍 已跳过，继续保持！")

    st.write("---")


def render_review_card(index: int, row: pd.Series):
    """
    渲染错题复习卡片（包含掌握度显示和复习操作）。
    """
    question = row["问题"]
    answer = row["参考"]

    # 掌握度星星
    mastery = int(row.get("掌握度", 0)) if pd.notna(row.get("掌握度", 0)) else 0
    review_count = int(row.get("复习次数", 0)) if pd.notna(row.get("复习次数", 0)) else 0

    stars_html = render_mastery_stars(mastery)
    st.markdown(
        f'<div class="question-title">📌 {safe_format(question)}</div>'
        f'<div style="margin: 4px 0;">{stars_html} '
        f'<span style="color: #6b7280; font-size: 0.85rem;">已复习 {review_count} 次</span></div>',
        unsafe_allow_html=True,
    )

    # 笔记
    if "备注" in row and pd.notna(row["备注"]) and str(row["备注"]).strip():
        date_str = row.get("日期", "")
        st.markdown(
            f'<div class="note-box">📝 <b>我的总结 ({date_str})：</b><br>'
            f'{safe_format(row["备注"])}</div>',
            unsafe_allow_html=True,
        )

    # 答案 + 操作
    with st.expander("💡 点击查看参考答案"):
        st.markdown(safe_format(answer))
        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            new_mastery = st.selectbox(
                "⭐ 更新掌握度",
                options=[1, 2, 3, 4, 5],
                index=max(0, min(4, int(row.get("掌握度", 3)) - 1)),  # 显示当前掌握度
                format_func=lambda x: ["⭐ 1分 - 完全不会", "⭐⭐ 2分 - 勉强记得",
                                        "⭐⭐⭐ 3分 - 基本掌握", "⭐⭐⭐⭐ 4分 - 熟练", "⭐⭐⭐⭐⭐ 5分 - 完全掌握"][x - 1],
                key=f"review_mastery_{index}",
            )
        with col2:
            if st.button("🔄 标记为已复习", key=f"reviewed_{index}",
                         use_container_width=True):
                increment_review_count(question)
                update_mastery(question, new_mastery)
                st.toast("✅ 复习记录已更新！")
                st.rerun()

    st.write("---")
