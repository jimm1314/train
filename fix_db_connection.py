"""
修复数据库连接问题
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def fix_db_connection():
    """修复数据库连接问题"""
    print("=== 修复数据库连接问题 ===")
    
    # 检查db.py文件
    print("\n1. 检查db.py文件:")
    try:
        from utils import db
        print(f"   ✓ db模块加载成功")
        print(f"   是否使用MySQL: {db.is_mysql()}")
    except Exception as e:
        print(f"   ✗ db模块加载失败: {e}")
        return
    
    # 检查数据库配置
    print("\n2. 检查数据库配置:")
    try:
        from utils.db_config import DB_CONFIG, DB_NAME
        print(f"   主机: {DB_CONFIG['host']}")
        print(f"   端口: {DB_CONFIG['port']}")
        print(f"   用户: {DB_CONFIG['user']}")
        print(f"   数据库: {DB_NAME}")
    except Exception as e:
        print(f"   ✗ 数据库配置加载失败: {e}")
        return
    
    # 测试数据库连接
    print("\n3. 测试数据库连接:")
    try:
        import pymysql
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset'],
            connect_timeout=10
        )
        print("   ✓ 数据库连接成功")
        conn.close()
    except Exception as e:
        print(f"   ✗ 数据库连接失败: {e}")
        return
    
    # 检查db.py中的连接逻辑
    print("\n4. 检查db.py中的连接逻辑:")
    try:
        # 重新加载db模块
        import importlib
        importlib.reload(db)
        
        print(f"   是否使用MySQL: {db.is_mysql()}")
        
        if db.is_mysql():
            print("   ✓ 数据库连接正常")
        else:
            print("   ✗ 数据库连接失败，将使用SQLite")
            
            # 尝试手动设置_USE_MYSQL
            print("\n5. 尝试手动修复:")
            try:
                # 获取数据库配置
                from utils.db_config import DB_CONFIG, DB_NAME
                
                # 测试连接
                import pymysql
                conn = pymysql.connect(
                    host=DB_CONFIG['host'],
                    port=DB_CONFIG['port'],
                    user=DB_CONFIG['user'],
                    password=DB_CONFIG['password'],
                    charset=DB_CONFIG['charset'],
                    connect_timeout=10
                )
                print("   ✓ 数据库连接成功")
                conn.close()
                
                # 手动设置_USE_MYSQL
                db._USE_MYSQL = True
                print("   ✓ 手动设置_USE_MYSQL为True")
                
            except Exception as e:
                print(f"   ✗ 手动修复失败: {e}")
    except Exception as e:
        print(f"   ✗ 检查db.py中的连接逻辑失败: {e}")

if __name__ == "__main__":
    fix_db_connection()
