import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd, numpy as np

plt.rcParams['axes.unicode_minus'] = False
os.makedirs("outputs", exist_ok=True)
df = pd.read_pickle("data_processed/clean_q.pkl")
df['rc'] = df['ret'].fillna(0.0)
dates = sorted(df['date'].unique())

# [Q1] 시가총액 Top 30 변화
ds = df[df['date']==dates[0]][['code','name','sec','market_cap']].copy()
de = df[df['date']==dates[-1]][['code','name','sec','market_cap']].copy()
ds['rs'], de['re'] = ds['market_cap'].rank(ascending=False), de['market_cap'].rank(ascending=False)
m = pd.merge(ds, de, on=['code','sec'], suffixes=('_s','_e')).dropna()
m['diff'] = (m['rs'] - m['re']).abs()
ret_c = len(set(ds[ds['rs']<=30]['code']) & set(de[de['re']<=30]['code']))
sq = m.groupby('sec').filter(lambda g: len(g)>=15).groupby('sec')['diff'].mean().sort_values(ascending=False).head(8).iloc[::-1]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8), dpi=150)
b1 = ax1.bar(['Retained (21)', 'New Entrants (9)'], [ret_c, 30-ret_c], color=['#1f4e78','#ed7d31'], width=0.45)
for b in b1: ax1.text(b.get_x()+b.get_width()/2, b.get_height()+0.5, f"{int(b.get_height())} stocks", ha='center', fontweight='bold')
ax1.set_ylim(0, 35); ax1.set_title("Q1-A. Top 30 Market Cap Turnover", fontweight='bold'); ax1.grid(axis='y', alpha=0.3)
ax2.barh(range(len(sq)), sq.values, color='#2e75b6', height=0.6)
ax2.set_yticks(range(len(sq))); ax2.set_yticklabels([f"Top-{len(sq)-i} Volatile Sector" for i in range(len(sq))])
ax2.set_xlabel("Mean Absolute Rank Change"); ax2.set_title("Q1-B. Top 8 Sectors by Rank Mobility", fontweight='bold'); ax2.grid(axis='x', alpha=0.3)
plt.tight_layout(); plt.savefig("outputs/q1_chart.png"); plt.close()

# [Q2] 업종별 수익률 격차
valid_sec = df.groupby('sec')['code'].nunique()
valid_sec = valid_sec[valid_sec >= 10].index
sec_daily = df[df['sec'].isin(valid_sec) & (df['rc'].abs() <= 0.305)].pivot_table(index='date', columns='sec', values='rc', aggfunc='mean').iloc[9:]
cum_sec = ((1 + sec_daily).cumprod().iloc[-1] - 1) * 100
comb = pd.concat([cum_sec.sort_values().head(5), cum_sec.sort_values(ascending=False).head(5).iloc[::-1]])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8), dpi=150)
ax1.barh(range(len(comb)), comb.values, color=['#c00000' if v < 0 else '#1f4e78' for v in comb.values], height=0.6)
ax1.set_yticks(range(len(comb))); ax1.set_yticklabels([f"Bot-{5-i}" if i<5 else f"Top-{10-i}" for i in range(len(comb))])
ax1.axvline(0, color='black', lw=0.8); ax1.set_title("Q2-A. Top 5 vs Bottom 5 Sector Return (%)", fontweight='bold'); ax1.grid(axis='x', alpha=0.3)
cs_std = ((1 + sec_daily).cumprod() - 1).std(axis=1) * 100
ax2.plot(pd.to_datetime(cs_std.index), cs_std.values, color='#ed7d31', lw=2)
ax2.set_title("Q2-B. Cross-Sector Return Dispersion (%p)", fontweight='bold'); ax2.set_ylabel("Std Dev (%p)"); ax2.grid(alpha=0.3)
plt.tight_layout(); plt.savefig("outputs/q2_chart.png"); plt.close()

# [Q3] 업종 동조화
mkt_ret = sec_daily.mean(axis=1)
high_vol = mkt_ret.abs() >= mkt_ret.abs().quantile(0.90)
def avg_corr(s):
    c = s.corr().values
    return np.nanmean(c[np.triu_indices_from(c, k=1)])

