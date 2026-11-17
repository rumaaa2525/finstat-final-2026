import os
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np

plt.rcParams['axes.unicode_minus'] = False
OUT_DIR = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)

print("1. 마스터 데이터 로드 및 공통 필터링 적용 중...")
df = pd.read_pickle("data_processed/daily_market.pkl")

# [정의 1] 분석 기간: 전체 시장 수집 시작일 2024-04-15 ~ 2026-09-02
df = df[df['date'] >= '2024-04-15'].copy()

# [정의 2] 순수 보통주 필터링: 업종명 존재 + 스팩 제외 + 우선주(코드 끝자리 != 0) 제외
df = df[df['sector'].notna()].copy()
latest_names = df.sort_values('date').groupby('code')['name'].last()
spac_codes = set(latest_names[latest_names.str.contains(r"스팩|제\d+호", na=False)].index)
df = df[~df['code'].isin(spac_codes)]
df = df[df['code'].str[-1] == '0'].copy()

# [정의 3] 업종 재분류 처리: 종료일 기준 최신 업종으로 통일 (일관된 패널 추적용)
latest_sector = df.sort_values('date').groupby('code')['sector'].last()
df['sector_fixed'] = df['code'].map(latest_sector)

df = df.sort_values(['code', 'date']).reset_index(drop=True)

# [정의 4] 일별 수익률 산출 및 액면분할/병합(+-30.5% 초과) 불연속 보정
df['prev_close_seq'] = df.groupby('code')['close'].shift(1)
df['raw_ret'] = (df['close'] - df['prev_close_seq']) / df['prev_close_seq']
# 첫 거래일 또는 가격제한폭(30.5%) 초과 불연속일은 수익률 0(결측 보정) 처리
df['ret'] = np.where((df['raw_ret'].abs() > 0.305) | (df['raw_ret'].isna()), 0.0, df['raw_ret'])
df['prev_mcap'] = df.groupby('code')['market_cap'].shift(1)

dates = sorted(df['date'].unique())
start_date, end_date = dates[0], dates[-1]
print(f"필터링 완료: {start_date} ~ {end_date} ({len(dates)}일) | 보통주 {df['code'].nunique():,}종목 | {len(df):,}행")

# ==============================================================================
# 공통 질문 1: 시가총액 순위는 2년 반 동안 얼마나 바뀌었는가?
# ==============================================================================
print("\n--- [공통 질문 1 분석] ---")
df_start = df[df['date'] == start_date][['code', 'name', 'sector_fixed', 'market_cap']].copy()
df_end = df[df['date'] == end_date][['code', 'name', 'sector_fixed', 'market_cap']].copy()

df_start['rank_start'] = df_start['market_cap'].rank(ascending=False, method='min')
df_end['rank_end'] = df_end['market_cap'].rank(ascending=False, method='min')

m_rank = pd.merge(df_start, df_end, on=['code', 'sector_fixed'], suffixes=('_s', '_e'), how='outer')
top30_s = set(df_start[df_start['rank_start'] <= 30]['code'])
top30_e = set(df_end[df_end['rank_end'] <= 30]['code'])
retained = top30_s & top30_e
new_in = top30_e - top30_s

print(f"시작일({start_date}) Top 30 중 종료일({end_date}) 잔류 종목 수: {len(retained)}개 / 신규 진입: {len(new_in)}개")
new_in_df = df_end[df_end['code'].isin(new_in)].sort_values('rank_end')
print("[신규 Top 30 진입 종목 및 업종]")
print(new_in_df[['rank_end', 'code', 'name', 'sector_fixed', 'market_cap']].to_string(index=False))

# 업종별 순위 이동 크기 (양 시점 모두 존재하는 종목 기준, 상위 100위권 또는 전체 평균 절대 순위 변동)
both_rank = m_rank.dropna(subset=['rank_start', 'rank_end']).copy()
both_rank['rank_diff'] = both_rank['rank_start'] - both_rank['rank_end']  # 양수면 순위 상승
both_rank['abs_diff'] = both_rank['rank_diff'].abs()

