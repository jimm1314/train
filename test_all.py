"""
全面功能测试脚本
测试所有新增功能模块的正确性和兼容性。
"""
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = 0
FAIL = 0
ERRORS = []


def test(name, func):
    global PASS, FAIL
    try:
        func()
        print(f"  ✅ {name}")
        PASS += 1
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        traceback.print_exc()
        ERRORS.append((name, str(e)))
        FAIL += 1


# ==========================================
# 1. 模块导入测试
# ==========================================
print("\n" + "=" * 60)
print("1. 模块导入测试")
print("=" * 60)


def test_import_session_state():
    from utils.session_state import init_session_state
    assert callable(init_session_state)

def test_import_styles():
    from utils.styles import inject_global_styles, render_difficulty_tag, render_knowledge_tag, render_mastery_stars
    assert callable(inject_global_styles)
    assert callable(render_difficulty_tag)
    assert callable(render_knowledge_tag)
    assert callable(render_mastery_stars)

def test_import_data_loader():
    from utils.data_loader import (
        load_question_banks, get_filtered_questions,
        get_knowledge_categories, get_user_data_dir,
        ensure_user_data_dir, get_review_file,
        get_study_log_file, get_checkin_file,
        get_dictation_file, DATA_DIR,
    )
    assert callable(load_question_banks)
    assert callable(get_filtered_questions)
    assert callable(get_knowledge_categories)

def test_import_auth():
    from utils.auth import (
        init_db, login_user, register_user,
        is_authenticated, get_current_user, is_admin,
        check_auth, check_admin, get_all_users, delete_user, logout,
    )
    assert callable(init_db)

def test_import_review_manager():
    from utils.review_manager import (
        sm2, _read_review_file, _write_review_file,
        save_to_review_book, delete_from_review_book,
        update_mastery, update_note, increment_review_count,
        get_review_stats, check_in, get_checkin_stats,
        log_study_session, load_study_log,
        update_sm2_after_review, get_due_reviews,
        get_attribution_stats, update_attribution,
        REVIEW_COLUMNS, ATTRIBUTION_OPTIONS,
    )
    assert callable(sm2)
    assert callable(save_to_review_book)
    assert callable(get_due_reviews)
    assert callable(get_attribution_stats)
    assert "归因" in REVIEW_COLUMNS
    assert "next_review" in REVIEW_COLUMNS
    assert "ease_factor" in REVIEW_COLUMNS
    assert "interval" in REVIEW_COLUMNS
    assert "repetitions" in REVIEW_COLUMNS
    assert len(ATTRIBUTION_OPTIONS) == 5

def test_import_goal_manager():
    from utils.goal_manager import (
        load_goals, save_goals, get_today_progress,
        get_weekly_progress, get_review_progress,
        render_goal_progress, DEFAULT_GOALS,
    )
    assert callable(load_goals)
    assert callable(save_goals)
    assert callable(render_goal_progress)
    assert "daily_questions" in DEFAULT_GOALS
    assert "weekly_questions" in DEFAULT_GOALS
    assert "daily_review" in DEFAULT_GOALS

def test_import_ai_scorer():
    from utils.ai_scorer import (
        score_answer, render_score_result,
        get_score_color, get_score_label, get_method_label,
        _extract_keywords, _local_score,
        MIMO_API_KEY, MIMO_API_BASE, MIMO_MODEL,
    )
    assert callable(score_answer)
    assert callable(render_score_result)
    assert callable(get_score_color)
    assert callable(get_score_label)
    assert callable(get_method_label)
    assert callable(_extract_keywords)
    assert callable(_local_score)
    assert MIMO_API_KEY == "tp-crw2b6hlsmwym0dxyyoxzy5pjz5umwanf5vt70svh6eujcpk"
    assert "mimo" in MIMO_MODEL.lower()

def test_import_question_card():
    from components.question_card import (
        render_question_card, render_review_card, safe_format,
    )
    assert callable(render_question_card)
    assert callable(render_review_card)
    assert callable(safe_format)

