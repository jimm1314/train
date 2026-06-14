"""
数据库连接 & 通用 CRUD 基础设施
优先使用 TiDB/MySQL，不可用时 fallback 到本地 SQLite。
所有其他模块通过本模块获取连接，不再直接操作文件。

性能优化：使用连接池复用连接，避免每次查询都建立/关闭 TCP+SSL 连接。
"""
import os
import re
import time
import sqlite3
import threading
import contextlib
import pandas as pd
import streamlit as st

_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
_SQLITE_PATH = os.path.join(_DB_DIR, "app.db")

_USE_MYSQL = False
_DB_CONFIG = {}
_DB_NAME = "quiz_system"

# ==========================================
# 连接池（避免每次查询都新建/关闭连接）
# ==========================================
class _ConnectionPool:
    """简单的 MySQL 连接池，复用连接减少 TCP+SSL 握手开销"""

    def __init__(self, max_size: int = 5, max_idle_time: float = 300):
        self._pool: list = []
        self._lock = threading.Lock()
        self._max_size = max_size
        self._max_idle_time = max_idle_time  # 连接最大空闲时间（秒）

    def get(self):
        """从池中获取一个可用连接，池为空则新建"""
        with self._lock:
            now = time.time()
            # 清理过期连接
            self._pool = [
                (conn, ts) for conn, ts in self._pool
                if now - ts < self._max_idle_time
            ]
            if self._pool:
                conn, _ = self._pool.pop()
                # 检查连接是否存活
                try:
                    conn.ping(reconnect=True)
                    return conn
                except Exception:
                    try:
                        conn.close()
                    except Exception:
                        pass
            # 新建连接
            return self._create()

    def put(self, conn):
        """归还连接到池中"""
        with self._lock:
            if len(self._pool) < self._max_size:
                self._pool.append((conn, time.time()))
            else:
                try:
                    conn.close()
                except Exception:
                    pass

    def _create(self):
        import pymysql
        import pymysql.cursors
        return pymysql.connect(
            **_DB_CONFIG,
            database=_DB_NAME,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
            connect_timeout=10,
            read_timeout=30,
            write_timeout=30,
        )

    def close_all(self):
        with self._lock:
            for conn, _ in self._pool:
                try:
                    conn.close()
                except Exception:
                    pass
            self._pool.clear()


_pool: _ConnectionPool | None = None


def _get_pool() -> _ConnectionPool:
    global _pool
    if _pool is None:
        _pool = _ConnectionPool(max_size=5, max_idle_time=300)
    return _pool

try:
    import pymysql
    import pymysql.cursors

    _secrets_found = False

    try:
        if "database" in st.secrets:
            _DB_CONFIG = {
                "host": st.secrets["database"]["host"],
                "port": int(st.secrets["database"].get("port", 4000)),
                "user": st.secrets["database"]["user"],
                "password": st.secrets["database"]["password"],
                "charset": "utf8mb4",
                "ssl": {},
            }
            _DB_NAME = st.secrets["database"].get("database", "quiz_system")
            _secrets_found = True
    except Exception:
        pass

    if not _secrets_found:
        from utils.db_config import DB_CONFIG, DB_NAME
        _DB_CONFIG = dict(DB_CONFIG)  # 创建副本避免修改原配置
        _DB_NAME = DB_NAME

    # 确保 SSL 配置存在（TiDB Cloud 强制要求）
    if "ssl" not in _DB_CONFIG:
        _DB_CONFIG["ssl"] = {}

    _test_params = {**_DB_CONFIG, "database": _DB_NAME}
    _test_conn = pymysql.connect(**_test_params)
    _test_conn.close()
    _USE_MYSQL = True
    print(f"✓ 成功连接到 MySQL/TiDB: {_DB_CONFIG['host']}:{_DB_CONFIG['port']}/{_DB_NAME}")
except Exception as e:
    _USE_MYSQL = False
    print(f"⚠ MySQL/TiDB 连接失败，将使用 SQLite 模式: {e}")
    import traceback
    traceback.print_exc()


def _ensure_data_dir():
    os.makedirs(_DB_DIR, exist_ok=True)


def is_mysql() -> bool:
    return _USE_MYSQL


