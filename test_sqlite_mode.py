"""
测试 SQLite 模式运行
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_sqlite_mode():
    """测试在 SQLite 模式下运行"""
    print("=== 测试 SQLite 模式 ===")
    
    try:
        # 测试导入关键模块
        from utils import db
        print("✓ 数据库模块加载成功")
        
        # 检查当前使用的数据库类型
        if db.is_mysql():
            print("当前使用: MySQL/TiDB 模式")
        else:
            print("当前使用: SQLite 模式（MySQL 不可用时的后备方案）")
        
        # 测试初始化表结构
        print("\n初始化数据库表结构...")
        db.init_tables()
        print("✓ 表结构初始化成功")
        
        # 测试查询
        print("\n测试数据库查询...")
        result = db.query_df("SELECT name FROM sqlite_master WHERE type='table'")
        if not result.empty:
            print("✓ 数据库表列表:")
            for _, row in result.iterrows():
                print(f"  - {row['name']}")
        
        return True
        
    except Exception as e:
        print(f"✗ SQLite 模式测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_loader():
    """测试数据加载功能"""
    print("\n=== 测试数据加载 ===")
    
    try:
        from utils.data_loader import load_question_banks, get_filtered_questions
        
        print("加载题库数据...")
        df = load_question_banks()
        
        if not df.empty:
            print(f"✓ 成功加载 {len(df)} 道题目")
            print(f"  列名: {list(df.columns)}")
            
            # 显示前3道题
            print("\n前3道题目预览:")
            for i, row in df.head(3).iterrows():
                question = str(row.get('问题', ''))[:50]
                print(f"  {i+1}. {question}...")
            
            return True
        else:
            print("✗ 题库为空，需要导入数据")
            return False
            
    except Exception as e:
        print(f"✗ 数据加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("SQLite 模式运行测试")
    print("=" * 50)
    
    # 测试1：SQLite 模式
    sqlite_ok = test_sqlite_mode()
    
    # 测试2：数据加载
    data_ok = test_data_loader()
    
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print(f"  SQLite 模式: {'通过' if sqlite_ok else '失败'}")
    print(f"  数据加载: {'通过' if data_ok else '失败'}")
    
    if sqlite_ok and data_ok:
        print("\n✓ 项目可以在 SQLite 模式下正常运行")
        print("  启动命令: streamlit run app.py")
    elif sqlite_ok and not data_ok:
        print("\n⚠ SQLite 模式正常，但题库为空")
        print("  建议：先运行导入脚本添加题目")
    else:
        print("\n✗ 存在未通过的测试，请修复后再运行")

if __name__ == "__main__":
    main()