def test_import_metrics():
    from components.metrics import render_metric_row, render_overview_cards
    assert callable(render_metric_row)
    assert callable(render_overview_cards)

def test_import_timer():
    from components.timer import render_timer
    assert callable(render_timer)

test("session_state 导入", test_import_session_state)
test("styles 导入", test_import_styles)
test("data_loader 导入", test_import_data_loader)
test("auth 导入", test_import_auth)
test("review_manager 导入", test_import_review_manager)
test("goal_manager 导入", test_import_goal_manager)
test("ai_scorer 导入", test_import_ai_scorer)
test("question_card 导入", test_import_question_card)
test("metrics 导入", test_import_metrics)
test("timer 导入", test_import_timer)


# ==========================================
# 2. SM-2 算法测试
# ==========================================
print("\n" + "=" * 60)
print("2. SM-2 间隔重复算法测试")
print("=" * 60)

from utils.review_manager import sm2


def test_sm2_first_correct():
    rep, ef, iv = sm2(quality=4, repetitions=0, ease_factor=2.5, interval=1)
    assert rep == 1, f"Expected rep=1, got {rep}"
    assert iv == 1, f"Expected iv=1, got {iv}"
    assert ef >= 2.5, f"Expected ef>=2.5, got {ef}"

def test_sm2_second_correct():
    rep, ef, iv = sm2(quality=5, repetitions=1, ease_factor=2.5, interval=1)
    assert rep == 2, f"Expected rep=2, got {rep}"
    assert iv == 6, f"Expected iv=6, got {iv}"

def test_sm2_high_repetition():
    rep, ef, iv = sm2(quality=4, repetitions=3, ease_factor=2.5, interval=15)
    assert rep == 4, f"Expected rep=4, got {rep}"
    assert iv > 15, f"Expected iv>15, got {iv}"

def test_sm2_wrong_answer():
    rep, ef, iv = sm2(quality=2, repetitions=3, ease_factor=2.5, interval=10)
    assert rep == 0, f"Expected rep=0, got {rep}"
    assert iv == 1, f"Expected iv=1, got {iv}"
    assert ef < 2.5, f"Expected ef<2.5, got {ef}"

def test_sm2_boundary_quality():
    rep3, _, _ = sm2(quality=3, repetitions=0, ease_factor=2.5, interval=1)
    rep2, _, _ = sm2(quality=2, repetitions=0, ease_factor=2.5, interval=1)
    assert rep3 == 1, "quality=3 should be correct"
    assert rep2 == 0, "quality=2 should be incorrect"

def test_sm2_ease_factor_min():
    for _ in range(10):
        _, ef, _ = sm2(quality=0, repetitions=0, ease_factor=1.3, interval=1)
    assert ef >= 1.3, f"Ease factor should not go below 1.3, got {ef}"

def test_sm2_quality_clamping():
    rep, ef, iv = sm2(quality=10, repetitions=0, ease_factor=2.5, interval=1)
    assert rep == 1, "quality>5 should be clamped to 5"
    rep2, _, _ = sm2(quality=-5, repetitions=0, ease_factor=2.5, interval=1)
    assert rep2 == 0, "quality<0 should be clamped to 0"

test("首次正确回答", test_sm2_first_correct)
test("第二次正确回答", test_sm2_second_correct)
test("高重复次数正确回答", test_sm2_high_repetition)
test("错误回答重置", test_sm2_wrong_answer)
test("边界质量值 (2 vs 3)", test_sm2_boundary_quality)
test("Ease Factor 最小值", test_sm2_ease_factor_min)
test("Quality 值钳位", test_sm2_quality_clamping)


# ==========================================
# 3. AI 评分测试
# ==========================================
print("\n" + "=" * 60)
print("3. AI 评分功能测试")
print("=" * 60)

from utils.ai_scorer import score_answer, _extract_keywords, _local_score, get_score_color, get_score_label, get_method_label


