import pandas as pd
import numpy as np

print("1. 데이터 로딩 중...")
df = pd.read_pickle("data_processed/daily_market.pkl")
df = df.sort_values(["code", "date"]).reset_index(drop=True)

print(f"\n[기본 규모]")
print(f"총 행 수: {len(df):,} | 고유 코드: {df['code'].nunique():,} | 날짜 수: {df['date'].nunique()}일")

# 1. 업종명 결측 (ETF/ETN/펀드 등)
no_sector_codes = df[df['sector'].isna()]['code'].unique()
has_sector_codes = df[df['sector'].notna()]['code'].unique()
print(f"\n[1. 업종 분류 유무]")
print(f"업종명 있음(일반 주식·스팩 등): {len(has_sector_codes):,}개 코드")
print(f"업종명 없음(ETF·ETN 등): {len(no_sector_codes):,}개 코드")

# 2. 비정상 거래일 (거래량이 찍힌 종목이 거의 없는 휴장일 수집 폴더)
daily_active = df.groupby("date").apply(lambda g: (g['volume'].fillna(0) > 0).sum())
zero_vol_days = daily_active[daily_active < 100]
print(f"\n[2. 휴장일/비거래일 폴더 의심]")
print(f"거래량 > 0 인 종목이 100개 미만인 날: {len(zero_vol_days)}일")
if len(zero_vol_days) > 0:
    print(zero_vol_days.head(10))

# 3. 일반 주식(업종명 보유) 내 스팩(SPAC) 및 우선주 비중
stock_df = df[df['sector'].notna()].copy()
latest_names = stock_df.groupby("code")['name'].last()
spac_codes = latest_names[latest_names.str.contains("스팩|제\d+호", na=False)].index
pref_codes = latest_names[latest_names.index.str[-1] != '0'].index  # 종목코드 끝자리가 0이 아니면 우선주/신형우선주
print(f"\n[3. 업종 보유 종목 내 특수 종목]")
print(f"스팩(SPAC) 의심 코드 수: {len(spac_codes):,}개")
print(f"우선주(코드 끝자리 != 0) 수: {len(pref_codes):,}개")

# 4. 업종 재분류(업종명 변경) 종목 탐지
sec_changes = stock_df.groupby("code")['sector'].nunique()
changed_sec_codes = sec_changes[sec_changes > 1]
print(f"\n[4. 업종 재분류(업종명 변경) 종목]")
print(f"분석 기간 중 업종명이 1회 이상 바뀐 종목 수: {len(changed_sec_codes):,}개")
if len(changed_sec_codes) > 0:
    sample_c = changed_sec_codes.index[:5]
    for c in sample_c:
        s_list = stock_df[stock_df['code'] == c]['sector'].dropna().unique().tolist()
        nm = latest_names.get(c, c)
        print(f"  - {nm}({c}): {s_list}")

# 5. 액면분할/병합/감자 의심 (일일 수익률 +-30% 초과)
stock_df['prev_close_calc'] = stock_df.groupby("code")['close'].shift(1)
stock_df['ret'] = (stock_df['close'] - stock_df['prev_close_calc']) / stock_df['prev_close_calc']
outliers = stock_df[(stock_df['ret'] > 0.305) | (stock_df['ret'] < -0.305)]
print(f"\n[5. 가격 불연속(액면분할·병합·권리락 의심, 일간 변동 +-30.5% 초과)]")
print(f"발생 건수: {len(outliers):,}건 (해당 종목 수: {outliers['code'].nunique():,}개)")
print(outliers[['date', 'code', 'name', 'prev_close_calc', 'close', 'ret']].head(10).to_string(index=False))

# 6. 결측치 비율 (시가총액, PER, PBR)
print(f"\n[6. 주요 변수 결측률 (업종 보유 종목 기준)]")
print((stock_df[['sector', 'close', 'volume', 'market_cap', 'per', 'pbr']].isna().mean() * 100).round(2))
