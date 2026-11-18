import os, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd, numpy as np

plt.rcParams['axes.unicode_minus'] = False
df = pd.read_pickle("data_processed/daily_market.pkl")
df = df[(df['date'] >= '2024-04-15') & (df['sector'].notna())].copy()
ln = df.sort_values('date').groupby('code')['name'].last()
sp = set(ln[ln.str.contains(r"스팩|제\d+호", na=False)].index)
df = df[(~df['code'].isin(sp)) & (df['code'].str[-1] == '0')].copy()
df['sec'] = df['code'].map(df.sort_values('date').groupby('code')['sector'].last())
df = df.sort_values(['code', 'date']).reset_index(drop=True)
df['raw_ret'] = df.groupby('code')['close'].pct_change()
df['ret'] = np.where(df['raw_ret'].abs() > 0.305, np.nan, df['raw_ret'])
df['prev_mcap'] = df.groupby('code')['market_cap'].shift(1)
df.to_pickle("data_processed/clean_q.pkl")

dates = sorted(df['date'].unique())
ds = df[df['date']==dates[0]][['code','sec','market_cap']].copy()
de = df[df['date']==dates[-1]][['code','sec','market_cap']].copy()
ds['rs'], de['re'] = ds['market_cap'].rank(ascending=False), de['market_cap'].rank(ascending=False)
m = pd.merge(ds, de, on=['code','sec']).dropna()
m['diff'] = (m['rs'] - m['re']).abs()
ret_c = len(set(ds[ds['rs']<=30]['code']) & set(de[de['re']<=30]['code']))
sq = m.groupby('sec').filter(lambda g: len(g)>=15).groupby('sec')['diff'].mean().sort_values(ascending=False).head(10).iloc[::-1]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=150)
ax1.bar(['Retained', 'New Entrants'], [ret_c, 30-ret_c], color=['#1f4e78','#ed7d31'], width=0.45)
ax1.set_ylim(0, 35); ax1.set_title("Q1-A. Top 30 Market Cap Turnover", fontweight='bold')
ax2.barh(range(len(sq)), sq.values, color='#2e75b6')
ax2.set_yticks(range(len(sq))); ax2.set_yticklabels([f"Sector #{10-i}" for i in range(len(sq))])
ax2.set_title("Q1-B. Mean |Rank_start - Rank_end|", fontweight='bold')
plt.tight_layout(); plt.savefig("outputs/q1_mcap_rank_shift.png"); plt.close()
print("Q1 저장 완료")
