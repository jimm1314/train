"""
检查数据库中的分类字段
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

def check_categories():
    """检查数据库中的分类字段"""
    print("=== 检查数据库分类字段 ===")
    
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
            # 检查category字段的所有值
            cursor.execute("SELECT DISTINCT category FROM interview_questions ORDER BY category")
            categories = cursor.fetchall()
            
            print("数据库中的分类字段:")
            for cat in categories:
                print(f"  - {cat[0]}")
            
            # 检查每个分类的题目数量
            print("\n各分类题目数量:")
            cursor.execute("SELECT category, COUNT(*) as count FROM interview_questions GROUP BY category ORDER BY count DESC")
            category_counts = cursor.fetchall()
            
            for cat, count in category_counts:
                print(f"  {cat}: {count} 道题目")
            
            # 检查source字段
            print("\n数据库中的来源字段:")
            cursor.execute("SELECT DISTINCT source FROM interview_questions ORDER BY source")
            sources = cursor.fetchall()
            
            for source in sources:
                print(f"  - {source[0]}")
            
            # 检查difficulty字段
            print("\n数据库中的难度字段:")
            cursor.execute("SELECT DISTINCT difficulty FROM interview_questions ORDER BY difficulty")
            difficulties = cursor.fetchall()
            
            for diff in difficulties:
                print(f"  - {diff[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return False

if __name__ == "__main__":
    check_categories()
