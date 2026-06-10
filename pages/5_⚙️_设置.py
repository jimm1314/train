"""
设置页面
系统配置、数据管理、导入导出。
"""
import streamlit as st

st.set_page_config(page_title="设置", page_icon="⚙️", layout="wide")

import pandas as pd
import os
from datetime import datetime
from utils.session_state import init_session_state
from utils.styles import inject_global_styles
from utils.data_loader import DATA_DIR, _resolve_data_folder, get_review_file, get_study_log_file, get_user_data_dir, load_question_banks
from utils.auth import check_auth, get_current_user
from utils.goal_manager import load_goals, save_goals

check_auth()
init_session_state()
inject_global_styles()

st.title("⚙️ 系统设置")

# ==========================================
# 数据路径信息
# ==========================================
st.markdown("### 📁 数据路径")
data_folder = _resolve_data_folder()
user_data_folder = get_user_data_dir()

st.code(f"题库目录: {data_folder}", language=None)
st.code(f"个人数据: {user_data_folder}", language=None)

if os.path.exists(user_data_folder):
    files = os.listdir(user_data_folder)
    st.markdown(f"个人数据目录下共 **{len(files)}** 个文件：")
    for f in files:
        fpath = os.path.join(user_data_folder, f)
        size = os.path.getsize(fpath)
        size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f} MB"
        st.markdown(f"- 📄 `{f}` ({size_str})")
else:
    st.info("个人数据目录尚未创建，开始使用后会自动生成。")

st.markdown("---")

# ==========================================
# 错题本管理
# ==========================================
st.markdown("### 📝 错题本管理")

review_file = get_review_file()
if os.path.exists(review_file):
    review_df = pd.read_csv(review_file, encoding="utf-8-sig")
    st.metric("错题本条目数", f"{len(review_df)} 条")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📥 导出错题本")
        csv_data = review_df.to_csv(index=False, encoding="utf-8-sig")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="📥 下载错题本 CSV",
            data=csv_data,
            file_name=f"review_book_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        st.markdown("#### 📤 导入错题本")
        uploaded_file = st.file_uploader(
            "上传 CSV 文件",
            type=["csv"],
            help="上传的 CSV 需包含「问题」和「参考」列",
        )
        if uploaded_file is not None:
            try:
                import_df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
                if "问题" in import_df.columns and "参考" in import_df.columns:
                    st.success(f"文件解析成功！共 {len(import_df)} 条记录。")
                    st.dataframe(import_df.head(10), use_container_width=True)

                    if st.button("✅ 确认导入（合并到现有错题本）", use_container_width=True):
                        merged = pd.concat([review_df, import_df], ignore_index=True)
                        merged = merged.drop_duplicates(subset=["问题"], keep="last")
                        merged.to_csv(review_file, index=False, encoding="utf-8-sig")
                        st.success(f"导入完成！当前错题本共 {len(merged)} 条。")
                        st.rerun()
                else:
                    st.error("CSV 文件必须包含「问题」和「参考」两列！")
            except Exception as e:
                st.error(f"文件解析失败: {e}")

    st.markdown("---")

    # 危险操作
    st.markdown("### ⚠️ 危险操作")
    with st.expander("🗑️ 清空错题本（不可恢复）"):
        st.warning("此操作将永久删除所有错题记录，且无法恢复！")
        confirm_text = st.text_input("请输入「确认清空」来执行操作：", key="confirm_clear")
        if st.button("🗑️ 执行清空", type="primary", disabled=(confirm_text != "确认清空")):
            os.remove(review_file)
            load_question_banks.clear()
            st.success("错题本已清空！")
            st.rerun()
else:
    st.info("错题本尚未创建。")

st.markdown("---")

# ==========================================
# 学习记录管理
# ==========================================
st.markdown("### 📊 学习记录管理")
study_log_path = get_study_log_file()

if os.path.exists(study_log_path):
    study_df = pd.read_csv(study_log_path, encoding="utf-8-sig")
    st.metric("学习记录条数", f"{len(study_df)} 条")

    with st.expander("🗑️ 清空学习记录"):
        st.warning("此操作将永久清空所有学习记录，且无法恢复！")
        confirm_log = st.text_input("请输入「确认清空」来执行操作：", key="confirm_clear_log")
        if st.button("🗑️ 执行清空", disabled=(confirm_log != "确认清空"), key="btn_clear_log"):
            os.remove(study_log_path)
            st.success("学习记录已清空！")
            st.rerun()
else:
    st.info("暂无学习记录。")

st.markdown("---")

# ==========================================
# 缓存管理
# ==========================================
st.markdown("### 🔄 缓存管理")
st.markdown("如果数据文件已更新但页面未刷新，可以清除缓存。")

if st.button("🔄 清除所有缓存", use_container_width=True):
    st.cache_data.clear()
    st.success("缓存已清除！页面将重新加载数据。")
    st.rerun()

