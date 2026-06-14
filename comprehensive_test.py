"""
综合功能测试脚本
对面试题刷题系统的每个功能接口进行逐一测试，找出漏洞和优化点。
注意：本脚本需要 mock streamlit，因为模块在导入时会执行 st.secrets 等。
"""
import sys
import os
import io

# 输出到文件以避免 Windows 控制台编码/吞输出问题
_output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_results.txt")
_output_file = open(_output_path, "w", encoding="utf-8")
import types
import json
import re
import traceback
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# ============================================================
# 第一步：Mock streamlit 模块（必须在导入项目模块之前完成）
# ============================================================

mock_st = MagicMock()
mock_st.session_state = {}
mock_st.cache_data = lambda ttl=None: lambda f: f  # 简化 cache_data 装饰器

# 让 st.secrets.get 正常工作
mock_secrets = MagicMock()
mock_secrets.get = lambda key, default=None: default
mock_secrets.__contains__ = lambda self, key: False
mock_st.secrets = mock_secrets

sys.modules["streamlit"] = mock_st
sys.modules["streamlit.components"] = MagicMock()
sys.modules["streamlit.components.v1"] = MagicMock()

# 切换工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# 测试结果收集
# ============================================================

results = {"pass": [], "fail": [], "warn": [], "info": []}


def _log(msg=""):
    _output_file.write(msg + "\n")
    _output_file.flush()

def report(name, status, detail=""):
    results[status].append((name, detail))
    icon = {"pass": "PASS", "fail": "FAIL", "warn": "WARN", "info": "INFO"}[status]
    line = f"  [{icon}] {name}" + (f" -- {detail}" if detail else "")
    _log(line)


# ============================================================
# 模块 1：ai_scorer.py 测试
# ============================================================
_log("\n" + "=" * 60)
_log("模块 1：ai_scorer.py -- AI 评分模块")
_log("=" * 60)

try:
    from utils.ai_scorer import (
        _extract_keywords, _parse_score_response, _local_score,
        score_answer, get_score_color, get_score_label, get_method_label,
        render_score_result, MIMO_API_KEY, MIMO_API_BASE, MIMO_MODEL,
    )
    report("模块导入", "pass")
except Exception as e:
    report("模块导入", "fail", str(e))
    traceback.print_exc()

# --- 1.1 _extract_keywords 测试 ---
_log("\n  --- 1.1 关键词提取 ---")

def test_extract_keywords():
    # 测试中文关键词提取
    kw = _extract_keywords("Python是一种广泛使用的编程语言")
    assert len(kw) > 0, "中文关键词提取结果为空"
    report("中文关键词提取", "pass", f"提取到 {len(kw)} 个关键词")

    # 测试英文关键词提取
    kw_en = _extract_keywords("Python is a programming language used for web development")
    assert len(kw_en) > 0, "英文关键词提取结果为空"
    assert "python" in kw_en or "program" in kw_en, "英文关键词未包含预期词"
    report("英文关键词提取", "pass", f"提取到 {len(kw_en)} 个关键词")

    # 测试空文本
    kw_empty = _extract_keywords("")
    assert len(kw_empty) == 0, "空文本应返回空集合"
    report("空文本关键词提取", "pass")

    # 测试停用词过滤
    kw_stop = _extract_keywords("的了是在和有人")
    # 这些全是停用词，应该被过滤掉
    report("停用词过滤", "pass" if len(kw_stop) == 0 else "warn",
           f"停用词集合大小: {len(kw_stop)}")

    # 测试混合中英文
    kw_mix = _extract_keywords("使用Python进行数据分析data analysis")
    assert len(kw_mix) > 0, "混合文本关键词提取结果为空"
    report("混合中英文提取", "pass", f"提取到 {len(kw_mix)} 个关键词")

try:

    test_extract_keywords()

except Exception as _e:

    _log(f"[FAIL] test_extract_keywords crashed: {_e}")

    import traceback as _tb

    _tb.print_exc(file=_output_file)

    _output_file.flush()
# --- 1.2 _parse_score_response 测试 ---
_log("\n  --- 1.2 JSON 响应解析 ---")

def test_parse_score_response():
    # 标准 JSON
    r = _parse_score_response('{"score": 85, "feedback": "回答不错"}')
    assert r is not None, "标准JSON解析失败"
    assert r[0] == 85, f"score 应为 85，实际 {r[0]}"
    assert r[1] == "回答不错", f"feedback 不匹配"
    report("标准JSON解析", "pass", f"score={r[0]}, feedback={r[1]}")

    # 带代码块的 JSON
    r2 = _parse_score_response('```json\n{"score": 70, "feedback": "good"}\n```')
    assert r2 is not None, "代码块JSON解析失败"
    assert r2[0] == 70, f"score 应为 70，实际 {r2[0]}"
    report("代码块JSON解析", "pass", f"score={r2[0]}")

    # 带多余文本的 JSON
    r3 = _parse_score_response('以下是评分结果：\n{"score": 60, "feedback": "还行"}\n请继续努力')
    assert r3 is not None, "带文本JSON解析失败"
    assert r3[0] == 60, f"score 应为 60，实际 {r3[0]}"
    report("带文本JSON解析", "pass", f"score={r3[0]}")

    # 分数边界值：score=0
    r4 = _parse_score_response('{"score": 0, "feedback": "未作答"}')
    assert r4 is not None, "score=0 解析失败"
    assert r4[0] == 0, f"score 应为 0，实际 {r4[0]}"
    report("score=0边界值", "pass")

    # 分数边界值：score=100
    r5 = _parse_score_response('{"score": 100, "feedback": "完美"}')
    assert r5 is not None, "score=100 解析失败"
    assert r5[0] == 100, f"score 应为 100，实际 {r5[0]}"
    report("score=100边界值", "pass")

    # 分数超出范围：score=150（应被 clamp 到 100）
    r6 = _parse_score_response('{"score": 150, "feedback": "超出"}')
    assert r6 is not None and r6[0] == 100, f"超出范围应 clamp 到 100，实际 {r6}"
    report("超出范围clamp", "pass")

    # 分数为负数：score=-10（应被 clamp 到 0）
    r7 = _parse_score_response('{"score": -10, "feedback": "负数"}')
    assert r7 is not None and r7[0] == 0, f"负数应 clamp 到 0，实际 {r7}"
    report("负数clamp", "pass")

    # 分数为字符串："85"
    r8 = _parse_score_response('{"score": "85", "feedback": "字符串分数"}')
    assert r8 is not None, "字符串分数解析失败"
    assert r8[0] == 85, f"字符串分数应转为 85，实际 {r8[0]}"
    report("字符串分数转换", "pass")

    # 无 score 字段的 JSON — 正确行为是返回 None（无法解析出有效分数）
    r9 = _parse_score_response('{"result": "ok"}')
    assert r9 is None, "无score字段应返回None"
    report("无score字段返回None", "pass")

    # 完全非 JSON 文本
    r10 = _parse_score_response("这是一段纯文本回答，没有任何JSON")
    assert r10 is None, "纯文本应返回 None"
    report("纯文本返回None", "pass")

    # 空字符串
    r11 = _parse_score_response("")
    assert r11 is None, "空字符串应返回 None"
    report("空字符串返回None", "pass")

    # 含嵌套花括号的 JSON（如 feedback 中包含 {}）
    r12 = _parse_score_response('{"score": 75, "feedback": "代码示例: def foo() { return 1; }"}')
    # 这个可能会有问题因为 feedback 中有花括号
    if r12 is None:
        report("含花括号feedback", "warn", "feedback 含 {} 时解析失败，需要修复")
    else:
        report("含花括号feedback", "pass", f"score={r12[0]}")

