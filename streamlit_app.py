import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ====================== 【页面全局配置 + 高级美化CSS】 ======================
st.set_page_config(
    page_title="上市企业去内卷化指数分析系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS：提升页面高级感、卡片样式、字体优化
st.markdown("""
<style>
/* 全局字体与背景 */
html, body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}
/* 主标题样式 */
h1 {
    color: #2563eb;
    font-weight: 700;
    margin-bottom: 0.5rem;
}
/* 副标题样式 */
h2, h3 {
    color: #1e293b;
    font-weight: 600;
}
/* 卡片容器样式 */
.card {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 1.2rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    margin-bottom: 1rem;
}
/* 指标卡片高亮 */
.metric-card {
    text-align: center;
    border-left: 4px solid #2563eb;
}
/* 侧边栏样式优化 */
.css-1d391kg {
    padding-top: 1rem;
}
/* 表格样式优化 */
.stDataFrame {
    border-radius: 8px;
    overflow: hidden;
}
/* 隐藏Streamlit默认的汉堡菜单和页脚 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ====================== 【数据加载与预处理】 ======================
@st.cache_data
def load_full_data():
    """加载并预处理全量数据"""
    df = pd.read_csv("de_involution_final_result.csv", dtype={'stkcd': str, 'year': int})
    # 数据清洗：去除空值、标准化字段名
    df = df.dropna(subset=['stkcd', 'year', 'de_involution_index_calc'])
    # 重命名列，方便展示
    df = df.rename(columns={
        'stkcd': '股票代码',
        'stknm': '企业名称',
        'year': '年份',
        'province': '省份',
        'region_name': '区域',
        'city': '城市',
        'indnm': '行业大类',
        'sub_ind': '行业细分',
        'rd_high': '研发高强度',
        'rd_me': '研发中等强度',
        'innov_qual1': '创新质量1',
        'innov_qual2': '创新质量2',
        'hr_struct': '人力资源结构',
        'human_cap': '人力资本',
        'oper_eff': '经营效率',
        'tech_dens': '技术密度',
        'profit': '盈利能力',
        'growth_exp': '成长预期',
        'de_involution_index': '原去内卷化指数',
        'de_involution_index_calc': '熵权法计算指数'
    })
    return df

# 加载全量数据
df_full = load_full_data()
# 核心指标列表（用于雷达图、统计）
core_indicators = [
    '研发高强度', '研发中等强度', '创新质量1', '创新质量2',
    '人力资源结构', '人力资本', '经营效率', '技术密度',
    '盈利能力', '成长预期'
]
index_columns = ['原去内卷化指数', '熵权法计算指数']

# ====================== 【侧边栏：多维度级联筛选】 ======================
with st.sidebar:
    st.markdown("## 🔍 筛选条件")
    st.divider()

    # 1. 年份筛选
    year_list = sorted(df_full['年份'].unique())
    selected_years = st.multiselect(
        "📅 选择年份",
        options=year_list,
        default=year_list
    )

    # 2. 区域级联筛选
    region_list = sorted(df_full['区域'].unique())
    selected_region = st.multiselect(
        "🌎 选择区域",
        options=region_list,
        default=[]
    )
    # 级联：选中区域后，只显示对应省份
    province_df = df_full[df_full['区域'].isin(selected_region)] if selected_region else df_full
    province_list = sorted(province_df['省份'].unique())
    selected_province = st.multiselect(
        "🏙️ 选择省份",
        options=province_list,
        default=[]
    )

    # 3. 行业级联筛选
    industry_list = sorted(df_full['行业大类'].unique())
    selected_industry = st.multiselect(
        "🏭 选择行业大类",
        options=industry_list,
        default=[]
    )
    # 级联：选中行业后，只显示对应细分行业
    sub_ind_df = df_full[df_full['行业大类'].isin(selected_industry)] if selected_industry else df_full
    sub_ind_list = sorted(sub_ind_df['行业细分'].unique())
    selected_sub_ind = st.multiselect(
        "🔬 选择细分行业",
        options=sub_ind_list,
        default=[]
    )

    # 4. 企业精准搜索
    st.divider()
    search_key = st.text_input(
        "🔎 企业名称/股票代码搜索",
        placeholder="例如：深康佳A / 000016"
    )

    # 筛选逻辑执行
    df_filtered = df_full.copy()
    if selected_years:
        df_filtered = df_filtered[df_filtered['年份'].isin(selected_years)]
    if selected_region:
        df_filtered = df_filtered[df_filtered['区域'].isin(selected_region)]
    if selected_province:
        df_filtered = df_filtered[df_filtered['省份'].isin(selected_province)]
    if selected_industry:
        df_filtered = df_filtered[df_filtered['行业大类'].isin(selected_industry)]
    if selected_sub_ind:
        df_filtered = df_filtered[df_filtered['行业细分'].isin(selected_sub_ind)]
    if search_key:
        df_filtered = df_filtered[
            (df_filtered['股票代码'].str.contains(search_key, case=False)) |
            (df_filtered['企业名称'].str.contains(search_key, case=False))
        ]

    # 筛选结果统计
    st.divider()
    st.markdown("### 📊 当前筛选结果")
    st.metric("有效样本量", len(df_filtered))
    st.metric("覆盖企业数", df_filtered['股票代码'].nunique())
    st.metric("覆盖行业数", df_filtered['行业大类'].nunique())

# ====================== 【页面顶部：全局概览卡片】 ======================
st.markdown("# 📊 上市企业去内卷化指数分析系统")
st.markdown("基于年度动态熵权法构建的A股上市公司去内卷化指数全景分析平台 | 样本区间：{} - {}年".format(df_full['年份'].min(), df_full['年份'].max()))
st.divider()

# 核心指标卡片行
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.markdown('<div class="card metric-card">', unsafe_allow_html=True)
    st.metric("总样本量", len(df_full))
    st.markdown('</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="card metric-card">', unsafe_allow_html=True)
    st.metric("覆盖企业", df_full['股票代码'].nunique())
    st.markdown('</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="card metric-card">', unsafe_allow_html=True)
    st.metric("覆盖行业", df_full['行业大类'].nunique())
    st.markdown('</div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="card metric-card">', unsafe_allow_html=True)
    st.metric("指数均值", round(df_full['熵权法计算指数'].mean(), 4))
    st.markdown('</div>', unsafe_allow_html=True)
with col5:
    st.markdown('<div class="card metric-card">', unsafe_allow_html=True)
    st.metric("指数最大值", round(df_full['熵权法计算指数'].max(), 4))
    st.markdown('</div>', unsafe_allow_html=True)
with col6:
    st.markdown('<div class="card metric-card">', unsafe_allow_html=True)
    st.metric("指数最小值", round(df_full['熵权法计算指数'].min(), 4))
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# ====================== 【主页面：6大功能标签页】 ======================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 全局趋势分析",
    "🏢 企业深度详情",
    "🏆 指数排名榜单",
    "🌍 多维度对比",
    "📋 原始数据查询",
    "🔍 指数一致性验证"
])

# ---------------------- Tab1：全局趋势分析 ----------------------
with tab1:
    st.markdown("### 全市场去内卷化指数年度趋势")
    # 年度统计：均值、中位数、25分位、75分位
    year_stats = df_filtered.groupby('年份')['熵权法计算指数'].agg([
        'mean', 'median', 'quantile', 'min', 'max'
    ]).reset_index()
    year_stats.columns = ['年份', '均值', '中位数', '25分位', '最小值', '最大值']

    # 趋势线图
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=year_stats['年份'], y=year_stats['均值'], name='全市场均值', line=dict(color='#2563eb', width=3), mode='lines+markers'))
    fig_trend.add_trace(go.Scatter(x=year_stats['年份'], y=year_stats['中位数'], name='全市场中位数', line=dict(color='#16a34a', width=2), mode='lines+markers'))
    fig_trend.add_trace(go.Scatter(x=year_stats['年份'], y=year_stats['25分位'], name='25分位', line=dict(color='#94a3b8', width=1, dash='dash')))
    fig_trend.update_layout(
        title="全市场去内卷化指数年度走势",
        xaxis_title="年份",
        yaxis_title="去内卷化指数",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500
    )
    st.plotly_chart(fig_trend, width='stretch')

    # 分栏：指数分布 + 区域年度趋势
    col_dist, col_region = st.columns(2)
    with col_dist:
        st.markdown("### 指数整体分布")
        fig_dist = px.histogram(
            df_filtered, x='熵权法计算指数',
            nbins=50, color_discrete_sequence=['#2563eb'],
            marginal="box", title="去内卷化指数分布直方图"
        )
        fig_dist.update_layout(height=400)
        st.plotly_chart(fig_dist, width='stretch')

    with col_region:
        st.markdown("### 四大区域年度趋势对比")
        region_year = df_filtered.groupby(['年份', '区域'])['熵权法计算指数'].mean().reset_index()
        fig_region = px.line(
            region_year, x='年份', y='熵权法计算指数', color='区域',
            markers=True, title="各区域去内卷化指数年度均值走势"
        )
        fig_region.update_layout(height=400, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_region, width='stretch')

# ---------------------- Tab2：企业深度详情 ----------------------
with tab2:
    st.markdown("### 🏢 企业详情与行业对标分析")
    # 企业选择器
    if search_key and not df_filtered.empty:
        # 搜索到的企业列表
        enterprise_list = sorted(df_filtered['企业名称'].unique())
        selected_enterprise = st.selectbox("选择要查看的企业", options=enterprise_list, index=0)
    else:
        # 无搜索时，全量企业列表
        enterprise_list = sorted(df_full['企业名称'].unique())
        selected_enterprise = st.selectbox("选择要查看的企业", options=enterprise_list, index=0)

    # 提取该企业全量数据
    df_enterprise = df_full[df_full['企业名称'] == selected_enterprise].sort_values('年份')
    stkcd = df_enterprise['股票代码'].iloc[0]
    industry = df_enterprise['行业大类'].iloc[0]
    province = df_enterprise['省份'].iloc[0]
    region = df_enterprise['区域'].iloc[0]

    # 企业基础信息卡片
    st.markdown(f"""
    <div class="card">
        <h3>{selected_enterprise} ({stkcd})</h3>
        <p><b>所属区域：</b>{region} | <b>所属省份：</b>{province} | <b>所属行业：</b>{industry}</p>
        <p><b>样本区间：</b>{df_enterprise['年份'].min()}年 - {df_enterprise['年份'].max()}年</p>
    </div>
    """, unsafe_allow_html=True)

    # 分栏：历年指数走势 + 最新年份指标雷达图
    col_trend, col_radar = st.columns(2)
    with col_trend:
        st.markdown("#### 历年去内卷化指数走势")
        # 提取行业年度均值，做对标
        industry_year_mean = df_full[df_full['行业大类'] == industry].groupby('年份')['熵权法计算指数'].mean().reset_index()
        industry_year_mean.columns = ['年份', '行业均值']
        # 合并企业数据和行业均值
        df_enterprise_compare = df_enterprise.merge(industry_year_mean, on='年份', how='left')

        fig_ent_trend = go.Figure()
        fig_ent_trend.add_trace(go.Scatter(
            x=df_enterprise_compare['年份'], y=df_enterprise_compare['熵权法计算指数'],
            name=f"{selected_enterprise}", line=dict(color='#2563eb', width=3), mode='lines+markers'
        ))
        fig_ent_trend.add_trace(go.Scatter(
            x=df_enterprise_compare['年份'], y=df_enterprise_compare['行业均值'],
            name=f"{industry}行业均值", line=dict(color='#94a3b8', width=2, dash='dash'), mode='lines+markers'
        ))
        fig_ent_trend.update_layout(
            xaxis_title="年份",
            yaxis_title="去内卷化指数",
            hovermode="x unified",
            height=450,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_ent_trend, width='stretch')

    with col_radar:
        st.markdown("#### 最新年份核心指标雷达图（行业对标）")
        # 取最新年份数据
        latest_year = df_enterprise['年份'].max()
        df_latest = df_enterprise[df_enterprise['年份'] == latest_year].iloc[0]
        # 行业同年度均值
        industry_latest_mean = df_full[
            (df_full['行业大类'] == industry) & (df_full['年份'] == latest_year)
        ][core_indicators].mean()

        # 雷达图数据标准化（0-1区间，方便对比）
        def normalize_series(s):
            return (s - s.min()) / (s.max() - s.min()) if s.max() != s.min() else 0.5

        # 全量数据的指标极值，用于标准化
        indicator_min = df_full[core_indicators].min()
        indicator_max = df_full[core_indicators].max()

        # 企业指标标准化
        ent_normalized = []
        industry_normalized = []
        for ind in core_indicators:
            ent_val = (df_latest[ind] - indicator_min[ind]) / (indicator_max[ind] - indicator_min[ind]) if indicator_max[ind] != indicator_min[ind] else 0.5
            ind_val = (industry_latest_mean[ind] - indicator_min[ind]) / (indicator_max[ind] - indicator_min[ind]) if indicator_max[ind] != indicator_min[ind] else 0.5
            ent_normalized.append(ent_val)
            industry_normalized.append(ind_val)

        # 绘制雷达图
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=ent_normalized,
            theta=core_indicators,
            fill='toself',
            name=f"{selected_enterprise}（{latest_year}年）",
            line=dict(color='#2563eb')
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=industry_normalized,
            theta=core_indicators,
            fill='toself',
            name=f"{industry}行业均值",
            line=dict(color='#94a3b8', dash='dash')
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            height=450,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_radar, width='stretch')

    # 企业历年完整指标表格
    st.markdown("#### 企业历年完整指标数据")
    st.dataframe(
        df_enterprise[['年份', '熵权法计算指数', '原去内卷化指数'] + core_indicators],
        width='stretch',
        height=300
    )

# ---------------------- Tab3：指数排名榜单 ----------------------
with tab3:
    st.markdown("### 🏆 去内卷化指数排名榜单")
    # 榜单筛选条件
    col_rank_year, col_rank_type, col_rank_range = st.columns(3)
    with col_rank_year:
        rank_year = st.selectbox("选择年份", options=sorted(df_full['年份'].unique()), index=len(df_full['年份'].unique())-1)
    with col_rank_type:
        rank_type = st.radio("榜单类型", options=["全市场排名", "分行业排名", "分区域排名"], horizontal=True)
    with col_rank_range:
        rank_top_n = st.slider("榜单展示数量", min_value=5, max_value=50, value=10, step=5)

    # 筛选对应年份的数据
    df_rank = df_full[df_full['年份'] == rank_year].copy()

    # 分类型处理榜单
    if rank_type == "分行业排名":
        industry_rank = st.selectbox("选择行业", options=sorted(df_rank['行业大类'].unique()))
        df_rank = df_rank[df_rank['行业大类'] == industry_rank]
        st.markdown(f"#### {rank_year}年 {industry_rank} 行业去内卷化指数TOP{rank_top_n} / BOTTOM{rank_top_n}")
    elif rank_type == "分区域排名":
        region_rank = st.selectbox("选择区域", options=sorted(df_rank['区域'].unique()))
        df_rank = df_rank[df_rank['区域'] == region_rank]
        st.markdown(f"#### {rank_year}年 {region_rank} 去内卷化指数TOP{rank_top_n} / BOTTOM{rank_top_n}")
    else:
        st.markdown(f"#### {rank_year}年 全市场去内卷化指数TOP{rank_top_n} / BOTTOM{rank_top_n}")

    # 分栏展示TOP和BOTTOM榜单
    col_top, col_bottom = st.columns(2)
    with col_top:
        st.markdown(f"##### ✨ TOP{rank_top_n} 榜单")
        df_top = df_rank.sort_values('熵权法计算指数', ascending=False).head(rank_top_n)[
            ['股票代码', '企业名称', '行业大类', '省份', '熵权法计算指数']
        ].reset_index(drop=True)
        df_top.index = df_top.index + 1
        st.dataframe(df_top, width='stretch', height=rank_top_n*36 + 50)

    with col_bottom:
        st.markdown(f"##### ⚠️ BOTTOM{rank_top_n} 榜单")
        df_bottom = df_rank.sort_values('熵权法计算指数', ascending=True).head(rank_top_n)[
            ['股票代码', '企业名称', '行业大类', '省份', '熵权法计算指数']
        ].reset_index(drop=True)
        df_bottom.index = df_bottom.index + 1
        st.dataframe(df_bottom, width='stretch', height=rank_top_n*36 + 50)

    # 行业均值排名
    st.markdown("#### 🏭 行业去内卷化指数均值排名")
    industry_rank_all = df_rank.groupby('行业大类')['熵权法计算指数'].agg(['mean', 'count']).reset_index()
    industry_rank_all.columns = ['行业大类', '指数均值', '样本企业数']
    industry_rank_all = industry_rank_all.sort_values('指数均值', ascending=False).reset_index(drop=True)
    industry_rank_all.index = industry_rank_all.index + 1

    # 行业排名柱状图
    fig_industry_rank = px.bar(
        industry_rank_all, x='指数均值', y='行业大类',
        orientation='h', color='指数均值',
        color_continuous_scale='Blues',
        title=f"{rank_year}年各行业去内卷化指数均值排名"
    )
    fig_industry_rank.update_layout(height=800, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_industry_rank, width='stretch')

# ---------------------- Tab4：多维度对比分析 ----------------------
with tab4:
    st.markdown("### 🌍 多维度指数对比分析")
    compare_type = st.radio("选择对比维度", options=["行业对比", "区域对比", "省份对比"], horizontal=True)

    if compare_type == "行业对比":
        # 行业多选
        compare_industries = st.multiselect(
            "选择要对比的行业",
            options=sorted(df_full['行业大类'].unique()),
            default=sorted(df_full['行业大类'].unique())[:5]
        )
        df_compare = df_full[df_full['行业大类'].isin(compare_industries)]
        group_col = '行业大类'
        title = "行业去内卷化指数年度对比"
    elif compare_type == "区域对比":
        compare_regions = st.multiselect(
            "选择要对比的区域",
            options=sorted(df_full['区域'].unique()),
            default=sorted(df_full['区域'].unique())
        )
        df_compare = df_full[df_full['区域'].isin(compare_regions)]
        group_col = '区域'
        title = "区域去内卷化指数年度对比"
    else:
        # 省份多选
        compare_provinces = st.multiselect(
            "选择要对比的省份",
            options=sorted(df_full['省份'].unique()),
            default=sorted(df_full['省份'].unique())[:5]
        )
        df_compare = df_full[df_full['省份'].isin(compare_provinces)]
        group_col = '省份'
        title = "省份去内卷化指数年度对比"

    if not df_compare.empty:
        # 年度分组统计
        compare_data = df_compare.groupby(['年份', group_col])['熵权法计算指数'].mean().reset_index()
        # 对比折线图
        fig_compare = px.line(
            compare_data, x='年份', y='熵权法计算指数', color=group_col,
            markers=True, title=title
        )
        fig_compare.update_layout(
            height=600,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_compare, width='stretch')

        # 箱线图：分布对比
        st.markdown("#### 指数分布箱线图对比")
        fig_box = px.box(
            df_compare, x=group_col, y='熵权法计算指数',
            color=group_col, title=f"{compare_type}指数分布对比"
        )
        fig_box.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig_box, width='stretch')
    else:
        st.warning("请至少选择一个对比项")

# ---------------------- Tab5：原始数据查询 ----------------------
with tab5:
    st.markdown("### 📋 原始数据查询与下载")
    st.markdown("当前展示的是左侧筛选条件过滤后的结果，可直接下载CSV文件")

    # 展示完整数据
    st.dataframe(
        df_filtered,
        width='stretch',
        height=600
    )

    # 下载按钮
    csv_data = df_filtered.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 下载当前筛选结果CSV",
        data=csv_data,
        file_name="去内卷化指数筛选结果.csv",
        mime="text/csv"
    )

    # 全量数据下载
    full_csv_data = df_full.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 下载全量数据集CSV",
        data=full_csv_data,
        file_name="上市企业去内卷化指数全量数据集.csv",
        mime="text/csv"
    )

# ---------------------- Tab6：指数一致性验证 ----------------------
with tab6:
    st.markdown("### 🔍 原指数与熵权法计算指数一致性验证")
    # 相关性计算
    corr = df_full[['原去内卷化指数', '熵权法计算指数']].corr().iloc[0,1]
    # 描述性统计对比
    desc_compare = df_full[['原去内卷化指数', '熵权法计算指数']].describe().T

    # 核心指标卡片
    col_corr, col_mean_diff, col_max_diff = st.columns(3)
    with col_corr:
        st.markdown('<div class="card metric-card">', unsafe_allow_html=True)
        st.metric("相关系数", round(corr, 6))
        st.markdown('</div>', unsafe_allow_html=True)
    with col_mean_diff:
        # 修复FutureWarning，改成iloc规范写法
        mean_diff = abs(desc_compare['mean'].iloc[0] - desc_compare['mean'].iloc[1])
        st.markdown('<div class="card metric-card">', unsafe_allow_html=True)
        st.metric("均值绝对差", round(mean_diff, 6))
        st.markdown('</div>', unsafe_allow_html=True)
    with col_max_diff:
        max_diff = (df_full['原去内卷化指数'] - df_full['熵权法计算指数']).abs().max()
        st.markdown('<div class="card metric-card">', unsafe_allow_html=True)
        st.metric("最大绝对差", round(max_diff, 6))
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # 分栏：散点图 + 描述性统计
    col_scatter, col_desc = st.columns(2)
    with col_scatter:
        st.markdown("#### 指数散点图拟合")
        fig_scatter = px.scatter(
            df_full, x='原去内卷化指数', y='熵权法计算指数',
            trendline='ols', opacity=0.5,
            title="原指数 vs 熵权法计算指数散点图",
            color_discrete_sequence=['#2563eb']
        )
        fig_scatter.update_layout(height=500)
        st.plotly_chart(fig_scatter, width='stretch')

    with col_desc:
        st.markdown("#### 描述性统计对比")
        st.dataframe(desc_compare, width='stretch', height=500)

    # 年度相关性走势
    st.markdown("#### 年度相关性走势")
    year_corr = df_full.groupby('年份').apply(
        lambda x: x[['原去内卷化指数', '熵权法计算指数']].corr().iloc[0,1]
    ).reset_index()
    year_corr.columns = ['年份', '相关系数']

    fig_year_corr = px.line(
        year_corr, x='年份', y='相关系数',
        markers=True, title="各年度指数相关系数走势",
        color_discrete_sequence=['#2563eb']
    )
    fig_year_corr.update_layout(yaxis_range=[0.9, 1], height=400)
    st.plotly_chart(fig_year_corr, width='stretch')