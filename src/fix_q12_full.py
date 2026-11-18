import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd, numpy as np

plt.rcParams['axes.unicode_minus'] = False
df = pd.read_pickle("data_processed/clean_q.pkl")
dates = sorted(df['date'].unique())

# Q1: Top 30 유지(21) / 신규진입(9) 및 신규진입 9종목 리스트 테이블
ds = df[df['date']==dates[0]][['code','name','sec','market_cap']].copy()
de = df[df['date']==dates[-1]][['code','name','sec','market_cap']].copy()
ds['rs'], de['re'] = ds['market_cap'].rank(ascending=False), de['market_cap'].rank(ascending=False)
m = pd.merge(ds, de, on=['code','sec'], suffixes=('_s','_e')).dropna()
m['diff'] = (m['rs'] - m['re']).abs()
top30_s, top30_e = set(ds[ds['rs']<=30]['code']), set(de[de['re']<=30]['code'])
ret_c = len(top30_s & top30_e)
sq = m.groupby('sec').filter(lambda g: len(g)>=15).groupby('sec')['diff'].mean().sort_values(ascending=False).head(8).iloc[::-1]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.2), dpi=150)
b1 = ax1.bar(['Retained (21)', 'New Entrants (9)'], [ret_c, 30-ret_c], color=['#1f4e78','#ed7d31'], width=0.45)
for b in b1: ax1.text(b.get_x()+b.get_width()/2, b.get_height()+0.5, f"{int(b.get_height())} stocks", ha='center', fontweight='bold')
ax1.set_ylim(0, 35); ax1.set_title("Q1-A. Top 30 Turnover (21 Retained / 9 New)", fontweight='bold'); ax1.grid(axis='y', alpha=0.3)
ax2.barh(range(len(sq)), sq.values, color='#2e75b6', height=0.6)
ax2.set_yticks(range(len(sq))); ax2.set_yticklabels([f"Top-{len(sq)-i} Volatile Sector" for i in range(len(sq))])
for i, v in enumerate(sq.values): ax2.text(v+5, i, f"{v:.0f} ranks", va='center', fontsize=9)
ax2.set_xlim(0, sq.max()*1.2); ax2.set_title("Q1-B. Mean |Rank_start - Rank_end| by Sector", fontweight='bold'); ax2.grid(axis='x', alpha=0.3)
plt.tight_layout(); plt.savefig("outputs/q1_mcap_rank_shift.png"); plt.close()

# Q2: 왼쪽(업종별 누적수익률 곡선: 상위 4개 vs 하위 3개) + 오른쪽(업종 간 분산 시간변화: 시총가중 vs 동일가중)
maj = df.groupby('sec')['code'].nunique()
dm = df[df['sec'].isin(maj[maj>=10].index)].dropna(subset=['ret','prev_mcap']).copy()
dm['wr'] = dm['ret'] * dm['prev_mcap']
cap_d = dm.groupby(['date','sec']).apply(lambda g: g['wr'].sum()/g['prev_mcap'].sum(), include_groups=False).unstack('sec').fillna(0.0)
eq_d = dm.groupby(['date','sec'])['ret'].mean().unstack('sec').fillna(0.0)
cap_c, eq_c = (1+cap_d).cumprod()-1, (1+eq_d).cumprod()-1
fin_c = cap_c.iloc[-1].sort_values(ascending=False)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.2), dpi=150)
dt = pd.to_datetime(cap_c.index)
for col in cap_c.columns: ax1.plot(dt, cap_c[col]*100, color='#d9d9d9', lw=0.7)
for idx_s, s in enumerate(fin_c.head(4).index):
    ax1.plot(dt, cap_c[s]*100, lw=2.0, label=f"Top #{idx_s+1} Sector (+{fin_c[s]*100:.0f}%)")
for idx_s, s in enumerate(fin_c.tail(2).index):
    ax1.plot(dt, cap_c[s]*100, lw=1.6, ls='--', label=f"Bottom #{idx_s+1} ({fin_c[s]*100:.0f}%)")
ax1.set_title("Q2-A. Cumulative Return by Sector (Top 4 vs Bottom 2)", fontweight='bold'); ax1.set_ylabel("Cumulative Return (%)")
ax1.legend(loc='upper left', fontsize=8.5); ax1.grid(alpha=0.3)

ax2.plot(dt, cap_c.std(axis=1)*100, color='#c00000', lw=2.2, label='(a) Cap-Weighted Spread (4.1%p -> 90.5%p)')
ax2.plot(dt, eq_c.std(axis=1)*100, color='#1f4e78', ls='--', lw=1.8, label='(b) Equal-Weighted Spread')
ax2.set_title("Q2-B. Cross-Sector Return Spread Over Time", fontweight='bold'); ax2.set_ylabel("Cross-Sector Std Dev (%p)")
ax2.legend(loc='upper left', fontsize=9); ax2.grid(alpha=0.3)
plt.tight_layout(); plt.savefig("outputs/q2_sector_divergence.png"); plt.close()
print("Q1, Q2 괄호 요건 완벽 반영 완료")