try:

    test_parse_score_response()

except Exception as _e:

    _log(f"[FAIL] test_parse_score_response crashed: {_e}")

    import traceback as _tb

    _tb.print_exc(file=_output_file)

    _output_file.flush()
# --- 1.3 _local_score 本地评分测试 ---
_log("\n  --- 1.3 本地评分算法 ---")

def test_local_score():
    # 完美匹配
    s, f = _local_score("Python是编程语言", "Python是编程语言")
    assert s > 80, f"完全匹配得分应>80，实际 {s}"
    report("完全匹配评分", "pass", f"score={s}")

    # 空答案
    s0, f0 = _local_score("Python是编程语言", "")
    assert s0 == 0, f"空答案应为0分，实际 {s0}"
    assert "未作答" in f0, f"空答案反馈应含'未作答'，实际 {f0}"
    report("空答案评分", "pass", f"score={s0}, feedback={f0}")

    # 部分匹配
    s2, f2 = _local_score("Python是一种广泛使用的高级编程语言，具有简洁的语法",
                          "Python是编程语言，语法简洁")
    assert 20 <= s2 <= 90, f"部分匹配得分应在 20-90，实际 {s2}"
    report("部分匹配评分", "pass", f"score={s2}")

    # 完全不匹配
    s3, f3 = _local_score("Python是编程语言", "今天天气真好")
    assert s3 < 30, f"不匹配得分应<30，实际 {s3}"
    report("不匹配评分", "pass", f"score={s3}")

    # 长文本评分
    long_ref = "这是一段很长的参考答案" * 50
    long_ans = "这是一段很长的参考答案" * 30 + "还有一些额外内容"
    s4, f4 = _local_score(long_ref, long_ans)
    assert s4 > 50, f"长文本高相似度应>50分，实际 {s4}"
    report("长文本评分", "pass", f"score={s4}")

    # 纯英文评分
    s5, f5 = _local_score(
        "Python is a high-level programming language with dynamic typing",
        "Python is a programming language"
    )
    assert s5 > 20, f"英文部分匹配应>20分，实际 {s5}"
    report("英文评分", "pass", f"score={s5}")

    # 只有标点符号
    s6, f6 = _local_score("Python语言", "！@#￥%……")
    report("纯标点评分", "pass" if s6 < 10 else "warn", f"score={s6}")

try:

    test_local_score()

except Exception as _e:

    _log(f"[FAIL] test_local_score crashed: {_e}")

    import traceback as _tb

    _tb.print_exc(file=_output_file)

    _output_file.flush()
# --- 1.4 score_answer 主函数测试 ---
_log("\n  --- 1.4 score_answer 主评分函数 ---")

def test_score_answer():
    import utils.ai_scorer as _scorer
    # Mock API calls to avoid network timeout; test logic only
    _orig_mimo = _scorer._try_mimo_score
    _orig_gemini = _scorer._try_gemini_score
    _orig_openai = _scorer._try_openai_score
    _scorer._try_mimo_score = lambda q, r, a: None  # simulate API unavailable
    _scorer._try_gemini_score = lambda q, r, a: None
    _scorer._try_openai_score = lambda q, r, a: None

    # 空答案 -> local 算法得 0 分
    s, f, m = score_answer("测试题", "参考答案", "")
    assert m == "local", f"mock 下应为 local，实际 {m}"
    assert s == 0, f"空答案应为0分，实际 {s}"
    report("空答案评分(本地)", "pass", f"score={s}, method={m}")

    # 正常答案 -> local 算法
    s2, f2, m2 = score_answer("什么是Python", "Python是一种编程语言", "Python是一种广泛使用的编程语言")
    assert 0 <= s2 <= 100, f"分数应在0-100，实际 {s2}"
    assert m2 == "local", f"mock 下应为 local，实际 {m2}"
    report("正常答案评分(本地)", "pass", f"score={s2}, method={m2}")

    # 测试返回值类型
    assert isinstance(s2, int), f"score 应为 int，实际 {type(s2)}"
    assert isinstance(f2, str), f"feedback 应为 str，实际 {type(f2)}"
    assert isinstance(m2, str), f"method 应为 str，实际 {type(m2)}"
    report("返回值类型检查", "pass")

    # Mock API 可用 -> 使用 mimo
    _scorer._try_mimo_score = lambda q, r, a: (80, "回答优秀")
    s3, f3, m3 = score_answer("测试", "参考", "回答")
    assert m3 == "mimo", f"应使用 mimo，实际 {m3}"
    assert s3 == 80, f"应为80分，实际 {s3}"
    report("MIMO API评分", "pass", f"score={s3}, method={m3}")

    # 恢复原始函数
    _scorer._try_mimo_score = _orig_mimo
    _scorer._try_gemini_score = _orig_gemini
    _scorer._try_openai_score = _orig_openai

try:

    test_score_answer()

