"""
数据库配置文件
优先级：Streamlit Cloud secrets > 本地配置
"""

# ==========================================
# TiDB Cloud 配置（需要SSL连接）
# ==========================================
DB_CONFIG = {
    "host": "gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com",
    "port": 4000,
    "user": "42S5q2MAmcRFfHT.root",
    "password": "YJofMq4ilpYzt4TW",
    "charset": "utf8mb4",
    "ssl": {},
}

DB_NAME = "quiz_system"