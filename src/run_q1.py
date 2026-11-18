import os, json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams['axes.unicode_minus'] = False
os.makedirs("outputs", exist_ok=True)
df = pd.read_pickle("data_processed/clean_q.pkl").sort_values(['code', 'date'])
dates = sorted(df['date'].unique())

ds = df[df['date']==dates[0]][['code','sec','market_cap']].copy()
de = df[df['date']==dates[-1]][['code','sec','market_cap']].copy()
ds['rs'], de['re'] = ds['market_cap'].rank(ascending=False), de['market_cap'].rank(ascending=False)
m = pd.merge(ds, de, on=['code','sec'], suffixes=('_s','_e')).dropna()
m['diff'] = (m['rs'] - m['re']).abs()
m['pct_diff'] = ((m['rs'] - m['re']) / m['rs']).abs()

ret_c = len(set(ds[ds['rs']<=30]['code']) & set(de[de['re']<=30]['code']))
sq_abs = m.groupby('sec').filter(lambda g: len(g)>=15).groupby('sec')['diff'].mean().sort_values(ascending=False)
sq_pct = m.groupby('sec').filter(lambda g: len(g)>=15).groupby('sec')['pct_diff'].mean().sort_values(ascending=False)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8), dpi=150)
b1 = ax1.bar(['Retained (21)', 'New Entrants (9)'], [ret_c, 30-ret_c], color=['#1f4e78','#ed7d31'], width=0.45)
for b in b1: ax1.text(b.get_x()+b.get_width()/2, b.get_height()+0.5, f"{int(b.get_height())} stocks", ha='center', fontweight='bold')
ax1.set_ylim(0, 35); ax1.set_title("Q1-A. Top 30 Turnover", fontweight='bold'); ax1.set_ylabel("Stocks"); ax1.grid(axis='y', alpha=0.3)

top8 = sq_abs.head(8).iloc[::-1]
ax2.barh(range(len(top8)), top8.values, color='#2e75b6', height=0.6)
ax2.set_yticks(range(len(top8))); ax2.set_yticklabels([f"Rank-{8-i} Sector" for i in range(len(top8))])
ax2.set_xlabel("Mean Absolute Rank Change"); ax2.set_title("Q1-B. Top 8 Sectors by Rank Shift", fontweight='bold'); ax2.grid(axis='x', alpha=0.3)
plt.tight_layout(); plt.savefig("outputs/q1_def.png"); plt.close()

meta = {"q1_ret": int(ret_c), "q1_new": int(30-ret_c), "q1_top_abs": sq_abs.index[0], "q1_top_abs_v": round(float(sq_abs.iloc[0]), 1), "q1_top_pct": sq_pct.index[0], "q1_top_pct_v": round(float(sq_pct.iloc[0])*100, 1)}
json.dump(meta, open("outputs/meta.json", "w", encoding="utf-8"), ensure_ascii=False)
print("1/5 완료: Q1 차트 생성 성공")