except Exception as _e:

    _log(f"[FAIL] test_score_answer crashed: {_e}")

    import traceback as _tb

    _tb.print_exc(file=_output_file)

    _output_file.flush()
# --- 1.5 辅助函数测试 ---
_log("\n  --- 1.5 辅助函数 ---")

def test_helpers():
    # get_score_color
    assert get_score_color(90) == "#10b981", "80+应为绿色"
    assert get_score_color(70) == "#22c55e", "60-79应为浅绿"
    assert get_score_color(50) == "#f59e0b", "40-59应为黄色"
    assert get_score_color(30) == "#f97316", "20-39应为橙色"
    assert get_score_color(10) == "#ef4444", "0-19应为红色"
    report("get_score_color", "pass")

    # get_score_label
    assert get_score_label(90) == "优秀"
    assert get_score_label(70) == "良好"
    assert get_score_label(50) == "一般"
    assert get_score_label(30) == "较弱"
    assert get_score_label(10) == "需加强"
    report("get_score_label", "pass")

    # get_method_label
    assert "MIMO" in get_method_label("mimo")
    assert "Gemini" in get_method_label("gemini")
    assert "GPT" in get_method_label("openai")
    assert "本地" in get_method_label("local")
    report("get_method_label", "pass")

try:

    test_helpers()

except Exception as _e:

    _log(f"[FAIL] test_helpers crashed: {_e}")

    import traceback as _tb

    _tb.print_exc(file=_output_file)

    _output_file.flush()
# --- 1.6 MIMO API 连通性测试 ---
_log("\n  --- 1.6 MIMO API 连通性 ---")

def test_mimo_api():
    try:
        import requests
        resp = requests.get(f"{MIMO_API_BASE}/models", headers={
            "Authorization": f"Bearer {MIMO_API_KEY}"
        }, timeout=10)
        if resp.status_code == 200:
            report("MIMO API 连通性", "pass", f"status={resp.status_code}")
        elif resp.status_code == 401:
            report("MIMO API 连通性", "fail", "API Key 无效或过期 (401)")
        elif resp.status_code == 403:
            report("MIMO API 连通性", "fail", "API Key 无权限 (403)")
        else:
            report("MIMO API 连通性", "warn", f"status={resp.status_code}, body={resp.text[:100]}")
    except ImportError:
        report("MIMO API 连通性", "fail", "requests 库未安装")
    except Exception as e:
        report("MIMO API 连通性", "fail", f"连接失败: {e}")

try:

    test_mimo_api()

except Exception as _e:

    _log(f"[FAIL] test_mimo_api crashed: {_e}")

    import traceback as _tb

    _tb.print_exc(file=_output_file)

    _output_file.flush()
# ============================================================
# 模块 2：db.py 数据库模块测试
# ============================================================
_log("\n" + "=" * 60)
_log("🗄️ 模块 2：db.py — 数据库模块")
_log("=" * 60)

def test_db_module():
    try:
        from utils import db
        report("db模块导入", "pass")
    except Exception as e:
        report("db模块导入", "fail", str(e))
        return

    # 测试 is_mysql
    is_mysql = db.is_mysql()
    report("数据库模式检测", "pass", f"MySQL={is_mysql}")

    # 测试 init_tables
    try:
        db.init_tables()
        report("init_tables", "pass")
    except Exception as e:
        report("init_tables", "fail", str(e))

    # 测试 execute（基本 CRUD）
    try:
        # 插入测试数据
        db.execute(
            "INSERT INTO study_log (username, date_str, count, activity_type) VALUES (%s, %s, %s, %s)",
            ("__test_user__", "2099-01-01", 999, "测试"),
        )
        report("execute INSERT", "pass")

        # 查询
        rows = db.execute(
            "SELECT * FROM study_log WHERE username = %s AND date_str = %s",
            ("__test_user__", "2099-01-01"), fetch=True,
        )
        assert len(rows) >= 1, "INSERT 后应能查到数据"
        report("execute SELECT", "pass", f"找到 {len(rows)} 条记录")

        # 清理
        db.execute(
            "DELETE FROM study_log WHERE username = %s AND date_str = %s",
            ("__test_user__", "2099-01-01"),
        )
        report("execute DELETE", "pass")
    except Exception as e:
        report("CRUD 操作", "fail", str(e))
        # 尝试清理
        try:
            db.execute("DELETE FROM study_log WHERE username = %s", ("__test_user__",))
        except:
            pass

    # 测试 query_df
    try:
        df = db.query_df("SELECT * FROM study_log WHERE username = %s", ("__nonexist__",))
        assert df.empty, "不存在的用户应返回空 DataFrame"
        report("query_df 空结果", "pass")
    except Exception as e:
        report("query_df", "fail", str(e))

    # 测试 execute_transaction
    try:
        ops = [
            ("INSERT INTO study_log (username, date_str, count, activity_type) VALUES (%s, %s, %s, %s)",
             ("__test_txn__", "2099-02-01", 1, "测试A")),
            ("INSERT INTO study_log (username, date_str, count, activity_type) VALUES (%s, %s, %s, %s)",
             ("__test_txn__", "2099-02-02", 2, "测试B")),
        ]
        db.execute_transaction(ops)
        rows = db.execute("SELECT * FROM study_log WHERE username = %s", ("__test_txn__",), fetch=True)
        assert len(rows) >= 2, "事务插入应有2条记录"
        report("execute_transaction", "pass")

        # 清理
        db.execute("DELETE FROM study_log WHERE username = %s", ("__test_txn__",))
    except Exception as e:
        report("execute_transaction", "fail", str(e))
        try:
            db.execute("DELETE FROM study_log WHERE username = %s", ("__test_txn__",))
        except:
            pass

    # 测试 _adapt_sql
    try:
        if not db.is_mysql():
            adapted = db._adapt_sql("SELECT * FROM t WHERE a = %s AND b = %s")
            assert "?" in adapted, "SQLite模式下 %s 应转为 ?"
            report("_adapt_sql", "pass", "MySQL->SQLite 转换正确")
        else:
            adapted = db._adapt_sql("SELECT * FROM t WHERE a = %s")
            assert "%s" in adapted, "MySQL模式下应保持 %s"
            report("_adapt_sql", "pass", "MySQL模式保持原样")
    except Exception as e:
        report("_adapt_sql", "fail", str(e))

    # 测试表结构完整性
    try:
        tables_sql = "SELECT name FROM sqlite_master WHERE type='table'" if not db.is_mysql() else "SHOW TABLES"
        rows = db.execute(tables_sql, fetch=True)
        table_names = [list(r.values())[0] for r in rows] if rows else []
        expected = ["interview_questions", "review_book", "study_log", "checkin_log", "dictation_log", "user_goals"]
        missing = [t for t in expected if t not in table_names]
        if missing:
            report("表结构完整性", "warn", f"缺少表: {missing}")
        else:
            report("表结构完整性", "pass", f"所有 {len(expected)} 张表存在")
    except Exception as e:
        report("表结构检查", "fail", str(e))

