import os
import re
import time
import pickle
import pandas as pd
from bs4 import BeautifulSoup
from concurrent.futures import ProcessPoolExecutor, as_completed

BASE_DIR = "/mnt/data/stock"
OUT_DIR = "data_processed"
LOG_DIR = "logs"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# 정규표현식 사전 컴파일 (초고속 추출용)
RE_BLIND = re.compile(r'<dl class="blind">(.*?)</dl>', re.S)
RE_DD = re.compile(r'<dd>(.*?)</dd>', re.S)
RE_SECTOR = re.compile(r'업종명\s*:\s*([^｜|<]+)')
RE_TAB1 = re.compile(r'<div class="tab_con1">(.*?)<div class="section cop_analysis"', re.S)
RE_COP = re.compile(r'<div class="section cop_analysis">(.*?)</div>\s*</div>', re.S)

def parse_num(text):
    if not text:
        return None
    s = re.sub(r'[^\d.\-]', '', text.replace(',', ''))
    if s in ('', '-', '.', '-.'):
        return None
    try:
        return float(s)
    except ValueError:
        return None

def parse_market_cap(text):
    # 예: "490조 7,161 억원" -> 4907161.0 (단위: 억원)
    if not text:
        return None
    clean = re.sub(r'\s+', '', text)
    jo = 0.0
    eok = 0.0
    m_jo = re.search(r'([\d,]+)조', clean)
    if m_jo:
        jo = float(m_jo.group(1).replace(',', ''))
    m_eok = re.search(r'(?:조)?([\d,]+)억', clean)
    if m_eok:
        eok = float(m_eok.group(1).replace(',', ''))
    val = jo * 10000.0 + eok
    return val if val > 0 else None

def process_single_date(date_str):
    folder = os.path.join(BASE_DIR, date_str)
    files = sorted([f for f in os.listdir(folder) if f.endswith(".html")])
    
    daily_rows = []
    cop_records = {}  # code -> raw_table_sig + parsed_rows
    errors = []
    
    for fn in files:
        fpath = os.path.join(folder, fn)
        code = fn[:-5]
        
        if os.path.getsize(fpath) < 10240:
            errors.append((date_str, code, "SMALL_OR_ERROR_PAGE", os.path.getsize(fpath)))
            continue
            
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                html = f.read()
        except Exception as e:
            errors.append((date_str, code, f"READ_ERR:{e}", 0))
            continue

        # 1. dl.blind 추출
        m_blind = RE_BLIND.search(html)
        if not m_blind:
            errors.append((date_str, code, "NO_BLIND_TAG", len(html)))
            continue
            
        dds = [re.sub(r'<[^>]+>', '', x).strip() for x in RE_DD.findall(m_blind.group(1))]
        name = None
        market = None
        close_p = prev_p = open_p = high_p = low_p = volume = None
        
        for item in dds:
            if item.startswith("종목명 "):
                name = item[4:].strip()
            elif item.startswith("종목코드 "):
                parts = item.split()
                if len(parts) >= 3:
                    market = parts[2]
            elif item.startswith("현재가 "):
                parts = item.split()
                if len(parts) >= 2:
                    close_p = parse_num(parts[1])
            elif item.startswith("전일가 "):
                prev_p = parse_num(item[4:])
            elif item.startswith("시가 "):
                open_p = parse_num(item[3:])
            elif item.startswith("고가 "):
                high_p = parse_num(item[3:])
            elif item.startswith("저가 "):
                low_p = parse_num(item[3:])
            elif item.startswith("거래량 "):
                volume = parse_num(item[4:])

        # 2. 업종명 추출
        m_sec = RE_SECTOR.search(html)
        sector = m_sec.group(1).strip() if m_sec else None

        # 3. tab_con1 (시가총액, 상장주식수, PER, PBR, 배당수익률)
        m_tab = RE_TAB1.search(html)
        mcap = shares = per = pbr = div_yield = None
        if m_tab:
            t_html = m_tab.group(1)
            # 시가총액
            m_mc = re.search(r'시가총액</th>\s*<td[^>]*>(.*?)</td>', t_html, re.S)
            if m_mc:
                mcap = parse_market_cap(re.sub(r'<[^>]+>', ' ', m_mc.group(1)))
            # 상장주식수
            m_sh = re.search(r'상장주식수</th>\s*<td[^>]*>(.*?)</td>', t_html, re.S)
            if m_sh:
                shares = parse_num(re.sub(r'<[^>]+>', '', m_sh.group(1)))
            # PER
            m_per = re.search(r'id="_per"[^>]*>(.*?)</em>', t_html, re.S)
            if m_per:
                per = parse_num(m_per.group(1))
            # PBR
            m_pbr = re.search(r'id="_pbr"[^>]*>(.*?)</em>', t_html, re.S)
            if m_pbr:
                pbr = parse_num(m_pbr.group(1))
            # 배당수익률
            m_div = re.search(r'id="_dvr"[^>]*>(.*?)</em>', t_html, re.S)
            if m_div:
                div_yield = parse_num(m_div.group(1))

        daily_rows.append((
            date_str, code, name, market, sector,
            close_p, prev_p, open_p, high_p, low_p, volume,
            mcap, shares, per, pbr, div_yield
        ))

        # 4. 기업실적분석 표 추출 (존재하는 종목만)
        idx_cop = html.find('section cop_analysis')
        if idx_cop != -1:
            sub_html = html[idx_cop:idx_cop + 25000]
            idx_tbl_end = sub_html.find('</table>')
            if idx_tbl_end != -1:
                tbl_html = sub_html[:idx_tbl_end + 8]
                soup_tbl = BeautifulSoup(tbl_html, "html.parser")
                trs = soup_tbl.select("tr")
                if len(trs) >= 17:
                    parsed_tbl = []
                    for r in trs[1:]:
                        parsed_tbl.append(tuple(c.get_text(strip=True) for c in r.select("th, td")))
                    cop_records[code] = tuple(parsed_tbl)

    return date_str, daily_rows, cop_records, errors

