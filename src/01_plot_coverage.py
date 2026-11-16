import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 영문 폰트 기본 설정 (서버 한글 폰트 깨짐 방지용 깔끔한 영문 라벨 사용)
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv("outputs/archive_scan_summary.csv")
df['dt'] = pd.to_datetime(df['date'])
df = df.sort_values('dt').reset_index(drop=True)

# 10KB 미만 의심 파일 정보 출력
small_df = df[df['small_under_10kb'] > 0]
if not small_df.empty:
    print("[10KB 미만 의심 파일 발생일]")
    print(small_df[['date', 'total_html', 'small_under_10kb']])

# 전체 영업일 대비 빠진 평일(결측 날짜) 체크
all_bdays = pd.date_range(df['dt'].min(), df['dt'].max(), freq='B')
missing_bdays = sorted(list(set(all_bdays) - set(df['dt'])))
print(f"\n전체 평일 수: {len(all_bdays)}일 | 실제 폴더 수: {len(df)}일 | 폴더 없는 평일(공휴일+누락): {len(missing_bdays)}일")

fig, ax = plt.subplots(figsize=(13, 5.5), dpi=150)

ax.plot(df['dt'], df['valid_est'], color='#1f4e78', linewidth=1.2, label='Valid HTML Files per Day')
ax.fill_between(df['dt'], df['valid_est'], color='#1f4e78', alpha=0.12)

# 주요 결함/특이 구간 주석 표시
# 1) 초기 947개 구간
ax.axvspan(pd.to_datetime('2024-03-27'), pd.to_datetime('2024-04-12'), color='#f4b183', alpha=0.35, label='Initial Phase (947 stocks only)')
# 2) 2024-11-21~22 수집 급감일
dip_df = df[df['valid_est'] < 2000]
dip_df_later = dip_df[dip_df['dt'] > '2024-05-01']
ax.scatter(dip_df_later['dt'], dip_df_later['valid_est'], color='#c00000', zorder=5, s=45, label='Partial Collection Drop (<2,000 files)')
for _, row in dip_df_later.iterrows():
    ax.annotate(f"{row['date']}\n({row['valid_est']:,})",
                xy=(row['dt'], row['valid_est']),
                xytext=(10, -5), textcoords='offset points',
                fontsize=8.5, color='#c00000', fontweight='bold')

ax.set_title("Archive Coverage & Data Anomalies (2024-03-27 to 2026-09-02 | 591 Days, 2.40M Files)", fontsize=13, fontweight='bold', pad=12)
ax.set_xlabel("Date", fontsize=11)
ax.set_ylabel("Number of Valid HTML Files", fontsize=11)
ax.set_ylim(0, 4800)
ax.grid(True, linestyle='--', alpha=0.4)
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.xticks(rotation=30)
ax.legend(loc='lower right', frameon=True, fontsize=9.5)

plt.tight_layout()
plt.savefig("outputs/week1_archive_coverage.png")
print("\n시각화 저장 완료: outputs/week1_archive_coverage.png")
