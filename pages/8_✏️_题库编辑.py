"""
题库编辑器页面
在线管理题库：添加、编辑、删除题目。
"""
import streamlit as st

st.set_page_config(page_title="题库编辑", page_icon="✏️", layout="wide")

import os
import pandas as pd
from utils.session_state import init_session_state
from utils.styles import inject_global_styles
from utils.data_loader import DATA_DIR, load_question_banks
from utils.auth import check_admin

check_admin()
init_session_state()
inject_global_styles()

st.title("✏️ 题库在线编辑器")

st.markdown("""
<div style="background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(16,185,129,0.1));
            border: 1px solid rgba(99,102,241,0.2); border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
    <div style="font-size: 1.1rem; font-weight: 700; color: #e2e8f0; margin-bottom: 0.8rem;">
        ✏️ 题库管理，轻松编辑
    </div>
    <div style="color: #94a3b8; font-size: 0.9rem; line-height: 1.6;">
        <p>📂 <strong>文件管理</strong>：选择题库文件进行编辑</p>
        <p>📝 <strong>在线编辑</strong>：直接在表格中修改题目内容</p>
        <p>➕ <strong>新增题目</strong>：快速添加新题目到题库</p>
        <p>🗑️ <strong>删除题目</strong>：移除不需要的题目</p>
    </div>
</div>
""", unsafe_allow_html=True)

REQUIRED_COLS = ["问题", "参考"]
OPTIONAL_COLS = ["知识点", "难度", "来源", "是否显示"]
ALL_COLS = REQUIRED_COLS + OPTIONAL_COLS


def get_question_files() -> list:
    files = []
    for f in os.listdir(DATA_DIR):
        if f.endswith((".xlsx", ".csv")) and not f.startswith("~"):
            if f not in ("review_book.csv", "study_log.csv", "checkin_log.csv"):
                files.append(f)
    return sorted(files)


def read_file(filepath: str) -> pd.DataFrame:
    try:
        if filepath.endswith(".csv"):
            try:
                df = pd.read_csv(filepath, encoding="utf-8-sig")
            except UnicodeDecodeError:
                df = pd.read_csv(filepath, encoding="gbk")
        else:
            df = pd.read_excel(filepath, engine="calamine")
        rename_map = {}
        if "参考答案" in df.columns:
            rename_map["参考答案"] = "参考"
        if "答案" in df.columns:
            rename_map["答案"] = "参考"
        if rename_map:
            df.rename(columns=rename_map, inplace=True)
        return df
    except Exception as e:
        st.error(f"读取文件失败: {e}")
        return pd.DataFrame()


def save_file(filepath: str, df: pd.DataFrame):
    try:
        if filepath.endswith(".csv"):
            df.to_csv(filepath, index=False, encoding="utf-8-sig")
        else:
            df.to_excel(filepath, index=False, engine="openpyxl")
        load_question_banks.clear()
        return True
    except Exception as e:
        st.error(f"保存失败: {e}")
        return False


files = get_question_files()
if not files:
    st.warning("data/ 目录下没有找到题库文件。请先添加 Excel 或 CSV 文件。")
    st.stop()

st.markdown("### 📂 选择题库文件")
selected_file = st.selectbox("选择要编辑的文件", files, key="editor_file")
filepath = os.path.join(DATA_DIR, selected_file)

st.markdown("---")

df = read_file(filepath)
if df.empty:
    st.error("无法读取该文件或文件为空。")
    st.stop()

for col in REQUIRED_COLS:
    if col not in df.columns:
        df[col] = ""

for col in OPTIONAL_COLS:
    if col not in df.columns:
        default_val = "中等" if col == "难度" else ("未分类" if col == "知识点" else (1 if col == "是否显示" else ""))
        df[col] = default_val

display_cols = [c for c in ALL_COLS if c in df.columns]
df_display = df[display_cols].copy()

st.markdown(f"### 📊 当前题库：`{selected_file}`（共 {len(df)} 题）")

col_info1, col_info2, col_info3 = st.columns(3)
with col_info1:
    if "知识点" in df.columns:
        st.metric("知识点分类", f"{df['知识点'].nunique()} 个")
with col_info2:
    if "难度" in df.columns:
        st.metric("难度分布", f"简单 {len(df[df['难度']=='简单'])} / 中等 {len(df[df['难度']=='中等'])} / 困难 {len(df[df['难度']=='困难'])}")
with col_info3:
    st.metric("文件大小", f"{os.path.getsize(filepath) / 1024:.1f} KB")

st.markdown("---")

tab_edit, tab_add, tab_delete = st.tabs(["📝 编辑题目", "➕ 新增题目", "🗑️ 删除题目"])

