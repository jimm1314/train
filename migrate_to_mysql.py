"""
SQLite → MySQL 数据迁移脚本
将现有 SQLite 中的用户数据迁移到 MySQL。
运行方式：cd genmini && python migrate_to_mysql.py
"""
import os
import sys
import sqlite3
import pymysql
import pymysql.cursors

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.db_config import DB_CONFIG, DB_NAME

SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "users.db")


def main():
    print("=" * 50)
    print("SQLite → MySQL 数据迁移")
    print("=" * 50)

    # 检查 SQLite 文件是否存在
    if not os.path.exists(SQLITE_PATH):
        print(f"\n[错误] SQLite 文件不存在: {SQLITE_PATH}")
        print("无需迁移，直接使用 MySQL 即可。")
        return

    # 读取 SQLite 数据
    print(f"\n[1/4] 读取 SQLite 数据: {SQLITE_PATH}")
    sq_conn = sqlite3.connect(SQLITE_PATH)
    sq_conn.row_factory = sqlite3.Row
    rows = sq_conn.execute("SELECT * FROM users").fetchall()
    sq_conn.close()

    if not rows:
        print("  SQLite 中没有用户数据，无需迁移。")
        return

    print(f"  读取到 {len(rows)} 条用户记录:")
    for row in rows:
        admin_tag = " [管理员]" if row["is_admin"] else ""
        print(f"    - {row['username']}{admin_tag}")

    # 连接 MySQL
    print(f"\n[2/4] 连接 MySQL...")
    try:
        config = DB_CONFIG.copy()
        config["cursorclass"] = pymysql.cursors.DictCursor
        conn = pymysql.connect(**config)
        print("  连接成功！")
    except pymysql.Error as e:
        print(f"  [错误] 无法连接 MySQL: {e}")
        print("  请检查 utils/db_config.py 中的配置。")
        return

    # 创建数据库和表
    print(f"\n[3/4] 创建数据库 `{DB_NAME}` 和表...")
    with conn.cursor() as cur:
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
            f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cur.execute(f"USE `{DB_NAME}`")
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
    print("  表结构已就绪。")

    # 迁移数据
    print(f"\n[4/4] 迁移数据...")
    success = 0
    skipped = 0
    failed = 0

    for row in rows:
        try:
            with conn.cursor() as cur:
                created_at = row["created_at"] if row["created_at"] else None
                cur.execute(
                    "INSERT INTO users (username, password_hash, salt, is_admin, created_at) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (row["username"], row["password_hash"], row["salt"],
                     row["is_admin"], created_at),
                )
            conn.commit()
            success += 1
            print(f"  [成功] {row['username']}")
        except pymysql.IntegrityError:
            skipped += 1
            print(f"  [跳过] {row['username']} (MySQL 中已存在)")
        except Exception as e:
            failed += 1
            print(f"  [失败] {row['username']}: {e}")

    conn.close()

    print("\n" + "=" * 50)
    print(f"迁移完成！成功: {success}, 跳过: {skipped}, 失败: {failed}")
    print("=" * 50)

    if success > 0:
        print("\n提示：迁移成功后，可以删除 SQLite 文件:")
        print(f"  {SQLITE_PATH}")


if __name__ == "__main__":
    main()
