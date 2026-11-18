import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams['axes.unicode_minus'] = False
df = pd.read_pickle("data_processed/clean_q.pkl").sort_values(['code', 'date'])
df['rc'] = df['ret'].fillna(0.0)
df['w_prev'] = df.groupby('code')['market_cap'].shift(1)

valid_sec = df.groupby('sec')['code'].nunique()
valid_sec = valid_sec[valid_sec >= 10].index
sub2 = df[df['sec'].isin(valid_sec) & (df['rc'].abs() <= 0.305)].dropna(subset=['rc', 'w_prev']).copy()

sub2['wr'] = sub2['rc'] * sub2['w_prev']
g_sum = sub2.groupby(['date', 'sec'])[['wr', 'w_prev']].sum()
sec_cap = (g_sum['wr'] / g_sum['w_prev']).unstack('sec').iloc[9:]
cum_cap = ((1 + sec_cap).cumprod() - 1) * 100

sec_eq = sub2.groupby(['date', 'sec'])['rc'].mean().unstack('sec').iloc[9:]
cum_eq = ((1 + sec_eq).cumprod() - 1) * 100

disp_cap, disp_eq = cum_cap.std(axis=1), cum_eq.std(axis=1)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8), dpi=150)
end_cap = cum_cap.iloc[-1].sort_values()
comb = pd.concat([end_cap.head(5), end_cap.tail(5)])
ax1.barh(range(len(comb)), comb.values, color=['#c00000' if v < 0 else '#1f4e78' for v in comb.values], height=0.6)
ax1.set_yticks(range(len(comb))); ax1.set_yticklabels([f"Bot-{5-i}" if i<5 else f"Top-{10-i}" for i in range(len(comb))])
ax1.axvline(0, color='black', lw=0.8); ax1.set_xlabel("Cumulative Return (%) [Cap-Weighted]")
ax1.set_title("Q2-A. Top 5 vs Bottom 5 Sector Return", fontweight='bold'); ax1.grid(axis='x', alpha=0.3)

ax2.plot(pd.to_datetime(disp_cap.index), disp_cap.values, color='#1f4e78', lw=2, label='(a) Cap-Weighted Std Dev (%p)')
ax2.plot(pd.to_datetime(disp_eq.index), disp_eq.values, color='#ed7d31', lw=1.8, ls='--', label='(b) Equal-Weighted Std Dev (%p)')
ax2.set_ylabel("Cross-Sector Cumulative Return Std Dev (%p)")
ax2.set_title("Q2-B. Sector Return Dispersion Over Time", fontweight='bold'); ax2.legend(); ax2.grid(alpha=0.3)
plt.tight_layout(); plt.savefig("outputs/q2_def.png"); plt.close()

meta = json.load(open("outputs/meta.json", encoding="utf-8"))
meta.update({"q2_cap_s": round(float(disp_cap.iloc[0]), 1), "q2_cap_e": round(float(disp_cap.iloc[-1]), 1), "q2_eq_e": round(float(disp_eq.iloc[-1]), 1)})
json.dump(meta, open("outputs/meta.json", "w", encoding="utf-8"), ensure_ascii=False)
print("2/5 완료: Q2 차트 생성 성공")