with tab_edit:
    st.markdown("直接在下方表格中修改题目内容，修改完成后点击「保存更改」按钮。")

    edited_df = st.data_editor(
        df_display,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "问题": st.column_config.TextColumn("问题", required=True, width="large"),
            "参考": st.column_config.TextColumn("参考答案", required=True, width="large"),
            "知识点": st.column_config.TextColumn("知识点", width="medium"),
            "难度": st.column_config.SelectboxColumn("难度", options=["简单", "中等", "困难"], required=True),
            "来源": st.column_config.TextColumn("来源", width="small"),
            "是否显示": st.column_config.NumberColumn("显示", min_value=0, max_value=1, step=1, default=1),
        },
        key="editor_table",
    )

    if st.button("💾 保存更改", type="primary", use_container_width=True):
        save_df = edited_df.copy()
        for col in REQUIRED_COLS:
            if col in save_df.columns:
                save_df = save_df.dropna(subset=[col])
                save_df = save_df[save_df[col].astype(str).str.strip() != ""]

        if save_df.empty:
            st.error("保存失败：至少需要保留一道包含「问题」和「参考」的题目。")
        else:
            if save_file(filepath, save_df):
                st.success(f"✅ 保存成功！共 {len(save_df)} 道题目。")
                st.rerun()

with tab_add:
    st.markdown("填写新题目信息，点击「添加」按钮将其加入题库。")

    with st.form("add_question_form", clear_on_submit=True):
        new_question = st.text_area("📝 题目内容", height=100, placeholder="请输入题目...")
        new_answer = st.text_area("✅ 参考答案", height=120, placeholder="请输入参考答案...")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            new_category = st.text_input("📋 知识点", placeholder="如：网络、数据库...")
        with col_b:
            new_difficulty = st.selectbox("🎯 难度", ["简单", "中等", "困难"], index=1)
        with col_c:
            new_source = st.text_input("📂 来源", placeholder="选填")

        submitted = st.form_submit_button("➕ 添加题目", type="primary", use_container_width=True)

        if submitted:
            if not new_question.strip():
                st.error("题目内容不能为空！")
            elif not new_answer.strip():
                st.error("参考答案不能为空！")
            else:
                new_row = {
                    "问题": new_question.strip(),
                    "参考": new_answer.strip(),
                    "知识点": new_category.strip() if new_category.strip() else "未分类",
                    "难度": new_difficulty,
                    "来源": new_source.strip(),
                    "是否显示": 1,
                }
                updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                if save_file(filepath, updated_df):
                    st.success(f"✅ 新题目已添加！当前共 {len(updated_df)} 道题。")
                    st.rerun()

    st.markdown("---")
    st.markdown("#### 📤 批量导入")
    uploaded = st.file_uploader("上传 CSV 或 Excel 文件批量导入", type=["csv", "xlsx", "xls"], key="batch_upload")
    if uploaded is not None:
        try:
            if uploaded.name.endswith(".csv"):
                import_df = pd.read_csv(uploaded, encoding="utf-8-sig")
            else:
                import_df = pd.read_excel(uploaded, engine="calamine")

            rename_map = {}
            if "参考答案" in import_df.columns:
                rename_map["参考答案"] = "参考"
            if "答案" in import_df.columns:
                rename_map["答案"] = "参考"
            if rename_map:
                import_df.rename(columns=rename_map, inplace=True)

            if "问题" not in import_df.columns or "参考" not in import_df.columns:
                st.error("文件必须包含「问题」和「参考」列！")
            else:
                st.success(f"解析成功！共 {len(import_df)} 道题。预览：")
                st.dataframe(import_df.head(5), use_container_width=True, hide_index=True)

                if st.button("✅ 确认导入", type="primary"):
                    for col in OPTIONAL_COLS:
                        if col not in import_df.columns:
                            import_df[col] = "中等" if col == "难度" else ("未分类" if col == "知识点" else (1 if col == "是否显示" else ""))
                    merged = pd.concat([df, import_df[display_cols]], ignore_index=True)
                    merged = merged.drop_duplicates(subset=["问题"], keep="last")
                    if save_file(filepath, merged):
                        st.success(f"✅ 导入完成！当前共 {len(merged)} 道题。")
                        st.rerun()
        except Exception as e:
            st.error(f"文件解析失败: {e}")

with tab_delete:
    st.markdown("⚠️ 删除操作不可恢复，请谨慎操作。")

    if "知识点" in df.columns:
        cats = ["全部"] + sorted(df["知识点"].dropna().unique().tolist())
        del_cat = st.selectbox("按知识点筛选", cats, key="del_cat")
    else:
        del_cat = "全部"

    if del_cat != "全部":
        del_df = df[df["知识点"] == del_cat].copy()
    else:
        del_df = df.copy()

    st.markdown(f"当前筛选结果：**{len(del_df)}** 道题目")

    if not del_df.empty:
        questions_to_delete = st.multiselect(
            "选择要删除的题目",
            options=del_df["问题"].tolist(),
            format_func=lambda x: x[:80] + ("..." if len(x) > 80 else ""),
            key="del_select",
        )

        if questions_to_delete:
            st.warning(f"即将删除 {len(questions_to_delete)} 道题目，此操作不可恢复！")
            if st.button(f"🗑️ 确认删除 {len(questions_to_delete)} 道题", type="primary"):
                updated_df = df[~df["问题"].isin(questions_to_delete)].copy()
                if save_file(filepath, updated_df):
                    st.success(f"✅ 已删除 {len(questions_to_delete)} 道题。剩余 {len(updated_df)} 道。")
                    st.rerun()
