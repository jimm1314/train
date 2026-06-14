"""
迁移数据到 TiDB Cloud
"""
import pandas as pd
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
    """测试TiDB Cloud连接"""
    print("=== 测试 TiDB Cloud 连接 ===")
    print(f"主机: {DB_CONFIG['host']}")
    print(f"端口: {DB_CONFIG['port']}")
    print(f"用户: {DB_CONFIG['user']}")
    print(f"数据库: {DB_CONFIG['database']}")
    
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
        print("✓ TiDB Cloud 连接成功")
        
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

def create_database_and_tables():
    """创建数据库和表结构"""
    print("\n=== 创建数据库和表结构 ===")
    
    try:
        # 连接到TiDB（不指定数据库）
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset'],
            connect_timeout=10
        )
        
        with conn.cursor() as cursor:
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            print(f"✓ 数据库 '{DB_CONFIG['database']}' 已创建或已存在")
            
            # 切换到目标数据库
            cursor.execute(f"USE {DB_CONFIG['database']}")
            
            # 读取SQL文件
            sql_file_path = os.path.join(os.path.dirname(__file__), 'tidb_schema.sql')
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 分割SQL语句
            sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for stmt in sql_statements:
                if stmt.upper().startswith('CREATE') or stmt.upper().startswith('DROP'):
                    try:
                        cursor.execute(stmt)
                        print(f"✓ 执行SQL: {stmt[:50]}...")
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            print(f"⚠ SQL执行警告: {e}")
            
            conn.commit()
            print("✓ 表结构创建完成")
        
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 创建数据库和表失败: {e}")
        return False

def import_excel_data():
    """导入Excel数据到TiDB Cloud"""
    print("\n=== 导入Excel数据 ===")
    
    try:
        # 连接到TiDB
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset=DB_CONFIG['charset'],
            connect_timeout=10
        )
        
        # Excel文件配置
        excel_files = [
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
        
        total_inserted = 0
        
        for file_config in excel_files:
            file_path = file_config['path']
            sheet_name = file_config['sheet']
            source = file_config['source']
            category = file_config['category']
            
            print(f"\n处理文件: {os.path.basename(file_path)}")
            
            try:
                # 读取Excel文件
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                print(f"读取到 {len(df)} 行数据")
                
                # 准备插入语句
                insert_sql = """
                INSERT INTO interview_questions 
                (question, answer, is_visible, source, category)
                VALUES (%s, %s, %s, %s, %s)
                """
                
                # 批量插入数据
                batch_size = 100
                file_inserted = 0
                
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size]
                    
                    # 准备数据
                    data_to_insert = []
                    for _, row in batch.iterrows():
                        question = str(row['问题']) if pd.notna(row['问题']) else ''
                        answer = str(row['参考答案']) if pd.notna(row['参考答案']) else ''
                        is_visible = int(row['是否显示']) if pd.notna(row['是否显示']) else 1
                        
                        data_to_insert.append((
                            question,
                            answer,
                            is_visible,
                            source,
                            category
                        ))
                    
                    # 执行批量插入
                    with conn.cursor() as cursor:
                        cursor.executemany(insert_sql, data_to_insert)
                        conn.commit()
                        
                        file_inserted += len(data_to_insert)
                        print(f"已插入 {file_inserted}/{len(df)} 行")
                
                total_inserted += file_inserted
                print(f"✓ 文件 {os.path.basename(file_path)} 导入完成，共 {file_inserted} 行")
                
            except Exception as e:
                print(f"✗ 处理文件 {os.path.basename(file_path)} 时出错: {e}")
                import traceback
                traceback.print_exc()
        
        conn.close()
        print(f"\n✓ 所有文件导入完成，总共 {total_inserted} 行")
        return True
    except Exception as e:
        print(f"✗ 导入数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_import():
    """验证导入结果"""
    print("\n=== 验证导入结果 ===")
    
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
            # 查询总记录数
            cursor.execute("SELECT COUNT(*) FROM interview_questions")
            total_count = cursor.fetchone()[0]
            
            # 按来源统计
            cursor.execute("SELECT source, COUNT(*) FROM interview_questions GROUP BY source")
            source_counts = cursor.fetchall()
            
            print(f"总记录数: {total_count}")
            print("按来源统计:")
            for source, count in source_counts:
                print(f"  {source}: {count} 条")
            
            # 显示示例数据
            cursor.execute("SELECT question, source, category FROM interview_questions LIMIT 3")
            sample_data = cursor.fetchall()
            
            print("\n示例数据:")
            for question, source, category in sample_data:
                print(f"  问题: {question[:50]}...")
                print(f"  来源: {source}, 分类: {category}")
                print()
        
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        return False

def main():
    """主函数"""
    print("=== TiDB Cloud 数据迁移工具 ===")
    print(f"目标数据库: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    
    # 步骤1：测试连接
    if not test_connection():
        print("\n连接失败，请检查配置信息")
        return
    
    # 步骤2：创建数据库和表结构
    if not create_database_and_tables():
        print("\n创建数据库和表失败")
        return
    
    # 步骤3：导入数据
    if not import_excel_data():
        print("\n导入数据失败")
        return
    
    # 步骤4：验证导入
    if not verify_import():
        print("\n验证失败")
        return
    
    print("\n=== 迁移完成 ===")
    print("您的数据已成功迁移到 TiDB Cloud！")
    print("现在可以重新启动 Streamlit 应用，它将使用云端数据库。")

if __name__ == "__main__":
    main()
