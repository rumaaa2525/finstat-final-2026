import os
import re
import time
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed

BASE_DIR = "/mnt/data/stock"
PKL_PATH = "data_processed/daily_market.pkl"

RE_SEC = re.compile(r'업종명\s*:\s*<a[^>]*>([^<]+)</a>', re.S)

def extract_sector_for_date(date_str):
    folder = os.path.join(BASE_DIR, date_str)
    files = [f for f in os.listdir(folder) if f.endswith(".html")]
    out = []
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

        m = RE_SEC.search(html)
        sec = m.group(1).strip() if m else None
        out.append((date_str, code, sec))
    return out

if __name__ == "__main__":
    t0 = time.time()
    df = pd.read_pickle(PKL_PATH)
    dates = sorted(df['date'].unique())
    print(f"총 {len(dates)}일 정확한 업종명 추출 시작...", flush=True)

    rows = []
    with ProcessPoolExecutor(max_workers=64) as ex:
        futures = [ex.submit(extract_sector_for_date, d) for d in dates]
        for idx, fut in enumerate(as_completed(futures), 1):
            rows.extend(fut.result())
            if idx % 150 == 0 or idx == len(dates):
                print(f"[{idx}/{len(dates)}일 완료] 경과: {time.time()-t0:.1f}초", flush=True)

    df_sec = pd.DataFrame(rows, columns=["date", "code", "sector"])
    df = df.drop(columns=["sector"]).merge(df_sec, on=["date", "code"], how="left")
    df.to_pickle(PKL_PATH)

    stock_only = df[df['sector'].notna()]
    print("\n=== 업종명 보정 최종 결과 ===", flush=True)
    print(f"업종명 보유 행 수: {len(stock_only):,}행 | 고유 종목코드: {stock_only['code'].nunique():,}개")
    print(f"총 고유 업종 수: {stock_only['sector'].nunique()}개")
    print("\n[상위 10개 업종 (고유 종목 수 기준)]")
    print(stock_only.groupby('sector')['code'].nunique().sort_values(ascending=False).head(10))

    # 업종 재분류(업종명 변경) 종목 탐색
    sec_chg = stock_only.groupby('code')['sector'].nunique()
    chg_codes = sec_chg[sec_chg > 1].index
    print(f"\n[결함 탐색: 분석 기간 중 업종명이 바뀐 종목 수 = {len(chg_codes)}개]")
    for c in chg_codes[:10]:
        nm = stock_only[stock_only['code'] == c]['name'].iloc[-1]
        secs = stock_only[stock_only['code'] == c]['sector'].unique().tolist()
        print(f"  - {nm}({c}): {secs}")
