import streamlit as st
import pandas as pd
import plotly.express as px

# ====================== 页面基础配置 ======================
st.set_page_config(
    page_title="上市企业去内卷化指数分析系统",
    page_icon="📊",
    layout="wide"
)

# ====================== 读取计算完成的最终数据 ======================
@st.cache_data
def load_data():
    df = pd.read_csv("de_involution_final_result.csv", dtype={'stkcd': str})
    return df

df = load_data()
# 检查是否有行业列，做容错处理
has_industry = 'indnm' in df.columns

# ====================== 页面标题与核心概览 ======================
st.title("📊 上市企业去内卷化指数分析系统")
st.markdown("基于年度动态熵权法构建的上市公司去内卷化指数可视化分析平台")

# 核心指标概览
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("总样本量", len(df))
with col2:
    st.metric("覆盖企业数量", df['stkcd'].nunique())
with col3:
    st.metric("时间跨度", f"{df['year'].min()} - {df['year'].max()}年")
with col4:
    st.metric("指数均值", round(df['de_involution_index_calc'].mean(), 4))

# ====================== 侧边栏筛选条件 ======================
with st.sidebar:
    st.header("🔍 查询筛选")
    # 股票代码/名称查询
    search_key = st.text_input("输入股票代码/企业名称", placeholder="例如：000016 / 深康佳A")
    # 年份筛选
    year_list = sorted(df['year'].unique())
    selected_years = st.multiselect("选择年份", year_list, default=year_list)
    # 行业筛选（仅当有行业列时显示）
    selected_industries = []
    if has_industry:
        industry_list = sorted(df['indnm'].unique())
        selected_industries = st.multiselect("选择行业", industry_list)

# 筛选数据
filtered_df = df.copy()
if search_key:
    filtered_df = filtered_df[
        (filtered_df['stkcd'].str.contains(search_key, case=False)) | 
        (filtered_df['stknm'].str.contains(search_key, case=False))
    ]
if selected_years:
    filtered_df = filtered_df[filtered_df['year'].isin(selected_years)]
if has_industry and selected_industries:
    filtered_df = filtered_df[filtered_df['indnm'].isin(selected_industries)]

# ====================== 数据详情展示 ======================
st.subheader("📋 企业去内卷化指数详情")
st.dataframe(
    filtered_df[[
        'stkcd', 'stknm', 'year', 
        'de_involution_index_calc', 'de_involution_index'
    ]],
    width='stretch',  # 替换过期的use_container_width参数
    height=400
)

# ====================== 可视化分析 ======================
# 动态生成标签页（适配有无行业列的情况）
tabs = ["年度趋势", "企业历年走势"]
if has_industry:
    tabs.insert(1, "行业对比")
tab_list = st.tabs(tabs)

# 年度趋势标签页
with tab_list[0]:
    st.subheader("全市场去内卷化指数年度趋势")
    year_trend = filtered_df.groupby('year')['de_involution_index_calc'].agg(['mean', 'median']).reset_index()
    fig = px.line(
        year_trend, x='year', y=['mean', 'median'],
        markers=True,
        labels={'value': '去内卷化指数', 'year': '年份', 'variable': '统计指标'},
        title="全市场去内卷化指数年度均值/中位数走势"
    )
    st.plotly_chart(fig, width='stretch')

# 行业对比标签页（仅当有行业列时显示）
if has_industry:
    with tab_list[1]:
        st.subheader("行业去内卷化指数对比")
        industry_rank = filtered_df.groupby('indnm')['de_involution_index_calc'].mean().reset_index().sort_values('de_involution_index_calc', ascending=False)
        fig = px.bar(
            industry_rank, x='de_involution_index_calc', y='indnm',
            orientation='h',
            labels={'de_involution_index_calc': '去内卷化指数均值', 'indnm': '行业'},
            title="各行业去内卷化指数均值排名"
        )
        st.plotly_chart(fig, width='stretch')
    enterprise_tab_index = 2
else:
    enterprise_tab_index = 1

# 单企业历年走势标签页
with tab_list[enterprise_tab_index]:
    if search_key and not filtered_df.empty:
        selected_stk = filtered_df['stkcd'].iloc[0]
        st.subheader(f"{filtered_df['stknm'].iloc[0]} ({selected_stk}) 历年去内卷化指数走势")
        enterprise_trend = df[df['stkcd'] == selected_stk].sort_values('year')
        fig = px.line(
            enterprise_trend, x='year', y='de_involution_index_calc',
            markers=True,
            labels={'de_involution_index_calc': '去内卷化指数', 'year': '年份'},
            title=f"{filtered_df['stknm'].iloc[0]} 历年去内卷化指数"
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("请在左侧输入股票代码/企业名称，查看单企业历年走势")

# ====================== 数据下载 ======================
st.subheader("📥 数据下载")
csv_data = filtered_df.to_csv(index=False, encoding='utf-8-sig')
st.download_button(
    label="下载当前筛选结果",
    data=csv_data,
    file_name="去内卷化指数筛选结果.csv",
    mime="text/csv"
)