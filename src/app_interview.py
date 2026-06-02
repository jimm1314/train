import streamlit as st
import pandas as pd
import glob
import os
import random
from datetime import datetime
import streamlit.components.v1 as components

# ==========================================
# 1. 页面配置 & 样式
# ==========================================
st.set_page_config(page_title="面试题刷题系统", page_icon="📚", layout="wide")

st.markdown("""
<style>
    .note-box {
        background-color: #f0f2f6;
        color: #1f1f1f; 
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .history-header {
        color: #ff4b4b;
        font-size: 1.4rem;
        font-weight: bold;
        margin-top: 40px;
        border-bottom: 2px solid #ff4b4b;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .question-title {
        font-size: 1.1rem;
        font-weight: bold;
        color: #1e3a8a;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 核心变量 & 数据读写
# ==========================================
DATA_FOLDER = r"D:\software\PyCharm 2023.2.5\file_saves\genmini\data"
REVIEW_FILE = os.path.join(DATA_FOLDER, "review_book.csv")


def save_to_review_book(q, a, note):
    today_str = datetime.now().strftime("%Y-%m-%d")
    new_data = pd.DataFrame([{"日期": today_str, "问题": q, "参考": a, "备注": note}])

    if os.path.exists(REVIEW_FILE):
        exist_df = pd.read_csv(REVIEW_FILE, encoding='utf-8-sig')
        exist_df = exist_df[exist_df['问题'] != q]
        updated_df = pd.concat([exist_df, new_data], ignore_index=True)
        updated_df.to_csv(REVIEW_FILE, index=False, encoding='utf-8-sig')
    else:
        new_data.to_csv(REVIEW_FILE, index=False, encoding='utf-8-sig')

    # 🌟 核心修复1：每次保存后强制清除缓存，让页面立刻读取到最新收藏的错题！
    load_data.clear()


@st.cache_data
def load_data(mode, force_load_all=False):
    if mode == "📝 错题复习":
        if os.path.exists(REVIEW_FILE):
            df = pd.read_csv(REVIEW_FILE, encoding='utf-8-sig')
            if '参考答案' in df.columns: df.rename(columns={'参考答案': '参考'}, inplace=True)
            if '答案' in df.columns: df.rename(columns={'答案': '参考'}, inplace=True)
            return df
        return pd.DataFrame()

    all_files = glob.glob(os.path.join(DATA_FOLDER, "*.xlsx")) + glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
    df_list = []

    for file in all_files:
        try:
            if file.endswith('.csv'):
                try:
                    temp_df = pd.read_csv(file, encoding='utf-8-sig')
                except:
                    temp_df = pd.read_csv(file, encoding='gbk')
            else:
                temp_df = pd.read_excel(file, engine='calamine')

            if '参考答案' in temp_df.columns: temp_df.rename(columns={'参考答案': '参考'}, inplace=True)
            if '答案' in temp_df.columns: temp_df.rename(columns={'答案': '参考'}, inplace=True)

            temp_df['来源文件'] = os.path.basename(file)
            df_list.append(temp_df)
        except Exception as e:
            st.warning(f"读取文件 {os.path.basename(file)} 时出错: {e}")

    if not df_list: return pd.DataFrame()
    df = pd.concat(df_list, ignore_index=True)

    if not force_load_all and '是否显示' in df.columns:
        df['是否显示'] = pd.to_numeric(df['是否显示'], errors='coerce').fillna(1)
        df = df[df['是否显示'] == 1]

    if '问题' in df.columns and '参考' in df.columns:
        df = df.dropna(subset=['问题', '参考'])
        df = df.drop_duplicates(subset=['问题'])
    else:
        st.error("表格中必须包含『问题』和『参考』两列！")
        return pd.DataFrame()
    return df


# ==========================================
# 3. 初始化 Session State
# ==========================================
if 'drawn_questions' not in st.session_state: st.session_state.drawn_questions = []
if 'drawn_answers' not in st.session_state: st.session_state.drawn_answers = []
if 'total_drawn_count' not in st.session_state: st.session_state.total_drawn_count = 0
if 'seen_questions' not in st.session_state: st.session_state.seen_questions = set()
if 'history_log' not in st.session_state: st.session_state.history_log = []
if 'countdown_trigger' not in st.session_state: st.session_state.countdown_trigger = 0

# ==========================================
# 4. 侧边栏设计
# ==========================================
with st.sidebar:
    st.title("📚 面试题刷题系统")
    st.markdown("---")

    st.subheader("导航")
    page_mode = st.radio("请选择模式：", ["🏠 抽题模式", "📖 背题模式", "📝 错题复习"], label_visibility="collapsed")
    st.markdown("---")

    st.subheader("⚙️ 详细设置")

    force_load = False
    selected_date = "全部"

    if page_mode == "🏠 抽题模式":
        num_to_draw = st.number_input("每次抽取题目数量", min_value=1, max_value=20, value=3)
        force_load = st.checkbox("强制加载所有题目(无视是否显示)", value=False)

        st.markdown("---")
        st.subheader("⏱️ 倒计时工具")
        timer_minutes = st.number_input("设置答题时间 (分钟)", min_value=1, max_value=60, value=5)
        if st.button("▶️ 启动倒计时", use_container_width=True):
            st.session_state.countdown_trigger += 1

    elif page_mode == "📖 背题模式":
        force_load = True
        st.info("此模式下将直接展示所有题目，方便连续背诵阅读。")

    elif page_mode == "📝 错题复习":
        force_load = True
        if os.path.exists(REVIEW_FILE):
            review_df = pd.read_csv(REVIEW_FILE, encoding='utf-8-sig')
            dates = ["全部"] + sorted(review_df['日期'].dropna().unique().tolist(), reverse=True)
            selected_date = st.selectbox("📅 选择复习日期:", dates)
        else:
            st.warning("尚未生成错题本！")

    if page_mode == "🏠 抽题模式":
        if st.button("♻️ 重置抽题记忆 (重新洗牌)", use_container_width=True):
            st.session_state.seen_questions = set()
            st.session_state.history_log = []
            st.success("洗牌完成！")

# 切换页面时清空抽题状态
if 'last_page' not in st.session_state or st.session_state.last_page != page_mode:
    st.session_state.drawn_questions = []
    st.session_state.drawn_answers = []
    st.session_state.history_log = []
    st.session_state.last_page = page_mode

# 加载数据
df = load_data(page_mode, force_load)
if page_mode == "📝 错题复习" and selected_date != "全部" and not df.empty:
    df = df[df['日期'] == selected_date]


# ==========================================
# 5. 安全展示格式化
# ==========================================
def safe_format(text):
    if pd.isna(text): return ""
    return str(text).replace('\n', '\n\n')


# ==========================================
# 6. HTML 倒计时组件
# ==========================================
def render_timer(minutes, trigger_key):
    html_code = f"""
    <div id="timer_display_{trigger_key}" style="font-size:24px; font-weight:bold; color:#ff4b4b; background-color:#fef2f2; padding:10px; border-radius:8px; text-align:center; border:1px solid #fca5a5;">
        ⏳ 准备就绪...
    </div>
    <script>
    var time_left = {minutes} * 60;
    var display = document.getElementById("timer_display_{trigger_key}");

    clearInterval(window.my_timer); 

    window.my_timer = setInterval(function() {{
        var m = Math.floor(time_left / 60);
        var s = time_left % 60;
        m = m < 10 ? "0" + m : m;
        s = s < 10 ? "0" + s : s;

        display.innerHTML = "⏱️ 倒计时: " + m + " 分 " + s + " 秒";
        time_left--;

        if (time_left < 0) {{
            clearInterval(window.my_timer);
            display.innerHTML = "⏰ 时间到！请停止作答！";
            display.style.color = "white";
            display.style.backgroundColor = "#ef4444";
        }}
    }}, 1000);
    </script>
    """
    components.html(html_code, height=70)


# ==========================================
# 7. 页面路由与主逻辑
# ==========================================

# ----------------- 🏠 抽题模式 -----------------
# ----------------- 🏠 抽题模式 -----------------
if page_mode == "🏠 抽题模式":
    st.title("🎲 抽题模式")

    # 🌟 修复关键：先挖好 3 个占位符（不填数据），保证排版在顶部
    col1, col2, col3 = st.columns(3)
    metric_placeholder1 = col1.empty()
    metric_placeholder2 = col2.empty()
    metric_placeholder3 = col3.empty()
    st.markdown("---")

    if st.session_state.countdown_trigger > 0:
        render_timer(timer_minutes, st.session_state.countdown_trigger)

    # 🌟 执行抽题和数据更新逻辑
    if st.button(f"🚀 抽取 {num_to_draw} 道新题目", use_container_width=True, type="primary"):
        if not df.empty:
            if st.session_state.drawn_questions:
                for old_q, old_a in zip(st.session_state.drawn_questions, st.session_state.drawn_answers):
                    if not any(item['q'] == old_q for item in st.session_state.history_log):
                        st.session_state.history_log.insert(0, {"q": old_q, "a": old_a})

            available_df = df[~df['问题'].isin(st.session_state.seen_questions)]
            if len(available_df) < num_to_draw:
                st.warning("🔄 题库已抽完一轮，正在为您重新洗牌...")
                st.session_state.seen_questions = set()
                available_df = df

            sample_size = min(num_to_draw, len(available_df))
            random_rows = available_df.sample(n=sample_size)
            st.session_state.drawn_questions = random_rows['问题'].tolist()
            st.session_state.drawn_answers = random_rows['参考'].tolist()

            # 👇 这里就是后台更新数据的地方
            st.session_state.seen_questions.update(st.session_state.drawn_questions)
            st.session_state.total_drawn_count += sample_size
        else:
            st.error("题库为空！")

    # 🌟 修复关键：不管按钮有没有被点，都在最后把【最新的数据】填进占位符里！
    metric_placeholder1.metric(label="📚 当前可用题库", value=f"{len(df)} 道")
    metric_placeholder2.metric(label="🔥 累计刷题", value=f"{st.session_state.total_drawn_count} 道")
    metric_placeholder3.metric(label="🧠 已抽过 (记忆中)", value=f"{len(st.session_state.seen_questions)} 道")

    # 展示刚抽到的题目
    if st.session_state.drawn_questions:
        st.success("👇 最新抽取的题目已就绪！")
        for i in range(len(st.session_state.drawn_questions)):
            q = st.session_state.drawn_questions[i]
            ans = st.session_state.drawn_answers[i]

            with st.container():
                st.markdown(f"<div class='question-title'>【第 {i + 1} 题】 {safe_format(q)}</div>",
                            unsafe_allow_html=True)

                with st.expander(f"💡 点击查看参考及做笔记"):
                    st.markdown(safe_format(ans))
                    st.markdown("---")
                    user_note = st.text_area("✍️ 记录我的理解和总结（选填）",
                                             key=f"note_{i}_{st.session_state.total_drawn_count}")
                    if st.button("🚩 保存并归档至错题本", key=f"save_{i}_{st.session_state.total_drawn_count}"):
                        save_to_review_book(q, ans, user_note)
                        st.toast("✅ 错题本已更新！去左侧【错题复习】即可查看。")
                st.write("---")

    # 展示历史记录
    if st.session_state.history_log:
        st.markdown("<div class='history-header'>📜 本次会话历史记录</div>", unsafe_allow_html=True)
        for idx, item in enumerate(st.session_state.history_log):
            st.markdown(f"**🔄 历史回顾 {idx + 1}：** {safe_format(item['q'])}")
            with st.expander("查看参考答案"):
                st.markdown(safe_format(item['a']))
            st.write("---")

# ----------------- 📖 背题模式 -----------------
elif page_mode == "📖 背题模式":
    st.title("📖 沉浸式背题模式")

    if df.empty:
        st.error("当前数据文件夹为空！")
    else:
        file_list = ["全部文件"] + list(df['来源文件'].unique())
        selected_file = st.selectbox("📂 选择要背诵的文件：", file_list)

        display_df = df if selected_file == "全部文件" else df[df['来源文件'] == selected_file]

        st.metric(label="当前阅读题目总数", value=f"{len(display_df)} 道")
        st.markdown("---")

        for idx, row in display_df.reset_index().iterrows():
            st.markdown(f"<div class='question-title'>Q{idx + 1}: {safe_format(row['问题'])}</div>",
                        unsafe_allow_html=True)
            st.info(safe_format(row['参考']))
            st.write("")

        # ----------------- 📝 错题复习模式 (🌟核心重构) -----------------
elif page_mode == "📝 错题复习":
    st.title("📝 我的错题与笔记")

    if df.empty:
        st.info("当前日期下没有错题记录，或者您还没有收藏任何题目哦！快去抽题模式刷两道吧~")
    else:
        st.metric(label="当前已归档错题总数", value=f"{len(df)} 道")
        st.markdown("---")

        # 🌟 核心修复2：不再需要抽题！像看笔记本一样直接按顺序把错题全列出来
        for idx, row in df.reset_index().iterrows():
            st.markdown(f"<div class='question-title'>📌 {safe_format(row['问题'])}</div>", unsafe_allow_html=True)

            # 展示专属笔记
            if '备注' in row and not pd.isna(row['备注']) and str(row['备注']).strip() != "":
                st.markdown(
                    f"<div class='note-box'>📝 <b>我的总结 ({row['日期']})：</b><br>{safe_format(row['备注'])}</div>",
                    unsafe_allow_html=True)

            # 答案折叠框
            with st.expander("💡 点击查看参考答案"):
                st.markdown(safe_format(row['参考']))
            st.write("---")