c_all, c_norm, c_high = avg_corr(sec_daily), avg_corr(sec_daily[~high_vol]), avg_corr(sec_daily[high_vol])
roll_corr = [avg_corr(sec_daily.iloc[i-60:i]) for i in range(60, len(sec_daily))]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8), dpi=150)
ax1.plot(pd.to_datetime(sec_daily.index[60:]), roll_corr, color='#1f4e78', lw=1.8)
ax1.axhline(c_all, color='#ed7d31', ls='--', label=f'Mean ({c_all:.3f})')
ax1.set_title("Q3-A. 60-Day Rolling Cross-Sector Correlation", fontweight='bold'); ax1.legend(); ax1.grid(alpha=0.3)
bars = ax2.bar(['Normal Days (90%)', 'Market Shock (Top 10%)'], [c_norm, c_high], color=['#5b9bd5', '#c00000'], width=0.45)
for b in bars: ax2.text(b.get_x()+b.get_width()/2, b.get_height()+0.015, f"{b.get_height():.3f}", ha='center', fontweight='bold')
ax2.set_ylim(0, 0.9); ax2.set_title("Q3-B. Conditional Correlation by Volatility", fontweight='bold'); ax2.grid(axis='y', alpha=0.3)
plt.tight_layout(); plt.savefig("outputs/q3_chart.png"); plt.close()

# [Q4] 거래량과 가격 선후관계
df['vr'] = df['volume'] / df.groupby('code')['volume'].transform(lambda s: s.shift(1).rolling(20, min_periods=15).mean())
df['ve'] = (df['close'] * df['volume']) / 1e8
lags = list(range(-5, 21))
for k in lags: df[f'l_{k}'] = df.groupby('code')['rc'].shift(-k)

def get_path(mask):
    sub = df[mask].dropna(subset=[f'l_{k}' for k in lags])
    cp = (np.cumprod([1 + sub[f'l_{k}'].mean() for k in lags]) - 1) * 100
    return cp - cp[4], len(sub)

mb = (df['ve']>=100) & (df['vr']>=5.0) & (df['rc'].abs()<=0.305)
pb, nb = get_path(mb)
p10, n10 = get_path((df['ve']>=100) & (df['vr']>=10.0) & (df['rc'].abs()<=0.305))
pu, nu = get_path(mb & (df['rc']>0))
pdn, ndn = get_path(mb & (df['rc']<0))

fig, ax = plt.subplots(figsize=(12, 4.8), dpi=150)
ax.axvline(0, color='gray', ls=':'); ax.axhline(0, color='black', lw=0.8)
ax.plot(lags, pb, '-o', ms=3.5, color='#1f4e78', lw=2, label=f'(a) Vol>=5x (n={nb:,}): t+5={pb[10]:.2f}%, t+20={pb[25]:.2f}%')
ax.plot(lags, p10, '-s', ms=3.5, color='#ed7d31', lw=1.8, label=f'(b1) Vol>=10x (n={n10:,}): t+5={p10[10]:.2f}%, t+20={p10[25]:.2f}%')
ax.plot(lags, pu, '--^', ms=3.5, color='#2e75b6', lw=1.5, label=f'(b2) Up-Surge (n={nu:,}): t+5={pu[10]:.2f}%')
ax.plot(lags, pdn, '--v', ms=3.5, color='#c00000', lw=1.5, label=f'(b3) Down-Surge (n={ndn:,}): t+5={pdn[10]:.2f}%')
ax.set_title("Q4. Cumulative Return Trajectory Around Volume Surge (t-5 to t+20)", fontweight='bold')
ax.set_xlabel("Event Window (Trading Days)"); ax.set_ylabel("Cumulative Return (%)"); ax.legend(loc='upper left', fontsize=9); ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig("outputs/q4_chart.png"); plt.close()
print("파트 1 완료: Q1~Q4 차트 4개 생성 완료!")
