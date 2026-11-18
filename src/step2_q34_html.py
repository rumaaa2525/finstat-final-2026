import os, json, base64, re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd, numpy as np

plt.rcParams['axes.unicode_minus'] = False
df = pd.read_pickle("data_processed/clean_q.pkl").sort_values(['code', 'date'])
df['rc'] = df['ret'].fillna(0.0)
meta = json.load(open("outputs/q12_meta.json", encoding="utf-8"))

# ================= [Q3 계산: (a) 전체 기간 상관 vs (b) 급변동일 조건부 상관] =================
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
ax1.set_ylabel("60-Day Rolling Pairwise Correlation"); ax1.set_title("Q3-A. Rolling Cross-Sector Correlation", fontweight='bold'); ax1.legend(); ax1.grid(alpha=0.3)

bars = ax2.bar(['Normal Days (90%)', 'Market Shock (Top 10%)'], [c_norm, c_high], color=['#5b9bd5', '#c00000'], width=0.45)
for b in bars: ax2.text(b.get_x()+b.get_width()/2, b.get_height()+0.015, f"{b.get_height():.3f}", ha='center', fontweight='bold')
ax2.set_ylim(0, 0.9); ax2.set_ylabel("Conditional Pairwise Correlation"); ax2.set_title("Q3-B. Normal vs Market Shock Correlation", fontweight='bold'); ax2.grid(axis='y', alpha=0.3)
plt.tight_layout(); plt.savefig("outputs/q3_def.png"); plt.close()

# ================= [Q4 계산: (a) 거래량 5배 vs (b) 거래량 10배 & 방향 분해] =================
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

def embed(path, alt):
    b64 = base64.b64encode(open(path, "rb").read()).decode("utf-8")
    return f'<div class="imgbox"><img src="data:image/png;base64,{b64}" alt="{alt}" style="max-width:100%; height:auto; border:1px solid #ddd; border-radius:6px;"></div>'

