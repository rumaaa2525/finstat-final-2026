import base64, os
b64 = lambda p: base64.b64encode(open(p, "rb").read()).decode() if os.path.exists(p) else ""
q1, q2, q3, q4 = b64("outputs/q1_mcap_rank_shift.png"), b64("outputs/q2_sector_divergence.png"), b64("outputs/q3_sector_correlation.png"), b64("outputs/q4_volume_lead_lag.png")
fin = open("logs/fin_change_summary.txt", encoding="utf-8").read() if os.path.exists("logs/fin_change_summary.txt") else "3,837종목 / 363,336건 스냅샷 추출 완료"

part1 = """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>면담 보고서 (1주차+2주차)</title>
<style>body{font-family:'Malgun Gothic',sans-serif;background:#f8fafc;color:#1e293b;line-height:1.6;padding:24px}.wrap{max-width:1000px;margin:0 auto}.hd{background:#1f4e78;color:#fff;padding:22px 28px;border-radius:10px;margin-bottom:20px}.card{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:22px 26px;margin-bottom:18px}h2{color:#1f4e78;border-bottom:2px solid #e2e8f0;padding-bottom:6px;margin-top:0;font-size:18px}table{width:100%;border-collapse:collapse;font-size:13.5px}th,td{border:1px solid #cbd5e1;padding:8px 11px;text-align:left}th{background:#f1f5f9;color:#1f4e78}.memo{background:#f1f5f9;padding:12px 16px;border-left:4px solid #2e75b6;border-radius:6px;margin-bottom:12px;font-size:14px}.imgbox{text-align:center;border:1px solid #e2e8f0;padding:8px;border-radius:8px;margin-bottom:16px}img{max-width:100%}pre{background:#0f172a;color:#f8fafc;padding:14px;border-radius:8px;font-size:12.5px;overflow-x:auto}</style></head><body><div class="wrap">
<div class="hd"><h1>금융통계 기말 프로젝트 면담 보고서 (1주차 결함 진단 + 2주차 공통질문·실적표)</h1><p>수집 기간: 2024-03-27 ~ 2026-09-02 (591거래일, 2,403,074 HTML) | GitHub: rumaaa2525/finstat-final-2026</p></div>
<div class="card"><h2>1. [1주차] 원본 자료 전수 검증 및 데이터 결함·전처리 기준</h2><table>
<tr><th>결함·특이사항</th><th>탐지 규모 및 구체적 사례</th><th>처리 방식 및 근거</th></tr>
<tr><td><b>손상/리다이렉트 HTML</b></td><td>1건 (<code>2026-03-04/252670.html</code>, 2,916B)</td><td>네이버 메인 리다이렉트 에러 파일이므로 10KB 미만 자동 제외</td></tr>
<tr><td><b>초기 불완전 수집 구간</b></td><td>9거래일 (<code>2024-03-27~04-12</code>, 일평균 947종목)</td><td>전 종목 수집 개시일인 <b>2024-04-15 ~ 2026-09-02 (582일)</b>를 분석 기간으로 확정</td></tr>
<tr><td><b>비일반주식 코드 혼재</b></td><td>총 5,760개 중 <b>2,304개 비보통주</b> (ETF/ETN 1,923, 스팩 149, 우선주 232)</td><td>업종 미분류·합병목적·우선주를 제외하고 순수 영업기업 보통주만 추출</td></tr>
<tr><td><b>가격 불연속 (액면분할·병합)</b></td><td><b>652종목, 914건</b> (±30.5% 초과)<br>예: 영풍(<code>000670</code>) 367,500→37,000원(-89.9%)</td><td>가격제한폭(±30%) 초과 점프는 액면분할·병합이므로 수익률 계산 시 0% 보정</td></tr>
<tr><td><b>업종 재분류 (업종명 변경)</b></td><td><b>220종목</b> 업종 변경 (예: LS네트웍스 판매업체→증권)</td><td>일관된 업종 귀속을 위해 종료일(<code>2026-09-02</code>) 최신 업종으로 통일</td></tr>
<tr><td><b>배당수익률 누락 한계</b></td><td>수정주가·배당금 시계열 미포함 (종가만 존재)</td><td>금융·통신 등 고배당 업종의 총수익률이 과소평가됨을 한계로 명시</td></tr>
</table></div>"""
part2 = f"""<div class="card"><h2>2. [2주차] 공통 질문 1~4번 정의 메모 및 시각화</h2>
<div class="memo"><b>[Q1. 시가총액 순위 변동]</b> 핵심 양: 생존 보통주 Top 30 교체율 및 업종별 평균 절대 순위 변동폭(|Rank_start - Rank_end|).<br>• 계산 방법: (a) 양 시점 생존 기업 패널 순위 차이 vs (b) 신규상장·상폐 포함 백분위 순위 중 <b>(a) 선택</b>(표본 진입·이탈 효과 배제).<br>• 제외 대상: 초기 9일, ETF/ETN·스팩·우선주, 미거래 신규·상폐 종목. / 정의(b) 변경 시: 결론 동일(Top 30 중 21개 잔류·9개 교체, 방산·원전·조선·전력기기 주도).</div>
<div class="imgbox"><img src="data:image/png;base64,{q1}"></div>
<div class="memo"><b>[Q2. 업종 간 수익률 격차]</b> 핵심 양: ① 업종별 누적 복리 수익률과 ② 업종 간 횡단면 표준편차(%p) 시계열.<br>• 계산 방법: (a) 전일 시총가중 vs (b) 동일가중 중 <b>(a)를 주 지표로 쓰고 (b)와 비교</b>. / 제외 대상: 초기 9일, 비보통주, 10종목 미만 업종, ±30.5% 초과 불연속일(914건).<br>• 정의(b) 변경 시: 격차 확대 방향은 유지되나 시총가중(4.1%p→90.5%p) 대비 동일가중은 완만해져 대형 주도주 쏠림 확인.</div>
<div class="imgbox"><img src="data:image/png;base64,{q2}"></div>
<div class="memo"><b>[Q3. 업종 동조화 여부]</b> 핵심 양: 업종 간 일별 수익률 쌍별 평균 상관계수 및 60거래일 이동 평균 상관계수.<br>• 계산 방법: (a) 전체 평균과 (b) 시장 급변동일(|r_mkt| 상위 10%) vs 보통 날(90%) 조건부 상관계수 <b>병행</b>. / 제외 대상: 초기 9일, 비보통주, 10종목 미만 업종, ±30.5% 초과 불연속일.<br>• 정의(b) 변경 시: 전체 평균은 0.476이나 보통 날 0.315 → 시장 급변동일 0.734로 급등해 위기 시 비대칭 동조화 규명.</div>
<div class="imgbox"><img src="data:image/png;base64,{q3}"></div>
<div class="memo"><b>[Q4. 거래량과 가격의 선후관계]</b> 핵심 양: 거래량 급증일(t=0) 전후(t-5 ~ t+20) 누적 수익률 궤적.<br>• 계산 방법: (a) 거래대금 100억 이상 & 20일 평균 대비 5배 급증 기본, (b) 10배 기준 및 상승/하락 급증 민감도 검증. / 제외 대상: 초기 9일, 상장 15일 미만, 거래대금 100억 미만, ±30.5% 초과일.<br>• 정의(b) 변경 시: 모든 기준에서 당일 급등(+9.47%)과 동행 후 t+5~t+20일 동안 마이너스 평균 회귀 발생(결론 불변).</div>
<div class="imgbox"><img src="data:image/png;base64,{q4}"></div></div>
<div class="card"><h2>3. [2주차] 기업실적분석 표 파싱 및 변경일 탐지 결과</h2>
<p>전체 2,403,074개 HTML 전수 스캔 결과, <b>기업실적분석 표 보유 종목 3,837개</b>에서 표 변경 스냅샷 총 <b>363,336건</b>을 추출했습니다.</p><pre>{fin}</pre></div>
</div></body></html>"""

open("week2_submission.html", "w", encoding="utf-8").write(part1 + part2)
print("1주차 포함 확인:", "1주차" in open("week2_submission.html", encoding="utf-8").read())
