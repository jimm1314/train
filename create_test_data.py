"""
测试数据生成脚本
创建测试用户并填充刷题数据，用于管理员面板测试。
运行方式：cd genmini && python create_test_data.py
"""
import os
import sys
import hashlib
import secrets
import pymysql
import pymysql.cursors
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.db_config import DB_CONFIG, DB_NAME

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_DIR = os.path.join(DATA_DIR, "users")


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def _get_conn():
    config = DB_CONFIG.copy()
    config["database"] = DB_NAME
    config["cursorclass"] = pymysql.cursors.DictCursor
    return pymysql.connect(**config)


def create_user(username: str, password: str, is_admin: int = 0):
    """创建用户（如果不存在）"""
    conn = _get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        existing = cur.fetchone()
        if existing:
            print(f"  [跳过] 用户 {username} 已存在")
            conn.close()
            return

        salt = secrets.token_hex(16)
        password_hash = hash_password(password, salt)
        cur.execute(
            "INSERT INTO users (username, password_hash, salt, is_admin) VALUES (%s, %s, %s, %s)",
            (username, password_hash, salt, is_admin),
        )
    conn.commit()
    conn.close()

    user_dir = os.path.join(USERS_DIR, username)
    os.makedirs(user_dir, exist_ok=True)
    print(f"  [创建] 用户 {username}")


def write_review_book(username: str, data: list[dict]):
    """写入错题本"""
    df = pd.DataFrame(data)
    fpath = os.path.join(USERS_DIR, username, "review_book.csv")
    df.to_csv(fpath, index=False, encoding="utf-8-sig")
    print(f"  [写入] {username}/review_book.csv ({len(data)} 条)")


def write_study_log(username: str, data: list[dict]):
    """写入学习日志"""
    df = pd.DataFrame(data)
    fpath = os.path.join(USERS_DIR, username, "study_log.csv")
    df.to_csv(fpath, index=False, encoding="utf-8-sig")
    print(f"  [写入] {username}/study_log.csv ({len(data)} 条)")


def write_checkin_log(username: str, data: list[dict]):
    """写入签到记录"""
    df = pd.DataFrame(data)
    fpath = os.path.join(USERS_DIR, username, "checkin_log.csv")
    df.to_csv(fpath, index=False, encoding="utf-8-sig")
    print(f"  [写入] {username}/checkin_log.csv ({len(data)} 条)")


def write_dictation_log(username: str, data: list[dict]):
    """写入默写记录"""
    df = pd.DataFrame(data)
    fpath = os.path.join(USERS_DIR, username, "dictation_log.csv")
    df.to_csv(fpath, index=False, encoding="utf-8-sig")
    print(f"  [写入] {username}/dictation_log.csv ({len(data)} 条)")


def date_str(days_ago: int) -> str:
    """返回 N 天前的日期字符串"""
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def time_str(hour: int, minute: int) -> str:
    return f"{hour:02d}:{minute:02d}:00"


