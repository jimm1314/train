"""
测试MySQL/TiDB连接
"""
import pymysql
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.db_config import DB_CONFIG, DB_NAME
except ImportError:
    print("错误：找不到 db_config.py 配置文件")
    sys.exit(1)

def test_connection():
    """测试MySQL/TiDB连接"""
    print("=== 测试 MySQL/TiDB 连接 ===")
    print(f"主机: {DB_CONFIG['host']}")
    print(f"端口: {DB_CONFIG['port']}")
    print(f"用户: {DB_CONFIG['user']}")
    print(f"数据库: {DB_NAME}")
    
    try:
        # 测试连接
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset'],
            connect_timeout=10
        )
        print("✓ MySQL/TiDB 连接成功")
        
        # 检查数据库是否存在
        with conn.cursor() as cursor:
            cursor.execute("SHOW DATABASES LIKE %s", (DB_NAME,))
            result = cursor.fetchone()
            if result:
                print(f"✓ 数据库 '{DB_NAME}' 已存在")
                
                # 切换到目标数据库
                cursor.execute(f"USE {DB_NAME}")
                
                # 检查表是否存在
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                
                print(f"数据库中的表:")
                for table in tables:
                    print(f"  - {table[0]}")
                
                # 检查interview_questions表
                cursor.execute("SHOW TABLES LIKE 'interview_questions'")
                result = cursor.fetchone()
                
                if result:
                    print("✓ interview_questions 表存在")
                    
                    # 检查数据数量
                    cursor.execute("SELECT COUNT(*) FROM interview_questions")
                    count = cursor.fetchone()[0]
                    print(f"✓ 表中有 {count} 条记录")
                    
                    # 检查分类
                    cursor.execute("SELECT DISTINCT category FROM interview_questions")
                    categories = cursor.fetchall()
                    print(f"分类列表:")
                    for cat in categories:
                        print(f"  - {cat[0]}")
                else:
                    print("✗ interview_questions 表不存在")
            else:
                print(f"✗ 数据库 '{DB_NAME}' 不存在")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return False

if __name__ == "__main__":
    test_connection()
