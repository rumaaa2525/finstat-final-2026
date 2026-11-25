import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

# 1. 필요한 컬럼만 메모리 효율적으로 로드 (357만 행 최적화)
use_cols = ['Date', 'PeriodType', 'IsEstimate', 'roe', 'pbr', 'EventFlag']
df = pd.read_csv('/home/s202325492/fundamentals_events.csv', usecols=use_cols)

# --- 차트 1: 연월별 관측치 및 EventFlag 분포 ---
df['YearMonth'] = df['Date'].astype(str).str.slice(0, 7)
monthly_counts = df.groupby(['YearMonth', 'EventFlag']).size().unstack(fill_value=0)

plt.figure(figsize=(12, 5))
monthly_counts.plot(kind='bar', stacked=True, ax=plt.gca(), colormap='viridis', width=0.8)
plt.title('Monthly Fundamentals Observations by EventFlag', fontsize=13, fontweight='bold')
plt.xlabel('Year-Month')
plt.ylabel('Number of Rows')
plt.xticks(rotation=45, ha='right')
# x축 라벨이 너무 촘촘할 경우 간격 조정
ax = plt.gca()
if len(monthly_counts) > 20:
    step = max(1, len(monthly_counts) // 15)
    for idx, label in enumerate(ax.xaxis.get_ticklabels()):
        if idx % step != 0:
            label.set_visible(False)
plt.legend(title='EventFlag')
plt.tight_layout()
plt.savefig('events_timeline.png', dpi=300)
plt.close()

# --- 차트 2: Actual vs Estimate ROE & PBR 분포 비교 (이상치 제거) ---
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

actual = df[df['IsEstimate'] == 0]
est = df[df['IsEstimate'] == 1]

# ROE (-50% ~ 50% 구간)
axes[0].hist(actual['roe'].dropna().clip(-50, 50), bins=50, alpha=0.6, label='Actual (0)', density=True, color='steelblue')
axes[0].hist(est['roe'].dropna().clip(-50, 50), bins=50, alpha=0.6, label='Estimate (1)', density=True, color='coral')
axes[0].set_title('ROE Distribution (Clipped: -50 to 50)', fontweight='bold')
axes[0].set_xlabel('ROE (%)')
axes[0].set_ylabel('Density')
axes[0].legend()

# PBR (0 ~ 5배 구간)
axes[1].hist(actual['pbr'].dropna().clip(0, 5), bins=50, alpha=0.6, label='Actual (0)', density=True, color='steelblue')
axes[1].hist(est['pbr'].dropna().clip(0, 5), bins=50, alpha=0.6, label='Estimate (1)', density=True, color='coral')
axes[1].set_title('PBR Distribution (Clipped: 0 to 5)', fontweight='bold')
axes[1].set_xlabel('PBR (x)')
axes[1].legend()

plt.tight_layout()
plt.savefig('fundamentals_summary.png', dpi=300)
plt.close()

print("저장 완료: events_timeline.png, fundamentals_summary.png")
