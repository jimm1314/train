"""
简单的Streamlit应用测试数据加载
"""
import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader import load_question_banks, get_knowledge_categories

st.title("数据加载测试")

st.markdown("### 1. 加载题库数据")

try:
    df = load_question_banks()
    st.success(f"✓ 成功加载 {len(df)} 道题目")
    
    st.markdown("### 2. 数据列名")
    st.write(list(df.columns))
    
    st.markdown("### 3. 前3道题目")
    st.dataframe(df.head(3), use_container_width=True)
    
    st.markdown("### 4. 知识点分类")
    if "知识点" in df.columns:
        categories = get_knowledge_categories(df)
        st.write(f"知识点分类列表: {categories}")
        
        st.markdown("### 5. 知识点分布")
        st.write(df['知识点'].value_counts())
        
        st.markdown("### 6. 下拉框测试")
        selected_cat = st.selectbox("选择知识点分类", ["全部"] + categories)
        st.write(f"你选择了: {selected_cat}")
    else:
        st.error("知识点列不存在")
        
except Exception as e:
    st.error(f"加载失败: {e}")
    import traceback
    st.code(traceback.format_exc())
