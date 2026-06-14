"""Minimal fix verification"""
import sys, os, re, sqlite3
sys.path.insert(0, os.path.dirname(__file__))

db_path = os.path.join(os.path.dirname(__file__), "data", "app.db")
os.makedirs(os.path.dirname(db_path), exist_ok=True)
if os.path.exists(db_path):
    os.remove(db_path)

# Test 1: DDL conversion
print("=== Test 1: _to_sqlite DDL conversion ===")
from utils.db import _to_sqlite

schema_path = os.path.join(os.path.dirname(__file__), "tidb_schema.sql")
with open(schema_path, "r", encoding="utf-8") as f:
    content = f.read()
statements = [s.strip() for s in content.split(";") if s.strip()]

conn = sqlite3.connect(db_path)
for stmt in statements:
    clean = re.sub(r'--[^\n]*\n', '', stmt).strip()
    upper = clean.upper()
    if not upper.startswith("CREATE"):
        continue
    adapted = _to_sqlite(stmt)
    try:
        conn.execute(adapted)
        print(f"  [PASS] Created table from DDL")
    except Exception as e:
        print(f"  [FAIL] {e}")
        print(f"    DDL: {adapted[:300]}")
conn.commit()

cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print(f"\n  Tables created: {tables}")

expected = ['interview_questions', 'review_book', 'study_log', 'checkin_log', 'dictation_log', 'user_goals']
for t in expected:
    print(f"  [{'PASS' if t in tables else 'FAIL'}] {t}")

conn.close()

# Test 2: JSON parsing
print("\n=== Test 2: _parse_score_response ===")
from utils.ai_scorer import _parse_score_response

tests = [
    ('{"score": 85, "feedback": "good"}', 85),
    ('{"score": 75, "feedback": "code: def f() { return 1; }"}', 75),
    ('{"score": 70, "detail": {"sub": 50}, "feedback": "ok"}', 70),
    ('{"result": "ok"}', None),
    ('plain text', None),
]
for text, expected_score in tests:
    result = _parse_score_response(text)
    if expected_score is None:
        ok = result is None
    else:
        ok = result is not None and result[0] == expected_score
    print(f"  [{'PASS' if ok else 'FAIL'}] expected={expected_score}, got={result}, text={text[:50]}")

print("\nDone!")
