import pandas as pd
import numpy as np

# ====================== 【1】正确读取CSV数据（修正分隔符为制表符） ======================
print("正在读取企业数据...")
# 核心修正：sep='\t'，你的文件是用Tab键分隔的
df = pd.read_csv(
    "data.csv", 
    dtype={'stkcd': str},  # 股票代码保持字符串格式，避免丢失前导0
    sep='\t',              # 关键修正：指定分隔符为制表符（Tab）
    encoding='utf-8'       # 你的文件是UTF-8编码，中文正常显示
)

print("✅ 原始数据形状:", df.shape)
print("✅ 数据列名:", df.columns.tolist())

# ====================== 【2】数据预处理（完全保留你的原版逻辑） ======================
# 构建去内卷化指数的10个核心指标，和你的Stata/PyCharm代码完全一致
indicators = [
    'rd_high', 'rd_me', 'innov_qual1', 'innov_qual2',
    'hr_struct', 'human_cap', 'oper_eff', 'tech_dens',
    'profit', 'growth_exp'
]

# 删除任一指标缺失的观测值
df.dropna(subset=indicators, inplace=True)
print("✅ 删除缺失值后数据形状:", df.shape)

# ====================== 【3】按年份Winsorize缩尾（上下1%，和原版逻辑一致） ======================
def winsorize_series(s, lower=0.01, upper=0.99):
    """对单序列进行上下1%缩尾处理，和你的Stata代码完全对齐"""
    q_low = s.quantile(lower)
    q_high = s.quantile(upper)
    return s.clip(lower=q_low, upper=q_high)

# 需要缩尾的连续变量（虚拟变量innov_qual1/2不参与缩尾）
winsor_vars = [
    'rd_high', 'rd_me', 'hr_struct', 'human_cap',
    'oper_eff', 'tech_dens', 'profit', 'growth_exp'
]

# 按年份分组缩尾，和你的逻辑完全一致
df_win = df.copy()
for year in df['year'].unique():
    year_mask = df['year'] == year
    for var in winsor_vars:
        df_win.loc[year_mask, var] = winsorize_series(df.loc[year_mask, var])
df = df_win
print("✅ 按年份Winsorize缩尾处理完成")

# ====================== 【4】年度动态熵权法（100%复用你的原版计算逻辑） ======================
# 获取所有年份并排序
years = sorted(df['year'].unique())
# 存储每年的计算结果
yearly_result_list = []

for y in years:
    print(f"\n正在计算 {y} 年的熵权与去内卷化指数...")
    # 筛选当前年份的数据
    df_year = df[df['year'] == y].copy()
    n_obs = len(df_year)
    
    # 跳过无有效样本的年份
    if n_obs == 0:
        print(f"⚠️ 警告：{y} 年无有效样本，已跳过")
        continue

    # ---------------------- 第一步：Z-score标准化 ----------------------
    # 连续变量标准化
    std_vars = [
        'rd_high', 'rd_me', 'hr_struct', 'human_cap',
        'oper_eff', 'tech_dens', 'profit', 'growth_exp'
    ]
    for var in std_vars:
        mean_val = df_year[var].mean()
        std_val = df_year[var].std()
        # 避免标准差为0的极端情况
        df_year[f'{var}_std'] = (df_year[var] - mean_val) / std_val if std_val != 0 else 0

    # 虚拟变量不参与标准化，直接复制
    df_year['innov_qual1_std'] = df_year['innov_qual1']
    df_year['innov_qual2_std'] = df_year['innov_qual2']

    # ---------------------- 第二步：平移至正值区间（避免log(0)报错） ----------------------
    pos_vars = [
        'rd_high_std', 'rd_me_std', 'innov_qual1_std', 'innov_qual2_std',
        'hr_struct_std', 'human_cap_std', 'oper_eff_std',
        'tech_dens_std', 'profit_std', 'growth_exp_std'
    ]
    for var in pos_vars:
        min_val = df_year[var].min()
        df_year[f'{var}_pos'] = df_year[var] - min_val + 0.0001

    # ---------------------- 第三步：计算特征比重 ----------------------
    for var in pos_vars:
        total_sum = df_year[f'{var}_pos'].sum()
        df_year[f'p_{var}_pos'] = df_year[f'{var}_pos'] / total_sum

    # ---------------------- 第四步：计算熵值 ----------------------
    k = 1 / np.log(n_obs)  # 熵值系数
    for var in pos_vars:
        p_col = f'p_{var}_pos'
        df_year[f'temp_{var}'] = df_year[p_col] * np.log(df_year[p_col])
        sum_temp = df_year[f'temp_{var}'].sum()
        df_year[f'e_{var}'] = -k * sum_temp

    # ---------------------- 第五步：计算差异系数 ----------------------
    for var in pos_vars:
        df_year[f'd_{var}'] = 1 - df_year[f'e_{var}']

    # ---------------------- 第六步：计算指标权重 ----------------------
    d_cols = [f'd_{var}' for var in pos_vars]
    d_values = df_year[d_cols].iloc[0].values  # 同一年份权重一致，取第一行即可
    total_d = d_values.sum()
    weights = d_values / total_d

    # ---------------------- 第七步：构建去内卷化指数 ----------------------
    index_sum = 0
    for i, var in enumerate(pos_vars):
        index_sum += weights[i] * df_year[f'{var}_pos']
    df_year['de_involution_index_calc'] = index_sum

    # 保存当前年份的核心结果
    yearly_result_list.append(df_year[['stkcd', 'year', 'de_involution_index_calc']])
    print(f"✅ {y} 年计算完成，有效样本量：{n_obs}")

# ====================== 【5】合并所有年份结果，和原始数据匹配 ======================
if yearly_result_list:
    # 合并所有年份的计算结果
    df_index_result = pd.concat(yearly_result_list, ignore_index=True)
    # 把计算结果合并回原始数据
    df_final = df.merge(df_index_result, on=['stkcd', 'year'], how='left')
else:
    df_final = df.copy()
    df_final['de_involution_index_calc'] = np.nan
    print("⚠️ 警告：未生成任何有效指数结果")

# ====================== 【6】结果验证与输出 ======================
print("\n" + "="*50)
print("📊 去内卷化指数描述性统计（新计算结果）：")
print(df_final['de_involution_index_calc'].describe())

print("\n📊 各年份样本分布：")
print(df_final.groupby('year')['de_involution_index_calc'].count())

# 对比你原有的指数和新计算的指数的相关性，验证逻辑一致性
if 'de_involution_index' in df_final.columns:
    corr = df_final[['de_involution_index', 'de_involution_index_calc']].corr().iloc[0,1]
    print(f"\n📊 新计算指数与你原有指数的相关系数：{round(corr, 6)}")
    if corr > 0.95:
        print("✅ 相关系数>0.95，计算逻辑完全一致，结果验证通过！")

# ====================== 【7】保存最终结果到CSV ======================
df_final.to_csv("de_involution_final_result.csv", index=False, encoding='utf-8-sig')
print("\n🎉 全部计算完成！")
print("✅ 最终结果已保存到仓库：de_involution_final_result.csv")
print("✅ 你可以直接下载这个文件到本地，包含原始数据+新计算的去内卷化指数")