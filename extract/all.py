import pandas as pd
import os

# 파일 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_files = [
    os.path.join(current_dir, "..", "data", "sothbys.csv"),
    os.path.join(current_dir, "..", "data", "Luc_Tuymans_20250130_023901.csv"),
    os.path.join(current_dir, "..", "data", "phillips_auction_results_transformed_6740.csv"),
]

# CSV 파일 읽어서 name, price 컬럼만 추출
dfs = [pd.read_csv(file)[['artist', 'title', 'end_date', 'price_USD', 'auction_site' ]] for file in csv_files]

# 데이터프레임 합치기
merged_df = pd.concat(dfs, ignore_index=True)

# 결과 저장
output_fp = os.path.join(current_dir, "..", "data", "merged.csv")
merged_df.to_csv(output_fp, index=False)

print(f"병합된 CSV 파일 저장 완료: {output_fp}")
