import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd, numpy as np

df = pd.read_pickle("data_processed/clean_q.pkl")
df['rc'] = df['ret'].fillna(0.0)
df['vr'] = df['volume'] / df.groupby('code')['volume'].transform(lambda s: s.shift(1).rolling(20, min_periods=15).mean())
df['ve'] = (df['close'] * df['volume']) / 1e8
lags = list(range(-5, 21))
for k in lags: df[f'l_{k}'] = df.groupby('code')['rc'].shift(-k)

def path(m):
    s = df[m].dropna(subset=[f'l_{k}' for k in lags])
    cp = (np.cumprod([1 + s[f'l_{k}'].mean() for k in lags]) - 1) * 100
    return cp - cp[4], len(s)

mb = (df['ve']>=100) & (df['vr']>=5.0)
pb, nb = path(mb)
p10, n10 = path((df['ve']>=100) & (df['vr']>=10.0))
pu, nu = path(mb & (df['rc']>0))
pdn, ndn = path(mb & (df['rc']<0))

fig, ax = plt.subplots(figsize=(11, 5), dpi=150)
ax.axvline(0, color='gray', ls=':'); ax.axhline(0, color='black', lw=0.8)
ax.plot(lags, pb, '-o', ms=3.5, color='#1f4e78', lw=2, label=f'(a) Vol>=5x (n={nb:,})')
ax.plot(lags, p10, '--s', ms=3, color='#ed7d31', lw=1.7, label=f'(b1) Vol>=10x (n={n10:,})')
ax.plot(lags, pu, '-.', color='#c00000', lw=1.5, label=f'(b2) Vol>=5x & Up (n={nu:,})')
ax.plot(lags, pdn, '-.', color='#00b050', lw=1.5, label=f'(b3) Vol>=5x & Down (n={ndn:,})')
ax.set_title("Q4. Cumulative Return Trajectory (t-5 to t+20, Aligned at t-1 = 0%)", fontweight='bold')
ax.set_xlabel("Trading Days Relative to Volume Surge (t=0)"); ax.set_ylabel("Cumulative Return (%)")
ax.legend(); ax.grid(alpha=0.3); plt.tight_layout()
plt.savefig("outputs/q4_volume_lead_lag.png"); plt.close()
print("Q4 저장 완료")
