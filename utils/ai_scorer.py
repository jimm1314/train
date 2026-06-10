"""
AI 答案评分模块
支持 MIMO API、Gemini API、OpenAI API 和本地文本相似度评分。
优先使用 MIMO API，其他 API 作为备选，无 API 时使用本地算法。
"""
import os
import re
import difflib
import streamlit as st

MIMO_API_KEY = "tp-crw2b6hlsmwym0dxyyoxzy5pjz5umwanf5vt70svh6eujcpk"
MIMO_API_BASE = "https://token-plan-cn.xiaomimimo.com/v1"
MIMO_MODEL = "mimo-v2.5-pro"

CHINESE_STOPWORDS = {
    '的', '了', '是', '在', '和', '有', '不', '人', '这', '中', '为', '上', '个',
    '我', '他', '说', '也', '都', '对', '一', '它', '与', '到', '会', '可以',
    '能', '就', '没有', '没', '把', '让', '被', '从', '而', '但', '如果', '因为',
    '所以', '虽然', '或者', '以及', '而且', '但是', '那么', '这个', '那个', '什么',
    '怎么', '如何', '通过', '使用', '进行', '实现', '就是', '一个', '一些', '这些',
    '那些', '自己', '我们', '他们', '你们', '其', '中', '等', '之', '以', '于',
    '将', '已', '要', '需', '应', '可', '较', '很', '非常', '特别', '主要',
}

ENGLISH_STOPWORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'can', 'shall', 'it', 'its', 'this', 'that',
    'these', 'those', 'i', 'you', 'he', 'she', 'we', 'they', 'me', 'him',
    'her', 'us', 'them', 'my', 'your', 'his', 'our', 'their', 'and', 'or',
    'but', 'if', 'then', 'else', 'when', 'at', 'from', 'by', 'for', 'with',
    'about', 'between', 'through', 'during', 'before', 'after', 'to', 'of',
    'in', 'on', 'off', 'over', 'under', 'again', 'further', 'once', 'here',
    'there', 'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few',
    'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
    'own', 'same', 'so', 'than', 'too', 'very', 'just', 'because', 'as',
    'until', 'while', 'what', 'which', 'who', 'whom', 'into', 'out', 'up',
    'down', 'any', 'also', 'get', 'got', 'make', 'made', 'use', 'used',
}

ALL_STOPWORDS = CHINESE_STOPWORDS | ENGLISH_STOPWORDS


def _extract_keywords(text: str) -> set:
    cleaned = re.sub(r'[^\w\u4e00-\u9fff\s]', '', text.lower())
    words = re.findall(r'[\u4e00-\u9fff]+|[a-z0-9]+', cleaned)
    keywords = set()
    for w in words:
        if re.match(r'[\u4e00-\u9fff]', w):
            for i in range(len(w) - 1):
                bigram = w[i:i+2]
                if bigram not in ALL_STOPWORDS:
                    keywords.add(bigram)
        else:
            if len(w) >= 2 and w not in ALL_STOPWORDS:
                keywords.add(w)
    return keywords


def _local_score(reference: str, user_answer: str) -> tuple[int, str]:
    if not user_answer.strip():
        return 0, "未作答"

    matcher = difflib.SequenceMatcher(None, reference.lower(), user_answer.lower())
    similarity = matcher.ratio()

    ref_keywords = _extract_keywords(reference)
    user_keywords = _extract_keywords(user_answer)

    if ref_keywords:
        matched = ref_keywords & user_keywords
        coverage = len(matched) / len(ref_keywords)
    else:
        coverage = similarity

    score = int(similarity * 40 + coverage * 60)
    score = max(0, min(100, score))

    if score >= 80:
        feedback = "优秀！回答准确且完整，关键点覆盖全面。"
    elif score >= 60:
        feedback = "良好。回答基本正确，但部分关键点可以更详细。"
    elif score >= 40:
        feedback = "一般。回答有一定相关性，但遗漏了较多关键信息。"
    elif score >= 20:
        feedback = "较弱。回答与参考答案差距较大，建议重新学习。"
    else:
        feedback = "需要加强。回答与参考答案差异很大，请仔细复习。"

    if ref_keywords and user_keywords:
        missing = ref_keywords - user_keywords
        if missing:
            sample = list(missing)[:5]
            feedback += f"\n\n💡 可能遗漏的关键词：{'、'.join(sample)}"

    return score, feedback


