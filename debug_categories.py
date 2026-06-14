"""
调试分类显示问题
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from utils.data_loader import load_question_banks, get_filtered_questions, get_knowledge_categories

def debug_categories():
    """调试分类显示问题"""
    print("=== 调试分类显示问题 ===")
    
    # 测试1：加载题库
    print("\n1. 加载题库数据:")
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
                print(f"   知识点值分布:")
                print(df['知识点'].value_counts())
            else:
                print("\n   知识点列不存在")
                
            # 检查"难度"列
            if "难度" in df.columns:
                print(f"\n   难度列存在，唯一值: {df['难度'].unique().tolist()}")
            else:
                print("\n   难度列不存在")
        else:
            print("   DataFrame 为空")
    except Exception as e:
        print(f"   加载失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 测试2：获取筛选后的问题
    print("\n2. 获取筛选后的问题:")
    try:
        filtered_df = get_filtered_questions(force_show_all=False)
        print(f"   筛选后 DataFrame 形状: {filtered_df.shape}")
        
        if not filtered_df.empty:
            if "知识点" in filtered_df.columns:
                print(f"   筛选后知识点列唯一值: {filtered_df['知识点'].unique().tolist()}")
            else:
                print("   筛选后知识点列不存在")
    except Exception as e:
        print(f"   获取筛选后问题失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 测试3：获取知识点分类
    print("\n3. 获取知识点分类:")
    try:
        categories = get_knowledge_categories(df)
        print(f"   知识点分类列表: {categories}")
        
        if not categories:
            print("   警告：知识点分类列表为空！")
            
            # 尝试手动获取分类
            if "知识点" in df.columns:
                manual_categories = sorted(df["知识点"].dropna().unique().tolist())
                print(f"   手动获取的分类: {manual_categories}")
    except Exception as e:
        print(f"   获取知识点分类失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_categories()
