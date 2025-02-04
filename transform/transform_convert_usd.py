import requests
import json
import os
import csv
import requests
import re
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def convert_to_usd(row):
    if row['estimateCurrency'] == 'USD':
        return row['price_USD']
    
    ticker = f"{row['estimateCurrency']}USD=X"
    original_date = row['date']
    max_days_back = 365 * 5  # 최대 5년까지 거슬러 검색
    
    for days_back in range(0, max_days_back):
        current_date = original_date - timedelta(days=days_back)
        start_date = current_date.strftime('%Y-%m-%d')
        end_date = (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
            
        try : 
            fx_data = yf.download(ticker, start=start_date, end=end_date, progress=False)

            if not fx_data.empty and 'Close' in fx_data.columns:
                exchange_rate = fx_data['Close'].iloc[0]  # 첫 번째 값 가져오기
                
                match = re.search(r"([\d]+\.[\d]+)", str(fx_data))
                if match:
                    exchange_rate = float(match.group(1))
                    return row['price_USD'] * exchange_rate
        except :
            pass
    return None
    

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_fp = os.path.join(current_dir, "..", "data", "sothbys_picaaso_last.csv")
    df = pd.read_csv(json_fp)

    # 날짜 컬럼을 datetime 형식으로 변환 (컬럼 이름에 맞게 수정)
    df = df.dropna(subset=['end_date'])
    df['date'] = pd.to_datetime(df['end_date'])

        # USD 가격 계산
    df['change_price_usd'] = df.apply(convert_to_usd, axis=1)

    # 결과 저장
    df.to_csv('converted_prices_picasso.csv', index=False)

main()