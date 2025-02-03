
import pandas as pd
import os

# 특정 artwork_type을 제거해주는 함수
def remove_type():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_files = os.path.join(current_dir, "..", "data", "converted_prices_picasso.csv"),

    remove_types = {"linocut", "aquatint", "drypoint", "etching", "engraving", "lithograph"}

    df = pd.read_csv(csv_files[0])
    df = df[~df['artwork_type'].str.lower().isin(remove_types)]

    df.to_csv("removed_sotheby_picasso.csv")

remove_type()