"""
测试数据库连接和导入功能
"""
import pymysql
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from db_config import DB_CONFIG
except ImportError:
    print("错误：找不到 db_config.py 配置文件")
    sys.exit(1)

def test_connection():
    """测试数据库连接"""
    print("=== 测试数据库连接 ===")
    print(f"主机: {DB_CONFIG['host']}")
    print(f"端口: {DB_CONFIG['port']}")
    print(f"用户: {DB_CONFIG['user']}")
    print(f"数据库: {DB_CONFIG['database']}")
    
    try:
        # 测试连接（不指定数据库）
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset']
        )
        print("✓ 数据库连接成功")
        
        # 检查数据库是否存在
        with conn.cursor() as cursor:
            cursor.execute("SHOW DATABASES LIKE %s", (DB_CONFIG['database'],))
            result = cursor.fetchone()
            if result:
                print(f"✓ 数据库 '{DB_CONFIG['database']}' 已存在")
            else:
                print(f"✗ 数据库 '{DB_CONFIG['database']}' 不存在，需要创建")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return False

def test_excel_files():
    """测试Excel文件是否存在"""
    print("\n=== 检查Excel文件 ===")
    
    try:
        from db_config import EXCEL_FILES
        
        for file_config in EXCEL_FILES:
            file_path = file_config['path']
            if os.path.exists(file_path):
                print(f"✓ {os.path.basename(file_path)} - 存在")
            else:
                print(f"✗ {os.path.basename(file_path)} - 不存在")
                print(f"  路径: {file_path}")
        
        return True
    except Exception as e:
        print(f"检查文件时出错: {e}")
        return False

def test_import_script():
    """测试导入脚本是否能正常加载"""
    print("\n=== 测试导入脚本 ===")
    
    try:
        import import_to_tidb
        print("✓ 导入脚本可以正常加载")
        return True
    except Exception as e:
        print(f"✗ 导入脚本加载失败: {e}")
        return False

def main():
    print("项目运行检查工具")
    print("=" * 50)
    
    # 测试1：数据库连接
    db_ok = test_connection()
    
    # 测试2：Excel文件
    files_ok = test_excel_files()
    
    # 测试3：导入脚本
    script_ok = test_import_script()
    
    print("\n" + "=" * 50)
    print("检查结果汇总:")
    print(f"  数据库连接: {'通过' if db_ok else '失败'}")
    print(f"  Excel文件: {'通过' if files_ok else '失败'}")
    print(f"  导入脚本: {'通过' if script_ok else '失败'}")
    
    if db_ok and files_ok and script_ok:
        print("\n✓ 所有检查通过，可以运行导入脚本")
        print("  运行命令: python import_to_tidb.py")
    else:
        print("\n✗ 存在未通过的检查，请修复后再运行")

if __name__ == "__main__":
    main()