sec_cnt = both_rank.groupby('sector_fixed')['code'].count()
valid_secs = sec_cnt[sec_cnt >= 15].index
sec_rank_move = both_rank[both_rank['sector_fixed'].isin(valid_secs)].groupby('sector_fixed').agg(
    mean_abs_move=('abs_diff', 'mean'),
    median_shift=('rank_diff', 'median'),
    n=('code', 'count')
).sort_values('mean_abs_move', ascending=False)

print("\n[업종별 순위 이동 크기 상위 10개 업종 (15종목 이상 업종)]")
print(sec_rank_move.head(10).round(1))

# Q1 시각화: 왼쪽(Top 30 잔류/교체 요약 및 신규 진입 업종) + 오른쪽(업종별 평균 절대 순위 변동 Top 12)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=150)

# 좌측: Top 30 구성 변화 바 차트
bars = ax1.bar(['Retained in Top 30', 'Newly Entered Top 30'], [len(retained), len(new_in)], color=['#1f4e78', '#ed7d31'], width=0.5)
for b in bars:
    ax1.text(b.get_x() + b.get_width()/2, b.get_height() + 0.5, f"{int(b.get_height())} stocks", ha='center', fontweight='bold', fontsize=11)
ax1.set_ylim(0, 35)
ax1.set_title(f"Top 30 Market Cap Turnover\n({start_date} vs {end_date})", fontsize=12, fontweight='bold')
ax1.set_ylabel("Number of Stocks", fontsize=10)
ax1.grid(axis='y', linestyle='--', alpha=0.4)

# 우측: 업종별 평균 절대 순위 변동 Top 12
top_move = sec_rank_move.head(12).iloc[::-1]
ax2.barh(range(len(top_move)), top_move['mean_abs_move'], color='#2e75b6')
ax2.set_yticks(range(len(top_move)))
ax2.set_yticklabels([f"Sector #{i+1} (n={int(r.n)})" for i, r in enumerate(top_move.itertuples())], fontsize=9.5)
# 실제 한글 업종명 매핑 CSV 별도 저장 (한글 폰트 깨짐 방지용 코드번호 병기)
sec_map_q1 = pd.DataFrame({'label': [f"Sector #{i+1}" for i in range(len(top_move))], 'sector_kr': top_move.index, 'mean_abs_move': top_move['mean_abs_move'].values})
sec_map_q1.to_csv("outputs/q1_sector_labels.csv", index=False)

for idx_b, val in enumerate(top_move['mean_abs_move']):
    ax2.text(val + 3, idx_b, f"{val:.1f}", va='center', fontsize=9)
ax2.set_xlim(0, top_move['mean_abs_move'].max() * 1.15)
ax2.set_title("Mean Absolute Rank Change by Sector (Top 12)", fontsize=12, fontweight='bold')
ax2.set_xlabel("Mean |Rank_start - Rank_end|", fontsize=10)
ax2.grid(axis='x', linestyle='--', alpha=0.4)

plt.tight_layout()
plt.savefig("outputs/q1_mcap_rank_shift.png")
plt.close()

# ==============================================================================
# 공통 질문 2: 업종 간 수익률의 차이는 2년 반 동안 벌어졌는가, 좁혀졌는가?
# ==============================================================================
print("\n--- [공통 질문 2 분석] ---")
# 종목 수 15개 이상 업종만 추출하여 전일 시가총액 가중 일별 수익률 산출
sec_sizes = df.groupby('sector_fixed')['code'].nunique()
major_secs = sec_sizes[sec_sizes >= 15].index
df_maj = df[df['sector_fixed'].isin(major_secs)].copy()

