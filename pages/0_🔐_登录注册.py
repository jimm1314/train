"""
登录注册页面
玻璃拟态风格的用户认证入口。
"""
import streamlit as st
from utils.auth import init_db, login_user, register_user, is_authenticated

# 页面配置
st.set_page_config(page_title="登录注册", page_icon="🔐", layout="centered")

# 初始化数据库
init_db()

# ==========================================
# 页面样式
# ==========================================
st.markdown("""
<style>
    /* 隐藏 Streamlit 默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 页面背景 */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    }

    /* 登录卡片容器 */
    .auth-card {
        max-width: 440px;
        margin: 0 auto;
        padding: 2.5rem 2rem;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        box-shadow: 0 8px 40px rgba(0, 0, 0, 0.3);
    }

    /* 标题 */
    .auth-title {
        text-align: center;
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
        background: linear-gradient(135deg, #818cf8 0%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .auth-subtitle {
        text-align: center;
        color: #64748b;
        font-size: 0.92rem;
        margin-bottom: 2rem;
    }

    /* Tab 样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 4px;
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: 600;
        font-size: 0.92rem;
        color: #94a3b8;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
    .stTabs [data-baseweb="tab-border"] { display: none; }

    /* 输入框 */
    .stTextInput > div > div > input {
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 0.92rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(255, 255, 255, 0.04);
        color: #e2e8f0;
        transition: all 0.3s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
    }
    .stTextInput > div > div > input::placeholder {
        color: #475569;
    }

    /* 按钮 */
    .stButton > button {
        border-radius: 12px;
        padding: 10px 0;
        font-weight: 600;
        font-size: 0.95rem;
        border: none;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        letter-spacing: 0.03em;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
    }

    /* 已登录状态 */
    .logged-in-card {
        text-align: center;
        padding: 2rem;
    }
    .logged-in-avatar {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1rem auto;
        font-size: 2rem;
        color: white;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
    }
    .logged-in-name {
        font-size: 1.4rem;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 0.5rem;
    }
    .logged-in-hint {
        color: #64748b;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }

    /* 底部提示 */
    .auth-footer {
        text-align: center;
        color: #475569;
        font-size: 0.8rem;
        margin-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 已登录状态
# ==========================================
if is_authenticated():
    username = st.session_state.get("username", "用户")

    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        st.markdown(f"""
        <div class="auth-card logged-in-card">
            <div class="logged-in-avatar">👤</div>
            <div class="logged-in-name">{username}</div>
            <div class="logged-in-hint">您已登录，可以开始使用刷题系统</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📚 进入系统", use_container_width=True, type="primary"):
                st.switch_page("app.py")
        with col_b:
            if st.button("🚪 退出登录", use_container_width=True):
                from utils.auth import logout
                logout()
                st.rerun()

    st.stop()

# ==========================================
# 未登录：显示登录/注册表单
# ==========================================
_, col_center, _ = st.columns([1, 2, 1])

with col_center:
    st.markdown('<div class="auth-title">📚 面试题刷题系统</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-subtitle">系统化刷题，高效备战面试</div>', unsafe_allow_html=True)

    st.markdown('<div class="auth-card">', unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["🔑 登录", "📝 注册"])

    # ---- 登录 Tab ----
    with tab_login:
        with st.form("login_form", clear_on_submit=False):
            login_username = st.text_input(
                "用户名",
                placeholder="请输入用户名",
                key="login_user",
                label_visibility="collapsed",
            )
            login_password = st.text_input(
                "密码",
                type="password",
                placeholder="请输入密码",
                key="login_pass",
                label_visibility="collapsed",
            )
            st.markdown("")
            login_submitted = st.form_submit_button(
                "🔑 登 录", use_container_width=True, type="primary"
            )

            if login_submitted:
                if not login_username.strip():
                    st.error("请输入用户名")
                elif not login_password:
                    st.error("请输入密码")
                else:
                    success, msg = login_user(login_username, login_password)
                    if success:
                        st.success(msg)
                        st.switch_page("app.py")
                    else:
                        st.error(msg)

    # ---- 注册 Tab ----
    with tab_register:
        with st.form("register_form", clear_on_submit=False):
            reg_username = st.text_input(
                "用户名",
                placeholder="3-20个字符，字母/数字/下划线",
                key="reg_user",
                label_visibility="collapsed",
            )
            reg_password = st.text_input(
                "密码",
                type="password",
                placeholder="至少8位，包含字母和数字",
                key="reg_pass",
                label_visibility="collapsed",
            )
            reg_confirm = st.text_input(
                "确认密码",
                type="password",
                placeholder="再次输入密码",
                key="reg_confirm",
                label_visibility="collapsed",
            )
            st.markdown("")
            reg_submitted = st.form_submit_button(
                "📝 注 册", use_container_width=True, type="primary"
            )

            if reg_submitted:
                if not reg_username.strip():
                    st.error("请输入用户名")
                elif not reg_password:
                    st.error("请输入密码")
                elif reg_password != reg_confirm:
                    st.error("两次输入的密码不一致")
                else:
                    success, msg = register_user(reg_username, reg_password)
                    if success:
                        st.success("注册成功！请切换到「登录」标签页输入账号密码登录。")
                        st.balloons()
                    else:
                        st.error(msg)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        '<p class="auth-footer">首次使用请先注册账号 · 所有数据相互隔离</p>',
        unsafe_allow_html=True,
    )
