"""Q1·Q2 그림 생성 (수정본).

변경점 (원본 fix_q12_full.py 대비)
  1. Q1 제목·막대 라벨의 '21 / 9' 하드코딩 제거 -> 계산값(잔류 수, 신규 수)으로 표시
  2. Q2 범례의 '4.1%p -> 90.5%p' 하드코딩 제거 -> 계산값(첫 날 -> 마지막 날)으로 표시
  3. 한글 폰트가 있으면 업종명을 그림에 표시 (없으면 번호 라벨 + 콘솔 출력)
  4. 신규 진입 종목·업종별 순위 이동·상·하위 업종을 outputs/q1_q2_summary.txt 로 저장
     (README 표를 채울 때 그대로 복사)
  5. 업종 수익률 계산을 벡터화 (결과는 동일, pandas 버전 의존 제거)
계산 로직(필터, 가중, 누적)은 원본과 같다.

실행: 저장소 루트에서  python src/fix_q12_full.py
입력: data_processed/clean_q.pkl  (src/run_q12.py 가 생성)
출력: outputs/q1_mcap_rank_shift.png, outputs/q2_sector_divergence.png, outputs/q1_q2_summary.txt
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd
import numpy as np

plt.rcParams['axes.unicode_minus'] = False
os.makedirs("outputs", exist_ok=True)


def setup_korean_font():
    names = {f.name for f in font_manager.fontManager.ttflist}
    for cand in ["Malgun Gothic", "AppleGothic", "NanumGothic", "NanumBarunGothic",
                 "Noto Sans CJK KR", "Noto Sans KR"]:
        if cand in names:
            plt.rcParams['font.family'] = cand
            return True
    return False


HAS_KO = setup_korean_font()
if not HAS_KO:
    print("[경고] 한글 폰트를 찾지 못했습니다. 그림에는 번호 라벨을 쓰고 업종명은 summary 파일에 저장합니다.")

df = pd.read_pickle("data_processed/clean_q.pkl")
dates = sorted(df['date'].unique())
start_date, end_date = dates[0], dates[-1]
summary = [f"기간: {start_date} ~ {end_date} ({len(dates)}거래일)"]

# ------------------------------------------------------------------ Q1
ds = df[df['date'] == start_date][['code', 'name', 'sec', 'market_cap']].copy()
de = df[df['date'] == end_date][['code', 'name', 'sec', 'market_cap']].copy()
ds['rs'] = ds['market_cap'].rank(ascending=False)
de['re'] = de['market_cap'].rank(ascending=False)

m = pd.merge(ds, de, on=['code', 'sec'], suffixes=('_s', '_e')).dropna()
m['diff'] = (m['rs'] - m['re']).abs()

top30_s = set(ds[ds['rs'] <= 30]['code'])
top30_e = set(de[de['re'] <= 30]['code'])
n_ret = len(top30_s & top30_e)
n_new = len(top30_e - top30_s)

sq = (m.groupby('sec').filter(lambda g: len(g) >= 15)
        .groupby('sec')['diff'].mean().sort_values(ascending=False).head(8).iloc[::-1])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.2), dpi=150)
bars = ax1.bar([f'Retained ({n_ret})', f'New Entrants ({n_new})'], [n_ret, n_new],
               color=['#1f4e78', '#ed7d31'], width=0.45)
for b in bars:
    ax1.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5,
             f"{int(b.get_height())} stocks", ha='center', fontweight='bold')
ax1.set_ylim(0, 35)
ax1.set_title(f"Q1-A. Top 30 Turnover ({n_ret} Retained / {n_new} New)\n{start_date} vs {end_date}",
              fontweight='bold')
ax1.grid(axis='y', alpha=0.3)

ax2.barh(range(len(sq)), sq.values, color='#2e75b6', height=0.6)
ax2.set_yticks(range(len(sq)))
if HAS_KO:
    ax2.set_yticklabels(list(sq.index))
else:
    ax2.set_yticklabels([f"Top-{len(sq) - i} Volatile Sector" for i in range(len(sq))])
for i, v in enumerate(sq.values):
    ax2.text(v + sq.max() * 0.01, i, f"{v:.0f} ranks", va='center', fontsize=9)
ax2.set_xlim(0, sq.max() * 1.2)
ax2.set_title("Q1-B. Mean |Rank_start - Rank_end| by Sector (>=15 stocks)", fontweight='bold')
ax2.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig("outputs/q1_mcap_rank_shift.png")
plt.close()

new_df = de[de['code'].isin(top30_e - top30_s)].merge(ds[['code', 'rs']], on='code', how='left')
new_df = new_df.sort_values('re')
summary.append(f"\n[Q1] 상위 30위 잔류 {n_ret}개 / 신규 진입 {n_new}개")
summary.append("신규 진입 종목 (종료일 순위, 종목명, 업종, 시작일 순위[없으면 신규상장·미수집])")
for r in new_df.itertuples():
    rs = "-" if pd.isna(r.rs) else f"{int(r.rs)}위"
    summary.append(f"  {int(r.re):>3}위  {r.name}  [{r.sec}]  (시작일 {rs})")
summary.append("업종별 평균 |순위 이동| 상위 8 (>=15종목 업종)")
for name, v in sq.iloc[::-1].items():
    summary.append(f"  {name}: {v:.1f}위")

# ------------------------------------------------------------------ Q2
maj = df.groupby('sec')['code'].nunique()
dm = df[df['sec'].isin(maj[maj >= 10].index)].dropna(subset=['ret', 'prev_mcap']).copy()
dm['wr'] = dm['ret'] * dm['prev_mcap']

g = dm.groupby(['date', 'sec'])
cap_d = (g['wr'].sum() / g['prev_mcap'].sum()).unstack('sec').fillna(0.0)   # 전일 시총 가중
eq_d = g['ret'].mean().unstack('sec').fillna(0.0)                           # 동일 가중
cap_c = (1 + cap_d).cumprod() - 1
eq_c = (1 + eq_d).cumprod() - 1
fin_c = cap_c.iloc[-1].sort_values(ascending=False)

spread_cap = cap_c.std(axis=1) * 100
spread_eq = eq_c.std(axis=1) * 100

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.2), dpi=150)
dt = pd.to_datetime(cap_c.index)
for col in cap_c.columns:
    ax1.plot(dt, cap_c[col] * 100, color='#d9d9d9', lw=0.7)
for i, s in enumerate(fin_c.head(4).index):
    tag = s if HAS_KO else f"Top #{i + 1} Sector"
    ax1.plot(dt, cap_c[s] * 100, lw=2.0, label=f"{tag} ({fin_c[s] * 100:+.0f}%)")
for i, s in enumerate(fin_c.tail(2).index[::-1]):
    tag = s if HAS_KO else f"Bottom #{i + 1}"
    ax1.plot(dt, cap_c[s] * 100, lw=1.6, ls='--', label=f"{tag} ({fin_c[s] * 100:+.0f}%)")
ax1.set_title("Q2-A. Cumulative Return by Sector (Top 4 vs Bottom 2, Cap-Weighted)", fontweight='bold')
ax1.set_ylabel("Cumulative Return (%)")
ax1.legend(loc='upper left', fontsize=8.5)
ax1.grid(alpha=0.3)

ax2.plot(dt, spread_cap, color='#c00000', lw=2.2,
         label=f"(a) Cap-Weighted ({spread_cap.iloc[0]:.1f} -> {spread_cap.iloc[-1]:.1f} %p)")
ax2.plot(dt, spread_eq, color='#1f4e78', ls='--', lw=1.8,
         label=f"(b) Equal-Weighted ({spread_eq.iloc[0]:.1f} -> {spread_eq.iloc[-1]:.1f} %p)")
ax2.set_title("Q2-B. Cross-Sector Return Spread Over Time", fontweight='bold')
ax2.set_ylabel("Cross-Sector Std Dev (%p)")
ax2.legend(loc='upper left', fontsize=9)
ax2.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("outputs/q2_sector_divergence.png")
plt.close()

summary.append("\n[Q2] 업종 간 누적 수익률 표준편차 (%p)")
summary.append(f"  시총가중: {spread_cap.iloc[0]:.1f} -> {spread_cap.iloc[-1]:.1f} (최대 {spread_cap.max():.1f}, {spread_cap.idxmax()})")
summary.append(f"  동일가중: {spread_eq.iloc[0]:.1f} -> {spread_eq.iloc[-1]:.1f} (최대 {spread_eq.max():.1f}, {spread_eq.idxmax()})")
summary.append("누적 수익률 상위 5 (시총가중)")
for name, v in fin_c.head(5).items():
    summary.append(f"  {name}: {v * 100:+.1f}%")
summary.append("누적 수익률 하위 5 (시총가중)")
for name, v in fin_c.tail(5).iloc[::-1].items():
    summary.append(f"  {name}: {v * 100:+.1f}%")

text = "\n".join(summary)
with open("outputs/q1_q2_summary.txt", "w", encoding="utf-8") as f:
    f.write(text + "\n")
print(text)
print("\nQ1, Q2 그림 및 outputs/q1_q2_summary.txt 저장 완료")
