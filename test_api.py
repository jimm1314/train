"""Test score_answer in isolation"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Mock streamlit
import types
mock_st = types.ModuleType("streamlit")
mock_st.secrets = {}
sys.modules["streamlit"] = mock_st

print("Importing...", flush=True)
from utils.ai_scorer import score_answer, _try_mimo_score, _parse_score_response
print("Imported OK", flush=True)

print("Testing empty answer...", flush=True)
try:
    s, f, m = score_answer("测试题", "参考答案", "")
    print(f"  Result: score={s}, method={m}", flush=True)
except Exception as e:
    print(f"  Error: {e}", flush=True)

print("Testing normal answer...", flush=True)
try:
    s2, f2, m2 = score_answer("什么是Python", "Python是一种编程语言", "Python是一种广泛使用的编程语言")
    print(f"  Result: score={s2}, method={m2}", flush=True)
except Exception as e:
    print(f"  Error: {e}", flush=True)

print("Done!", flush=True)
