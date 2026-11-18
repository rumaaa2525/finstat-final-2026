html = open("week2_submission.html", encoding="utf-8").read()

q1_extra = """<table><tr><th>순위(종료일)</th><th>신규 진입 종목</th><th>업종</th><th>비고</th></tr>
<tr><td>11위 / 13위</td><td>한화에어로스페이스 / 두산에너빌리티</td><td>우주항공과국방 / 기계</td><td>방산·원전 주도</td></tr>
<tr><td>15위 / 26위</td><td>HD현대중공업 / 한화오션</td><td>조선</td><td>조선 슈퍼사이클</td></tr>
<tr><td>23위 / 26위</td><td>LS ELECTRIC / HD현대일렉트릭 / 효성중공업</td><td>전기장비</td><td>전력기기 3사 동반 진입</td></tr>
<tr><td>26위</td><td>고려아연 / 우리금융지주</td><td>비철금속 / 은행</td><td>밸류업·경영권 이슈</td></tr></table><br>"""

q2_extra = """<table><tr><th>구분</th><th>업종명 및 2년 반 누적 수익률 (시총가중 기준)</th></tr>
<tr><td><b>격차 견인 상위 5개 업종</b></td><td>반도체와반도체장비(+301.7%), 전기장비(+264.9%), 우주항공과국방(+253.5%), 전자장비와기기(+244.4%), 조선(+140.0%)</td></tr>
<tr><td><b>부진 하위 5개 업종</b></td><td>건강관리장비와용품(-36.1%), 핸드셋(-35.4%), 방송과엔터테인먼트(-35.1%), 디스플레이장비및부품(-34.4%), 소프트웨어(-32.4%)</td></tr>
<tr><td><b>업종별 순위 이동 Top 5</b></td><td>생명과학도구및서비스(평균 552.4위 이동), 양방향미디어(452.5위), 건강관리업체(452.2위), 방송과엔터(410.8위), 핸드셋(383.1위)</td></tr></table><br>"""

html = html.replace('<div class="imgbox"><img src="data:image/png;base64,', q1_extra + '<div class="imgbox"><img src="data:image/png;base64,', 1)
parts = html.split('<div class="imgbox">')
if len(parts) >= 3:
    parts[2] = q2_extra + '<div class="imgbox">' + parts[2]
    html = parts[0] + '<div class="imgbox">' + parts[1] + parts[2]

open("week2_submission.html", "w", encoding="utf-8").write(html)
