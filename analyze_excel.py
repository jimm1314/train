import pandas as pd
import os

# 定义文件路径
files = [
    r"d:\software\PyCharm 2025.3.5\file_saves\genmini\data\interview_questions_day01-07.xlsx",
    r"d:\software\PyCharm 2025.3.5\file_saves\genmini\data\interview_questions.xlsx",
    r"d:\software\PyCharm 2025.3.5\file_saves\genmini\data\投满分项目-课堂面试题.xlsx"
]

# 分析每个文件
for file_path in files:
    print(f"\n=== 分析文件: {os.path.basename(file_path)} ===")
    
    try:
        # 读取Excel文件
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        print(f"工作表数量: {len(sheet_names)}")
        print(f"工作表名称: {sheet_names}")
        
        # 分析每个工作表
        for sheet_name in sheet_names:
            print(f"\n--- 工作表: {sheet_name} ---")
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # 显示基本信息
            print(f"行数: {len(df)}, 列数: {len(df.columns)}")
            print(f"列名: {list(df.columns)}")
            
            # 显示前几行数据
            print("\n前3行数据:")
            print(df.head(3).to_string())
            
            # 显示数据类型
            print("\n数据类型:")
            print(df.dtypes)
            
            # 检查缺失值
            missing_values = df.isnull().sum()
            if missing_values.any():
                print("\n缺失值统计:")
                print(missing_values[missing_values > 0])
            
            # 显示唯一值统计（对于分类列）
            print("\n唯一值统计:")
            for col in df.columns:
                if df[col].dtype == 'object' or df[col].nunique() < 10:
                    unique_count = df[col].nunique()
                    print(f"  {col}: {unique_count}个唯一值")
                    if unique_count <= 5:
                        print(f"    示例值: {df[col].dropna().unique()[:5].tolist()}")
        
    except Exception as e:
        print(f"读取文件时出错: {e}")
        import traceback
        traceback.print_exc()