def test_keywords_extraction():
    keywords = _extract_keywords("HTTP 是超文本传输协议，用于 Web 通信")
    assert "http" in keywords, f"Expected 'http' in keywords, got {keywords}"
    assert "超文本" in keywords or "传输" in keywords, f"Expected Chinese keywords, got {keywords}"

def test_keywords_no_stopwords():
    keywords = _extract_keywords("这是一个测试")
    assert "这" not in keywords, "Stopword '这' should be filtered"
    assert "是" not in keywords, "Stopword '是' should be filtered"

def test_local_score_identical():
    score, feedback = _local_score("HTTP是超文本传输协议", "HTTP是超文本传输协议")
    assert score >= 90, f"Identical texts should score >= 90, got {score}"
    assert "优秀" in feedback

def test_local_score_empty():
    score, feedback = _local_score("HTTP是协议", "")
    assert score == 0, f"Empty answer should score 0, got {score}"
    assert "未作答" in feedback

def test_local_score_partial():
    score, feedback = _local_score(
        "HTTP是超文本传输协议用于Web通信",
        "HTTP是协议"
    )
    assert 0 < score < 80, f"Partial answer should score 0-80, got {score}"

def test_score_answer_returns_tuple():
    result = score_answer("What is HTTP?", "HTTP is a protocol", "HTTP is a web protocol")
    assert isinstance(result, tuple) and len(result) == 3
    score, feedback, method = result
    assert isinstance(score, int)
    assert isinstance(feedback, str)
    assert method in ("gemini", "openai", "local")

def test_score_color_mapping():
    assert get_score_color(90) == "#10b981"
    assert get_score_color(70) == "#22c55e"
    assert get_score_color(50) == "#f59e0b"
    assert get_score_color(30) == "#f97316"
    assert get_score_color(10) == "#ef4444"

def test_score_label_mapping():
    assert get_score_label(90) == "优秀"
    assert get_score_label(70) == "良好"
    assert get_score_label(50) == "一般"
    assert get_score_label(30) == "较弱"
    assert get_score_label(10) == "需加强"

def test_method_label_mapping():
    assert "MIMO" in get_method_label("mimo")
    assert "Gemini" in get_method_label("gemini")
    assert "GPT" in get_method_label("openai")
    assert "本地" in get_method_label("local")

test("关键词提取", test_keywords_extraction)
test("停用词过滤", test_keywords_no_stopwords)
test("本地评分-完全相同", test_local_score_identical)
test("本地评分-空答案", test_local_score_empty)
test("本地评分-部分匹配", test_local_score_partial)
test("score_answer 返回格式", test_score_answer_returns_tuple)
test("评分颜色映射", test_score_color_mapping)
test("评分标签映射", test_score_label_mapping)
test("评分方法标签", test_method_label_mapping)


# ==========================================
# 4. 学习目标管理测试
# ==========================================
print("\n" + "=" * 60)
print("4. 学习目标管理测试")
print("=" * 60)

from utils.goal_manager import load_goals, save_goals, DEFAULT_GOALS


def test_load_goals_default():
    goals = load_goals()
    assert isinstance(goals, dict)
    assert "daily_questions" in goals
    assert "weekly_questions" in goals
    assert "daily_review" in goals

def test_save_and_load_goals():
    original = load_goals()
    test_goals = {"daily_questions": 50, "weekly_questions": 200, "daily_review": 10}
    save_goals(test_goals)
    loaded = load_goals()
    assert loaded["daily_questions"] == 50
    assert loaded["weekly_questions"] == 200
    assert loaded["daily_review"] == 10
    save_goals(original)

def test_goals_merge_defaults():
    original = load_goals()
    partial = {"daily_questions": 30}
    save_goals(partial)
    loaded = load_goals()
    assert loaded["daily_questions"] == 30
    assert "weekly_questions" in loaded
    save_goals(original)

test("加载默认目标", test_load_goals_default)
test("保存和加载目标", test_save_and_load_goals)
test("目标合并默认值", test_goals_merge_defaults)


