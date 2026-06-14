"""
检查TiDB Cloud中的表结构
"""
import pymysql
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from db_config import DB_CONFIG
except ImportError:
    print("错误：找不到 db_config.py 配置文件")
    sys.exit(1)

def check_tables():
    """检查表结构"""
    print("=== 检查 TiDB Cloud 表结构 ===")
    
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset=DB_CONFIG['charset'],
            connect_timeout=10
        )
        
        with conn.cursor() as cursor:
            # 检查所有表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            print(f"数据库 '{DB_CONFIG['database']}' 中的表:")
            if tables:
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("  没有找到表")
            
            # 检查interview_questions表是否存在
            cursor.execute("SHOW TABLES LIKE 'interview_questions'")
            result = cursor.fetchone()
            
            if result:
                print("\n✓ interview_questions 表存在")
                
                # 显示表结构
                cursor.execute("DESCRIBE interview_questions")
                columns = cursor.fetchall()
                
                print("\n表结构:")
                for col in columns:
                    print(f"  {col[0]}: {col[1]}")
            else:
                print("\n✗ interview_questions 表不存在")
                
                # 尝试手动创建表
                print("\n尝试手动创建表...")
                create_sql = """
                CREATE TABLE IF NOT EXISTS interview_questions (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    question TEXT NOT NULL,
                    answer TEXT,
                    is_visible TINYINT DEFAULT 1,
                    source VARCHAR(50) NOT NULL DEFAULT '',
                    category VARCHAR(50) NOT NULL DEFAULT '未分类',
                    difficulty VARCHAR(20) NOT NULL DEFAULT '中等',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_source (source),
                    INDEX idx_category (category),
                    INDEX idx_is_visible (is_visible),
                    FULLTEXT INDEX ft_question (question),
                    FULLTEXT INDEX ft_answer (answer)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
                
                try:
                    cursor.execute(create_sql)
                    conn.commit()
                    print("✓ 表创建成功")
                    
                    # 再次检查
                    cursor.execute("SHOW TABLES LIKE 'interview_questions'")
                    result = cursor.fetchone()
                    if result:
                        print("✓ 表已确认存在")
                    else:
                        print("✗ 表创建失败")
                except Exception as e:
                    print(f"✗ 创建表失败: {e}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return False

if __name__ == "__main__":
    check_tables()
