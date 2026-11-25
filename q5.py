import os
import glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

# 서버 내 한글 폰트 자동 탐색 및 등록
font_candidates = []
for pattern in ['*Nanum*.ttf', '*NotoSansCJK*.ttc', '*NotoSansKR*.otf', '*UnDotum*.ttf', '*Baekmuk*.ttf', '*Malgun*.ttf']:
    font_candidates.extend(glob.glob(f'/usr/share/fonts/**/{pattern}', recursive=True))
    font_candidates.extend(glob.glob(os.path.expanduser(f'~/.local/share/fonts/**/{pattern}'), recursive=True))

if font_candidates:
    font_path = font_candidates[0]
    fm.fontManager.addfont(font_path)
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rcParams['font.family'] = font_name
    print(f"[사용 폰트] {font_name} ({font_path})")
else:
    print("[경고] 서버에 한글 폰트가 없습니다. 아래 '한글 폰트 설치' 안내를 참고하세요.")

plt.rcParams['axes.unicode_minus'] = False
plt.style.use('seaborn-v0_8-whitegrid')
if font_candidates:
    plt.rcParams['font.family'] = font_name  # style.use 이후 폰트 재적용 필수

sectors = ['반도체', '자동차', '조선', '바이오', '금융', '유통', '철강', '화학']
opm_initial = [12.0, 7.0, -2.7, 16.5, 20.0, 4.9, 6.9, 6.7]
opm_change = [6.5, 1.2, 8.1, -1.5, 2.0, -0.8, -2.1, -3.5]
cum_return = [45.2, 18.5, 62.0, 25.4, 31.0, -5.2, -12.4, -18.0]

intra_high_opm_ret = [52.0, 22.1, 70.5, 34.0, 35.2, 1.5, -6.0, -10.2]
intra_low_opm_ret = [31.4, 14.0, 48.2, 12.5, 24.8, -11.4, -18.5, -24.0]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

sc = ax1.scatter(
    opm_initial, cum_return,
    s=np.abs(opm_change) * 70 + 120,
    c=opm_change, cmap='RdYlBu_r', alpha=0.85, edgecolors='black', linewidth=1.2
)
for i, txt in enumerate(sectors):
    ax1.annotate(
        f"{txt}\n({opm_change[i]:+.1f}%p)",
        (opm_initial[i], cum_return[i]),
        xytext=(6, 6), textcoords='offset points', fontsize=9, fontweight='bold'
    )
ax1.axhline(0, color='gray', linestyle='--', linewidth=1)
ax1.axvline(np.mean(opm_initial), color='gray', linestyle=':', linewidth=1)
cbar = plt.colorbar(sc, ax=ax1)
cbar.set_label('영업이익률 개선폭 (%p)', fontsize=10)
ax1.set_title('업종 간: 기초 이익률 vs 누적 수익률 (색상: 개선폭)', fontsize=12, fontweight='bold')
ax1.set_xlabel('기초 영업이익률 (%)', fontsize=10.5)
ax1.set_ylabel('누적 수익률 (%)', fontsize=10.5)

x = np.arange(len(sectors))
width = 0.36
ax2.bar(x - width/2, intra_high_opm_ret, width, label='업종 내 상위 OPM 그룹', color='#d62728', alpha=0.85)
ax2.bar(x + width/2, intra_low_opm_ret, width, label='업종 내 하위 OPM 그룹', color='#1f77b4', alpha=0.85)
ax2.axhline(0, color='black', linewidth=0.9)
ax2.set_xticks(x)
ax2.set_xticklabels(sectors, fontsize=10)
ax2.set_title('업종 내: 고마진 종목 vs 저마진 종목 평균 수익률', fontsize=12, fontweight='bold')
ax2.set_ylabel('평균 누적 수익률 (%)', fontsize=10.5)
ax2.legend(fontsize=9.5)

plt.suptitle('Q5. 영업이익률 수준 및 개선 여부가 주가 수익률에 미친 영향', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('Q5_opm_vs_return.png', dpi=300, bbox_inches='tight')
print("저장 완료: Q5_opm_vs_return.png")
