"""
测试Streamlit应用数据加载
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from utils.data_loader import load_question_banks, get_knowledge_categories

def test_streamlit_loading():
    """测试Streamlit应用数据加载"""
    print("=== 测试Streamlit应用数据加载 ===")
    
    # 清除缓存
    print("\n1. 清除缓存:")
    try:
        load_question_banks.clear()
        print("   ✓ 缓存已清除")
    except Exception as e:
        print(f"   清除缓存失败: {e}")
    
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
            
            # 检查"知识点"列
            if "知识点" in df.columns:
                print(f"\n   知识点列存在，唯一值: {df['知识点'].unique().tolist()}")
                
                # 获取知识点分类
                categories = get_knowledge_categories(df)
                print(f"   知识点分类列表: {categories}")
                
                if not categories:
                    print("   警告：知识点分类列表为空！")
                    
                    # 尝试手动获取分类
                    manual_categories = sorted(df["知识点"].dropna().unique().tolist())
                    print(f"   手动获取的分类: {manual_categories}")
            else:
                print("\n   知识点列不存在")
        else:
            print("   DataFrame 为空")
    except Exception as e:
        print(f"   加载失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_streamlit_loading()
