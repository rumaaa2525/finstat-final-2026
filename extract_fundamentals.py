import os
import re
import glob
import time
import pandas as pd
from concurrent.futures import ProcessPoolExecutor

RE_TABLE = re.compile(r'<table[^>]*class="[^"]*tb_type1_ifrs[^"]*"[^>]*>(.*?)</table>', re.S)
RE_TR = re.compile(r'<tr[^>]*>(.*?)</tr>', re.S)
RE_CELL = re.compile(r'<t[hd][^>]*>(.*?)</t[hd]>', re.S)
RE_TAG = re.compile(r'<[^>]+>')

TARGET_METRICS = {
    '매출액': 'revenue',
    '영업이익': 'op_profit',
    '당기순이익': 'net_income',
    '영업이익률': 'op_margin',
    '순이익률': 'net_margin',
    'ROE(지배주주)': 'roe',
    '부채비율': 'debt_ratio',
    'EPS(원)': 'eps',
    'PER(배)': 'per',
    'BPS(원)': 'bps',
    'PBR(배)': 'pbr',
    '주당배당금(원)': 'dps',
    '시가배당률(%)': 'div_yield',
    '배당성향(%)': 'payout_ratio',
}

def clean_text(s):
    return RE_TAG.sub('', s).replace('&nbsp;', '').strip()

def parse_num(val):
    if not val or val in ('-', 'N/A', '완전잠식'):
        return None
    try:
        return float(val.replace(',', ''))
    except ValueError:
        return None

def parse_html_table(path):
    date_str = os.path.basename(os.path.dirname(path))
    fname = os.path.basename(path)
    if not fname.endswith('.html'):
        return None
    # '삼성전자_005930.html'과 '005930.html' 모두 '005930'으로 추출
    code = fname[:-5].split('_')[-1]

    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()
        
        m = RE_TABLE.search(html)
        if not m:
            return None
        
        trs = RE_TR.findall(m.group(1))
        if len(trs) < 5:
            return None

        # 1번째 행(인덱스 0)에서 연간/분기 컬럼 개수 파악 (보통 연간 4, 분기 6)
        top_cells = [c for c in RE_CELL.findall(trs[0])]
        annual_cnt = 4
        for tc in top_cells:
            if '연간' in clean_text(tc):
                cs = re.search(r'colspan=["\']?(\d+)', tc)
                if cs:
                    annual_cnt = int(cs.group(1))

        headers = [clean_text(c) for c in RE_CELL.findall(trs[1])]
        n_cols = len(headers)
        if n_cols == 0:
            return None

        raw_rows = {}
        for tr in trs[3:]:
            cells = [clean_text(c) for c in RE_CELL.findall(tr)]
            if len(cells) >= n_cols + 1 and cells[0] in TARGET_METRICS:
                raw_rows[TARGET_METRICS[cells[0]]] = [parse_num(x) for x in cells[1:n_cols+1]]

        if not raw_rows:
            return None

        records = []
        for idx, h in enumerate(headers):
            if not h:
                continue
            period_type = 'Y' if idx < annual_cnt else 'Q'
            is_est = 1 if '(E)' in h else 0
            fiscal_period = h.replace('(E)', '').strip()

            rec = [date_str, code, period_type, fiscal_period, is_est]
            for key in TARGET_METRICS.values():
                vals = raw_rows.get(key)
                rec.append(vals[idx] if vals and idx < len(vals) else None)
            records.append(tuple(rec))

        return (code, date_str, records)
    except Exception:
        return None

if __name__ == '__main__':
    t0 = time.time()
    files = sorted(glob.glob("/mnt/data/stock/*/*.html"))
    files = [f for f in files if len(os.path.basename(os.path.dirname(f))) == 10]
    total = len(files)
    print(f"총 {total:,}개 파일에서 기업실적분석 표 추출 시작...", flush=True)

    last_snapshot = {}
    last_date_seen = {}
    saved_rows = []

    cols = ['Date', 'Code', 'PeriodType', 'FiscalPeriod', 'IsEstimate'] + list(TARGET_METRICS.values())

    with ProcessPoolExecutor(max_workers=8) as ex:
        for i, res in enumerate(ex.map(parse_html_table, files, chunksize=1000), 1):
            if res is not None:
                code, date_str, records = res
                sig = tuple(r[1:] for r in records)
                prev_sig = last_snapshot.get(code)

                if prev_sig is None:
                    for r in records:
                        saved_rows.append(r + ('first_obs',))
                    last_snapshot[code] = sig
                elif sig != prev_sig:
                    for r in records:
                        saved_rows.append(r + ('changed',))
                    last_snapshot[code] = sig
                
                last_date_seen[code] = (date_str, records)

            if i % 200000 == 0:
                elapsed = time.time() - t0
                rem = (total - i) / (i / elapsed)
                print(f"진행: {i:,}/{total:,} ({i/total*100:.1f}%) | 추출행: {len(saved_rows):,} | 남은시간: 약 {rem/60:.1f}분", flush=True)

    for code, (date_str, records) in last_date_seen.items():
        for r in records:
            saved_rows.append(r + ('last_obs',))

    out_df = pd.DataFrame(saved_rows, columns=cols + ['EventFlag']).drop_duplicates(
        subset=['Date', 'Code', 'PeriodType', 'FiscalPeriod', 'IsEstimate']
    )
    out_path = os.path.expanduser("~/fundamentals_events.csv")
    out_df.to_csv(out_path, index=False)
    print(f"완료! 총 {len(out_df):,}행 저장 -> {out_path} (소요시간: {(time.time()-t0)/60:.1f}분)")
