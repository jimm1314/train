# TiDB Cloud 数据库配置
# 请根据您的TiDB连接信息修改以下配置

DB_CONFIG = {
    'host': 'gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com',
    'port': 4000,
    'user': '42S5q2MAmcRFfHT.root',
    'password': 'YJofMq4ilpYzt4TW',
    'charset': 'utf8mb4',
    'ssl': {},
}

DB_NAME = 'quiz_system'

# Excel文件配置
EXCEL_FILES = [
    {
        'path': r"d:\software\PyCharm 2025.3.5\file_saves\genmini\data\interview_questions_day01-07.xlsx",
        'sheet': 'Sheet1',
        'source': 'day01-07',
        'category': '深度学习'
    },
    {
        'path': r"d:\software\PyCharm 2025.3.5\file_saves\genmini\data\interview_questions.xlsx",
        'sheet': '面试题',
        'source': 'interview',
        'category': 'NLP'
    },
    {
        'path': r"d:\software\PyCharm 2025.3.5\file_saves\genmini\data\投满分项目-课堂面试题.xlsx",
        'sheet': '面试题',
        'source': 'project',
        'category': '机器学习'
    }
]

# 导入配置
IMPORT_CONFIG = {
    'batch_size': 100,  # 批量插入大小
    'create_database': True,  # 是否创建数据库
    'drop_existing': False,   # 是否删除已存在的表
    'verbose': True          # 是否显示详细日志
}