"""
测试Streamlit应用中的数据库连接
"""
import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import db

st.title("数据库连接测试")

st.markdown("### 1. 数据库连接状态")

try:
    is_mysql = db.is_mysql()
    st.write(f"是否使用MySQL: {is_mysql}")
    
    if is_mysql:
        st.success("✓ 正在使用MySQL/TiDB数据库")
    else:
        st.warning("⚠ 正在使用SQLite数据库")
        
except Exception as e:
    st.error(f"检查数据库连接失败: {e}")

st.markdown("### 2. 测试数据库查询")

try:
    if db.is_mysql():
        st.write("尝试从MySQL/TiDB查询数据...")
        df = db.query_df("SELECT COUNT(*) as count FROM interview_questions")
        st.write(f"查询结果: {df}")
        
        if not df.empty:
            count = df.iloc[0]['count']
            st.success(f"✓ 数据库中有 {count} 道题目")
            
            # 查询分类
            categories_df = db.query_df("SELECT DISTINCT category FROM interview_questions ORDER BY category")
            st.write(f"分类列表: {categories_df['category'].tolist()}")
        else:
            st.error("✗ 查询结果为空")
    else:
        st.write("正在使用SQLite数据库，跳过MySQL测试")
        
except Exception as e:
    st.error(f"数据库查询失败: {e}")
    import traceback
    st.code(traceback.format_exc())
