"""
题库编辑器页面
在线管理题库：添加、编辑、删除题目。
"""
import streamlit as st

try:
    st.set_page_config(page_title="题库编辑", page_icon="✏️", layout="wide")
except Exception:
    pass

import pandas as pd
from utils.session_state import init_session_state
from utils.styles import inject_global_styles
from utils.data_loader import load_question_banks
from utils import db
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
        <p>📂 <strong>分类管理</strong>：按题目大类（机器学习、深度学习、NLP等）管理</p>
        <p>📝 <strong>在线编辑</strong>：直接在表格中修改题目内容</p>
        <p>➕ <strong>新增题目</strong>：快速添加新题目到题库</p>
        <p>🗑️ <strong>删除题目</strong>：安全地移除不需要的题目（按ID精确删除）</p>
    </div>
</div>
""", unsafe_allow_html=True)

REQUIRED_COLS = ["问题", "参考"]
OPTIONAL_COLS = ["知识点", "难度", "来源", "是否显示"]
ALL_COLS = REQUIRED_COLS + OPTIONAL_COLS

# ==========================================
# 辅助函数
# ==========================================

def get_question_categories() -> list:
    """获取所有题目分类"""
    try:
        db.init_tables()
        rows = db.execute("SELECT DISTINCT category FROM interview_questions ORDER BY category", fetch=True)
        return [r["category"] for r in rows] if rows else []
    except Exception as e:
        st.error(f"获取分类失败: {e}")
        return []


def read_from_db(category: str) -> pd.DataFrame:
    """根据分类读取题目（包含id字段）"""
    try:
        db.init_tables()
        sql = "SELECT id, question AS 问题, answer AS 参考, category AS 知识点, difficulty AS 难度, source AS 来源, is_visible AS 是否显示 FROM interview_questions WHERE category = %s"
        df = db.query_df(sql, (category,))
        if df.empty:
            return pd.DataFrame()
        return df
    except Exception as e:
        st.error(f"读取题目失败: {e}")
        return pd.DataFrame()


def save_single_question(question: str, answer: str, category: str,
                         difficulty: str = "中等", source: str = "", is_visible: int = 1):
    """安全添加单道题目（INSERT）"""
    try:
        db.execute(
            "INSERT INTO interview_questions (question, answer, category, difficulty, source, is_visible) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (question, answer, category, difficulty, source, is_visible),
        )
        load_question_banks.clear()
        return True
    except Exception as e:
        st.error(f"添加题目失败: {e}")
        return False


def update_single_question(qid: int, question: str, answer: str, category: str,
                           difficulty: str = "中等", source: str = "", is_visible: int = 1):
    """安全更新单道题目（UPDATE by ID）"""
    try:
        db.execute(
            "UPDATE interview_questions SET question=%s, answer=%s, category=%s, "
            "difficulty=%s, source=%s, is_visible=%s WHERE id=%s",
            (question, answer, category, difficulty, source, is_visible, qid),
        )
        return True
    except Exception as e:
        st.error(f"更新题目 ID={qid} 失败: {e}")
        return False


def save_to_db_safe(category: str, df: pd.DataFrame):
    """
    安全保存题目到数据库（事务保护）。
    - 有 id 的题目 → UPDATE
    - 无 id 的新题目 → INSERT
    - 删除的题目（数据库有但 df 没有）→ DELETE
    全部在同一事务中完成。
    """
    try:
        # 1. 查询当前数据库中该分类的所有题目id
        existing = db.execute(
            "SELECT id FROM interview_questions WHERE category = %s", (category,), fetch=True
        )
        existing_ids = {r["id"] for r in existing} if existing else set()
        df_ids = set()
        if "id" in df.columns:
            df_ids = set(df["id"].dropna().astype(int).tolist())

        operations = []

        # 2. 删除 df 中不存在的题目
        ids_to_delete = existing_ids - df_ids
        for qid in ids_to_delete:
            operations.append(("DELETE FROM interview_questions WHERE id = %s", (qid,)))

        # 3. 更新或插入
        for _, row in df.iterrows():
            q = str(row.get("问题", "")).strip()
            a = str(row.get("参考", "")).strip()
            if not q:
                continue
            d = str(row.get("难度", "中等"))
            s = str(row.get("来源", ""))
            vis = int(row.get("是否显示", 1)) if pd.notna(row.get("是否显示", 1)) else 1
            qid = int(row["id"]) if "id" in df.columns and pd.notna(row.get("id")) else None

            if qid and qid in existing_ids:
                # UPDATE 现有题目
                operations.append((
                    "UPDATE interview_questions SET question=%s, answer=%s, category=%s, "
                    "difficulty=%s, source=%s, is_visible=%s WHERE id=%s",
                    (q, a, category, d, s, vis, qid),
                ))
            else:
                # INSERT 新题目
                operations.append((
                    "INSERT INTO interview_questions (question, answer, category, difficulty, source, is_visible) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (q, a, category, d, s, vis),
                ))

        if operations:
            db.execute_transaction(operations)

        load_question_banks.clear()
        return True
    except Exception as e:
        st.error(f"保存失败: {e}")
        return False


# ==========================================
# 刷新按钮
# ==========================================
col_title, col_refresh = st.columns([5, 1])
with col_refresh:
    if st.button("🔄 刷新数据", use_container_width=True):
        load_question_banks.clear()
        st.rerun()

# ==========================================
# 分类选择
# ==========================================
categories = get_question_categories()
if not categories:
    db.init_tables()
    categories = get_question_categories()
if not categories:
    st.warning("数据库中暂无题库数据。请先导入题库。")
    st.stop()

st.markdown("### 📂 选择题目分类")
selected_category = st.selectbox("选择要编辑的题目分类", categories, key="editor_category")

st.markdown("---")

df = read_from_db(selected_category)
if df.empty:
    st.error("无法读取该分类或该分类下没有题目。")
    st.stop()

for col in REQUIRED_COLS:
    if col not in df.columns:
        df[col] = ""

for col in OPTIONAL_COLS:
    if col not in df.columns:
        default_val = "中等" if col == "难度" else ("未分类" if col == "知识点" else (1 if col == "是否显示" else ""))
        df[col] = default_val

display_cols = ["id"] + [c for c in ALL_COLS if c in df.columns]
df_display = df[display_cols].copy()

# ==========================================
# 统计信息
# ==========================================
st.markdown(f"### 📊 当前分类：`{selected_category}`（共 {len(df)} 题）")

col_info1, col_info2, col_info3 = st.columns(3)
with col_info1:
    if "难度" in df.columns:
        st.metric("难度分布", f"简单 {len(df[df['难度']=='简单'])} / 中等 {len(df[df['难度']=='中等'])} / 困难 {len(df[df['难度']=='困难'])}")
with col_info2:
    if "来源" in df.columns:
        st.metric("来源分布", f"{df['来源'].nunique()} 个来源")
with col_info3:
    if "是否显示" in df.columns:
        visible_count = len(df[df["是否显示"] == 1])
        hidden_count = len(df) - visible_count
        st.metric("可见性", f"显示 {visible_count} / 隐藏 {hidden_count}")

st.markdown("---")

# ==========================================
# 三个Tab：编辑、新增、删除
# ==========================================
tab_edit, tab_add, tab_delete = st.tabs(["📝 编辑题目", "➕ 新增题目", "🗑️ 删除题目"])

# ==========================================
# Tab 1: 编辑题目（带分页和搜索）
# ==========================================
with tab_edit:
    st.markdown("直接在下方表格中修改题目内容，修改完成后点击「保存更改」按钮。")

    # 搜索功能
    search_col1, search_col2, search_col3 = st.columns([3, 1, 1])
    with search_col1:
        search_keyword = st.text_input("🔍 搜索题目或答案", placeholder="输入关键词搜索...", key="edit_search")
    with search_col2:
        if "难度" in df.columns:
            filter_diff = st.selectbox("按难度筛选", ["全部"] + sorted(df["难度"].dropna().unique().tolist()), key="edit_diff_filter")
        else:
            filter_diff = "全部"
    with search_col3:
        if "是否显示" in df.columns:
            filter_vis = st.selectbox("按显示筛选", ["全部", "仅显示", "仅隐藏"], key="edit_vis_filter")
        else:
            filter_vis = "全部"

    # 应用筛选
    filtered_df = df.copy()
    if search_keyword:
        kw = search_keyword.lower()
        mask = (
            filtered_df["问题"].astype(str).str.lower().str.contains(kw, na=False) |
            filtered_df["参考"].astype(str).str.lower().str.contains(kw, na=False)
        )
        filtered_df = filtered_df[mask]
    if filter_diff != "全部":
        filtered_df = filtered_df[filtered_df["难度"] == filter_diff]
    if filter_vis == "仅显示":
        filtered_df = filtered_df[filtered_df["是否显示"] == 1]
    elif filter_vis == "仅隐藏":
        filtered_df = filtered_df[filtered_df["是否显示"] != 1]

    # 分页功能
    PAGE_SIZE = 20
    total_filtered = len(filtered_df)
    total_pages = max(1, (total_filtered + PAGE_SIZE - 1) // PAGE_SIZE)

    if "edit_page" not in st.session_state:
        st.session_state.edit_page = 1

    page_col1, page_col2, page_col3 = st.columns([1, 2, 1])
    with page_col1:
        if st.button("⬅️ 上一页", disabled=(st.session_state.edit_page <= 1), key="prev_page"):
            st.session_state.edit_page -= 1
            st.rerun()
    with page_col2:
        page_num = st.number_input(
            f"页码 (共 {total_pages} 页，共 {total_filtered} 题)",
            min_value=1, max_value=total_pages, value=st.session_state.edit_page, key="page_input"
        )
        st.session_state.edit_page = page_num
    with page_col3:
        if st.button("下一页 ➡️", disabled=(st.session_state.edit_page >= total_pages), key="next_page"):
            st.session_state.edit_page += 1
            st.rerun()

    # 切片当前页
    start_idx = (st.session_state.edit_page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_df = filtered_df.iloc[start_idx:end_idx].copy()
    page_display = page_df[display_cols].copy()

    # 编辑表格
    edited_df = st.data_editor(
        page_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "问题": st.column_config.TextColumn("问题", required=True, width="large"),
            "参考": st.column_config.TextColumn("参考答案", required=True, width="large"),
            "知识点": st.column_config.TextColumn("知识点", width="medium"),
            "难度": st.column_config.SelectboxColumn("难度", options=["简单", "中等", "困难"], required=True),
            "来源": st.column_config.TextColumn("来源", width="small"),
            "是否显示": st.column_config.NumberColumn("显示", min_value=0, max_value=1, step=1, default=1),
        },
        key="editor_table",
    )

    if st.button("💾 保存当前页更改", type="primary", use_container_width=True):
        save_df = edited_df.copy()
        for col in REQUIRED_COLS:
            if col in save_df.columns:
                save_df = save_df.dropna(subset=[col])
                save_df = save_df[save_df[col].astype(str).str.strip() != ""]

        if save_df.empty:
            st.error("保存失败：至少需要保留一道包含「问题」和「参考」的题目。")
        else:
            # 将编辑后的数据与未编辑的页合并，然后保存整个分类
            all_other_pages = pd.concat([
                filtered_df.iloc[:start_idx],
                filtered_df.iloc[end_idx:],
            ], ignore_index=True)
            full_df = pd.concat([all_other_pages, save_df], ignore_index=True)

            # 去重：按 id 去重，保留最后出现的（即编辑后的版本）
            if "id" in full_df.columns:
                full_df = full_df.drop_duplicates(subset=["id"], keep="last")

            if save_to_db_safe(selected_category, full_df):
                st.success(f"✅ 保存成功！当前分类共 {len(full_df)} 道题目。")
                st.rerun()

# ==========================================
# Tab 2: 新增题目（支持设置分类和是否显示）
# ==========================================
with tab_add:
    st.markdown("填写新题目信息，点击「添加」按钮将其加入题库。")

    with st.form("add_question_form", clear_on_submit=True):
        new_question = st.text_area("📝 题目内容", height=100, placeholder="请输入题目...")
        new_answer = st.text_area("✅ 参考答案", height=120, placeholder="请输入参考答案...")

        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            new_difficulty = st.selectbox("🎯 难度", ["简单", "中等", "困难"], index=1)
        with col_b:
            new_source = st.text_input("📂 来源", placeholder="选填")
        with col_c:
            new_category = st.selectbox("📂 分类", categories, index=categories.index(selected_category) if selected_category in categories else 0)
        with col_d:
            new_visible = st.selectbox("👁️ 是否显示", [1, 0], format_func=lambda x: "显示" if x == 1 else "隐藏", index=0)

        submitted = st.form_submit_button("➕ 添加题目", type="primary", use_container_width=True)

        if submitted:
            if not new_question.strip():
                st.error("题目内容不能为空！")
            elif not new_answer.strip():
                st.error("参考答案不能为空！")
            else:
                if save_single_question(
                    question=new_question.strip(),
                    answer=new_answer.strip(),
                    category=new_category,
                    difficulty=new_difficulty,
                    source=new_source.strip(),
                    is_visible=new_visible,
                ):
                    st.success(f"✅ 新题目已添加到「{new_category}」分类！")
                    st.rerun()

    st.markdown("---")
    st.markdown("#### 📤 批量导入")
    st.info("💡 提示：文件需包含「问题」列，答案列可为「参考答案」或「参考」。")

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
                # 填充缺失列
                for col in OPTIONAL_COLS:
                    if col not in import_df.columns:
                        if col == "难度":
                            import_df[col] = "中等"
                        elif col == "知识点":
                            import_df[col] = selected_category
                        elif col == "是否显示":
                            import_df[col] = 1
                        else:
                            import_df[col] = ""

                st.success(f"解析成功！共 {len(import_df)} 道题。预览：")
                st.dataframe(import_df.head(5), use_container_width=True, hide_index=True)

                # 导入目标分类选择
                import_category = st.selectbox("导入到分类", categories,
                                                index=categories.index(selected_category) if selected_category in categories else 0,
                                                key="import_category")

                if st.button("✅ 确认导入", type="primary"):
                    # 去重：与现有题目比较
                    existing_df = read_from_db(import_category)
                    if not existing_df.empty:
                        existing_questions = set(existing_df["问题"].astype(str).str.strip().tolist())
                        before_count = len(import_df)
                        import_df = import_df[~import_df["问题"].astype(str).str.strip().isin(existing_questions)]
                        skipped = before_count - len(import_df)
                        if skipped > 0:
                            st.warning(f"跳过 {skipped} 道重复题目。")

                    if import_df.empty:
                        st.warning("没有新题目可导入（全部重复）。")
                    else:
                        # 逐条插入新题目（安全，每条独立操作）
                        success_count = 0
                        fail_count = 0
                        for _, row in import_df.iterrows():
                            q = str(row.get("问题", "")).strip()
                            a = str(row.get("参考", "")).strip()
                            if not q:
                                continue
                            d = str(row.get("难度", "中等"))
                            s = str(row.get("来源", ""))
                            vis = int(row.get("是否显示", 1)) if pd.notna(row.get("是否显示", 1)) else 1
                            try:
                                db.execute(
                                    "INSERT INTO interview_questions (question, answer, category, difficulty, source, is_visible) "
                                    "VALUES (%s, %s, %s, %s, %s, %s)",
                                    (q, a, import_category, d, s, vis),
                                )
                                success_count += 1
                            except Exception as e:
                                print(f"[导入] 失败: {q[:30]}... -> {e}")
                                fail_count += 1

                        load_question_banks.clear()
                        msg = f"✅ 导入完成！成功 {success_count} 道"
                        if fail_count > 0:
                            msg += f"，失败 {fail_count} 道"
                        st.success(msg)
                        st.rerun()
        except Exception as e:
            st.error(f"文件解析失败: {e}")

# ==========================================
# Tab 3: 删除题目（按ID精确删除）
# ==========================================
with tab_delete:
    st.markdown("⚠️ 删除操作不可恢复，请谨慎操作。")

    del_col1, del_col2 = st.columns(2)
    with del_col1:
        if "难度" in df.columns:
            diff_list = ["全部"] + sorted(df["难度"].dropna().unique().tolist())
            del_diff = st.selectbox("按难度筛选", diff_list, key="del_diff")
        else:
            del_diff = "全部"
    with del_col2:
        del_search = st.text_input("🔍 搜索要删除的题目", placeholder="输入关键词...", key="del_search")

    del_df = df.copy()
    if del_diff != "全部":
        del_df = del_df[del_df["难度"] == del_diff]
    if del_search:
        kw = del_search.lower()
        del_df = del_df[del_df["问题"].astype(str).str.lower().str.contains(kw, na=False)]

    st.markdown(f"当前筛选结果：**{len(del_df)}** 道题目")

    if not del_df.empty:
        # 构建显示选项：ID + 题目内容
        del_options = {}
        for _, row in del_df.iterrows():
            qid = int(row["id"])
            q_text = str(row["问题"])
            label = f"[ID:{qid}] {q_text[:60]}{'...' if len(q_text) > 60 else ''}"
            del_options[label] = qid

        selected_labels = st.multiselect(
            "选择要删除的题目（按ID精确匹配）",
            options=list(del_options.keys()),
            key="del_select",
        )

        if selected_labels:
            ids_to_delete = [del_options[label] for label in selected_labels]
            st.warning(f"即将删除 {len(ids_to_delete)} 道题目（ID: {', '.join(map(str, ids_to_delete[:10]))}{'...' if len(ids_to_delete) > 10 else ''}），此操作不可恢复！")
            if st.button(f"🗑️ 确认删除 {len(ids_to_delete)} 道题", type="primary"):
                try:
                    # 使用事务批量删除
                    operations = []
                    for qid in ids_to_delete:
                        operations.append(("DELETE FROM interview_questions WHERE id = %s", (qid,)))
                    db.execute_transaction(operations)
                    load_question_banks.clear()
                    st.success(f"✅ 已删除 {len(ids_to_delete)} 道题。")
                    st.rerun()
                except Exception as e:
                    st.error(f"删除失败: {e}")
