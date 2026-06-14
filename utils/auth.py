"""
用户认证模块
负责用户注册、登录、密码哈希、会话管理。
所有数据库操作统一通过 utils.db 模块，避免重复连接。
"""
import os
import re
import hashlib
import secrets
import streamlit as st
from utils import db

# 数据目录（用户 CSV 数据仍存在本地文件）
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


# ==========================================
# 通用工具函数
# ==========================================

def _hash_password(password: str, salt: str) -> str:
    """使用 SHA-256 + 盐值对密码进行哈希"""
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def _ensure_data_dir():
    """确保数据目录存在"""
    os.makedirs(DB_DIR, exist_ok=True)
    os.makedirs(os.path.join(DB_DIR, "users"), exist_ok=True)


# ==========================================
# 统一接口（全部通过 utils.db 操作）
# ==========================================

def init_db():
    """初始化用户表，自动创建管理员账户"""
    _ensure_data_dir()
    db.init_tables()
    # 确保 admin 账户存在
    rows = db.execute("SELECT id FROM users WHERE username = %s", ("admin",), fetch=True)
    if not rows:
        salt = secrets.token_hex(16)
        password_hash = _hash_password("19870118826", salt)
        db.execute(
            "INSERT INTO users (username, password_hash, salt, is_admin) VALUES (%s, %s, %s, 1)",
            ("admin", password_hash, salt),
        )
        os.makedirs(os.path.join(DB_DIR, "users", "admin"), exist_ok=True)


def register_user(username: str, password: str) -> tuple[bool, str]:
    """注册新用户。返回 (成功?, 消息)"""
    username = username.strip()
    if not username:
        return False, "用户名不能为空"
    if len(username) < 3 or len(username) > 20:
        return False, "用户名长度需在 3-20 个字符之间"
    if not username.isascii() or not username.replace("_", "").replace("-", "").isalnum():
        return False, "用户名只能包含英文字母、数字、下划线和连字符"
    if len(password) < 8:
        return False, "密码长度不能少于 8 个字符"
    if len(password) > 50:
        return False, "密码长度不能超过 50 个字符"
    if not re.search(r"[a-zA-Z]", password):
        return False, "密码必须包含至少一个字母"
    if not re.search(r"\d", password):
        return False, "密码必须包含至少一个数字"

    salt = secrets.token_hex(16)
    password_hash = _hash_password(password, salt)

    try:
        db.execute(
            "INSERT INTO users (username, password_hash, salt) VALUES (%s, %s, %s)",
            (username, password_hash, salt),
        )
        os.makedirs(os.path.join(DB_DIR, "users", username), exist_ok=True)
        return True, "注册成功！"
    except Exception as e:
        if "Duplicate" in str(e) or "UNIQUE" in str(e):
            return False, "该用户名已被注册"
        return False, f"注册失败: {e}"


def login_user(username: str, password: str) -> tuple[bool, str]:
    """验证用户登录。返回 (成功?, 消息)"""
    username = username.strip()
    if not username or not password:
        return False, "用户名和密码不能为空"

    rows = db.execute(
        "SELECT * FROM users WHERE username = %s", (username,), fetch=True
    )
    row = rows[0] if rows else None

    if row is None:
        return False, "用户名或密码错误"

    password_hash = _hash_password(password, row["salt"])
    if password_hash != row["password_hash"]:
        return False, "用户名或密码错误"

    st.session_state["authenticated"] = True
    st.session_state["username"] = row["username"]
    st.session_state["is_admin"] = bool(row["is_admin"])
    return True, "登录成功！"


def logout():
    """退出登录"""
    st.session_state["authenticated"] = False
    st.session_state.pop("username", None)
    st.session_state.pop("is_admin", None)


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def get_current_user() -> str | None:
    if is_authenticated():
        return st.session_state.get("username")
    return None


def check_auth():
    """认证守卫"""
    init_db()
    if not is_authenticated():
        st.warning("⚠️ 请先登录后再访问此页面")
        st.markdown("👈 请使用左侧导航栏前往 **登录注册** 页面")
        st.stop()


def is_admin() -> bool:
    return st.session_state.get("is_admin", False)


def check_admin():
    """管理员守卫"""
    check_auth()
    if not is_admin():
        st.error("⛔ 权限不足：仅管理员可访问此页面")
        st.stop()


def get_all_users() -> list[dict]:
    """获取所有用户列表"""
    rows = db.execute(
        "SELECT id, username, is_admin, created_at FROM users ORDER BY id", fetch=True
    )
    for row in rows:
        if row.get("created_at") and not isinstance(row["created_at"], str):
            row["created_at"] = row["created_at"].strftime("%Y-%m-%d %H:%M:%S")
    return rows


def get_user_count() -> int:
    rows = db.execute("SELECT COUNT(*) AS cnt FROM users", fetch=True)
    return rows[0]["cnt"] if rows else 0


def delete_user(username: str) -> tuple[bool, str]:
    """删除用户及其数据"""
    if username == "admin":
        return False, "不能删除管理员账户"

    rows = db.execute(
        "SELECT id FROM users WHERE username = %s", (username,), fetch=True
    )
    if not rows:
        return False, "用户不存在"

    db.execute("DELETE FROM users WHERE username = %s", (username,))

    import shutil
    user_dir = os.path.join(DB_DIR, "users", username)
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)
    return True, f"用户 {username} 已删除"