section_html = f"""
<h2>2. [2주차] 공통 질문 1~4번 정의 메모 및 시각화</h2>

<div class="memo">
<b>[Q1. 시가총액 순위는 2년 반 동안 얼마나 바뀌었는가]</b><br>
• <b>핵심 양:</b> (1) 시작일(2024-03-27) 상위 30위 종목의 종료일(2026-09-02) 잔류 수, (2) 업종별 종목 시가총액 순위 이동의 크기.<br>
• <b>계산 방법:</b> (a) 절대 순위 차이(|종료 순위 - 시작 순위|)의 업종별 평균, (b) 상대 순위 변화율(|종료 순위 - 시작 순위|/시작 순위)의 업종별 평균이 있고, 나는 <b>(a) 절대 순위 차이</b>를 기본으로 쓰되 (b)와 비교한다. 이유는 직관적인 계단 이동 폭을 보기에 (a)가 명확하기 때문이다.<br>
• <b>계산에서 뺀 종목·날짜:</b> 양 시점 중 한쪽이라도 결측인 신규상장·상장폐지 종목, 우선주·리츠 등 비보통주, 15종목 미만 소형 업종. 이유: 생존/신규 편입 착시와 소수 종목 왜곡을 막기 위함.<br>
• <b>정의를 (b)로 바꾸면 결론이 바뀌는가:</b> <b>바뀐다.</b> (a)에서는 중하위권 종목이 많은 <b>{meta['q1_top_abs']}</b>(평균 {meta['q1_top_abs_v']}위 이동)이 1위지만, 상위권 체급 변동을 크게 반영하는 (b)로 바꾸면 <b>{meta['q1_top_pct']}</b>(평균 {meta['q1_top_pct_v']}% 변동)이 1위로 올라선다.<br>
• <b>▶ 한 문장 결론:</b> 2년 반 동안 상위 30위 중 <b>{meta['q1_ret']}개만 유지되고 {meta['q1_new']}개가 방산·조선·전력기기 중심으로 교체</b>되었으며, 순위 변동 폭은 중소형주 중심 업종에서 가장 컸다.
</div>
<table><tr><th>순위(종료일)</th><th>신규 진입 종목 (9개)</th><th>업종</th><th>비고</th></tr>
<tr><td>11위 / 13위</td><td>한화에어로스페이스 / 두산에너빌리티</td><td>우주항공과국방 / 기계</td><td>방산·원전 주도</td></tr>
<tr><td>15위 / 26위</td><td>HD현대중공업 / 한화오션</td><td>조선</td><td>조선 슈퍼사이클</td></tr>
<tr><td>23위 / 26위</td><td>LS ELECTRIC / HD현대일렉트릭 / 효성중공업</td><td>전기장비</td><td>전력기기 3사 동반 진입</td></tr>
<tr><td>26위</td><td>고려아연 / 우리금융지주</td><td>비철금속 / 은행</td><td>밸류업·경영권 이슈</td></tr></table>
{embed("outputs/q1_def.png", "Q1")}

<div class="memo">
<b>[Q2. 업종 간 수익률의 차이는 2년 반 동안 벌어졌는가, 좁혀졌는가]</b><br>
• <b>핵심 양:</b> (1) 업종별 일별·누적 수익률, (2) 시점별 업종 간 누적 수익률의 횡단면 표준편차(퍼짐).<br>
• <b>계산 방법:</b> 업종 수익률은 (a) 전일 시가총액 가중 평균과 (b) 동일 가중 평균이 있고, 나는 <b>(a) 시총 가중</b>을 주 지표로 쓰며 (b)를 함께 비교한다. 이유는 실제 시장 자금 쏠림과 주도 섹터의 지수 견인력을 반영하기 때문이다. 분산은 누적 수익률의 일별 횡단면 표준편차를 쓴다.<br>
• <b>계산에서 뺀 종목·날짜:</b> 초기 9거래일, 일별 수익률 ±30.5% 초과 불연속일(액면분할·감자), 10종목 미만 영세 업종, 배당(종가 기준이므로 고배당 업종 과소평가 한계 명시). 이유: 가격 점프 왜곡과 단일 종목 쏠림을 배제하기 위함.<br>
• <b>정의를 (b) 동일 가중으로 바꾸면 결론이 바뀌는가:</b> <b>격차의 크기가 크게 바뀐다.</b> (a) 시총 가중 기준 표준편차는 {meta['q2_cap_std_s']}%p에서 <b>{meta['q2_cap_std_e']}%p</b>까지 폭증하지만, (b) 동일 가중으로 바꾸면 <b>{meta['q2_eq_std_e']}%p</b>로 절반 이하로 줄어든다. 즉, 업종 격차 확대는 업종 내 초대형 주도주가 견인한 결과다.<br>
• <b>▶ 한 문장 결론:</b> 업종 간 수익률 격차는 2년 반 동안 <b>크게 벌어졌으며(표준편차 {meta['q2_cap_std_e']}%p)</b>, 반도체·전기장비·우주항공·전자장비·조선 상위 5개 업종의 대형주가 이 확대를 주도했다.
</div>
<table><tr><th>구분</th><th>업종명 및 2년 반 누적 수익률 (시총가중 기준)</th></tr>
<tr><td><b>격차 견인 상위 5개</b></td><td>반도체와반도체장비(+301.7%), 전기장비(+264.9%), 우주항공과국방(+253.5%), 전자장비와기기(+244.4%), 조선(+140.0%)</td></tr>
<tr><td><b>부진 하위 5개</b></td><td>건강관리장비(-36.1%), 핸드셋(-35.4%), 방송과엔터(-35.1%), 디스플레이장비(-34.4%), 소프트웨어(-32.4%)</td></tr></table>
{embed("outputs/q2_def.png", "Q2")}

<div class="memo">
<b>[Q3. 업종들은 같이 움직이는가, 따로 움직이는가]</b><br>
• <b>핵심 양:</b> 10종목 이상 업종 간 일별 수익률의 쌍별(Pairwise) 평균 상관계수 및 60거래일 이동 평균 상관계수.<br>
• <b>계산 방법:</b> (a) 전체 기간 무조건부 평균 상관계수와 (b) 시장 급변동일(|시장수익률| 상위 10%) vs 보통 날(하위 90%) 조건부 상관계수가 있고, 나는 <b>(b) 조건부 비교를 핵심 분석으로 병행</b>한다. 이유는 시장 국면에 따른 동조화 비대칭성을 포착하기 위함이다.<br>
• <b>계산에서 뺀 종목·날짜:</b> 초기 9거래일, 비보통주, 10종목 미만 업종, ±30.5% 초과 불연속일. 이유: 업종 지수 내 극단치로 인한 허위 상관을 제거하기 위함.<br>
• <b>정의를 (b)로 바꾸면 결론이 바뀌는가:</b> <b>결론이 정반대로 바뀐다.</b> (a) 전체 평균({c_all:.3f})만 보면 중간 정도 동조화로 보이나, (b)로 나누면 <b>보통 날에는 {c_norm:.3f}로 각자 따로 움직이다가 시장이 크게 흔들리는 날에만 {c_high:.3f}로 급등</b>하며 강하게 동조화된다.<br>
• <b>▶ 한 문장 결론:</b> 업종들은 평소에는 <b>서로 따로 움직이지만(상관계수 {c_norm:.3f}), 시장 급변동일에는 일제히 같이 움직이는(상관계수 {c_high:.3f}) 비대칭적 동조화</b>를 보인다.
</div>
{embed("outputs/q3_def.png", "Q3")}

<div class="memo">
<b>[Q4. 거래량은 가격을 앞서는가, 뒤따르는가]</b><br>
• <b>핵심 양:</b> 거래량 급증 이벤트 발생일(t=0) 전후(t-5 ~ t+20)의 평균 누적 수익률 궤적.<br>
• <b>계산 방법:</b> 급증 정의로 (a) 거래대금 100억 원 이상 & 직전 20일 평균 대비 거래량 5배 이상과 (b) 10배 이상 및 상승/하락 급증 분해 기준이 있고, 나는 <b>(a) 5배 기준</b>을 주 정의로 쓰되 (b)와 비교한다. 이유는 충분한 표본 수(n={nb:,})와 유동성 하한을 동시에 확보하기 위함이다.<br>
• <b>계산에서 뺀 종목·날짜:</b> 초기 9일, 상장 15일 미만, 거래대금 100억 원 미만 소형주, ±30.5% 초과일. 이유: 거래정지 해제나 저유동성 종목의 호가 공백 착시를 막기 위함.<br>
• <b>정의를 (b)로 바꾸면 결론이 바뀌는가:</b> <b>바뀌지 않는다.</b> 10배 기준(n={n10:,})으로 강화하거나 상승/하락 급증으로 나누어도, 거래량 급증은 가격을 선행하지 않고 <b>t=0 당일 가격 급등({pb[5]:+.2f}%)과 동행한 뒤 t+5일({pb[10]:.2f}%), t+10일({pb[15]:.2f}%), t+20일({pb[25]:.2f}%) 모두 단기 과열 해소(음의 수익률 반전)</b>가 나타난다.<br>
• <b>▶ 한 문장 결론:</b> 거래량 급증은 미래 주가 상승을 선행하기보다 <b>당일 가격 급등과 동행한 뒤 이후 5·10·20거래일 동안 단기 차익실현(평균 회귀)이 뒤따르는 패턴</b>을 보인다.
</div>
{embed("outputs/q4_def.png", "Q4")}
"""

html = open("week2_submission.html", encoding="utf-8").read()
pattern = r'<h2>2\. \[2주차\].*?(?=<div class="card"><h2>3\. \[2주차\]|<h2>3\. \[2주차\])'
if re.search(pattern, html, flags=re.S):
    html = re.sub(pattern, section_html + '</div><div class="card">', html, count=1, flags=re.S)
else:
    html = html.replace('</body>', '<div class="card">' + section_html + '</div></body>', 1)

open("week2_submission.html", "w", encoding="utf-8").write(html)
print("2단계 완료! 반영된 차트:", re.findall(r'alt="(Q[1-4])"', html))