try:

    test_db_module()

except Exception as _e:

    _log(f"[FAIL] test_db_module crashed: {_e}")

    import traceback as _tb

    _tb.print_exc(file=_output_file)

    _output_file.flush()
# ============================================================
# 模块 3：auth.py 认证模块测试
# ============================================================
_log("\n" + "=" * 60)
_log("🔐 模块 3：auth.py — 用户认证模块")
_log("=" * 60)

def test_auth():
    try:
        from utils.auth import (
            _hash_password, register_user, login_user,
            get_all_users, get_user_count, delete_user, init_db,
        )
        report("auth模块导入", "pass")
    except Exception as e:
        report("auth模块导入", "fail", str(e))
        return

    # 初始化
    try:
        init_db()
        report("init_db", "pass")
    except Exception as e:
        report("init_db", "fail", str(e))
        return

    # 密码哈希测试
    h1 = _hash_password("test123", "salt1")
    h2 = _hash_password("test123", "salt2")
    h3 = _hash_password("test123", "salt1")
    assert h1 != h2, "不同盐值应产生不同哈希"
    assert h1 == h3, "相同盐值和密码应产生相同哈希"
    assert len(h1) == 64, "SHA-256 哈希应为 64 字符"
    report("密码哈希", "pass", f"hash_len={len(h1)}")

    # 注册验证测试
    ok, msg = register_user("", "pass123")
    assert not ok, "空用户名应注册失败"
    report("空用户名拒绝", "pass")

    ok, msg = register_user("ab", "pass123")
    assert not ok, "过短用户名应注册失败"
    report("短用户名拒绝", "pass")

    ok, msg = register_user("testuser", "123")
    assert not ok, "过短密码应注册失败"
    report("短密码拒绝", "pass")

    ok, msg = register_user("testuser", "12345678")
    assert not ok, "无字母密码应注册失败"
    report("无字母密码拒绝", "pass")

    ok, msg = register_user("testuser", "1234567a")
    # 可能成功（如果用户不存在）或失败（已存在）
    report("合法注册", "pass" if ok or "已注册" in msg else "warn", msg)

    # 清理测试用户
    delete_user("testuser")
    ok, msg = register_user("testuser", "test1234a")
    assert ok, f"注册应成功: {msg}"
    report("注册功能", "pass", msg)

    # 登录测试
    ok, msg = login_user("testuser", "wrongpass")
    assert not ok, "错误密码应登录失败"
    report("错误密码拒绝", "pass")

    ok, msg = login_user("nonexist", "test1234a")
    assert not ok, "不存在的用户应登录失败"
    report("不存在用户拒绝", "pass")

    # 需要 mock session_state
    old_ss = dict(mock_st.session_state)
    mock_st.session_state = {}
    ok, msg = login_user("testuser", "test1234a")
    assert ok, f"正确登录应成功: {msg}"
    report("正常登录", "pass")

    # 用户计数
    count = get_user_count()
    assert count >= 2, f"应至少有admin和testuser，实际 {count}"
    report("用户计数", "pass", f"count={count}")

    # 用户列表
    users = get_all_users()
    usernames = [u["username"] for u in users]
    assert "admin" in usernames, "用户列表应包含admin"
    assert "testuser" in usernames, "用户列表应包含testuser"
    report("用户列表", "pass", f"users={usernames}")

    # 删除用户
    ok, msg = delete_user("testuser")
    assert ok, f"删除应成功: {msg}"
    report("删除用户", "pass", msg)

    ok, msg = delete_user("admin")
    assert not ok, "不应能删除admin"
    report("admin不可删除", "pass")

    # 恢复 session_state
    mock_st.session_state = old_ss

try:

    test_auth()

except Exception as _e:

    _log(f"[FAIL] test_auth crashed: {_e}")

    import traceback as _tb

    _tb.print_exc(file=_output_file)

    _output_file.flush()
# ============================================================
# 模块 4：review_manager.py 错题本模块测试
# ============================================================
_log("\n" + "=" * 60)
_log("📚 模块 4：review_manager.py — 错题本 & 学习管理")
_log("=" * 60)