# ==========================================
# 5. 错题本功能测试（含新字段）
# ==========================================
print("\n" + "=" * 60)
print("5. 错题本功能测试（含新字段）")
print("=" * 60)

from utils.review_manager import (
    _read_review_file, save_to_review_book, delete_from_review_book,
    update_mastery, update_sm2_after_review, get_due_reviews,
    get_attribution_stats, update_attribution, REVIEW_COLUMNS, ATTRIBUTION_OPTIONS,
)


def test_review_columns_complete():
    df = _read_review_file()
    for col in REVIEW_COLUMNS:
        assert col in df.columns, f"Missing column: {col}"

def test_save_with_attribution():
    save_to_review_book(
        "测试题目_归因测试", "测试答案", note="测试备注",
        mastery=3, tags="测试", attribution="知识盲区"
    )
    df = _read_review_file()
    row = df[df["问题"] == "测试题目_归因测试"]
    assert not row.empty, "Question should be saved"
    assert row.iloc[0]["归因"] == "知识盲区"
    assert row.iloc[0]["ease_factor"] == 2.5
    assert row.iloc[0]["interval"] == 1
    assert row.iloc[0]["repetitions"] == 0
    delete_from_review_book("测试题目_归因测试")

def test_sm2_update():
    save_to_review_book("测试题目_SM2", "测试答案", mastery=3)
    update_sm2_after_review("测试题目_SM2", quality=4)
    df = _read_review_file()
    row = df[df["问题"] == "测试题目_SM2"]
    assert not row.empty
    assert row.iloc[0]["repetitions"] == 1
    assert row.iloc[0]["ease_factor"] >= 2.5
    delete_from_review_book("测试题目_SM2")

def test_sm2_wrong_answer_resets():
    save_to_review_book("测试题目_重置", "测试答案", mastery=3)
    update_sm2_after_review("测试题目_重置", quality=4)
    update_sm2_after_review("测试题目_重置", quality=2)
    df = _read_review_file()
    row = df[df["问题"] == "测试题目_重置"]
    assert not row.empty
    assert row.iloc[0]["repetitions"] == 0
    assert row.iloc[0]["interval"] == 1
    delete_from_review_book("测试题目_重置")

def test_get_due_reviews():
    save_to_review_book("测试题目_待复习", "测试答案", mastery=1)
    due = get_due_reviews()
    assert isinstance(due, pd.DataFrame)
    delete_from_review_book("测试题目_待复习")

def test_attribution_stats():
    save_to_review_book("测试题目_统计A", "答案", attribution="理解偏差")
    save_to_review_book("测试题目_统计B", "答案", attribution="粗心大意")
    stats = get_attribution_stats()
    assert isinstance(stats, dict)
    assert "理解偏差" in stats
    assert "粗心大意" in stats
    delete_from_review_book("测试题目_统计A")
    delete_from_review_book("测试题目_统计B")

def test_update_attribution():
    save_to_review_book("测试题目_改归因", "答案", attribution="知识盲区")
    update_attribution("测试题目_改归因", "表达问题")
    df = _read_review_file()
    row = df[df["问题"] == "测试题目_改归因"]
    assert not row.empty
    assert row.iloc[0]["归因"] == "表达问题"
    delete_from_review_book("测试题目_改归因")

def test_backward_compatibility():
    import pandas as pd
    import tempfile
    from utils.data_loader import get_review_file
    review_file = get_review_file()
    if os.path.exists(review_file):
        df = pd.read_csv(review_file, encoding="utf-8-sig")
        old_cols = [c for c in df.columns if c not in ["归因", "next_review", "ease_factor", "interval", "repetitions"]]
        df_old = df[old_cols] if old_cols else df
        df_old.to_csv(review_file, index=False, encoding="utf-8-sig")
        df_new = _read_review_file()
        for col in REVIEW_COLUMNS:
            assert col in df_new.columns, f"Backward compat: missing {col}"

