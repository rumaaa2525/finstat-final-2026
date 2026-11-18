import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd, numpy as np

plt.rcParams['axes.unicode_minus'] = False
df = pd.read_pickle("data_processed/clean_q.pkl").sort_values(['code', 'date'])
df['rc'] = df['ret'].fillna(0.0)
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
ax.plot(lags, pb, '-o', ms=3.5, color='#1f4e78', lw=2, label=f'(a) Vol>=5x (n={nb:,}): t+5={pb[10]:.2f}%, t+10={pb[15]:.2f}%, t+20={pb[25]:.2f}%')
ax.plot(lags, p10, '-s', ms=3.5, color='#ed7d31', lw=1.8, label=f'(b1) Vol>=10x (n={n10:,}): t+5={p10[10]:.2f}%, t+10={p10[15]:.2f}%, t+20={p10[25]:.2f}%')
ax.plot(lags, pu, '--^', ms=3.5, color='#2e75b6', lw=1.5, label=f'(b2) Up-Surge (n={nu:,}): t+5={pu[10]:.2f}%, t+20={pu[25]:.2f}%')
ax.plot(lags, pdn, '--v', ms=3.5, color='#c00000', lw=1.5, label=f'(b3) Down-Surge (n={ndn:,}): t+5={pdn[10]:.2f}%, t+20={pdn[25]:.2f}%')
ax.set_title("Q4. Cumulative Return Trajectory Around Volume Surge (t-5 to t+20)", fontweight='bold')
ax.set_xlabel("Event Window (Trading Days)"); ax.set_ylabel("Cumulative Return Relative to t-1 (%)"); ax.legend(loc='upper left', fontsize=8.8); ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig("outputs/q4_def.png"); plt.close()

meta = json.load(open("outputs/meta.json", encoding="utf-8"))
meta.update({"nb": int(nb), "n10": int(n10), "pb0": round(float(pb[5]), 2), "pb5": round(float(pb[10]), 2), "pb10": round(float(pb[15]), 2), "pb20": round(float(pb[25]), 2)})
json.dump(meta, open("outputs/meta.json", "w", encoding="utf-8"), ensure_ascii=False)
print("4/5 완료: Q4 차트 생성 성공")