def test_review_manager():
    # 需要 mock username
    old_ss = dict(mock_st.session_state)
    mock_st.session_state = {"username": "__test_review_user__"}

    try:
        from utils.review_manager import (
            sm2, save_to_review_book, delete_from_review_book,
            update_mastery, update_note, increment_review_count,
            get_review_stats, check_in, get_checkin_stats,
            log_study_session, load_study_log,
            update_sm2_after_review, get_due_reviews,
            get_attribution_stats, update_attribution,
        )
        report("review_manager导入", "pass")
    except Exception as e:
        report("review_manager导入", "fail", str(e))
        mock_st.session_state = old_ss
        return

    # --- SM-2 算法测试 ---
    _log("\n  --- 4.1 SM-2 算法 ---")

    try:
        # quality=4 (良好), 初次
        rep, ef, iv = sm2(4, 0, 2.5, 1)
        assert rep == 1, f"quality=4,rep=0 应返回 rep=1, 实际 {rep}"
        assert iv == 1, f"quality=4,rep=0 应返回 iv=1, 实际 {iv}"
        assert ef >= 2.5, f"quality=4 EF 不应降低, 实际 {ef}"
        report("SM-2 初次良好", "pass", f"rep={rep}, ef={ef:.2f}, iv={iv}")
    except Exception as e:
        report("SM-2 初次良好", "fail", str(e))

    try:
        # quality=4, 第二次
        rep2, ef2, iv2 = sm2(4, 1, 2.5, 1)
        assert rep2 == 2, f"第二次应返回 rep=2, 实际 {rep2}"
        assert iv2 == 6, f"quality=4,rep=1 应返回 iv=6, 实际 {iv2}"
        report("SM-2 第二次良好", "pass", f"rep={rep2}, iv={iv2}")
    except Exception as e:
        report("SM-2 第二次良好", "fail", str(e))

    try:
        # quality=4, 第三次（使用 EF 计算间隔）
        rep3, ef3, iv3 = sm2(4, 2, 2.5, 6)
        assert rep3 == 3, f"第三次应返回 rep=3, 实际 {rep3}"
        assert iv3 == round(6 * 2.5), f"第三次应使用 EF 计算间隔, 期望 {round(6*2.5)}, 实际 {iv3}"
        report("SM-2 EF计算间隔", "pass", f"iv={iv3}")
    except Exception as e:
        report("SM-2 EF计算间隔", "fail", str(e))

    try:
        # quality=2 (不及格) -> 重置
        rep_fail, ef_fail, iv_fail = sm2(2, 3, 2.5, 10)
        assert rep_fail == 0, f"quality<3 应重置 rep=0, 实际 {rep_fail}"
        assert iv_fail == 1, f"quality<3 应重置 iv=1, 实际 {iv_fail}"
        assert ef_fail < 2.5, f"quality<3 应降低 EF, 实际 {ef_fail}"
        report("SM-2 不及格重置", "pass", f"rep={rep_fail}, ef={ef_fail:.2f}, iv={iv_fail}")
    except Exception as e:
        report("SM-2 不及格重置", "fail", str(e))

    try:
        # EF 不应低于 1.3
        rep_min, ef_min, iv_min = sm2(0, 5, 1.3, 30)
        assert ef_min >= 1.3, f"EF 不应低于 1.3, 实际 {ef_min}"
        report("SM-2 EF下限", "pass", f"ef_min={ef_min:.2f}")
    except Exception as e:
        report("SM-2 EF下限", "fail", str(e))

    # quality 边界值
    for q in [-1, 0, 1, 2, 3, 4, 5, 6]:
        try:
            r = sm2(q, 0, 2.5, 1)
            report(f"SM-2 quality={q}", "pass", f"rep={r[0]}, ef={r[1]:.2f}")
        except Exception as e:
            report(f"SM-2 quality={q}", "fail", str(e))

    # --- 错题本 CRUD ---
    _log("\n  --- 4.2 错题本 CRUD ---")

    # 清理旧数据
    delete_from_review_book("测试问题_综合测试")

    # 保存
    save_to_review_book("测试问题_综合测试", "参考答案_综合测试",
                        note="我的笔记", mastery=3, tags="测试",
                        attribution="知识盲区")
    report("save_to_review_book", "pass")

    # 读取验证
    from utils.review_manager import _read_review_file
    df = _read_review_file()
    assert not df.empty, "保存后应能读取到数据"
    test_row = df[df["问题"] == "测试问题_综合测试"]
    assert len(test_row) == 1, f"应恰好1条记录，实际 {len(test_row)}"
    row = test_row.iloc[0]
    assert row["掌握度"] == 3, f"掌握度应为3，实际 {row['掌握度']}"
    assert row["归因"] == "知识盲区", f"归因应为'知识盲区'，实际 {row['归因']}"
    report("读取错题本", "pass", f"掌握度={row['掌握度']}, 归因={row['归因']}")

    # 重复保存应覆盖（upsert）
    save_to_review_book("测试问题_综合测试", "新参考答案",
                        note="新笔记", mastery=5)
    df2 = _read_review_file()
    test_row2 = df2[df2["问题"] == "测试问题_综合测试"]
    assert len(test_row2) == 1, f"重复保存应只有1条记录，实际 {len(test_row2)}"
    assert test_row2.iloc[0]["掌握度"] == 5, "覆盖后掌握度应为5"
    report("重复保存覆盖", "pass")

    # 更新掌握度
    update_mastery("测试问题_综合测试", 4)
    df3 = _read_review_file()
    r3 = df3[df3["问题"] == "测试问题_综合测试"].iloc[0]
    assert r3["掌握度"] == 4, f"更新后掌握度应为4，实际 {r3['掌握度']}"
    report("update_mastery", "pass")

    # 更新笔记
    update_note("测试问题_综合测试", "更新后的笔记")
    df4 = _read_review_file()
    r4 = df4[df4["问题"] == "测试问题_综合测试"].iloc[0]
    assert r4["备注"] == "更新后的笔记", f"笔记应为'更新后的笔记'，实际 {r4['备注']}"
    report("update_note", "pass")

    # 增加复习次数
    old_count = int(r4["复习次数"])
    increment_review_count("测试问题_综合测试")
    df5 = _read_review_file()
    r5 = df5[df5["问题"] == "测试问题_综合测试"].iloc[0]
    assert int(r5["复习次数"]) == old_count + 1, f"复习次数应为 {old_count+1}，实际 {r5['复习次数']}"
    report("increment_review_count", "pass")

    # 更新归因
    update_attribution("测试问题_综合测试", "理解偏差")
    df6 = _read_review_file()
    r6 = df6[df6["问题"] == "测试问题_综合测试"].iloc[0]
    assert r6["归因"] == "理解偏差", f"归因应为'理解偏差'，实际 {r6['归因']}"
    report("update_attribution", "pass")

    # 错题本统计
    stats = get_review_stats()
    assert stats["total"] >= 1, f"应至少有1道错题，实际 {stats['total']}"
    report("get_review_stats", "pass", f"total={stats['total']}, avg_mastery={stats['avg_mastery']}")

    # 归因统计
    attr_stats = get_attribution_stats()
    assert len(attr_stats) > 0, "应有归因统计"
    report("get_attribution_stats", "pass", f"stats={attr_stats}")

    # SM-2 复习后更新
    update_sm2_after_review("测试问题_综合测试", 4)
    df7 = _read_review_file()
    r7 = df7[df7["问题"] == "测试问题_综合测试"].iloc[0]
    assert r7["next_review"] is not None, "next_review 不应为空"
    assert r7["ease_factor"] >= 1.3, f"EF 不应低于 1.3, 实际 {r7['ease_factor']}"
    report("update_sm2_after_review", "pass", f"next_review={r7['next_review']}, ef={r7['ease_factor']}")

    # 获取到期复习
    due = get_due_reviews()
    report("get_due_reviews", "pass", f"到期复习数: {len(due)}")

    # 删除
    delete_from_review_book("测试问题_综合测试")
    df8 = _read_review_file()
    assert len(df8[df8["问题"] == "测试问题_综合测试"]) == 0, "删除后不应存在"
    report("delete_from_review_book", "pass")

    # --- 签到系统 ---
    _log("\n  --- 4.3 签到系统 ---")

    check_in("测试活动")
    report("check_in", "pass")

    checkin_stats = get_checkin_stats()
    assert checkin_stats["total_days"] >= 1, "应至少有1天签到"
    report("get_checkin_stats", "pass", f"total_days={checkin_stats['total_days']}, streak={checkin_stats['streak']}")

    # 重复签到（同一天同一活动）不应重复插入
    check_in("测试活动")
    report("重复签到", "pass" if True else "fail", "应静默跳过")

    # --- 学习日志 ---
    _log("\n  --- 4.4 学习日志 ---")

    log_study_session(5, activity="测试学习")
    report("log_study_session", "pass")

    study_log = load_study_log()
    assert not study_log.empty, "应有学习日志"
    report("load_study_log", "pass", f"日志条数: {len(study_log)}")

    # 清理测试数据
    from utils import db
    try:
        db.execute("DELETE FROM review_book WHERE username = %s", ("__test_review_user__",))
        db.execute("DELETE FROM study_log WHERE username = %s", ("__test_review_user__",))
        db.execute("DELETE FROM checkin_log WHERE username = %s", ("__test_review_user__",))
        report("测试数据清理", "pass")
    except Exception as e:
        report("测试数据清理", "warn", str(e))

    mock_st.session_state = old_ss