if __name__ == "__main__":
    t0 = time.time()
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    dates = sorted([d for d in os.listdir(BASE_DIR) if date_pattern.match(d) and os.path.isdir(os.path.join(BASE_DIR, d))])
    print(f"총 {len(dates)}개 날짜 폴더 병렬 파싱 시작 (워커 64개)...", flush=True)

    all_daily = []
    all_errors = []
    last_cop_sig = {}      # code -> 직전 날짜의 parsed_tbl 튜플
    fin_snapshots = []     # 변경된 날의 (date, code, parsed_tbl)

    # 날짜 순서대로 상태 비교가 필요하므로 청크 단위로 병렬 실행 후 날짜순 정렬 병합
    CHUNK = 64
    for i in range(0, len(dates), CHUNK):
        batch_dates = dates[i:i+CHUNK]
        batch_results = {}
        with ProcessPoolExecutor(max_workers=64) as ex:
            futures = {ex.submit(process_single_date, d): d for d in batch_dates}
            for fut in as_completed(futures):
                d_str, d_rows, c_recs, errs = fut.result()
                batch_results[d_str] = (d_rows, c_recs, errs)

        for d_str in batch_dates:
            d_rows, c_recs, errs = batch_results[d_str]
            all_daily.extend(d_rows)
            all_errors.extend(errs)
            for code, tbl_tuple in c_recs.items():
                if last_cop_sig.get(code) != tbl_tuple:
                    last_cop_sig[code] = tbl_tuple
                    fin_snapshots.append((d_str, code, tbl_tuple))

        elapsed = time.time() - t0
        done_cnt = min(i + CHUNK, len(dates))
        print(f"[{done_cnt}/{len(dates)}일 완료] 누적 시세행: {len(all_daily):,} | 재무변경 스냅샷: {len(fin_snapshots):,} | 경과: {elapsed:.1f}초", flush=True)

    cols = [
        "date", "code", "name", "market", "sector",
        "close", "prev_close", "open", "high", "low", "volume",
        "market_cap", "shares", "per", "pbr", "div_yield"
    ]
    df_daily = pd.DataFrame(all_daily, columns=cols)
    df_daily.to_pickle(os.path.join(OUT_DIR, "daily_market.pkl"))

    with open(os.path.join(OUT_DIR, "financial_snapshots.pkl"), "wb") as f:
        pickle.dump(fin_snapshots, f)

    df_err = pd.DataFrame(all_errors, columns=["date", "code", "error_type", "detail"])
    df_err.to_csv(os.path.join(LOG_DIR, "parse_error_log.csv"), index=False)

    print("\n=== 전수 파싱 최종 완료 ===", flush=True)
    print(f"총 소요 시간: {time.time() - t0:.1f}초")
    print(f"총 시세 데이터 행 수: {len(df_daily):,}행 (고유 종목코드 수: {df_daily['code'].nunique():,}개)")
    print(f"총 재무제표 변경 스냅샷 수: {len(fin_snapshots):,}건")
    print(f"파싱 제외/에러 건수: {len(df_err):,}건")
