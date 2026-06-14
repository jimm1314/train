import pandas as pd
import pymysql
import sys
import os
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from db_config import DB_CONFIG, EXCEL_FILES, IMPORT_CONFIG
except ImportError:
    print("错误：找不到 db_config.py 配置文件")
    sys.exit(1)

def create_database():
    """创建数据库（如果不存在）"""
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset']
        )
        
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            print(f"数据库 {DB_CONFIG['database']} 已创建或已存在")
        
        conn.close()
        return True
    except Exception as e:
        print(f"创建数据库失败: {e}")
        return False

def create_tables():
    """创建表结构"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        
        with conn.cursor() as cursor:
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
                        if IMPORT_CONFIG['verbose']:
                            print(f"执行SQL: {stmt[:50]}...")
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            print(f"SQL执行警告: {e}")
            
            conn.commit()
            print("表结构创建完成")
        
        conn.close()
        return True
    except Exception as e:
        print(f"创建表失败: {e}")
        return False

def import_excel_data():
    """导入Excel数据到TiDB"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        
        for file_config in EXCEL_FILES:
            file_path = file_config['path']
            sheet_name = file_config['sheet']
            source = file_config['source']
            category = file_config['category']
            
            print(f"\n处理文件: {os.path.basename(file_path)}")
            
            try:
                # 读取Excel文件
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                if IMPORT_CONFIG['verbose']:
                    print(f"读取到 {len(df)} 行数据")
                
                # 准备插入语句
                insert_sql = """
                INSERT INTO interview_questions 
                (question, answer, is_visible, source, category)
                VALUES (%s, %s, %s, %s, %s)
                """
                
                # 批量插入数据
                batch_size = IMPORT_CONFIG['batch_size']
                total_inserted = 0
                
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
                        
                        total_inserted += len(data_to_insert)
                        if IMPORT_CONFIG['verbose']:
                            print(f"已插入 {total_inserted}/{len(df)} 行")
                
                print(f"文件 {os.path.basename(file_path)} 导入完成，共 {total_inserted} 行")
                
            except Exception as e:
                print(f"处理文件 {os.path.basename(file_path)} 时出错: {e}")
                import traceback
                traceback.print_exc()
        
        conn.close()
        return True
    except Exception as e:
        print(f"导入数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_import():
    """验证导入结果"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        
        with conn.cursor() as cursor:
            # 查询总记录数
            cursor.execute("SELECT COUNT(*) FROM interview_questions")
            total_count = cursor.fetchone()[0]
            
            # 按来源统计
            cursor.execute("SELECT source, COUNT(*) FROM interview_questions GROUP BY source")
            source_counts = cursor.fetchall()
            
            print(f"\n=== 导入验证 ===")
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
        print(f"验证失败: {e}")
        return False

def main():
    """主函数"""
    print("=== TiDB 数据导入工具 ===")
    print(f"目标数据库: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print(f"导入文件数量: {len(EXCEL_FILES)}")
    
    # 步骤1：创建数据库
    if IMPORT_CONFIG['create_database']:
        print("\n步骤1: 创建数据库...")
        if not create_database():
            print("创建数据库失败，退出")
            return
    
    # 步骤2：创建表结构
    print("\n步骤2: 创建表结构...")
    if not create_tables():
        print("创建表失败，退出")
        return
    
    # 步骤3：导入数据
    print("\n步骤3: 导入数据...")
    if not import_excel_data():
        print("导入数据失败，退出")
        return
    
    # 步骤4：验证导入
    print("\n步骤4: 验证导入...")
    verify_import()
    
    print("\n=== 导入完成 ===")

if __name__ == "__main__":
    main()