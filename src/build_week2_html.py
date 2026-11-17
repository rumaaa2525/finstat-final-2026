import base64
import os

def img_to_base64(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

q1_img = img_to_base64("outputs/q1_mcap_rank_shift.png")
q2_img = img_to_base64("outputs/q2_sector_divergence.png")
q3_img = img_to_base64("outputs/q3_sector_correlation.png")
q4_img = img_to_base64("outputs/q4_volume_lead_lag.png")

fin_log = ""
if os.path.exists("logs/fin_change_summary.txt"):
    with open("logs/fin_change_summary.txt", "r", encoding="utf-8") as f:
        fin_log = f.read()
else:
    fin_log = "(logs/fin_change_summary.txt 파일이 아직 없으면 python3 src/05a_check_fin_changes.py > logs/fin_change_summary.txt 를 먼저 실행하세요.)"

html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2주차 면담 제출 보고서 - 금융통계 기말 프로젝트</title>
<style>
  :root {{
    --primary: #1f4e78;
    --accent: #2e75b6;
    --bg: #f8fafc;
    --card: #ffffff;
    --border: #e2e8f0;
    --text: #1e293b;
    --muted: #64748b;
  }}
  body {{
    font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: var(--bg);
    color: var(--text);
    line-height: 1.65;
    margin: 0;
    padding: 32px 20px;
  }}
  .container {{
    max-width: 1020px;
    margin: 0 auto;
  }}
  header {{
    background: linear-gradient(135deg, #1f4e78 0%, #2e75b6 100%);
    color: #fff;
    padding: 32px 36px;
    border-radius: 12px;
    margin-bottom: 28px;
    box-shadow: 0 4px 12px rgba(31, 78, 120, 0.15);
  }}
  header h1 {{
    margin: 0 0 8px 0;
    font-size: 24px;
    font-weight: 700;
  }}
  header p {{
    margin: 0;
    font-size: 14px;
    opacity: 0.9;
  }}
  .section-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 28px 32px;
    margin-bottom: 24px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.03);
  }}
  h2 {{
    color: var(--primary);
    font-size: 19px;
    margin-top: 0;
    padding-bottom: 10px;
    border-bottom: 2px solid var(--border);
  }}
  h3 {{
    color: #0f172a;
    font-size: 17px;
    margin-top: 0;
    margin-bottom: 14px;
  }}
  .badge {{
    display: inline-block;
    background: #e0f2fe;
    color: #0369a1;
    font-size: 12px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 999px;
    margin-right: 8px;
    vertical-align: middle;
  }}
  .memo-grid {{
    display: grid;
    grid-template-columns: 1fr;
    gap: 10px;
    background: #f1f5f9;
    padding: 18px 20px;
    border-radius: 8px;
    border-left: 4px solid var(--accent);
    margin-bottom: 18px;
    font-size: 14.5px;
  }}
  .memo-item strong {{
    color: var(--primary);
  }}
  .chart-box {{
    text-align: center;
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
  }}
  .chart-box img {{
    max-width: 100%;
    height: auto;
    border-radius: 4px;
  }}
  pre {{
    background: #0f172a;
    color: #f8fafc;
    padding: 18px 20px;
    border-radius: 8px;
    font-size: 13px;
    overflow-x: auto;
    line-height: 1.5;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    margin-top: 10px;
  }}
  th, td {{
    border: 1px solid var(--border);
    padding: 10px 14px;
    text-align: left;
  }}
  th {{
    background: #f1f5f9;
    color: var(--primary);
    font-weight: 700;
    width: 22%;
  }}
  @media print {{
    body {{ background: #fff; padding: 0; }}
    .section-card {{ box-shadow: none; break-inside: avoid; }}
  }}
</style>
</head>
<body>
<div class="container">

  <header>
    <h1>2주차 면담 제출: 공통 질문 1~4번 분석 및 기업실적분석 표 변경일 탐지</h1>
    <p>데이터 범위: 2024-03-27 ~ 2026-09-02 (591거래일, 총 2,403,074 HTML) | GitHub: rumaaa2525/finstat-final-2026</p>
  </header>

  <div class="section-card">
    <h2>1. 공통 전처리 및 데이터 정제 기준 (Definitions)</h2>
    <table>
      <tr>
        <th>분석 기간</th>
        <td>전체 시장(코스피+코스닥) 수집이 완비된 <strong>2024-04-15 ~ 2026-09-02 (582거래일)</strong>. 초기 불완전 수집 구간(2024-03-27 ~ 2024-04-12, 9거래일) 및 10KB 미만 에러 페이지 1건(<code>2026-03-04/252670.html</code>) 제외.</td>
      </tr>
      <tr>
        <th>분석 유니버스</th>
        <td>업종 분류가 존재하는 <strong>순수 보통주</strong> (ETF/ETN 1,923개, 스팩 149개, 우선주 232개 제외).</td>
      </tr>
      <tr>
        <th>데이터 결함 보정</th>
        <td>업종 재분류(220종목)는 분석 종료일 최신 업종으로 통일. 액면분할·병합·감자로 일일 가격제한폭(±30.5%)을 초과한 914건의 가격 불연속 수익률은 0% 보정.</td>
      </tr>
    </table>
  </div>

  <div class="section-card">
    <h3><span class="badge">공통 질문 1</span>시가총액 순위는 2년 반 동안 얼마나 바뀌었는가?</h3>
    <div class="memo-grid">
      <div class="memo-item"><strong>• 핵심 양:</strong> 시작일과 종료일 양 시점 생존 보통주의 시가총액 상위 30위 교체율 및 업종별 평균 절대 순위 변동폭(|Rank_start - Rank_end|).</div>
      <div class="memo-item"><strong>• 계산 방법 선택:</strong> (a) 양 시점 모두 거래된 동일 기업 패널 기준 절대 순위 차이 vs (b) 신규상장·상장폐지 포함 백분위 순위 변화 중 <strong>(a) 선택</strong>. 신규 진입·이탈로 인한 표본 구성 효과를 배제하고 동일 기업의 실질적 위상 변화를 비교하기 위함.</div>
      <div class="memo-item"><strong>• 계산에서 뺀 종목·날짜:</strong> 초기 9거래일, ETF/ETN·스팩·우선주, 양 시점 중 한쪽이라도 미거래된 신규상장·상장폐지 종목.</div>
      <div class="memo-item"><strong>• 정의를 (b)로 바꾸면:</strong> 결론이 바뀌지 않음 (상위 30위 중 21개 잔류·9개 신규 진입, 방산·원전·조선·전력기기 업종 주도 결론 동일).</div>
    </div>
    <div class="chart-box">
      <img src="data:image/png;base64,{q1_img}" alt="Q1 Market Cap Rank Shift">
    </div>
  </div>

  <div class="section-card">
    <h3><span class="badge">공통 질문 2</span>업종 간 수익률의 차이는 2년 반 동안 벌어졌는가, 좁혀졌는가?</h3>
    <div class="memo-grid">
      <div class="memo-item"><strong>• 핵심 양:</strong> 주요 업종별 누적 복리 수익률의 시점별 횡단면 표준편차(%p) 추이.</div>
      <div class="memo-item"><strong>• 계산 방법 선택:</strong> (a) 전일 시총가중(Cap-Weighted) 업종 수익률 누적치 표준편차 vs (b) 동일가중(Equal-Weighted) 업종 수익률 누적치 표준편차 중 <strong>(a) 선택</strong>. 실제 시장 자금이 유입되는 산업별 경제적 규모와 주도 업종의 실질 격차를 반영하기 위함.</div>
      <div class="memo-item"><strong>• 계산에서 뺀 종목·날짜:</strong> 초기 9거래일, ETF/ETN·스팩·우선주, 종목 수 15개 미만 영세 업종, ±30.5% 초과 가격 불연속 수익률(914건).</div>
      <div class="memo-item"><strong>• 정의를 (b)로 바꾸면:</strong> 방향은 바뀌지 않으나 격차 크기가 완만해짐 (말기 횡단면 표준편차가 시총가중 90.51%p 대비 낮아지나, 기간 내 지속 확대 결론은 동일).</div>
    </div>
    <div class="chart-box">
      <img src="data:image/png;base64,{q2_img}" alt="Q2 Sector Divergence">
    </div>
  </div>

  <div class="section-card">
    <h3><span class="badge">공통 질문 3</span>업종들은 같이 움직이는가, 따로 움직이는가?</h3>
    <div class="memo-grid">
      <div class="memo-item"><strong>• 핵심 양:</strong> 주요 업종 간 일별 수익률 쌍별(Pairwise) 상관계수 평균 및 60거래일 이동(Rolling) 평균 상관계수.</div>
      <div class="memo-item"><strong>• 계산 방법 선택:</strong> (a) 전체 기간 단순 피어슨 상관계수 평균과 (b) 시장 전체 수익률 절댓값 상위 10% 급변동일(|r| ≥ 3.82%) vs 보통 날(하위 90%) 조건부 상관계수를 <strong>함께 사용</strong>. 평상시 차별화와 충격 시 동반 급등락이라는 비대칭 구조를 포착하기 위함.</div>
      <div class="memo-item"><strong>• 계산에서 뺀 종목·날짜:</strong> 초기 9거래일, ETF/ETN·스팩·우선주, 종목 수 15개 미만 업종, ±30.5% 초과 가격 불연속 수익률(914건).</div>
      <div class="memo-item"><strong>• 정의를 (b)로 바꾸면:</strong> 결론이 입체적으로 보완됨 (전체 평균은 0.476이나, 보통 날 0.315에서 시장 급변동일 0.734로 급등하는 위기 시 동조화 확인).</div>
    </div>
    <div class="chart-box">
      <img src="data:image/png;base64,{q3_img}" alt="Q3 Sector Correlation">
    </div>
  </div>

  <div class="section-card">
    <h3><span class="badge">공통 질문 4</span>거래량은 가격을 앞서는가, 뒤따르는가?</h3>
    <div class="memo-grid">
      <div class="memo-item"><strong>• 핵심 양:</strong> 거래량 급증 이벤트 발생일(t=0) 수익률과 이후 t+5, t+10, t+20거래일 누적 수익률(CAR).</div>
      <div class="memo-item"><strong>• 계산 방법 선택:</strong> (a) 거래대금 100억 원 이상 & 직전 20거래일 평균 대비 거래량 5배 이상 급증을 기본으로 쓰고, (b) 배수 기준(3배·10배) 및 당일 등락 방향(상승 급증 vs 하락 급증)으로 민감도 검증.</div>
      <div class="memo-item"><strong>• 계산에서 뺀 종목·날짜:</strong> 초기 9거래일, ETF/ETN·스팩·우선주, 상장 초기 15거래일 미만 관측치, 거래대금 100억 원 미만 소형 거래일, ±30.5% 초과 가격 불연속일.</div>
      <div class="memo-item"><strong>• 정의를 (b)로 바꾸면:</strong> 바뀌지 않음 (3배·5배·10배 및 당일 등락 방향 모두 당일 가격 급변과 동행한 뒤 t+5 ~ t+20일 동안 일관되게 마이너스 평균 회귀 발생).</div>
    </div>
    <div class="chart-box">
      <img src="data:image/png;base64,{q4_img}" alt="Q4 Volume Lead-Lag">
    </div>
  </div>

  <div class="section-card">
    <h2>2. 기업실적분석 표 파싱 및 변경일 탐지 결과</h2>
    <p>전체 591거래일(2,403,074개 HTML)을 전수 스캔하여 <strong>기업실적분석 표 보유 고유 종목 3,837개</strong> 및 직전 거래일 대비 표 내용이 바뀐 스냅샷 총 <strong>363,336건</strong>을 추출했습니다.</p>
    <pre>{fin_log}</pre>
  </div>

</div>
</body>
</html>
"""

with open("week2_submission.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("단일 HTML 보고서 생성 완료: week2_submission.html (크기:", round(os.path.getsize("week2_submission.html")/1024, 1), "KB)")