import pandas as pd
test("错题本列完整性", test_review_columns_complete)
test("保存含归因", test_save_with_attribution)
test("SM-2 更新", test_sm2_update)
test("SM-2 错误重置", test_sm2_wrong_answer_resets)
test("获取待复习", test_get_due_reviews)
test("归因统计", test_attribution_stats)
test("更新归因", test_update_attribution)
test("向后兼容性", test_backward_compatibility)


# ==========================================
# 6. 样式函数测试
# ==========================================
print("\n" + "=" * 60)
print("6. 样式函数测试")
print("=" * 60)

from utils.styles import render_difficulty_tag, render_knowledge_tag, render_mastery_stars


def test_difficulty_tag():
    html = render_difficulty_tag("简单")
    assert "简单" in html
    assert "tag" in html.lower() or "background" in html

def test_difficulty_tag_all():
    for d in ["简单", "中等", "困难"]:
        html = render_difficulty_tag(d)
        assert d in html

def test_knowledge_tag():
    html = render_knowledge_tag("网络")
    assert "网络" in html

def test_mastery_stars():
    html = render_mastery_stars(3)
    assert "★" in html
    assert "☆" in html

def test_mastery_stars_boundary():
    html0 = render_mastery_stars(0)
    html5 = render_mastery_stars(5)
    assert "☆" in html0
    assert "★" in html5

test("难度标签渲染", test_difficulty_tag)
test("所有难度标签", test_difficulty_tag_all)
test("知识点标签渲染", test_knowledge_tag)
test("掌握度星星渲染", test_mastery_stars)
test("掌握度边界值", test_mastery_stars_boundary)


# ==========================================
# 7. safe_format 测试
# ==========================================
print("\n" + "=" * 60)
print("7. safe_format 安全格式化测试")
print("=" * 60)

from components.question_card import safe_format


def test_safe_format_normal():
    result = safe_format("Hello World")
    assert "Hello World" in result

def test_safe_format_html_escape():
    result = safe_format("<script>alert('xss')</script>")
    assert "<script>" not in result
    assert "&lt;script&gt;" in result

def test_safe_format_newline():
    result = safe_format("line1\nline2")
    assert "\n\n" in result, "Newlines should be converted to double newlines for Markdown"

def test_safe_format_empty():
    result = safe_format("")
    assert result == ""

test("普通文本", test_safe_format_normal)
test("HTML 转义", test_safe_format_html_escape)
test("换行转换", test_safe_format_newline)
test("空字符串", test_safe_format_empty)


# ==========================================
# 8. 数据加载测试
# ==========================================
print("\n" + "=" * 60)
print("8. 数据加载测试")
print("=" * 60)

from utils.data_loader import (
    get_filtered_questions, get_knowledge_categories,
    get_user_data_dir, ensure_user_data_dir,
    get_review_file, get_study_log_file, get_checkin_file,
)


def test_data_dir_exists():
    from utils.data_loader import DATA_DIR
    assert os.path.exists(DATA_DIR), f"DATA_DIR not found: {DATA_DIR}"

def test_user_data_dir():
    d = get_user_data_dir()
    assert isinstance(d, str)
    assert len(d) > 0

def test_ensure_user_data_dir():
    ensure_user_data_dir()
    d = get_user_data_dir()
    assert os.path.exists(d), f"User data dir not created: {d}"

def test_review_file_path():
    path = get_review_file()
    assert path.endswith("review_book.csv")

def test_study_log_path():
    path = get_study_log_file()
    assert path.endswith("study_log.csv")

def test_checkin_path():
    path = get_checkin_file()
    assert path.endswith("checkin_log.csv")

test("数据目录存在", test_data_dir_exists)
test("用户数据目录路径", test_user_data_dir)
test("确保用户数据目录创建", test_ensure_user_data_dir)
test("错题本文件路径", test_review_file_path)
test("学习日志文件路径", test_study_log_path)
test("签到文件路径", test_checkin_path)


