"""
测试数据加载
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 模拟Streamlit环境
import streamlit as st
from utils.data_loader import load_question_banks, get_knowledge_categories, get_categories_from_db

def test_data_loading():
    """测试数据加载"""
    print("=== 测试数据加载 ===")
    
    # 测试直接从数据库获取分类
    print("\n1. 直接从数据库获取分类:")
    categories = get_categories_from_db()
    print(f"   分类列表: {categories}")
    
    # 测试加载题库
    print("\n2. 加载题库数据:")
    try:
        df = load_question_banks()
        print(f"   DataFrame 形状: {df.shape}")
        print(f"   列名: {list(df.columns)}")
        
        if not df.empty:
            print(f"   前3行数据:")
            for i, row in df.head(3).iterrows():
                print(f"     {i}: {row.get('问题', 'N/A')[:50]}...")
            
            # 测试获取知识点分类
            print("\n3. 获取知识点分类:")
            knowledge_categories = get_knowledge_categories(df)
            print(f"   知识点分类: {knowledge_categories}")
            
            # 检查"知识点"列是否存在
            if "知识点" in df.columns:
                print(f"   知识点列存在，唯一值: {df['知识点'].unique().tolist()}")
            else:
                print("   知识点列不存在")
            
            # 检查"难度"列是否存在
            if "难度" in df.columns:
                print(f"   难度列存在，唯一值: {df['难度'].unique().tolist()}")
            else:
                print("   难度列不存在")
        else:
            print("   DataFrame 为空")
    except Exception as e:
        print(f"   加载失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_data_loading()
