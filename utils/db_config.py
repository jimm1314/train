"""
数据库配置文件
优先级：Streamlit Cloud secrets > 本地配置
"""

# ==========================================
# 本地开发配置（在本机安装了 MySQL 时使用）
# ==========================================
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "charset": "utf8mb4",
}

DB_NAME = "quiz_system"

# ==========================================
# Streamlit Cloud 部署配置
# ==========================================
# 在 Streamlit Cloud 项目的 Settings → Secrets 中填写：
#
# [database]
# host = "gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com"
# port = 4000
# user = "42S5q2MAmcRFfHT.root"
# password = "WZyUpXU2NW77rkEo"
# database = "quiz_system"
