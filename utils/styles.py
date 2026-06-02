"""
全局 CSS 样式模块
现代设计系统：CSS 变量、玻璃拟态、渐变、微动画。
"""
import streamlit as st


def inject_global_styles():
    """注入全局 CSS 样式到 Streamlit 页面"""
    # 确保移动端 viewport 正确
    st.markdown(
        '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">',
        unsafe_allow_html=True,
    )
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


GLOBAL_CSS = """
<style>
    /* ========== CSS 变量 ========== */
    :root {
        --primary: #6366f1;
        --primary-light: #818cf8;
        --primary-dark: #4f46e5;
        --accent: #ec4899;
        --accent-light: #f472b6;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --bg-glass: rgba(255, 255, 255, 0.06);
        --bg-glass-hover: rgba(255, 255, 255, 0.1);
        --border-glass: rgba(255, 255, 255, 0.12);
        --border-glass-hover: rgba(255, 255, 255, 0.2);
        --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.1);
        --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.15);
        --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.2);
        --shadow-glow: 0 0 20px rgba(99, 102, 241, 0.15);
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 20px;
        --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* ========== 全局基础 ========== */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    }

    /* ========== 玻璃拟态卡片 ========== */
    .glass-card {
        background: var(--bg-glass);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--border-glass);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        transition: var(--transition);
    }
    .glass-card:hover {
        background: var(--bg-glass-hover);
        border-color: var(--border-glass-hover);
        box-shadow: var(--shadow-glow);
    }

    /* ========== 题目卡片 ========== */
    .question-card {
        background: var(--bg-glass);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--border-glass);
        border-radius: var(--radius-lg);
        padding: 1.5rem 1.5rem 1rem 1.5rem;
        margin-bottom: 1rem;
        position: relative;
        overflow: hidden;
        transition: var(--transition);
    }
    .question-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary), var(--accent));
        border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    }
    .question-card:hover {
        border-color: var(--border-glass-hover);
        box-shadow: var(--shadow-glow);
        transform: translateY(-2px);
    }

    .question-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #e2e8f0;
        line-height: 1.7;
        margin-bottom: 10px;
    }

    /* ========== 答案区域 ========== */
    .answer-box {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: var(--radius-md);
        padding: 1rem 1.2rem;
        margin-top: 0.5rem;
    }
    .answer-box-header {
        color: var(--success);
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* ========== 笔记盒子 ========== */
    .note-box {
        background: rgba(236, 72, 153, 0.08);
        border: 1px solid rgba(236, 72, 153, 0.2);
        border-left: 4px solid var(--accent);
        border-radius: var(--radius-md);
        padding: 1rem 1.2rem;
        margin: 0.75rem 0;
        color: #e2e8f0;
        font-size: 0.92rem;
    }

    /* ========== 标签系统 ========== */
    .tag {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        border: 1px solid transparent;
        transition: var(--transition);
    }
    .difficulty-easy {
        background: rgba(16, 185, 129, 0.12);
        color: #6ee7b7;
        border-color: rgba(16, 185, 129, 0.3);
    }
    .difficulty-medium {
        background: rgba(245, 158, 11, 0.12);
        color: #fcd34d;
        border-color: rgba(245, 158, 11, 0.3);
    }
    .difficulty-hard {
        background: rgba(239, 68, 68, 0.12);
        color: #fca5a5;
        border-color: rgba(239, 68, 68, 0.3);
    }
    .knowledge-tag {
        background: rgba(99, 102, 241, 0.12);
        color: #a5b4fc;
        border-color: rgba(99, 102, 241, 0.3);
    }

    /* ========== 统计卡片 ========== */
    .stat-card {
        background: var(--bg-glass);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--border-glass);
        border-radius: var(--radius-lg);
        padding: 1.4rem 1.2rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        transition: var(--transition);
    }
    .stat-card::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 10%;
        right: 10%;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--primary), transparent);
        border-radius: 2px;
    }
    .stat-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-glow);
        border-color: var(--primary-light);
    }
    .stat-card-value {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, var(--primary-light), var(--accent-light));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.2;
    }
    .stat-card-label {
        color: #94a3b8;
        font-size: 0.85rem;
        margin-top: 6px;
        font-weight: 500;
    }

    /* ========== 按钮样式 ========== */
    .stButton > button {
        border-radius: var(--radius-md);
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        font-size: 0.9rem;
        border: 1px solid var(--border-glass);
        transition: var(--transition);
        letter-spacing: 0.02em;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%) !important;
        border: none !important;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary) 100%) !important;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4) !important;
    }

    /* ========== 输入框 ========== */
    .stTextInput > div > div > input {
        border-radius: var(--radius-md);
        padding: 10px 14px;
        font-size: 0.92rem;
        border: 1px solid var(--border-glass);
        background: var(--bg-glass);
        color: #e2e8f0;
        transition: var(--transition);
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
    }
    .stTextArea > div > div > textarea {
        border-radius: var(--radius-md);
        border: 1px solid var(--border-glass);
        background: var(--bg-glass);
        color: #e2e8f0;
        transition: var(--transition);
    }
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
    }

    /* ========== Tab 样式 ========== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: var(--bg-glass);
        border: 1px solid var(--border-glass);
        border-radius: var(--radius-md);
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-sm);
        padding: 8px 20px;
        font-weight: 600;
        font-size: 0.88rem;
        color: #94a3b8;
        transition: var(--transition);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        color: white;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }
    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }

    /* ========== Metric 样式 ========== */
    [data-testid="stMetric"] {
        background: var(--bg-glass);
        border: 1px solid var(--border-glass);
        border-radius: var(--radius-md);
        padding: 1rem;
        transition: var(--transition);
    }
    [data-testid="stMetric"]:hover {
        border-color: var(--border-glass-hover);
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stMetricValue"] {
        color: #e2e8f0 !important;
        font-weight: 700 !important;
    }

    /* ========== Expander 样式 ========== */
    .streamlit-expanderHeader {
        background: var(--bg-glass);
        border: 1px solid var(--border-glass);
        border-radius: var(--radius-md);
        font-weight: 600;
        color: #cbd5e1;
        transition: var(--transition);
    }
    .streamlit-expanderHeader:hover {
        border-color: var(--primary);
        color: #e2e8f0;
    }
    .streamlit-expanderContent {
        background: rgba(15, 23, 42, 0.5);
        border: 1px solid var(--border-glass);
        border-top: none;
        border-radius: 0 0 var(--radius-md) var(--radius-md);
    }

    /* ========== 分割线 ========== */
    hr {
        border-color: rgba(255, 255, 255, 0.06) !important;
    }

    /* ========== 侧边栏 ========== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
        border-right: 1px solid var(--border-glass);
    }
    [data-testid="stSidebar"] [data-testid="stMarkdown"] {
        color: #cbd5e1;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: var(--bg-glass);
        border: 1px solid var(--border-glass);
        color: #e2e8f0;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        border-color: var(--primary);
        background: rgba(99, 102, 241, 0.1);
    }

    /* ========== 页面链接按钮 ========== */
    .stPageLink {
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--border-glass) !important;
        background: var(--bg-glass) !important;
        transition: var(--transition) !important;
    }
    .stPageLink:hover {
        border-color: var(--primary) !important;
        background: rgba(99, 102, 241, 0.08) !important;
        box-shadow: var(--shadow-glow) !important;
    }

    /* ========== 分页信息 ========== */
    .pagination-info {
        text-align: center;
        color: #64748b;
        font-size: 0.9rem;
        margin: 10px 0;
    }

    /* ========== 掌握度星星 ========== */
    .mastery-stars {
        color: var(--warning);
        font-size: 1rem;
        letter-spacing: 2px;
    }

    /* ========== 连续学习徽章 ========== */
    .streak-badge {
        display: inline-block;
        background: linear-gradient(135deg, var(--warning) 0%, var(--danger) 100%);
        color: white;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
    }

    /* ========== 历史记录标题 ========== */
    .history-header {
        color: var(--accent);
        font-size: 1.3rem;
        font-weight: 700;
        margin-top: 2rem;
        border-bottom: 2px solid rgba(236, 72, 153, 0.3);
        padding-bottom: 8px;
        margin-bottom: 1rem;
    }

    /* ========== 滚动条美化 ========== */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.25);
    }

    /* ========== 选中文本 ========== */
    ::selection {
        background: rgba(99, 102, 241, 0.3);
        color: white;
    }

    /* ========== 移动端响应式 ========== */
    @media (max-width: 768px) {
        /* 缩小标题字号 */
        h1 { font-size: 1.4rem !important; }
        h2 { font-size: 1.2rem !important; }
        h3 { font-size: 1.05rem !important; }

        /* 列布局自动堆叠 */
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
        }
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
            min-width: 100% !important;
            flex: 1 1 100% !important;
            padding: 0 0 !important;
        }

        /* 两列布局堆叠 */
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) {
            margin-top: 0.5rem;
        }

        /* 卡片内边距缩小 */
        .question-card { padding: 1rem; }
        .stat-card { padding: 1rem 0.8rem; }
        .stat-card-value { font-size: 1.5rem; }
        .stat-card-label { font-size: 0.78rem; }
        .glass-card { padding: 1rem; }

        /* 按钮全宽 */
        .stButton > button {
            width: 100% !important;
            font-size: 0.85rem !important;
            padding: 0.6rem 1rem !important;
        }

        /* Tab 更紧凑 */
        .stTabs [data-baseweb="tab"] {
            padding: 6px 12px !important;
            font-size: 0.8rem !important;
        }

        /* Metric 更紧凑 */
        [data-testid="stMetric"] { padding: 0.6rem; }
        [data-testid="stMetricLabel"] { font-size: 0.75rem !important; }
        [data-testid="stMetricValue"] { font-size: 1rem !important; }

        /* 输入框适配 */
        .stTextInput > div > div > input {
            font-size: 16px !important; /* 防止 iOS 缩放 */
            padding: 10px 12px !important;
        }
        .stTextArea > div > div > textarea {
            font-size: 16px !important;
        }

        /* Selectbox 适配 */
        .stSelectbox > div > div {
            font-size: 0.85rem !important;
        }

        /* 侧边栏默认收起时的内容区 */
        .block-container {
            padding: 1rem 0.8rem !important;
        }

        /* 页面链接按钮 */
        .stPageLink {
            margin-bottom: 0.3rem !important;
        }

        /* Plotly 图表 */
        .js-plotly-plot {
            width: 100% !important;
        }

        /* 侧边栏宽度 */
        [data-testid="stSidebar"] {
            min-width: 280px !important;
            max-width: 80vw !important;
        }
    }

    /* 超小屏幕 (< 480px) */
    @media (max-width: 480px) {
        .stat-card-value { font-size: 1.3rem; }
        .question-title { font-size: 0.95rem; }
        .auth-card { padding: 1.5rem 1rem !important; }
        .auth-title { font-size: 1.5rem !important; }
    }

    /* ========== 亮色主题适配 ========== */
    @media (prefers-color-scheme: light) {
        :root {
            --bg-glass: rgba(255, 255, 255, 0.7);
            --bg-glass-hover: rgba(255, 255, 255, 0.85);
            --border-glass: rgba(0, 0, 0, 0.08);
            --border-glass-hover: rgba(0, 0, 0, 0.15);
        }
        .stApp {
            background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 50%, #f8fafc 100%);
        }
        .question-title {
            color: #1e293b;
        }
        .note-box {
            color: #334155;
        }
        .stat-card-label {
            color: #64748b;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8fafc 0%, #e0e7ff 100%);
        }
        [data-testid="stSidebar"] [data-testid="stMarkdown"] {
            color: #334155;
        }
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
    return f'<span class="tag {css_class}">{difficulty}</span>'


def render_knowledge_tag(tag: str) -> str:
    """渲染知识点标签的 HTML"""
    return f'<span class="tag knowledge-tag">{tag}</span>'


def render_mastery_stars(level: int) -> str:
    """渲染掌握度星星（1-5）"""
    level = max(0, min(5, level))
    filled = "★" * level
    empty = "☆" * (5 - level)
    return f'<span class="mastery-stars">{filled}{empty}</span>'
