import pandas as pd
import os

# csv 파일들 'artist', 'title', 'end_date', 'price_USD', 'auction_site' 뽑아서 병합하는 함수 
def merge_csv():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_files = [
        os.path.join(current_dir, "..", "data", "removed_phillips_picasso_lastVersion.csv"),
        os.path.join(current_dir, "..", "data", "christies_Pablo_Picasso_20250201_121353.csv"),
        os.path.join(current_dir, "..", "data", "removed_sotheby_picasso.csv"),
    ]

    dfs = [pd.read_csv(file, encoding='latin1')[['artist', 'title', 'end_date', 'price_USD', 'auction_site' ]] for file in csv_files]

    merged_df = pd.concat(dfs, ignore_index=True)

    output_fp = os.path.join(current_dir, "..", "data", "merged_lastversion.csv")
    merged_df.to_csv(output_fp, index=False)

    print(f"병합된 CSV 파일 저장 완료: {output_fp}")

merge_csv()