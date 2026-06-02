"""
用户认证模块
负责用户注册、登录、密码哈希、会话管理。
自动检测环境：本地用 MySQL，Streamlit Cloud 用 SQLite。
"""
import os
import re
import hashlib
import secrets
import sqlite3
import streamlit as st

# 数据目录（用户 CSV 数据仍存在本地文件）
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SQLITE_PATH = os.path.join(DB_DIR, "users.db")

# 检测是否能连接 MySQL
_USE_MYSQL = False
_DB_CONFIG = {}
_DB_NAME = "quiz_system"

try:
    import pymysql
    import pymysql.cursors

    # 优先从 Streamlit secrets 读取（云端部署）
    _secrets_found = False
    try:
        if "database" in st.secrets:
            _DB_CONFIG = {
                "host": st.secrets["database"]["host"],
                "port": int(st.secrets["database"].get("port", 4000)),
                "user": st.secrets["database"]["user"],
                "password": st.secrets["database"]["password"],
                "charset": "utf8mb4",
            }
            _DB_NAME = st.secrets["database"].get("database", "quiz_system")
            _secrets_found = True
    except Exception:
        pass

    if not _secrets_found:
        # 本地开发：从 db_config.py 读取
        from utils.db_config import DB_CONFIG, DB_NAME
        _DB_CONFIG = DB_CONFIG
        _DB_NAME = DB_NAME

    # 尝试连接 MySQL
    _test_conn = pymysql.connect(
        host=_DB_CONFIG["host"], port=_DB_CONFIG["port"],
        user=_DB_CONFIG["user"], password=_DB_CONFIG["password"],
        charset="utf8mb4",
    )
    _test_conn.close()
    _USE_MYSQL = True
except Exception:
    _USE_MYSQL = False


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
# SQLite 实现
# ==========================================

def _sqlite_conn():
    _ensure_data_dir()
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _sqlite_init(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.commit()
    try:
        conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass


def _sqlite_ensure_admin(conn):
    row = conn.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    if row is None:
        salt = secrets.token_hex(16)
        password_hash = _hash_password("19870118826", salt)
        conn.execute(
            "INSERT INTO users (username, password_hash, salt, is_admin) VALUES (?, ?, ?, 1)",
            ("admin", password_hash, salt),
        )
        conn.commit()
        os.makedirs(os.path.join(DB_DIR, "users", "admin"), exist_ok=True)


# ==========================================
# MySQL 实现
# ==========================================

def _mysql_conn(with_db=True):
    config = _DB_CONFIG.copy()
    if with_db:
        config["database"] = _DB_NAME
    config["cursorclass"] = pymysql.cursors.DictCursor
    return pymysql.connect(**config)


def _mysql_init():
    try:
        conn = _mysql_conn(with_db=False)
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{_DB_NAME}` "
                f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.close()
    except pymysql.Error as e:
        st.error(f"无法连接 MySQL: {e}")
        st.stop()

    conn = _mysql_conn()
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(128) NOT NULL,
                salt VARCHAR(64) NOT NULL,
                is_admin TINYINT NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT NOW()
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
    conn.commit()
    _mysql_ensure_admin(conn)
    conn.close()


def _mysql_ensure_admin(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE username = 'admin'")
        if cur.fetchone() is None:
            salt = secrets.token_hex(16)
            password_hash = _hash_password("19870118826", salt)
            cur.execute(
                "INSERT INTO users (username, password_hash, salt, is_admin) VALUES (%s, %s, %s, 1)",
                ("admin", password_hash, salt),
            )
            conn.commit()
            os.makedirs(os.path.join(DB_DIR, "users", "admin"), exist_ok=True)


# ==========================================
# 统一接口
# ==========================================

def init_db():
    """初始化用户表，自动创建管理员账户"""
    _ensure_data_dir()
    if _USE_MYSQL:
        _mysql_init()
    else:
        conn = _sqlite_conn()
        _sqlite_init(conn)
        _sqlite_ensure_admin(conn)
        conn.close()


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
        if _USE_MYSQL:
            conn = _mysql_conn()
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, password_hash, salt) VALUES (%s, %s, %s)",
                    (username, password_hash, salt),
                )
            conn.commit()
            conn.close()
        else:
            conn = _sqlite_conn()
            conn.execute(
                "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                (username, password_hash, salt),
            )
            conn.commit()
            conn.close()

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

    if _USE_MYSQL:
        conn = _mysql_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
        conn.close()
    else:
        conn = _sqlite_conn()
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if row:
            row = dict(row)

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
    if _USE_MYSQL:
        conn = _mysql_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, is_admin, created_at FROM users ORDER BY id")
            rows = cur.fetchall()
        conn.close()
        for row in rows:
            if row.get("created_at") and not isinstance(row["created_at"], str):
                row["created_at"] = row["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        return rows
    else:
        conn = _sqlite_conn()
        rows = conn.execute("SELECT id, username, is_admin, created_at FROM users ORDER BY id").fetchall()
        conn.close()
        return [dict(row) for row in rows]


def get_user_count() -> int:
    if _USE_MYSQL:
        conn = _mysql_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM users")
            count = cur.fetchone()["cnt"]
        conn.close()
        return count
    else:
        conn = _sqlite_conn()
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        conn.close()
        return count


def delete_user(username: str) -> tuple[bool, str]:
    """删除用户及其数据"""
    if username == "admin":
        return False, "不能删除管理员账户"

    if _USE_MYSQL:
        conn = _mysql_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cur.fetchone() is None:
                conn.close()
                return False, "用户不存在"
            cur.execute("DELETE FROM users WHERE username = %s", (username,))
        conn.commit()
        conn.close()
    else:
        conn = _sqlite_conn()
        row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if row is None:
            conn.close()
            return False, "用户不存在"
        conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        conn.close()

    import shutil
    user_dir = os.path.join(DB_DIR, "users", username)
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)
    return True, f"用户 {username} 已删除"