# ==========================================
# 9. 认证模块测试
# ==========================================
print("\n" + "=" * 60)
print("9. 认证模块测试")
print("=" * 60)

from utils.auth import init_db, _hash_password


def test_init_db():
    init_db()

def test_hash_password():
    h1 = _hash_password("test123", "salt1")
    h2 = _hash_password("test123", "salt2")
    h3 = _hash_password("test123", "salt1")
    assert h1 != h2, "Different salts should produce different hashes"
    assert h1 == h3, "Same salt+password should produce same hash"
    assert len(h1) == 64, "SHA-256 should produce 64-char hex"

test("数据库初始化", test_init_db)
test("密码哈希一致性", test_hash_password)


# ==========================================
# 10. 页面文件语法检查
# ==========================================
print("\n" + "=" * 60)
print("10. 页面文件语法检查")
print("=" * 60)

import py_compile


def test_syntax_app():
    py_compile.compile(r"d:\software\PyCharm 2025.3.5\file_saves\genmini\app.py", doraise=True)

def test_syntax_login():
    py_compile.compile(r"d:\software\PyCharm 2025.3.5\file_saves\genmini\pages\0_🔐_登录注册.py", doraise=True)

def test_syntax_quiz():
    py_compile.compile(r"d:\software\PyCharm 2025.3.5\file_saves\genmini\pages\1_🎲_抽题模式.py", doraise=True)

def test_syntax_browse():
    py_compile.compile(r"d:\software\PyCharm 2025.3.5\file_saves\genmini\pages\2_📖_背题模式.py", doraise=True)

def test_syntax_review():
    py_compile.compile(r"d:\software\PyCharm 2025.3.5\file_saves\genmini\pages\3_📝_错题复习.py", doraise=True)

def test_syntax_stats():
    py_compile.compile(r"d:\software\PyCharm 2025.3.5\file_saves\genmini\pages\4_📊_学习统计.py", doraise=True)

def test_syntax_settings():
    py_compile.compile(r"d:\software\PyCharm 2025.3.5\file_saves\genmini\pages\5_⚙️_设置.py", doraise=True)

def test_syntax_dictation():
    py_compile.compile(r"d:\software\PyCharm 2025.3.5\file_saves\genmini\pages\6_✍️_默写模式.py", doraise=True)

def test_syntax_admin():
    py_compile.compile(r"d:\software\PyCharm 2025.3.5\file_saves\genmini\pages\7_👑_管理员.py", doraise=True)

def test_syntax_editor():
    py_compile.compile(r"d:\software\PyCharm 2025.3.5\file_saves\genmini\pages\8_✏️_题库编辑.py", doraise=True)

def test_syntax_interview():
    py_compile.compile(r"d:\software\PyCharm 2025.3.5\file_saves\genmini\pages\9_🎤_模拟面试.py", doraise=True)

test("app.py 语法", test_syntax_app)
test("登录页面 语法", test_syntax_login)
test("抽题模式 语法", test_syntax_quiz)
test("背题模式 语法", test_syntax_browse)
test("错题复习 语法", test_syntax_review)
test("学习统计 语法", test_syntax_stats)
test("设置页面 语法", test_syntax_settings)
test("默写模式 语法", test_syntax_dictation)
test("管理员页面 语法", test_syntax_admin)
test("题库编辑 语法", test_syntax_editor)
test("模拟面试 语法", test_syntax_interview)


# ==========================================
# 汇总报告
# ==========================================
print("\n" + "=" * 60)
print("📊 测试汇总报告")
print("=" * 60)
print(f"  ✅ 通过: {PASS}")
print(f"  ❌ 失败: {FAIL}")
print(f"  📋 总计: {PASS + FAIL}")

if ERRORS:
    print("\n❌ 失败详情:")
    for name, err in ERRORS:
        print(f"  - {name}: {err}")
else:
    print("\n🎉 所有测试通过！")

sys.exit(0 if FAIL == 0 else 1)