# ==========================================
# 主逻辑
# ==========================================
def main():
    print("=" * 50)
    print("测试数据生成脚本")
    print("=" * 50)

    # 确保数据库和表存在（通过 auth 模块初始化）
    from utils.auth import init_db
    init_db()

    # ---- 创建用户 ----
    print("\n[1/4] 创建用户...")
    create_user("admin", "19870118826", is_admin=1)
    create_user("zhangsan", "Zhang1234", is_admin=0)
    create_user("lisi", "Li567890", is_admin=0)
    create_user("wangwu", "Wang1234", is_admin=0)

    # ---- 张三的数据 ----
    print("\n[2/4] 生成 zhangsan 的数据...")
    write_review_book("zhangsan", [
        {"日期": date_str(1), "问题": "什么是闭包？", "参考": "闭包是指函数可以访问其词法作用域中变量的机制，即使函数在该作用域之外执行。",
         "备注": "需要结合实际例子理解", "掌握度": 2, "复习次数": 3, "标签": "JavaScript"},
        {"日期": date_str(2), "问题": "Python 中 *args 和 **kwargs 的区别？", "参考": "*args 接收任意数量的位置参数，打包为元组；**kwargs 接收任意数量的关键字参数，打包为字典。",
         "备注": "", "掌握度": 4, "复习次数": 5, "标签": "Python"},
        {"日期": date_str(3), "问题": "HTTP 和 HTTPS 的区别？", "参考": "HTTPS 在 HTTP 基础上加入了 SSL/TLS 加密层，数据传输更安全。默认端口从 80 变为 443。",
         "备注": "加密原理也要了解", "掌握度": 3, "复习次数": 2, "标签": "网络"},
        {"日期": date_str(5), "问题": "什么是 RESTful API？", "参考": "一种基于 REST 架构风格的 API 设计规范，使用 HTTP 方法（GET/POST/PUT/DELETE）操作资源。",
         "备注": "", "掌握度": 5, "复习次数": 4, "标签": "后端"},
        {"日期": date_str(7), "问题": "React 中 useEffect 的依赖数组是什么？", "参考": "useEffect 的第二个参数，控制 effect 在哪些值变化时重新执行。空数组表示仅在挂载/卸载时执行。",
         "备注": "空数组和不传的区别", "掌握度": 1, "复习次数": 1, "标签": "React"},
        {"日期": date_str(8), "问题": "数据库事务的 ACID 特性是什么？", "参考": "A-原子性：事务是不可分割的最小单位；C-一致性：事务前后数据保持一致；I-隔离性：并发事务互不干扰；D-持久性：事务提交后数据永久保存。",
         "备注": "", "掌握度": 3, "复习次数": 2, "标签": "数据库"},
        {"日期": date_str(10), "问题": "CSS 盒模型有哪些？区别是什么？", "参考": "标准盒模型和怪异盒模型（IE盒模型）。标准盒模型 width=content，怪异盒模型 width=content+padding+border。box-sizing: border-box 切换为怪异模式。",
         "备注": "", "掌握度": 4, "复习次数": 3, "标签": "CSS"},
        {"日期": date_str(12), "问题": "Git rebase 和 merge 的区别？", "参考": "merge 保留完整的分支历史，创建合并提交；rebase 将提交序列重新应用到目标分支上，产生线性历史。",
         "备注": "团队协作时要谨慎使用 rebase", "掌握度": 2, "复习次数": 1, "标签": "Git"},
    ])
    write_study_log("zhangsan", [
        {"日期": date_str(i), "刷题数": n, "活动类型": act}
        for i, n, act in [
            (0, 5, "抽题"), (0, 3, "默写"), (1, 8, "背题"), (2, 4, "抽题"),
            (3, 6, "错题复习"), (4, 3, "抽题"), (5, 5, "背题"), (6, 4, "默写"),
            (7, 7, "抽题"), (8, 2, "错题复习"), (9, 5, "背题"), (10, 6, "抽题"),
        ]
    ])
    write_checkin_log("zhangsan", [
        {"日期": date_str(i), "签到时间": time_str(9, i * 3 % 60), "活动类型": "签到"}
        for i in range(0, 11, 1)  # 连续签到 11 天
    ])
    write_dictation_log("zhangsan", [
        {"日期": date_str(0), "问题": "什么是闭包？", "参考答案": "闭包是指函数可以访问其词法作用域中变量的机制。",
         "我的默写": "闭包就是函数里面可以使用外面的变量"},
        {"日期": date_str(2), "问题": "HTTP 和 HTTPS 的区别？", "参考答案": "HTTPS 加了 SSL/TLS 加密层，默认端口 443。",
         "我的默写": "HTTPS 更安全，加了加密层"},
    ])

    # ---- 李四的数据 ----
    print("\n[3/4] 生成 lisi 的数据...")
    write_review_book("lisi", [
        {"日期": date_str(1), "问题": "什么是虚拟 DOM？", "参考": "虚拟 DOM 是对真实 DOM 的 JavaScript 对象表示，通过 diff 算法最小化 DOM 操作。",
         "备注": "性能优化的核心", "掌握度": 3, "复习次数": 2, "标签": "前端"},
        {"日期": date_str(3), "问题": "Python 装饰器是什么？", "参考": "装饰器是一个接受函数作为参数并返回新函数的高阶函数，用 @ 语法糖调用。",
         "备注": "手写一个装饰器", "掌握度": 2, "复习次数": 1, "标签": "Python"},
        {"日期": date_str(5), "问题": "什么是跨域？如何解决？", "参考": "浏览器同源策略限制不同源的请求。解决方案：CORS、代理服务器、JSONP、WebSocket。",
         "备注": "CORS 是最常用的方式", "掌握度": 4, "复习次数": 3, "标签": "网络"},
        {"日期": date_str(6), "问题": "MySQL 索引的类型有哪些？", "参考": "B+树索引、哈希索引、全文索引、空间索引。InnoDB 默认使用 B+树索引。",
         "备注": "", "掌握度": 1, "复习次数": 0, "标签": "数据库"},
        {"日期": date_str(9), "问题": "Promise 的三种状态？", "参考": "pending（进行中）、fulfilled（已成功）、rejected（已失败）。状态一旦改变就不可逆。",
         "备注": "", "掌握度": 5, "复习次数": 4, "标签": "JavaScript"},
    ])
    write_study_log("lisi", [
        {"日期": date_str(i), "刷题数": n, "活动类型": act}
        for i, n, act in [
            (0, 3, "抽题"), (1, 5, "背题"), (2, 4, "抽题"), (3, 6, "错题复习"),
            (5, 3, "默写"), (6, 4, "抽题"), (7, 5, "背题"), (9, 2, "抽题"),
        ]
    ])
    write_checkin_log("lisi", [
        {"日期": date_str(i), "签到时间": time_str(10, (i * 7) % 60), "活动类型": "签到"}
        for i in [0, 1, 2, 3, 5, 6, 7, 9]  # 不连续签到
    ])
    write_dictation_log("lisi", [
        {"日期": date_str(1), "问题": "什么是虚拟 DOM？", "参考答案": "虚拟 DOM 是真实 DOM 的 JS 对象表示。",
         "我的默写": "用 JS 对象模拟 DOM 结构，通过 diff 算法更新"},
    ])

    # ---- 王五的数据 ----
    print("\n[4/4] 生成 wangwu 的数据...")
    write_review_book("wangwu", [
        {"日期": date_str(0), "问题": "TCP 三次握手的过程？", "参考": "1) 客户端发 SYN；2) 服务端回 SYN+ACK；3) 客户端发 ACK。三次握手确认双方收发能力正常。",
         "备注": "面试高频题", "掌握度": 3, "复习次数": 2, "标签": "网络"},
        {"日期": date_str(2), "问题": "什么是进程和线程的区别？", "参考": "进程是资源分配的基本单位，线程是 CPU 调度的基本单位。一个进程可以包含多个线程。",
         "备注": "", "掌握度": 4, "复习次数": 3, "标签": "操作系统"},
        {"日期": date_str(4), "问题": "Linux 常用命令有哪些？", "参考": "ls, cd, pwd, mkdir, rm, cp, mv, cat, grep, find, chmod, ps, top, tar 等。",
         "备注": "重点掌握 grep 和 find", "掌握度": 2, "复习次数": 1, "标签": "Linux"},
        {"日期": date_str(6), "问题": "什么是 Docker？", "参考": "Docker 是一个开源的容器化平台，将应用及其依赖打包到一个轻量级、可移植的容器中。",
         "备注": "", "掌握度": 5, "复习次数": 5, "标签": "DevOps"},
        {"日期": date_str(8), "问题": "Redis 有哪些数据类型？", "参考": "String、List、Hash、Set、Sorted Set（ZSet）。5.0 后还有 Stream。",
         "备注": "每种类型的使用场景", "掌握度": 1, "复习次数": 0, "标签": "数据库"},
        {"日期": date_str(10), "问题": "什么是微服务架构？", "参考": "将单体应用拆分为多个小型、独立部署的服务，每个服务负责一个业务功能，通过 API 通信。",
         "备注": "了解与单体架构的对比", "掌握度": 3, "复习次数": 2, "标签": "架构"},
    ])
    write_study_log("wangwu", [
        {"日期": date_str(i), "刷题数": n, "活动类型": act}
        for i, n, act in [
            (0, 10, "抽题"), (0, 5, "背题"), (1, 8, "默写"), (2, 6, "错题复习"),
            (3, 4, "抽题"), (4, 7, "背题"), (5, 3, "抽题"), (6, 5, "默写"),
            (7, 9, "背题"), (8, 4, "错题复习"), (9, 6, "抽题"), (10, 8, "背题"),
            (11, 3, "抽题"), (12, 5, "默写"),
        ]
    ])
    write_checkin_log("wangwu", [
        {"日期": date_str(i), "签到时间": time_str(8, (i * 5) % 60), "活动类型": "签到"}
        for i in range(0, 13)  # 连续签到 13 天
    ])
    write_dictation_log("wangwu", [
        {"日期": date_str(0), "问题": "TCP 三次握手的过程？", "参考答案": "SYN → SYN+ACK → ACK",
         "我的默写": "客户端发 SYN，服务端回 SYN+ACK，客户端再发 ACK"},
        {"日期": date_str(2), "问题": "什么是进程和线程的区别？", "参考答案": "进程是资源分配单位，线程是 CPU 调度单位。",
         "我的默写": "进程拥有独立资源，线程共享进程资源"},
        {"日期": date_str(4), "问题": "Redis 有哪些数据类型？", "参考答案": "String, List, Hash, Set, ZSet",
         "我的默写": "String、List、Hash、Set、有序集合"},
    ])

    print("\n" + "=" * 50)
    print("测试数据生成完成！")
    print("=" * 50)
    print("\n测试账号：")
    print("  管理员：admin / 19870118826")
    print("  用户1：zhangsan / Zhang1234")
    print("  用户2：lisi / Li567890")
    print("  用户3：wangwu / Wang1234")


if __name__ == "__main__":
    main()