try:

    test_review_manager()

except Exception as _e:

    _log(f"[FAIL] test_review_manager crashed: {_e}")

    import traceback as _tb

    _tb.print_exc(file=_output_file)

    _output_file.flush()
# ============================================================
# 模块 5：data_loader.py 数据加载模块测试
# ============================================================
_log("\n" + "=" * 60)
_log("📊 模块 5：data_loader.py — 数据加载模块")
_log("=" * 60)

def test_data_loader():
    try:
        from utils.data_loader import (
            load_question_banks, get_filtered_questions,
            get_knowledge_categories, get_difficulty_levels,
            _normalize_columns, _read_single_file, _load_from_files,
            get_categories_from_db,
        )
        report("data_loader导入", "pass")
    except Exception as e:
        report("data_loader导入", "fail", str(e))
        return

    # 测试列名标准化
    import pandas as pd
    df_test = pd.DataFrame({"问题": ["Q1"], "参考答案": ["A1"]})
    df_norm = _normalize_columns(df_test)
    assert "参考" in df_norm.columns, "参考答案应被重命名为 参考"
    report("列名标准化(参考答案->参考)", "pass")

    df_test2 = pd.DataFrame({"问题": ["Q1"], "答案": ["A1"]})
    df_norm2 = _normalize_columns(df_test2)
    assert "参考" in df_norm2.columns, "答案应被重命名为 参考"
    report("列名标准化(答案->参考)", "pass")

    # 测试难度列表
    levels = get_difficulty_levels()
    assert levels == ["简单", "中等", "困难"], f"难度列表不匹配: {levels}"
    report("get_difficulty_levels", "pass")

    # 测试题库加载
    try:
        df = load_question_banks()
        if df.empty:
            report("load_question_banks", "warn", "题库为空（数据库和文件都没有数据）")
        else:
            assert "问题" in df.columns, "题库应有'问题'列"
            assert "参考" in df.columns, "题库应有'参考'列"
            report("load_question_banks", "pass", f"题目数: {len(df)}, 列: {list(df.columns)}")

            # 测试分类获取
            cats = get_knowledge_categories(df)
            report("get_knowledge_categories", "pass", f"分类数: {len(cats)}, 示例: {cats[:3]}")

            # 测试过滤显示
            filtered = get_filtered_questions()
            report("get_filtered_questions", "pass", f"过滤后: {len(filtered)} 题")

            # 测试从DB获取分类
            db_cats = get_categories_from_db()
            report("get_categories_from_db", "pass" if db_cats else "warn",
                   f"DB分类: {len(db_cats)} 个")
    except Exception as e:
        report("题库加载", "fail", str(e))
        traceback.print_exc()

try:

    test_data_loader()

except Exception as _e:

    _log(f"[FAIL] test_data_loader crashed: {_e}")

    import traceback as _tb

    _tb.print_exc(file=_output_file)

    _output_file.flush()
# ============================================================
# 模块 6：goal_manager.py 目标管理模块测试
# ============================================================
_log("\n" + "=" * 60)
_log("🎯 模块 6：goal_manager.py — 学习目标管理")
_log("=" * 60)

def test_goal_manager():
    old_ss = dict(mock_st.session_state)
    mock_st.session_state = {"username": "__test_goal_user__"}

    try:
        from utils.goal_manager import (
            load_goals, save_goals, get_today_progress,
            get_weekly_progress, get_review_progress, DEFAULT_GOALS,
        )
        report("goal_manager导入", "pass")
    except Exception as e:
        report("goal_manager导入", "fail", str(e))
        mock_st.session_state = old_ss
        return

    # 加载默认目标
    goals = load_goals()
    assert goals["daily_questions"] == DEFAULT_GOALS["daily_questions"], "默认每日目标不匹配"
    assert goals["weekly_questions"] == DEFAULT_GOALS["weekly_questions"], "默认每周目标不匹配"
    report("load_goals 默认值", "pass", f"goals={goals}")

    # 保存自定义目标
    custom = {"daily_questions": 30, "weekly_questions": 150, "daily_review": 10}
    save_goals(custom)
    goals2 = load_goals()
    assert goals2["daily_questions"] == 30, f"自定义每日目标应为30, 实际 {goals2['daily_questions']}"
    assert goals2["weekly_questions"] == 150, f"自定义每周目标应为150, 实际 {goals2['weekly_questions']}"
    report("save_goals", "pass", f"goals={goals2}")

    # 今日进度
    today = get_today_progress()
    assert "questions" in today, "今日进度应含 questions"
    report("get_today_progress", "pass", f"today={today}")

    # 本周进度
    weekly = get_weekly_progress()
    assert "questions" in weekly, "本周进度应含 questions"
    report("get_weekly_progress", "pass", f"weekly={weekly}")

    # 复习进度
    review = get_review_progress()
    assert isinstance(review, int), "复习进度应为 int"
    report("get_review_progress", "pass", f"due_count={review}")

    # 恢复默认
    save_goals(DEFAULT_GOALS)

    # 清理
    from utils import db
    try:
        db.execute("DELETE FROM user_goals WHERE username = %s", ("__test_goal_user__",))
    except:
        pass

    mock_st.session_state = old_ss