@contextlib.contextmanager
def get_conn():
    """获取数据库连接（从连接池复用，自动提交/回滚/归还）"""
    if _USE_MYSQL:
        pool = _get_pool()
        conn = pool.get()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            pool.put(conn)
    else:
        _ensure_data_dir()
        conn = sqlite3.connect(_SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def _adapt_sql(sql: str) -> str:
    """将 MySQL 占位符 %s 转为 SQLite 的 ?"""
    if _USE_MYSQL:
        return sql
    return sql.replace("%s", "?")


def execute(sql: str, params: tuple = (), *, fetch: bool = False):
    """执行 SQL，可选返回查询结果（list[dict]）"""
    adapted = _adapt_sql(sql)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(adapted, params)
        if fetch:
            if _USE_MYSQL:
                return cur.fetchall()
            else:
                cols = [d[0] for d in cur.description] if cur.description else []
                return [dict(zip(cols, row)) for row in cur.fetchall()]
        return cur.lastrowid


def execute_many(sql: str, data: list[tuple]):
    """批量执行 SQL"""
    adapted = _adapt_sql(sql)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.executemany(adapted, data)


def execute_transaction(operations: list[tuple]):
    """
    在同一事务中执行多条 SQL 操作。
    operations: [(sql, params), ...]
    所有操作要么全部成功，要么全部回滚。
    """
    with get_conn() as conn:
        cur = conn.cursor()
        for sql, params in operations:
            adapted = _adapt_sql(sql)
            cur.execute(adapted, params)


def query_df(sql: str, params: tuple = ()) -> pd.DataFrame:
    """执行查询，返回 DataFrame"""
    rows = execute(sql, params, fetch=True)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _to_sqlite(sql: str) -> str:
    """将 MySQL DDL 语法转换为 SQLite 兼容语法"""
    s = sql
    s = s.replace("BIGINT PRIMARY KEY AUTO_INCREMENT", "INTEGER PRIMARY KEY AUTOINCREMENT")
    s = s.replace("INT AUTO_INCREMENT PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
    s = s.replace("TINYINT DEFAULT 1", "INTEGER DEFAULT 1")
    s = s.replace("TINYINT NOT NULL DEFAULT 0", "INTEGER NOT NULL DEFAULT 0")
    s = s.replace("TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "TEXT DEFAULT (datetime('now','localtime'))")
    s = s.replace("ON UPDATE CURRENT_TIMESTAMP", "")
    s = s.replace("DATETIME NOT NULL DEFAULT NOW()", "TEXT NOT NULL DEFAULT (datetime('now','localtime'))")
    s = s.replace("ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci", "")
    s = s.replace("ENGINE=InnoDB", "")
    s = re.sub(r"COMMENT '[^']*'", "", s)
    # 移除 FULLTEXT INDEX（含行尾逗号）
    s = re.sub(r",?\s*FULLTEXT INDEX \w+ \([^)]+\)", "", s)
    # UNIQUE INDEX / UNIQUE KEY → UNIQUE 约束（SQLite 支持 UNIQUE(col1, col2) 语法，含行尾逗号处理）
    s = re.sub(r",?\s*UNIQUE (?:INDEX|KEY) \w+ \(([^)]+)\)", r",\n    UNIQUE(\1)", s)
    # 移除普通 INDEX（SQLite 不支持在 CREATE TABLE 内定义 INDEX，含行尾逗号）
    s = re.sub(r",?\s*INDEX \w+ \([^)]+\)", "", s)
    # 清理多余逗号（如连续逗号或最后一个字段后多余逗号）
    s = re.sub(r",\s*\)", ")", s)
    return s


_tables_initialized = False


def init_tables(schema_path: str | None = None):
    """初始化所有表结构（每个进程只执行一次）"""
    global _tables_initialized
    if _tables_initialized:
        return

    if schema_path is None:
        schema_path = os.path.join(os.path.dirname(__file__), "..", "tidb_schema.sql")

    if not os.path.exists(schema_path):
        return

    with open(schema_path, "r", encoding="utf-8") as f:
        content = f.read()

    statements = [s.strip() for s in content.split(";") if s.strip()]

    with get_conn() as conn:
        cur = conn.cursor()
        for stmt in statements:
            # 去掉 SQL 注释行后再判断语句类型
            clean = re.sub(r'--[^\n]*\n', '', stmt).strip()
            upper = clean.upper()
            if not (upper.startswith("CREATE") or upper.startswith("DROP") or upper.startswith("ALTER")):
                continue
            adapted = _adapt_sql(stmt) if _USE_MYSQL else _to_sqlite(_adapt_sql(stmt))
            try:
                cur.execute(adapted)
            except Exception as e:
                # "already exists" 类型的错误是正常的，其他错误需要记录
                err_msg = str(e).lower()
                if "already exists" not in err_msg and "duplicate" not in err_msg:
                    print(f"[DB] init_tables 执行警告: {e}")

    _tables_initialized = True
