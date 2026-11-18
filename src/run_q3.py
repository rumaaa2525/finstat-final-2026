import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd, numpy as np

plt.rcParams['axes.unicode_minus'] = False
df = pd.read_pickle("data_processed/clean_q.pkl").sort_values(['code', 'date'])
df['rc'] = df['ret'].fillna(0.0)

valid_sec = df.groupby('sec')['code'].nunique()
valid_sec = valid_sec[valid_sec >= 10].index
sec_daily = df[df['sec'].isin(valid_sec) & (df['rc'].abs() <= 0.305)].pivot_table(index='date', columns='sec', values='rc', aggfunc='mean').iloc[9:]

mkt_ret = sec_daily.mean(axis=1)
high_vol = mkt_ret.abs() >= mkt_ret.abs().quantile(0.90)
def avg_corr(s):
    c = s.corr().values
    return float(np.nanmean(c[np.triu_indices_from(c, k=1)]))

c_all, c_norm, c_high = avg_corr(sec_daily), avg_corr(sec_daily[~high_vol]), avg_corr(sec_daily[high_vol])
roll_corr = [avg_corr(sec_daily.iloc[i-60:i]) for i in range(60, len(sec_daily))]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8), dpi=150)
ax1.plot(pd.to_datetime(sec_daily.index[60:]), roll_corr, color='#1f4e78', lw=1.8)
ax1.axhline(c_all, color='#ed7d31', ls='--', label=f'Full Mean ({c_all:.3f})')
ax1.set_ylabel("60-Day Rolling Correlation"); ax1.set_title("Q3-A. Rolling Cross-Sector Correlation", fontweight='bold'); ax1.legend(); ax1.grid(alpha=0.3)

bars = ax2.bar(['Normal Days (90%)', 'Market Shock (Top 10%)'], [c_norm, c_high], color=['#5b9bd5', '#c00000'], width=0.45)
for b in bars: ax2.text(b.get_x()+b.get_width()/2, b.get_height()+0.015, f"{b.get_height():.3f}", ha='center', fontweight='bold')
ax2.set_ylim(0, 0.9); ax2.set_ylabel("Conditional Correlation"); ax2.set_title("Q3-B. Normal vs Market Shock Correlation", fontweight='bold'); ax2.grid(axis='y', alpha=0.3)
plt.tight_layout(); plt.savefig("outputs/q3_def.png"); plt.close()

meta = json.load(open("outputs/meta.json", encoding="utf-8"))
meta.update({"c_all": round(c_all, 3), "c_norm": round(c_norm, 3), "c_high": round(c_high, 3)})
json.dump(meta, open("outputs/meta.json", "w", encoding="utf-8"), ensure_ascii=False)
print("3/5 완료: Q3 차트 생성 성공")
