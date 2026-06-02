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
# TiDB Cloud 配置说明（部署到 Streamlit Cloud 时使用）
# ==========================================
# 在 Streamlit Cloud 项目的 Settings → Secrets 中填写以下内容：
#
# [database]
# host = "gateway01.us-west-2.prod.aws.tidbcloud.com"
# port = 4000
# user = "xxxxxxx.root"
# password = "xxxxxxxxxxxxxxx"
# database = "quiz_system"
#
# TiDB Cloud 注册地址：https://tidbcloud.com/free-trial
# 创建 Serverless 集群后，在 "Connect" 页面获取以上信息。
