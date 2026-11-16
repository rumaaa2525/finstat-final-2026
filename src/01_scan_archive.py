import os
import re
import pandas as pd

BASE_DIR = "/mnt/data/stock"
date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

records = []
other_dirs = []

for entry in sorted(os.listdir(BASE_DIR)):
    full_path = os.path.join(BASE_DIR, entry)
    if not os.path.isdir(full_path):
        continue
    if date_pattern.match(entry):
        files = [f for f in os.listdir(full_path) if f.endswith(".html")]
        total_files = len(files)
        zero_byte = 0
        small_files = 0  # 10KB 미만 (정상 종목 페이지가 아닌 에러/빈 페이지 의심)
        
        for f in files:
            fsize = os.path.getsize(os.path.join(full_path, f))
            if fsize == 0:
                zero_byte += 1
            elif fsize < 10240:
                small_files += 1
                
        records.append({
            "date": entry,
            "total_html": total_files,
            "zero_byte": zero_byte,
            "small_under_10kb": small_files,
            "valid_est": total_files - zero_byte - small_files
        })
    else:
        other_dirs.append(entry)

df = pd.DataFrame(records)
os.makedirs("outputs", exist_ok=True)
df.to_csv("outputs/archive_scan_summary.csv", index=False)

print("=== 아카이브 전수 스캔 결과 ===")
print(f"날짜 폴더 수: {len(df)}일 ({df['date'].min()} ~ {df['date'].max()})")
print(f"기타 폴더: {other_dirs}")
print(f"전체 HTML 파일 총합: {df['total_html'].sum():,}개")
print(f"0바이트 파일 총합: {df['zero_byte'].sum():,}개")
print(f"10KB 미만 의심 파일 총합: {df['small_under_10kb'].sum():,}개")
print("\n[날짜별 유효 추정 파일 수 요약 통계]")
print(df[['total_html', 'zero_byte', 'small_under_10kb', 'valid_est']].describe().round(1))
print("\n[파일 수가 유독 적은 하위 10일]")
print(df.sort_values("valid_est").head(10).to_string(index=False))