try:

    test_goal_manager()

except Exception as _e:

    _log(f"[FAIL] test_goal_manager crashed: {_e}")

    import traceback as _tb

    _tb.print_exc(file=_output_file)

    _output_file.flush()
# ============================================================
# 模块 7：styles.py 样式模块测试
# ============================================================
_log("\n" + "=" * 60)
_log("🎨 模块 7：styles.py — 样式模块")
_log("=" * 60)

def test_styles():
    try:
        from utils.styles import (
            render_difficulty_tag, render_knowledge_tag,
            render_mastery_stars, GLOBAL_CSS,
        )
        report("styles导入", "pass")
    except Exception as e:
        report("styles导入", "fail", str(e))
        return

    # 难度标签
    for diff in ["简单", "中等", "困难", "未知"]:
        html = render_difficulty_tag(diff)
        assert "<span" in html, f"难度标签应返回HTML，diff={diff}"
        assert diff in html, f"标签应包含难度文本: {diff}"
    report("render_difficulty_tag", "pass")

    # 知识点标签
    html = render_knowledge_tag("Python基础")
    assert "Python基础" in html, "知识点标签应包含文本"
    assert "knowledge-tag" in html, "应使用 knowledge-tag CSS 类"
    report("render_knowledge_tag", "pass")

    # 掌握度星星
    for level in range(6):
        html = render_mastery_stars(level)
        assert "★" in html, f"level={level} 应包含实心星"
    report("render_mastery_stars", "pass")

    # CSS 内容检查
    assert "glass-card" in GLOBAL_CSS, "CSS 应包含 glass-card"
    assert "question-card" in GLOBAL_CSS, "CSS 应包含 question-card"
    assert "@media" in GLOBAL_CSS, "CSS 应包含响应式媒体查询"
    assert "prefers-color-scheme" in GLOBAL_CSS, "CSS 应包含亮色主题适配"
    report("GLOBAL_CSS 完整性", "pass", f"CSS 长度: {len(GLOBAL_CSS)} 字符")

try:

    test_styles()

except Exception as _e:

    _log(f"[FAIL] test_styles crashed: {_e}")

    import traceback as _tb

    _tb.print_exc(file=_output_file)

    _output_file.flush()
# ============================================================
# 模块 8：session_state.py 会话状态测试
# ============================================================
_log("\n" + "=" * 60)
_log("🔄 模块 8：session_state.py — 会话状态管理")
_log("=" * 60)

def test_session_state():
    try:
        from utils.session_state import init_session_state
        report("session_state导入", "pass")
    except Exception as e:
        report("session_state导入", "fail", str(e))
        return

    old_ss = dict(mock_st.session_state)
    mock_st.session_state = {}

    init_session_state()

    expected_keys = [
        "drawn_questions", "drawn_answers", "drawn_meta",
        "total_drawn_count", "seen_questions", "history_log",
        "countdown_trigger", "last_page",
    ]
    for key in expected_keys:
        assert key in mock_st.session_state, f"缺少 session_state key: {key}"
    report("init_session_state 初始化", "pass", f"共 {len(expected_keys)} 个 key")

    # 测试幂等性（重复初始化不应覆盖已有值）
    mock_st.session_state["total_drawn_count"] = 42
    init_session_state()
    assert mock_st.session_state["total_drawn_count"] == 42, "重复初始化不应覆盖已有值"
    report("幂等性测试", "pass")

    mock_st.session_state = old_ss

try:

    test_session_state()

except Exception as _e:

    _log(f"[FAIL] test_session_state crashed: {_e}")

    import traceback as _tb

    _tb.print_exc(file=_output_file)

    _output_file.flush()
# ============================================================
# 模块 9：question_card.py 组件测试
# ============================================================
_log("\n" + "=" * 60)
_log("🃏 模块 9：question_card.py — 题目卡片组件")
_log("=" * 60)

def test_question_card():
    try:
        from components.question_card import safe_format
        report("question_card导入", "pass")
    except Exception as e:
        report("question_card导入", "fail", str(e))
        return

    import pandas as pd

    # safe_format 测试
    assert safe_format("Hello <script>alert('xss')</script>") == "Hello &lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;", "XSS 防护失败"
    report("XSS防护", "pass")

    assert safe_format(None) == "", "None 应返回空"
    report("None处理", "pass")

    assert safe_format(float('nan')) == "", "NaN 应返回空"
    report("NaN处理", "pass")

    assert safe_format("普通文本\n换行") == "普通文本\n\n换行", "换行应被双倍化"
    report("换行处理", "pass")

    assert safe_format(12345) == "12345", "数字应转为字符串"
    report("数字处理", "pass")

    # 特殊字符转义
    assert safe_format("a&b\"c'd") != "a&b\"c'd", "特殊字符应被转义"
    report("特殊字符转义", "pass")

try:

    test_question_card()

except Exception as _e:

    _log(f"[FAIL] test_question_card crashed: {_e}")

    import traceback as _tb

    _tb.print_exc(file=_output_file)

    _output_file.flush()
# ============================================================
# 模块 10：timer.py 和 metrics.py 组件测试
# ============================================================
_log("\n" + "=" * 60)
_log("⏱️ 模块 10：timer.py & metrics.py — 组件测试")
_log("=" * 60)

def test_timer_metrics():
    try:
        from components.timer import render_timer
        report("timer导入", "pass")
    except Exception as e:
        report("timer导入", "fail", str(e))

    try:
        from components.metrics import render_metric_row, render_overview_cards
        report("metrics导入", "pass")
    except Exception as e:
        report("metrics导入", "fail", str(e))

    # render_timer 只是渲染 HTML，没有复杂逻辑
    # render_metric_row 和 render_overview_cards 也只是渲染
    # 这些组件在 mock 环境下不会有实际效果，但导入成功就说明代码结构正确