df_maj['w_ret'] = df_maj['ret'] * df_maj['prev_mcap'].fillna(0)
sec_daily = df_maj.groupby(['date', 'sector_fixed']).agg(
    sum_w_ret=('w_ret', 'sum'),
    sum_mcap=('prev_mcap', 'sum')
).reset_index()
sec_daily['sec_ret'] = np.where(sec_daily['sum_mcap'] > 0, sec_daily['sum_w_ret'] / sec_daily['sum_mcap'], 0.0)

piv_ret = sec_daily.pivot(index='date', columns='sector_fixed', values='sec_ret').fillna(0.0)
piv_cum = (1 + piv_ret).cumprod() - 1  # 누적 수익률

final_cum = piv_cum.iloc[-1].sort_values(ascending=False)
print("[누적 수익률 상위 5개 업종]")
print((final_cum.head(5) * 100).round(2))
print("[누적 수익률 하위 5개 업종]")
print((final_cum.tail(5) * 100).round(2))

# 시점별 업종 간 누적 수익률 횡단면 표준편차 (격차 지표)
cross_std = piv_cum.std(axis=1) * 100
print(f"업종 간 누적 수익률 횡단면 표준편차: 초기 30일 평균 {cross_std.iloc[:30].mean():.2f}% -> 말기 30일 평균 {cross_std.iloc[-30:].mean():.2f}%")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 7.5), dpi=150, sharex=True)
dt_idx = pd.to_datetime(piv_cum.index)

# 상단: 전체 업종 누적 수익률 궤적 (상위 3개, 하위 2개 강조)
for col in piv_cum.columns:
    ax1.plot(dt_idx, piv_cum[col] * 100, color='#cccccc', alpha=0.5, linewidth=0.8)

top3_s = final_cum.head(3).index
bot2_s = final_cum.tail(2).index
colors_hi = ['#c00000', '#ed7d31', '#ffc000']
for idx_c, s_name in enumerate(top3_s):
    ax1.plot(dt_idx, piv_cum[s_name] * 100, color=colors_hi[idx_c], linewidth=2.0, label=f"Top {idx_c+1} Sector ({final_cum[s_name]*100:.1f}%)")
for idx_c, s_name in enumerate(bot2_s):
    ax1.plot(dt_idx, piv_cum[s_name] * 100, color='#1f4e78' if idx_c==0 else '#5b9bd5', linewidth=1.8, linestyle='--', label=f"Bottom {idx_c+1} Sector ({final_cum[s_name]*100:.1f}%)")

pd.DataFrame({'rank': ['Top1', 'Top2', 'Top3', 'Bot1', 'Bot2'], 'sector_kr': list(top3_s) + list(bot2_s), 'cum_ret_pct': [final_cum[x]*100 for x in list(top3_s) + list(bot2_s)]}).to_csv("outputs/q2_sector_labels.csv", index=False)

ax1.set_title("Cumulative Returns Across Major Sectors (Cap-Weighted, >=15 Stocks)", fontsize=12, fontweight='bold')
ax1.set_ylabel("Cumulative Return (%)", fontsize=10)
ax1.legend(loc='upper left', fontsize=9)
ax1.grid(True, linestyle='--', alpha=0.4)

# 하단: 업종 간 누적 수익률 횡단면 표준편차 추이
ax2.plot(dt_idx, cross_std, color='#2e75b6', linewidth=1.8)
ax2.fill_between(dt_idx, cross_std, color='#2e75b6', alpha=0.15)
ax2.set_title("Cross-Sectional Standard Deviation of Sector Cumulative Returns (Divergence Trend)", fontsize=12, fontweight='bold')
ax2.set_ylabel("Cross-Sector Std Dev (%p)", fontsize=10)
ax2.set_xlabel("Date", fontsize=10)
ax2.grid(True, linestyle='--', alpha=0.4)
ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

plt.tight_layout()
plt.savefig("outputs/q2_sector_divergence.png")
plt.close()

# ==============================================================================
# 공통 질문 3: 업종들은 같이 움직이는가, 따로 움직이는가?
# ==============================================================================
print("\n--- [공통 질문 3 분석] ---")
# 전체 평균 상관계수
corr_mat = piv_ret.corr()
upper_tri = corr_mat.where(np.triu(np.ones(corr_mat.shape), k=1).astype(bool))
mean_corr_all = upper_tri.stack().mean()

