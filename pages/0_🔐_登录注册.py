"""
登录注册页面
大气动效风格的用户认证入口。
"""
import streamlit as st
from utils.auth import init_db, login_user, register_user, is_authenticated

# 页面配置
try:
    st.set_page_config(page_title="登录注册", page_icon="🔐", layout="centered")
except Exception:
    pass

# 初始化数据库
init_db()

# ==========================================
# 页面样式 + 动效
# ==========================================
st.markdown("""
<style>
    /* 隐藏 Streamlit 默认元素 */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stDeployButton {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}

    /* 页面背景 */
    .stApp {
        background: linear-gradient(135deg, #0a0a1a 0%, #0d1b3e 30%, #1a0a2e 60%, #0a0a1a 100%) !important;
        min-height: 100vh;
    }

    /* ========== 浮动光球背景 ========== */
    .auth-bg {
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        overflow: hidden;
        pointer-events: none;
        z-index: 0;
    }
    .auth-bg .orb {
        position: absolute;
        border-radius: 50%;
        filter: blur(80px);
        opacity: 0.3;
        animation: float 20s ease-in-out infinite;
    }
    .auth-bg .orb:nth-child(1) {
        width: 400px; height: 400px;
        background: #6366f1;
        top: -100px; left: -100px;
        animation-delay: 0s;
    }
    .auth-bg .orb:nth-child(2) {
        width: 300px; height: 300px;
        background: #ec4899;
        bottom: -80px; right: -80px;
        animation-delay: -7s;
    }
    .auth-bg .orb:nth-child(3) {
        width: 250px; height: 250px;
        background: #06b6d4;
        top: 40%; left: 60%;
        animation-delay: -14s;
    }

    @keyframes float {
        0%, 100% { transform: translate(0, 0) scale(1); }
        25% { transform: translate(30px, -40px) scale(1.05); }
        50% { transform: translate(-20px, 20px) scale(0.95); }
        75% { transform: translate(40px, 30px) scale(1.02); }
    }

    /* ========== 登录卡片容器 ========== */
    .auth-card {
        position: relative;
        max-width: 460px;
        margin: 0 auto;
        padding: 3rem 2.5rem;
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        box-shadow:
            0 8px 40px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.06);
        z-index: 1;
        animation: cardFadeIn 0.8s ease-out;
    }
    @keyframes cardFadeIn {
        from { opacity: 0; transform: translateY(30px) scale(0.96); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }

    /* ========== Logo 区域 ========== */
    .auth-logo {
        text-align: center;
        margin-bottom: 2rem;
    }
    .auth-logo-icon {
        width: 72px;
        height: 72px;
        margin: 0 auto 1rem auto;
        background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.2rem;
        box-shadow: 0 8px 30px rgba(99, 102, 241, 0.3);
        animation: logoGlow 3s ease-in-out infinite;
    }
    @keyframes logoGlow {
        0%, 100% { box-shadow: 0 8px 30px rgba(99, 102, 241, 0.3); }
        50% { box-shadow: 0 8px 40px rgba(99, 102, 241, 0.5), 0 0 60px rgba(236, 72, 153, 0.15); }
    }
    .auth-title {
        text-align: center;
        font-size: 1.8rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
        background: linear-gradient(135deg, #c7d2fe 0%, #f9a8d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .auth-subtitle {
        text-align: center;
        color: #64748b;
        font-size: 0.9rem;
        margin-bottom: 0;
    }

    /* ========== Tab 样式 ========== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 5px;
        margin-bottom: 1.8rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 28px;
        font-weight: 600;
        font-size: 0.92rem;
        color: #64748b;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white !important;
        box-shadow: 0 2px 12px rgba(99, 102, 241, 0.3);
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
    .stTabs [data-baseweb="tab-border"] { display: none; }

    /* ========== 输入框 ========== */
    .stTextInput > div > div > input {
        border-radius: 12px;
        padding: 14px 16px;
        font-size: 0.92rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(255, 255, 255, 0.03);
        color: #e2e8f0;
        transition: all 0.3s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
        background: rgba(255, 255, 255, 0.05);
    }
    .stTextInput > div > div > input::placeholder {
        color: #475569;
    }

    /* 输入框图标标签 */
    .input-label {
        color: #94a3b8;
        font-size: 0.82rem;
        font-weight: 500;
        margin-bottom: 4px;
        display: block;
    }

    /* ========== 按钮 ========== */
    .stButton > button {
        border-radius: 12px;
        padding: 12px 0;
        font-weight: 700;
        font-size: 0.95rem;
        border: none;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        letter-spacing: 0.05em;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(99, 102, 241, 0.4);
    }
    .stButton > button:active {
        transform: translateY(0);
    }

    /* ========== 错误抖动动效 ========== */
    .shake {
        animation: shake 0.5s ease-in-out;
    }
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-6px); }
        20%, 40%, 60%, 80% { transform: translateX(6px); }
    }

    /* ========== 成功动效 ========== */
    .success-glow {
        animation: successPulse 1s ease-out;
    }
    @keyframes successPulse {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
        50% { box-shadow: 0 0 30px 10px rgba(16, 185, 129, 0.2); }
        100% { box-shadow: 0 8px 40px rgba(0, 0, 0, 0.4); }
    }

    /* ========== 成功/错误消息美化 ========== */
    .stAlert > div {
        border-radius: 12px !important;
        font-weight: 500;
    }
    div[data-baseweb="notification"] {
        border-radius: 12px !important;
    }

    /* ========== 已登录状态 ========== */
    .logged-in-card {
        text-align: center;
        padding: 2.5rem 2rem;
    }
    .logged-in-avatar {
        width: 90px;
        height: 90px;
        border-radius: 50%;
        background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1.2rem auto;
        font-size: 2.2rem;
        color: white;
        box-shadow: 0 6px 25px rgba(99, 102, 241, 0.3);
        animation: logoGlow 3s ease-in-out infinite;
    }
    .logged-in-name {
        font-size: 1.5rem;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 0.4rem;
    }
    .logged-in-hint {
        color: #64748b;
        font-size: 0.88rem;
        margin-bottom: 1.5rem;
    }

    /* ========== 底部提示 ========== */
    .auth-footer {
        text-align: center;
        color: #475569;
        font-size: 0.78rem;
        margin-top: 1.5rem;
        line-height: 1.6;
    }

    /* ========== 移动端适配 ========== */
    @media (max-width: 768px) {
        .auth-card {
            padding: 2rem 1.5rem;
            margin: 0 0.5rem;
            border-radius: 20px;
        }
        .auth-logo-icon {
            width: 60px; height: 60px;
            font-size: 1.8rem;
        }
        .auth-title { font-size: 1.5rem !important; }
        .stButton > button {
            width: 100% !important;
        }
    }
    @media (max-width: 480px) {
        .auth-card { padding: 1.5rem 1rem; }
        .auth-title { font-size: 1.3rem !important; }
    }
</style>

<!-- 浮动光球背景 -->
<div class="auth-bg">
    <div class="orb"></div>
    <div class="orb"></div>
    <div class="orb"></div>
</div>
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
            <div class="logged-in-hint">欢迎回来，可以开始使用刷题系统</div>
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
    # Logo + 标题
    st.markdown("""
    <div class="auth-logo">
        <div class="auth-logo-icon">📚</div>
        <div class="auth-title">面试题刷题系统</div>
        <div class="auth-subtitle">系统化刷题，高效备战面试</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-card" id="auth-card">', unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["🔑 登录", "📝 注册"])

    # ---- 登录 Tab ----
    with tab_login:
        with st.form("login_form", clear_on_submit=False):
            st.markdown("""
            <div style="text-align: center; margin-bottom: 1.2rem;">
                <div style="font-size: 0.85rem; color: #818cf8; font-weight: 600; letter-spacing: 0.1em;">
                    ✨ 欢迎回来，请登录您的账号
                </div>
                <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.3rem;">
                    登录后即可开始高效刷题之旅
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<span class="input-label">👤 用户名</span>', unsafe_allow_html=True)
            login_username = st.text_input(
                "用户名",
                placeholder="请输入用户名",
                key="login_user",
                label_visibility="collapsed",
            )
            st.markdown('<span class="input-label">🔒 密码</span>', unsafe_allow_html=True)
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
                    st.markdown('<script>document.getElementById("auth-card").classList.add("shake");setTimeout(()=>document.getElementById("auth-card").classList.remove("shake"),600);</script>', unsafe_allow_html=True)
                    st.error("请输入用户名")
                elif not login_password:
                    st.markdown('<script>document.getElementById("auth-card").classList.add("shake");setTimeout(()=>document.getElementById("auth-card").classList.remove("shake"),600);</script>', unsafe_allow_html=True)
                    st.error("请输入密码")
                else:
                    success, msg = login_user(login_username, login_password)
                    if success:
                        st.markdown('<script>document.getElementById("auth-card").classList.add("success-glow");</script>', unsafe_allow_html=True)
                        st.success("登录成功！正在跳转...")
                        st.balloons()
                        st.switch_page("app.py")
                    else:
                        st.markdown('<script>document.getElementById("auth-card").classList.add("shake");setTimeout(()=>document.getElementById("auth-card").classList.remove("shake"),600);</script>', unsafe_allow_html=True)
                        st.error(msg)

    # ---- 注册 Tab ----
    with tab_register:
        with st.form("register_form", clear_on_submit=False):
            st.markdown("""
            <div style="text-align: center; margin-bottom: 1.2rem;">
                <div style="font-size: 0.85rem; color: #ec4899; font-weight: 600; letter-spacing: 0.1em;">
                    🎉 创建新账号，开启学习之旅
                </div>
                <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.3rem;">
                    注册后即可使用所有刷题功能
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<span class="input-label">👤 用户名</span>', unsafe_allow_html=True)
            reg_username = st.text_input(
                "用户名",
                placeholder="3-20个字符，字母/数字/下划线",
                key="reg_user",
                label_visibility="collapsed",
            )
            st.markdown('<span class="input-label">🔒 密码</span>', unsafe_allow_html=True)
            reg_password = st.text_input(
                "密码",
                type="password",
                placeholder="至少8位，包含字母和数字",
                key="reg_pass",
                label_visibility="collapsed",
            )
            st.markdown('<span class="input-label">🔒 确认密码</span>', unsafe_allow_html=True)
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
                        st.success("注册成功！请切换到「登录」标签页登录。")
                        st.balloons()
                    else:
                        st.error(msg)

    st.markdown('</div>', unsafe_allow_html=True)

    # 底部提示
    st.markdown(
        '<p class="auth-footer">首次使用请先注册账号<br>所有用户数据相互隔离，安全可靠</p>',
        unsafe_allow_html=True,
    )
