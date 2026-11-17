import os
import re
import time
import pickle
from bs4 import BeautifulSoup
from concurrent.futures import ProcessPoolExecutor, as_completed

BASE_DIR = "/mnt/data/stock"
OUT_DIR = "data_processed"
os.makedirs(OUT_DIR, exist_ok=True)

def process_date_financials(date_str):
    folder = os.path.join(BASE_DIR, date_str)
    files = sorted([f for f in os.listdir(folder) if f.endswith(".html")])
    
    cop_records = {}
    for fn in files:
        fpath = os.path.join(folder, fn)
        if os.path.getsize(fpath) < 10240:
            continue
            
        code = fn[:-5]
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                html = f.read()
        except Exception:
            continue

        idx_cap = html.find("기업실적분석 테이블")
        if idx_cap == -1:
            continue
            
        # 캡션 직전 <table 부터 </table> 까지 슬라이싱
        idx_tbl_start = html.rfind("<table", max(0, idx_cap - 300), idx_cap)
        idx_tbl_end = html.find("</table>", idx_cap)
        if idx_tbl_start == -1 or idx_tbl_end == -1:
            continue
            
        tbl_html = html[idx_tbl_start:idx_tbl_end + 8]
        soup_tbl = BeautifulSoup(tbl_html, "html.parser")
        trs = soup_tbl.select("tr")
        if len(trs) >= 17:
            parsed_tbl = []
            for r in trs[1:]:
                parsed_tbl.append(tuple(c.get_text(strip=True) for c in r.select("th, td")))
            cop_records[code] = tuple(parsed_tbl)
            
    return date_str, cop_records

if __name__ == "__main__":
    t0 = time.time()
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    dates = sorted([d for d in os.listdir(BASE_DIR) if date_pattern.match(d) and os.path.isdir(os.path.join(BASE_DIR, d))])
    print(f"총 {len(dates)}일 기업실적분석 표 병렬 추출 시작...", flush=True)

    last_cop_sig = {}
    fin_snapshots = []  # (date, code, parsed_tbl)
    stocks_with_fin = set()

    CHUNK = 64
    for i in range(0, len(dates), CHUNK):
        batch_dates = dates[i:i+CHUNK]
        batch_results = {}
        with ProcessPoolExecutor(max_workers=64) as ex:
            futures = {ex.submit(process_date_financials, d): d for d in batch_dates}
            for fut in as_completed(futures):
                d_str, c_recs = fut.result()
                batch_results[d_str] = c_recs

        for d_str in batch_dates:
            c_recs = batch_results[d_str]
            for code, tbl_tuple in c_recs.items():
                stocks_with_fin.add(code)
                if last_cop_sig.get(code) != tbl_tuple:
                    last_cop_sig[code] = tbl_tuple
                    fin_snapshots.append((d_str, code, tbl_tuple))

        elapsed = time.time() - t0
        done_cnt = min(i + CHUNK, len(dates))
        print(f"[{done_cnt}/{len(dates)}일 완료] 재무표 보유 고유종목: {len(stocks_with_fin):,}개 | 변경 스냅샷: {len(fin_snapshots):,}건 | 경과: {elapsed:.1f}초", flush=True)

    with open(os.path.join(OUT_DIR, "financial_snapshots.pkl"), "wb") as f:
        pickle.dump(fin_snapshots, f)

    print("\n=== 기업실적분석 표 파싱 완료 ===", flush=True)
    print(f"총 소요 시간: {time.time() - t0:.1f}초")
    print(f"기업실적분석 표 보유 종목 수: {len(stocks_with_fin):,}개")
    print(f"총 변경 스냅샷 건수: {len(fin_snapshots):,}건")