# 60일 롤링 평균 상관계수
roll_corrs = []
roll_dates = []
win = 60
for i in range(win, len(piv_ret)):
    sub_c = piv_ret.iloc[i-win:i].corr()
    u_val = sub_c.where(np.triu(np.ones(sub_c.shape), k=1).astype(bool)).stack().mean()
    roll_corrs.append(u_val)
    roll_dates.append(pd.to_datetime(piv_ret.index[i]))

# 시장 전체(시총가중) 일별 수익률 기준 급변동일(|mkt_ret| 상위 10%) vs 보통 날(나머지 90%)
mkt_daily = df_maj.groupby('date').apply(lambda g: (g['ret'] * g['prev_mcap'].fillna(0)).sum() / g['prev_mcap'].fillna(0).sum(), include_groups=False)
thresh_90 = mkt_daily.abs().quantile(0.90)
shock_days = mkt_daily[mkt_daily.abs() >= thresh_90].index
normal_days = mkt_daily[mkt_daily.abs() < thresh_90].index

c_shock = piv_ret.loc[shock_days].corr()
c_norm = piv_ret.loc[normal_days].corr()
mean_shock = c_shock.where(np.triu(np.ones(c_shock.shape), k=1).astype(bool)).stack().mean()
mean_norm = c_norm.where(np.triu(np.ones(c_norm.shape), k=1).astype(bool)).stack().mean()

print(f"전체 기간 업종 간 평균 일별 상관계수: {mean_corr_all:.4f}")
print(f"시장 급변동일(상위 10%, |r|>={thresh_90*100:.2f}%) 평균 상관계수: {mean_shock:.4f} vs 보통 날: {mean_norm:.4f}")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.2), dpi=150, gridspec_kw={'width_ratios': [2.2, 1]})
ax1.plot(roll_dates, roll_corrs, color='#1f4e78', linewidth=1.6)
ax1.axhline(mean_corr_all, color='#c00000', linestyle='--', linewidth=1.2, label=f"Full-Period Mean ({mean_corr_all:.3f})")
ax1.set_title("60-Day Rolling Mean Pairwise Correlation Across Sectors", fontsize=12, fontweight='bold')
ax1.set_ylabel("Mean Pairwise Correlation", fontsize=10)
ax1.set_xlabel("Date", fontsize=10)
ax1.grid(True, linestyle='--', alpha=0.4)
ax1.legend(loc='upper right')
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

bars3 = ax2.bar(['Normal Days\n(Bottom 90% |Mkt|)', 'Shock Days\n(Top 10% |Mkt|)'], [mean_norm, mean_shock], color=['#5b9bd5', '#c00000'], width=0.5)
for b in bars3:
    ax2.text(b.get_x() + b.get_width()/2, b.get_height() + 0.015, f"{b.get_height():.3f}", ha='center', fontweight='bold', fontsize=11)
ax2.set_ylim(0, max(mean_shock, mean_norm) * 1.25)
ax2.set_title("Sector Co-movement:\nNormal vs Market Shock Days", fontsize=12, fontweight='bold')
ax2.set_ylabel("Mean Pairwise Correlation", fontsize=10)
ax2.grid(axis='y', linestyle='--', alpha=0.4)

plt.tight_layout()
plt.savefig("outputs/q3_sector_correlation.png")
plt.close()

# ==============================================================================
# 공통 질문 4: 거래량은 가격을 앞서는가, 뒤따르는가? (정의 변경 민감도 포함)
# ==============================================================================
print("\n--- [공통 질문 4 분석] ---")
# 직전 20일 평균 거래량 대비 배수 및 선행 누적수익률(t+1 ~ t+5, t+10, t+20) 계산
df['vol_ma20'] = df.groupby('code')['volume'].transform(lambda s: s.shift(1).rolling(20, min_periods=15).mean())
df['vol_ratio'] = df['volume'] / df['vol_ma20']
df['trading_val_eok'] = (df['close'] * df['volume']) / 1e8  # 거래대금(억원)

