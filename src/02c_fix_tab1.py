import os
import re
import time
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed

BASE_DIR = "/mnt/data/stock"
PKL_PATH = "data_processed/daily_market.pkl"

RE_MCAP = re.compile(r'id="_market_sum"[^>]*>(.*?)</em>', re.S)
RE_SHARES = re.compile(r'상장주식수</th>\s*<td><em>([\d,]+)</em>', re.S)
RE_PER = re.compile(r'id="_per"[^>]*>([\d,.\-]+)</em>', re.S)
RE_PBR = re.compile(r'id="_pbr"[^>]*>([\d,.\-]+)</em>', re.S)
RE_DVR = re.compile(r'id="_dvr"[^>]*>([\d,.\-]+)</em>', re.S)

def parse_num(s):
    if not s:
        return None
    s = s.replace(',', '').strip()
    try:
        return float(s)
    except ValueError:
        return None

def parse_mcap(raw_inner):
    clean = re.sub(r'\s+', '', raw_inner)
    jo = 0.0
    eok = 0.0
    m_jo = re.search(r'([\d,]+)조', clean)
    if m_jo:
        jo = float(m_jo.group(1).replace(',', ''))
    m_eok = re.search(r'(?:조|^)([\d,]+)', clean)
    if m_eok:
        eok = float(m_eok.group(1).replace(',', ''))
    val = jo * 10000.0 + eok
    return val if val > 0 else None

def extract_tab1_for_date(date_str):
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

        # 실제 HTML 테이블은 파일 후반부(80000바이트 이후)에 위치
        tail = html[70000:]
        mcap = shares = per = pbr = dvr = None

        m1 = RE_MCAP.search(tail)
        if m1:
            mcap = parse_mcap(m1.group(1))
        m2 = RE_SHARES.search(tail)
        if m2:
            shares = parse_num(m2.group(1))
        m3 = RE_PER.search(tail)
        if m3:
            per = parse_num(m3.group(1))
        m4 = RE_PBR.search(tail)
        if m4:
            pbr = parse_num(m4.group(1))
        m5 = RE_DVR.search(tail)
        if m5:
            dvr = parse_num(m5.group(1))

        out.append((date_str, code, mcap, shares, per, pbr, dvr))
    return out

if __name__ == "__main__":
    t0 = time.time()
    df = pd.read_pickle(PKL_PATH)
    dates = sorted(df['date'].unique())
    print(f"총 {len(dates)}일 tab_con1 보정 추출 시작...", flush=True)

    rows = []
    with ProcessPoolExecutor(max_workers=64) as ex:
        futures = [ex.submit(extract_tab1_for_date, d) for d in dates]
        for idx, fut in enumerate(as_completed(futures), 1):
            rows.extend(fut.result())
            if idx % 100 == 0 or idx == len(dates):
                print(f"[{idx}/{len(dates)}일 완료] 경과: {time.time()-t0:.1f}초", flush=True)

    df_fix = pd.DataFrame(rows, columns=["date", "code", "market_cap", "shares", "per", "pbr", "div_yield"])
    
    # 기존 결측 컬럼 교체 및 sector 정제 ('=' 뒤 노이즈 및 공백 제거)
    df = df.drop(columns=["market_cap", "shares", "per", "pbr", "div_yield"])
    df = df.merge(df_fix, on=["date", "code"], how="left")
    
    def clean_sector(s):
        if pd.isna(s):
            return None
        s_clean = str(s).split("=")[0].strip()
        return s_clean if s_clean != "" else None

    df['sector'] = df['sector'].apply(clean_sector)
    df.to_pickle(PKL_PATH)

    stock_only = df[df['sector'].notna()]
    print("\n=== 보정 완료 및 결측률 재확인 (일반주식 기준) ===", flush=True)
    print((stock_only[['sector', 'close', 'volume', 'market_cap', 'shares', 'per', 'pbr', 'div_yield']].isna().mean() * 100).round(2))
    print(f"고유 업종 수: {stock_only['sector'].nunique()}개")