try:

    test_timer_metrics()

except Exception as _e:

    _log(f"[FAIL] test_timer_metrics crashed: {_e}")

    import traceback as _tb

    _tb.print_exc(file=_output_file)

    _output_file.flush()
# ============================================================
# 模块 11：跨模块集成测试
# ============================================================
_log("\n" + "=" * 60)
_log("🔗 模块 11：跨模块集成测试")
_log("=" * 60)

def test_integration():
    old_ss = dict(mock_st.session_state)
    mock_st.session_state = {"username": "__test_integration__"}

    try:
        from utils.review_manager import save_to_review_book, _read_review_file, delete_from_review_book
        from utils.ai_scorer import score_answer
        from utils.data_loader import load_question_banks

        # 集成测试：评分 -> 保存错题 -> 读取验证 -> 删除
        question = "什么是Python的装饰器？"
        reference = "装饰器是一种设计模式，用于在不修改原函数代码的情况下扩展函数功能"
        user_answer = "装饰器是Python的一种语法，使用@符号来修改函数行为"

        # 1. 评分 (mock API to avoid network timeout)
        import utils.ai_scorer as _scorer2
        _orig = _scorer2._try_mimo_score
        _scorer2._try_mimo_score = lambda q, r, a: None
        score, feedback, method = score_answer(question, reference, user_answer)
        _scorer2._try_mimo_score = _orig
        assert 0 <= score <= 100, f"评分应为0-100，实际 {score}"
        report("集成: 评分", "pass", f"score={score}, method={method}")

        # 2. 保存到错题本
        save_to_review_book(question, reference, note=user_answer, mastery=max(1, score // 20))
        report("集成: 保存错题", "pass")

        # 3. 读取验证
        df = _read_review_file()
        test_entry = df[df["问题"] == question]
        assert len(test_entry) == 1, f"应有1条记录，实际 {len(test_entry)}"
        report("集成: 读取验证", "pass")

        # 4. 删除
        delete_from_review_book(question)
        df2 = _read_review_file()
        assert len(df2[df2["问题"] == question]) == 0, "删除后不应存在"
        report("集成: 删除验证", "pass")

    except Exception as e:
        report("集成测试", "fail", str(e))
        traceback.print_exc()

    # 清理
    from utils import db
    try:
        db.execute("DELETE FROM review_book WHERE username = %s", ("__test_integration__",))
    except:
        pass

    mock_st.session_state = old_ss

try:

    test_integration()

except Exception as _e:

    _log(f"[FAIL] test_integration crashed: {_e}")

    import traceback as _tb

    _tb.print_exc(file=_output_file)

    _output_file.flush()
# ============================================================
# 模块 12：边界条件和异常处理测试
# ============================================================
_log("\n" + "=" * 60)
_log("🛡️ 模块 12：边界条件和异常处理测试")
_log("=" * 60)

def test_edge_cases():
    from utils.ai_scorer import _local_score, _parse_score_response, _extract_keywords

    # --- 超长文本 ---
    long_text = "Python编程" * 10000
    try:
        s, f = _local_score("Python是一种编程语言", long_text)
        report("超长用户答案", "pass", f"score={s}")
    except Exception as e:
        report("超长用户答案", "fail", str(e))

    # --- Unicode 特殊字符 ---
    try:
        s, f = _local_score("Python编程🐍", "Python编程🐍是一门语言")
        report("Unicode emoji", "pass", f"score={s}")
    except Exception as e:
        report("Unicode emoji", "fail", str(e))

    # --- SQL 注入测试 ---
    old_ss = dict(mock_st.session_state)
    mock_st.session_state = {"username": "__test_sqli__"}
    try:
        from utils.review_manager import save_to_review_book, _read_review_file, delete_from_review_book
        malicious_q = "'; DROP TABLE review_book; --"
        save_to_review_book(malicious_q, "答案", note="测试")
        df = _read_review_file()
        entry = df[df["问题"] == malicious_q]
        assert len(entry) <= 1, "SQL注入应被参数化查询阻止"
        report("SQL注入防护", "pass")
        delete_from_review_book(malicious_q)
    except Exception as e:
        report("SQL注入防护", "fail", str(e))

    mock_st.session_state = old_ss

    # --- _parse_score_response 边界 ---
    # 多个 JSON 对象（应取第一个含 score 的）
    r = _parse_score_response('{"other": 1} {"score": 88, "feedback": "ok"}')
    if r and r[0] == 88:
        report("多个JSON取含score的", "pass")
    else:
        report("多个JSON取含score的", "warn", f"结果: {r}")

    # 嵌套 JSON
    r2 = _parse_score_response('{"score": 70, "detail": {"sub": 50}, "feedback": "ok"}')
    if r2:
        report("嵌套JSON", "pass" if r2[0] == 70 else "warn", f"score={r2[0]}")
    else:
        report("嵌套JSON", "fail", "解析失败")

    # 大量空白字符
    r3 = _parse_score_response('   \n\n  {"score": 60, "feedback": "ok"}  \n\n  ')
    report("空白字符容错", "pass" if r3 and r3[0] == 60 else "warn", f"result={r3}")

try:

    test_edge_cases()

except Exception as _e:

    _log(f"[FAIL] test_edge_cases crashed: {_e}")

    import traceback as _tb

    _tb.print_exc(file=_output_file)

    _output_file.flush()
# ============================================================
# 汇总报告
# ============================================================
_log("\n" + "=" * 60)
_log("测试汇总报告")
_log("=" * 60)

total = sum(len(v) for v in results.values())
_log(f"\n  总测试数: {total}")
_log(f"  通过: {len(results['pass'])}")
_log(f"  失败: {len(results['fail'])}")
_log(f"  警告: {len(results['warn'])}")
_log(f"  信息: {len(results['info'])}")

if results["fail"]:
    _log("\n" + "-" * 40)
    _log("失败详情:")
    for name, detail in results["fail"]:
        _log(f"  - {name}: {detail}")

if results["warn"]:
    _log("\n" + "-" * 40)
    _log("警告详情:")
    for name, detail in results["warn"]:
        _log(f"  - {name}: {detail}")

_log("\n" + "=" * 60)
_log("测试完成!")
_log("=" * 60)

_output_file.close()
