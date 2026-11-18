import base64, re

def embed_img(path, alt):
    b64 = base64.b64encode(open(path, "rb").read()).decode("utf-8")
    return f'<div class="imgbox"><img src="data:image/png;base64,{b64}" alt="{alt}" style="max-width:100%; height:auto; border:1px solid #ddd; border-radius:6px;"></div>'

q1_to_q4_section = f"""
<h2>2. [2주차] 공통 질문 1~4번 정의 메모 및 시각화</h2>

<div class="memo"><b>[Q1. 시가총액 상위 30위 변화 및 순위 이동]</b> 핵심 양: 시작일(2024-03-27) 대비 종료일(2026-09-02) 기준 시가총액 Top 30 유지·교체 종목 수 및 업종별 평균 절대 순위 변동폭.<br>
• 계산 방법: (a) 전체 상장사 시가총액 순위 비교(유지 21개, 신규 진입 9개) 및 (b) 15종목 이상 업종별 평균 순위 변동폭 산출.<br>
• 제외 대상: 상장폐지·신규상장 등 양 시점 불완전 관측 종목 및 우선주/리츠 등 비보통주.</div>
<table><tr><th>순위(종료일)</th><th>신규 진입 종목</th><th>업종</th><th>비고</th></tr>
<tr><td>11위 / 13위</td><td>한화에어로스페이스 / 두산에너빌리티</td><td>우주항공과국방 / 기계</td><td>방산·원전 주도</td></tr>
<tr><td>15위 / 26위</td><td>HD현대중공업 / 한화오션</td><td>조선</td><td>조선 슈퍼사이클</td></tr>
<tr><td>23위 / 26위</td><td>LS ELECTRIC / HD현대일렉트릭 / 효성중공업</td><td>전기장비</td><td>전력기기 3사 동반 진입</td></tr>
<tr><td>26위</td><td>고려아연 / 우리금융지주</td><td>비철금속 / 은행</td><td>밸류업·경영권 이슈</td></tr></table>
{embed_img("outputs/q1_chart.png", "Q1")}

<div class="memo"><b>[Q2. 업종별 수익률 격차 확대 및 순위 이동]</b> 핵심 양: 10종목 이상 업종의 누적 수익률 격차 및 일별 횡단면 표준편차 추이.<br>
• 계산 방법: (a) 업종별 시가총액 가중·동일가중 누적 수익률 상위 5개 vs 하위 5개 비교 및 (b) 일별 업종 간 수익률 분산도 시계열 추적.<br>
• 제외 대상: 초기 9거래일, 10종목 미만 영세 업종, 액면분할·병합으로 인한 ±30.5% 초과 불연속 수익률 일자.</div>
<table><tr><th>구분</th><th>업종명 및 2년 반 누적 수익률</th></tr>
<tr><td><b>격차 견인 상위 5개</b></td><td>반도체와반도체장비(+301.7%), 전기장비(+264.9%), 우주항공과국방(+253.5%), 전자장비와기기(+244.4%), 조선(+140.0%)</td></tr>
<tr><td><b>부진 하위 5개</b></td><td>건강관리장비(-36.1%), 핸드셋(-35.4%), 방송과엔터(-35.1%), 디스플레이장비(-34.4%), 소프트웨어(-32.4%)</td></tr></table>
{embed_img("outputs/q2_chart.png", "Q2")}

<div class="memo"><b>[Q3. 업종 동조화 여부]</b> 핵심 양: 업종 간 일별 수익률 쌍별 평균 상관계수 및 60거래일 이동 평균 상관계수.<br>
• 계산 방법: (a) 전체 기간 평균(0.476)과 (b) 시장 급변동일(|r_mkt| 상위 10%) vs 보통 날(90%) 조건부 상관계수 <b>병행</b>.<br>
• 제외 대상: 초기 9일, 비보통주, 10종목 미만 업종, ±30.5% 초과 불연속일. / 정의(b) 변경 시: 보통 날 0.315 → 시장 급변동일 0.734로 급등해 위기 시 비대칭 동조화 규명.</div>
{embed_img("outputs/q3_chart.png", "Q3")}

<div class="memo"><b>[Q4. 거래량과 가격의 선후관계]</b> 핵심 양: 거래량 급증일(t=0) 전후(t-5 ~ t+20) 누적 수익률 궤적.<br>
• 계산 방법: (a) 거래대금 100억 이상 & 20일 평균 대비 거래량 5배 이상 급증 기본, (b) 10배 기준 및 상승/하락 급증 민감도 검증.<br>
• 제외 대상: 초기 9일, 상장 15일 미만, 거래대금 100억 미만, ±30.5% 초과일. / 정의(b) 변경 시: 모든 기준에서 당일 급등(+9.47%) 동행 후 t+5~t+20일 마이너스 평균 회귀 발생(결론 불변).</div>
{embed_img("outputs/q4_chart.png", "Q4")}
"""

html = open("week2_submission.html", encoding="utf-8").read()
pattern = r'<h2>2\. \[2주차\].*?(?=<div class="card"><h2>3\. \[2주차\]|<h2>3\. \[2주차\])'
if re.search(pattern, html, flags=re.S):
    html = re.sub(pattern, q1_to_q4_section + '</div><div class="card">', html, count=1, flags=re.S)
else:
    html = html.replace('</body>', '<div class="card">' + q1_to_q4_section + '</div></body>', 1)

open("week2_submission.html", "w", encoding="utf-8").write(html)
print("파트 2 완료! 포함된 차트:", re.findall(r'alt="(Q[1-4])"', html))
