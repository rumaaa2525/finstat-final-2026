import os, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd, numpy as np

plt.rcParams['axes.unicode_minus'] = False
os.makedirs("outputs", exist_ok=True)
df = pd.read_pickle("data_processed/clean_q.pkl").sort_values(['code', 'date'])
df['rc'] = df['ret'].fillna(0.0)
dates = sorted(df['date'].unique())

# ================= [Q1 계산] =================
ds = df[df['date']==dates[0]][['code','name','sec','market_cap']].copy()
de = df[df['date']==dates[-1]][['code','name','sec','market_cap']].copy()
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
ax1.set_ylim(0, 35); ax1.set_title("Q1-A. Top 30 Market Cap Turnover (2.5 Yrs)", fontweight='bold')
ax1.set_ylabel("Number of Stocks"); ax1.grid(axis='y', alpha=0.3)

top8 = sq_abs.head(8).iloc[::-1]
ax2.barh(range(len(top8)), top8.values, color='#2e75b6', height=0.6)
ax2.set_yticks(range(len(top8))); ax2.set_yticklabels([f"Rank-{8-i} Sector" for i in range(len(top8))])
ax2.set_xlabel("Mean Absolute Rank Change (|Rank_end - Rank_start|)"); ax2.set_title("Q1-B. Top 8 Sectors by Absolute Rank Shift", fontweight='bold'); ax2.grid(axis='x', alpha=0.3)
plt.tight_layout(); plt.savefig("outputs/q1_def.png"); plt.close()

# ================= [Q2 계산: (a) 시총가중 vs (b) 동일가중] =================
df['w_prev'] = df.groupby('code')['market_cap'].shift(1)
valid_sec = df.groupby('sec')['code'].nunique()
valid_sec = valid_sec[valid_sec >= 10].index
sub2 = df[df['sec'].isin(valid_sec) & (df['rc'].abs() <= 0.305)].dropna(subset=['rc', 'w_prev']).copy()

# (a) 시총가중 업종 일별 수익률
sub2['wr'] = sub2['rc'] * sub2['w_prev']
g_sum = sub2.groupby(['date', 'sec'])[['wr', 'w_prev']].sum()
sec_cap = (g_sum['wr'] / g_sum['w_prev']).unstack('sec').iloc[9:]
cum_cap = ((1 + sec_cap).cumprod() - 1) * 100

# (b) 동일가중 업종 일별 수익률
sec_eq = sub2.groupby(['date', 'sec'])['rc'].mean().unstack('sec').iloc[9:]
cum_eq = ((1 + sec_eq).cumprod() - 1) * 100

# 분산: (a) 누적 수익률 횡단면 표준편차 vs (b) 월별 수익률 횡단면 표준편차
disp_cum_cap = cum_cap.std(axis=1)
disp_cum_eq = cum_eq.std(axis=1)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8), dpi=150)
end_cap = cum_cap.iloc[-1].sort_values()
comb = pd.concat([end_cap.head(5), end_cap.tail(5)])
ax1.barh(range(len(comb)), comb.values, color=['#c00000' if v < 0 else '#1f4e78' for v in comb.values], height=0.6)
ax1.set_yticks(range(len(comb))); ax1.set_yticklabels([f"Bot-{5-i}" if i<5 else f"Top-{10-i}" for i in range(len(comb))])
ax1.axvline(0, color='black', lw=0.8); ax1.set_xlabel("Cumulative Return (%) [Cap-Weighted]")
ax1.set_title("Q2-A. Top 5 vs Bottom 5 Sector Cumulative Return", fontweight='bold'); ax1.grid(axis='x', alpha=0.3)

ax2.plot(pd.to_datetime(disp_cum_cap.index), disp_cum_cap.values, color='#1f4e78', lw=2, label='(a) Cap-Weighted Std Dev (%p)')
ax2.plot(pd.to_datetime(disp_cum_eq.index), disp_cum_eq.values, color='#ed7d31', lw=1.8, ls='--', label='(b) Equal-Weighted Std Dev (%p)')
ax2.set_ylabel("Cross-Sector Cumulative Return Std Dev (%p)")
ax2.set_title("Q2-B. Sector Return Dispersion Over Time", fontweight='bold'); ax2.legend(); ax2.grid(alpha=0.3)
plt.tight_layout(); plt.savefig("outputs/q2_def.png"); plt.close()

meta = {
    "q1_ret": int(ret_c), "q1_new": int(30 - ret_c),
    "q1_top_abs": sq_abs.index[0], "q1_top_abs_v": round(float(sq_abs.iloc[0]), 1),
    "q1_top_pct": sq_pct.index[0], "q1_top_pct_v": round(float(sq_pct.iloc[0])*100, 1),
    "q2_cap_std_s": round(float(disp_cum_cap.iloc[0]), 1), "q2_cap_std_e": round(float(disp_cum_cap.iloc[-1]), 1),
    "q2_eq_std_e": round(float(disp_cum_eq.iloc[-1]), 1)
}
json.dump(meta, open("outputs/q12_meta.json", "w", encoding="utf-8"), ensure_ascii=False)
print("1단계(Q1, Q2) 완료:", meta)
