import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd, numpy as np

df = pd.read_pickle("data_processed/clean_q.pkl")
maj = df.groupby('sec')['code'].nunique()
dm = df[df['sec'].isin(maj[maj>=10].index)].dropna(subset=['ret','prev_mcap']).copy()
dm['wr'] = dm['ret'] * dm['prev_mcap']
cap_d = dm.groupby(['date','sec']).apply(lambda g: g['wr'].sum()/g['prev_mcap'].sum(), include_groups=False).unstack('sec').fillna(0.0)
eq_d = dm.groupby(['date','sec'])['ret'].mean().unstack('sec').fillna(0.0)
cap_c, eq_c = (1+cap_d).cumprod()-1, (1+eq_d).cumprod()-1

cap_dt = cap_d.copy(); cap_dt.index = pd.to_datetime(cap_dt.index)
eq_dt = eq_d.copy(); eq_dt.index = pd.to_datetime(eq_dt.index)
cm = cap_dt.resample('ME').apply(lambda x: (1+x).prod()-1)
em = eq_dt.resample('ME').apply(lambda x: (1+x).prod()-1)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=150)
dt = pd.to_datetime(cap_c.index)
ax1.plot(dt, cap_c.std(axis=1)*100, color='#c00000', lw=2, label='(a) Cap-Weighted')
ax1.plot(dt, eq_c.std(axis=1)*100, color='#1f4e78', ls='--', lw=1.8, label='(b) Equal-Weighted')
ax1.set_title("Q2-A. Cumulative Return Spread (%p)", fontweight='bold'); ax1.legend(); ax1.grid(alpha=0.3)
ax2.plot(cm.index, cm.std(axis=1)*100, '-o', ms=3.5, color='#ed7d31', label='(a) Cap-Weighted Monthly')
ax2.plot(em.index, em.std(axis=1)*100, '--s', ms=3, color='#5b9bd5', label='(b) Equal-Weighted Monthly')
ax2.set_title("Q2-B. Monthly Dispersion (%p)", fontweight='bold'); ax2.legend(); ax2.grid(alpha=0.3)
plt.tight_layout(); plt.savefig("outputs/q2_sector_divergence.png"); plt.close()

rc = [cap_d.iloc[i-60:i].corr().values[np.triu_indices(cap_d.shape[1], 1)].mean() for i in range(60, len(cap_d))]
rd = pd.to_datetime(cap_d.index[60:])
mkt = dm.groupby('date').apply(lambda g: g['wr'].sum()/g['prev_mcap'].sum(), include_groups=False)
q90 = mkt.abs().quantile(0.90)
m_sh = cap_d.loc[mkt[mkt.abs()>=q90].index].corr().values[np.triu_indices(cap_d.shape[1], 1)].mean()
m_nm = cap_d.loc[mkt[mkt.abs()<q90].index].corr().values[np.triu_indices(cap_d.shape[1], 1)].mean()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=150, gridspec_kw={'width_ratios':[2.2,1]})
ax1.plot(rd, rc, color='#1f4e78', lw=1.7)
ax1.set_title("Q3-A. 60-Day Rolling Pairwise Correlation", fontweight='bold'); ax1.grid(alpha=0.3)
b = ax2.bar(['Normal (90%)', 'Shock (10%)'], [m_nm, m_sh], color=['#5b9bd5','#c00000'], width=0.45)
for x in b: ax2.text(x.get_x()+x.get_width()/2, x.get_height()+0.015, f"{x.get_height():.3f}", ha='center', fontweight='bold')
ax2.set_ylim(0, max(m_sh, m_nm)*1.25); ax2.set_title("Q3-B. Co-movement by Regime", fontweight='bold')
plt.tight_layout(); plt.savefig("outputs/q3_sector_correlation.png"); plt.close()
print("Q2, Q3 저장 완료")