# 미래 수익률 계산 (종가 기준 누적수익률, 급격한 액면분할 노이즈 제거 위해 일별 ret 누적 사용)
df['log_ret'] = np.log1p(df['ret'])
for h in [5, 10, 20]:
    # t+1일부터 t+h일까지의 누적수익률
    df[f'fwd_ret_{h}'] = np.expm1(df.groupby('code')['log_ret'].transform(lambda s: s.iloc[::-1].rolling(h, min_periods=h).sum().iloc[::-1].shift(-1)))

# 기본 정의: 거래대금 100억 이상 & 직전 20일 평균 대비 거래량 5배 이상
base_cond = (df['trading_val_eok'] >= 100) & (df['vol_ratio'] >= 5.0)
# 정의 변경 A: 배수 기준 변경 (3배 vs 5배 vs 10배)
cond_3x = (df['trading_val_eok'] >= 100) & (df['vol_ratio'] >= 3.0)
cond_10x = (df['trading_val_eok'] >= 100) & (df['vol_ratio'] >= 10.0)
# 정의 변경 B: 당일 주가 방향 조건 추가 (상승 동반 거래량 5배 급증 vs 하락 동반 거래량 5배 급증)
cond_up5x = base_cond & (df['ret'] > 0)
cond_dn5x = base_cond & (df['ret'] < 0)

defs = {
    'Base: Vol >= 5x (Val>=100B)': base_cond,
    'Alt 1: Vol >= 3x (Looser)': cond_3x,
    'Alt 2: Vol >= 10x (Stricter)': cond_10x,
    'Alt 3a: Vol >= 5x & Up Day': cond_up5x,
    'Alt 3b: Vol >= 5x & Down Day': cond_dn5x
}

summary_q4 = []
for label, mask in defs.items():
    sub = df[mask].dropna(subset=['fwd_ret_5', 'fwd_ret_10', 'fwd_ret_20'])
    summary_q4.append({
        'definition': label,
        'events': len(sub),
        'day0_ret': sub['ret'].mean() * 100,
        'fwd_5d': sub['fwd_ret_5'].mean() * 100,
        'fwd_10d': sub['fwd_ret_10'].mean() * 100,
        'fwd_20d': sub['fwd_ret_20'].mean() * 100
    })

res_q4 = pd.DataFrame(summary_q4)
print(res_q4.round(3).to_string(index=False))

fig, ax = plt.subplots(figsize=(11, 5.5), dpi=150)
x = np.arange(3)
width = 0.16
horizons = ['fwd_5d', 'fwd_10d', 'fwd_20d']
h_labels = ['After 5 Days (t+5)', 'After 10 Days (t+10)', 'After 20 Days (t+20)']
palette = ['#1f4e78', '#5b9bd5', '#2e75b6', '#c00000', '#00b050']

for idx_d, row in res_q4.iterrows():
    vals = [row[h] for h in horizons]
    ax.bar(x + (idx_d - 2) * width, vals, width, label=f"{row['definition']} (n={row['events']:,})", color=palette[idx_d])

ax.axhline(0, color='black', linewidth=1.0)
ax.set_xticks(x)
ax.set_xticklabels(h_labels, fontsize=11, fontweight='bold')
ax.set_ylabel("Mean Forward Cumulative Return (%)", fontsize=10)
ax.set_title("Forward Returns After Volume Surge Across Alternative Definitions", fontsize=12, fontweight='bold')
ax.legend(loc='best', fontsize=8.8)
ax.grid(axis='y', linestyle='--', alpha=0.4)

plt.tight_layout()
plt.savefig("outputs/q4_volume_lead_lag.png")
plt.close()

print("\n=== 공통 질문 1~4번 분석 및 그림 4장 생성 완료 ===")