st.markdown("---")

st.markdown(
    '<div style="margin-bottom: 0.5rem;">'
    '<span style="font-size: 1.05rem; font-weight: 700; color: #e2e8f0;">🎯 学习目标设定</span>'
    '</div>',
    unsafe_allow_html=True,
)

goals = load_goals()

with st.form("goals_form"):
    daily_q = st.number_input("📝 每日刷题目标（道）", min_value=1, max_value=200,
                              value=goals.get("daily_questions", 20))
    weekly_q = st.number_input("📅 每周刷题目标（道）", min_value=1, max_value=1000,
                               value=goals.get("weekly_questions", 100))
    daily_r = st.number_input("🔄 每日复习目标（道）", min_value=0, max_value=100,
                              value=goals.get("daily_review", 5))

    if st.form_submit_button("💾 保存目标", use_container_width=True):
        new_goals = {
            "daily_questions": daily_q,
            "weekly_questions": weekly_q,
            "daily_review": daily_r,
        }
        save_goals(new_goals)
        st.success("✅ 学习目标已更新！")

st.markdown("---")

st.markdown(
    '<div style="margin-bottom: 0.5rem;">'
    '<span style="font-size: 1.05rem; font-weight: 700; color: #e2e8f0;">🤖 AI 评分配置</span>'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown("""
<div style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
    <p style="color: #94a3b8; font-size: 0.85rem; line-height: 1.6; margin: 0;">
        AI 评分功能支持 <strong>MIMO</strong>、<strong>Gemini</strong> 和 <strong>OpenAI</strong> 三种 API。
        默写模式和模拟面试将使用 AI 进行智能评分。
        未配置 API 时自动使用本地文本相似度算法（无需 API 也能使用）。
    </p>
</div>
""", unsafe_allow_html=True)

from utils.ai_scorer import MIMO_API_KEY

has_mimo = bool(MIMO_API_KEY)
has_gemini = bool(os.environ.get("GEMINI_API_KEY"))
has_openai = bool(os.environ.get("OPENAI_API_KEY"))
try:
    if not has_gemini:
        has_gemini = bool(st.secrets.get("GEMINI_API_KEY"))
    if not has_openai:
        has_openai = bool(st.secrets.get("OPENAI_API_KEY"))
except Exception:
    pass

col_ai0, col_ai1, col_ai2 = st.columns(3)
with col_ai0:
    status = "✅ 已配置（默认）" if has_mimo else "❌ 未配置"
    st.markdown(
        f'<div style="background:rgba(168,85,247,0.08);border:1px solid rgba(168,85,247,0.2);'
        f'border-radius:10px;padding:1rem;">'
        f'<div style="font-weight:700;color:#e2e8f0;">MIMO API（首选）</div>'
        f'<div style="color:#94a3b8;font-size:0.85rem;">{status}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
with col_ai1:
    status = "✅ 已配置" if has_gemini else "❌ 未配置"
    st.markdown(
        f'<div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);'
        f'border-radius:10px;padding:1rem;">'
        f'<div style="font-weight:700;color:#e2e8f0;">Gemini API（备选）</div>'
        f'<div style="color:#94a3b8;font-size:0.85rem;">{status}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
with col_ai2:
    status = "✅ 已配置" if has_openai else "❌ 未配置"
    st.markdown(
        f'<div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.2);'
        f'border-radius:10px;padding:1rem;">'
        f'<div style="font-weight:700;color:#e2e8f0;">OpenAI API（备选）</div>'
        f'<div style="color:#94a3b8;font-size:0.85rem;">{status}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown(
    '<div style="color:#64748b;font-size:0.8rem;margin-top:0.5rem;">'
    '评分优先级：MIMO API → Gemini API → OpenAI API → 本地算法。<br>'
    '如需使用其他 API，可在 <code>.streamlit/secrets.toml</code> 或环境变量中配置。</div>',
    unsafe_allow_html=True,
)

st.markdown("---")

# ==========================================
# 关于
# ==========================================
st.markdown("### ℹ️ 关于")
st.markdown("""
**面试题刷题系统 — 专业版 v3.0**

- 🎲 抽题模式：随机抽题，支持知识点/难度筛选
- ✍️ 默写模式：凭记忆默写，支持 AI 评分
- 📖 背题模式：分页浏览，沉浸式背诵
- 📝 错题复习：掌握度评估，归因分析
- 🎤 模拟面试：限时作答，AI 智能评分
- 📊 学习统计：多维度数据分析图表
- ⏰ 间隔重复：SM-2 算法智能安排复习
- 🎯 目标追踪：设定每日/每周学习目标
- ✏️ 题库编辑：在线管理题库
- 🤖 AI 评分：支持 MIMO / Gemini / OpenAI API
- 📱 PWA 支持：可添加到主屏幕

**技术栈：** Streamlit + Pandas + Plotly
""")