def _try_mimo_score(question: str, reference: str, user_answer: str) -> tuple[int, str] | None:
    api_key = MIMO_API_KEY
    if not api_key:
        return None

    try:
        import requests
        url = f"{MIMO_API_BASE}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        prompt = (
            f"请对以下面试回答进行评分（0-100分）并给出简洁反馈。\n\n"
            f"题目：{question}\n\n"
            f"参考答案：{reference}\n\n"
            f"用户回答：{user_answer}\n\n"
            f'请严格只返回JSON格式：{{"score": 分数, "feedback": "反馈内容"}}'
        )
        payload = {
            "model": MIMO_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            text = result["choices"][0]["message"]["content"]
            import json as _json
            m = re.search(r'\{.*\}', text, re.DOTALL)
            if m:
                data = _json.loads(m.group())
                return int(data.get("score", 50)), str(data.get("feedback", "评分完成"))
    except Exception:
        pass
    return None


def _try_gemini_score(question: str, reference: str, user_answer: str) -> tuple[int, str] | None:
    api_key = None
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        prompt = (
            f"请对以下面试回答进行评分（0-100分）并给出简洁反馈。\n\n"
            f"题目：{question}\n\n"
            f"参考答案：{reference}\n\n"
            f"用户回答：{user_answer}\n\n"
            f'请严格只返回JSON格式：{{"score": 分数, "feedback": "反馈内容"}}'
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        resp = requests.post(url, json=payload, timeout=20)
        if resp.status_code == 200:
            result = resp.json()
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            import json as _json
            m = re.search(r'\{.*\}', text, re.DOTALL)
            if m:
                data = _json.loads(m.group())
                return int(data.get("score", 50)), str(data.get("feedback", "评分完成"))
    except Exception:
        pass
    return None


def _try_openai_score(question: str, reference: str, user_answer: str) -> tuple[int, str] | None:
    api_key = None
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        import requests
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        prompt = (
            f"请对以下面试回答进行评分（0-100分）并给出简洁反馈。\n"
            f"题目：{question}\n参考答案：{reference}\n用户回答：{user_answer}\n"
            f'请严格只返回JSON：{{"score": 分数, "feedback": "反馈内容"}}'
        )
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            result = resp.json()
            text = result["choices"][0]["message"]["content"]
            import json as _json
            m = re.search(r'\{.*\}', text, re.DOTALL)
            if m:
                data = _json.loads(m.group())
                return int(data.get("score", 50)), str(data.get("feedback", "评分完成"))
    except Exception:
        pass
    return None


def score_answer(question: str, reference: str, user_answer: str) -> tuple[int, str, str]:
    """
    评分用户答案。
    返回: (score, feedback, method)
    method: "mimo" / "gemini" / "openai" / "local"
    """
    result = _try_mimo_score(question, reference, user_answer)
    if result:
        return result[0], result[1], "mimo"

    result = _try_gemini_score(question, reference, user_answer)
    if result:
        return result[0], result[1], "gemini"

    result = _try_openai_score(question, reference, user_answer)
    if result:
        return result[0], result[1], "openai"

    score, feedback = _local_score(reference, user_answer)
    return score, feedback, "local"


def get_score_color(score: int) -> str:
    if score >= 80:
        return "#10b981"
    elif score >= 60:
        return "#22c55e"
    elif score >= 40:
        return "#f59e0b"
    elif score >= 20:
        return "#f97316"
    return "#ef4444"


def get_score_label(score: int) -> str:
    if score >= 80:
        return "优秀"
    elif score >= 60:
        return "良好"
    elif score >= 40:
        return "一般"
    elif score >= 20:
        return "较弱"
    return "需加强"


def get_method_label(method: str) -> str:
    if method == "mimo":
        return "🤖 MIMO AI 评分"
    elif method == "gemini":
        return "🤖 Gemini AI 评分"
    elif method == "openai":
        return "🤖 GPT AI 评分"
    return "📊 本地算法评分"


def render_score_result(score: int, feedback: str, method: str):
    color = get_score_color(score)
    label = get_score_label(score)
    method_label = get_method_label(method)

    st.markdown(
        f'<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);'
        f'border-radius:12px;padding:1.2rem;margin:0.5rem 0;">'
        f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">'
        f'<span style="font-size:2rem;font-weight:800;color:{color};">{score}</span>'
        f'<div><div style="font-weight:700;color:{color};font-size:1rem;">{label}</div>'
        f'<div style="color:#64748b;font-size:0.78rem;">{method_label}</div></div>'
        f'</div>'
        f'<div style="color:#cbd5e1;font-size:0.9rem;line-height:1.6;">'
        f'{feedback.replace(chr(10), "<br>")}</div></div>',
        unsafe_allow_html=True,
    )
