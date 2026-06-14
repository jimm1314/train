"""
测试编辑题库页面
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from utils import db

def test_editor_page():
    """测试编辑题库页面"""
    print("=== 测试编辑题库页面 ===")
    
    # 测试数据库连接
    print("\n1. 测试数据库连接:")
    try:
        db.init_tables()
        print("   ✓ 数据库表初始化成功")
    except Exception as e:
        print(f"   ✗ 数据库表初始化失败: {e}")
        return
    
    # 测试获取分类
    print("\n2. 测试获取分类:")
    try:
        rows = db.execute("SELECT DISTINCT category FROM interview_questions ORDER BY category", fetch=True)
        categories = [r["category"] for r in rows] if rows else []
        print(f"   分类列表: {categories}")
    except Exception as e:
        print(f"   ✗ 获取分类失败: {e}")
        return
    
    # 测试读取题目
    print("\n3. 测试读取题目:")
    if categories:
        category = categories[0]
        try:
            sql = "SELECT id, question AS 问题, answer AS 参考, category AS 知识点, difficulty AS 难度, source AS 来源, is_visible AS 是否显示 FROM interview_questions WHERE category = %s"
            df = db.query_df(sql, (category,))
            print(f"   分类 '{category}' 中有 {len(df)} 道题目")
            
            if not df.empty:
                print(f"   列名: {list(df.columns)}")
                print(f"   前3道题目:")
                for i, row in df.head(3).iterrows():
                    print(f"     {i+1}. {row['问题'][:50]}...")
        except Exception as e:
            print(f"   ✗ 读取题目失败: {e}")
    else:
        print("   没有分类，跳过测试")

if __name__ == "__main__":
    test_editor_page()
