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

# 문제점
# p태그가 id도 없고, 순서도 그때그때 달라서 가져오기가 힘듦. 키워드 마다 규칙성도 없음.
# 실제로 정보가 없는것도 많음 
# 환율 아직 안바꿔줌
# 시간마다 태그도 바뀜: 어떨때는 p태그도 아님

data = {
  "requests": [
    {
      "indexName": "bsp_dotcom_prod_en",
      "params": "highlightPreTag=<ais-highlight-0000000000>&highlightPostTag=</ais-highlight-0000000000>&clickAnalytics=true&hitsPerPage=51&filters=type:\"Bid\" OR type:\"Buy Now\" OR type:\"Lot\" OR type:\"Private Sale\" OR type:\"Retail\"&query=luc tuymans&facets=[]&tagFilters="
    }
  ]
}

response = requests.post(
    "https://o28sy4q7wu-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.2.0)%3B%20Browser%20(lite)%3B%20JS%20Helper%20(3.2.2)%3B%20react%20(16.13.1)%3B%20react-instantsearch%20(6.7.0)&x-algolia-api-key=e732e65c70ebf8b51d4e2f922b536496&x-algolia-application-id=O28SY4Q7WU",
    json=data
)

filename = 'sothebys.json'



def unix2date(unix_time):
    if unix_time > 10**10: 
        unix_time = unix_time / 1000

    date_time = datetime.datetime.fromtimestamp(unix_time)
    return date_time.strftime("%Y-%m-%dT%H:%M:%S")

def extract_detail_sothebys(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_fp = os.path.join(current_dir, "..", "data", filename)
    
    try:
        with open(json_fp, 'r', encoding='utf-8') as f:
            data = json.load(f)  
    except:
        print(f"파일을 찾을 수 없습니다: {json_fp}")

    auction_data = []
    for index, item in enumerate(data["results"][0]["hits"]):
        try :
          edition = 1
          auction_site = "sotheby's"
          title = item["title"]
          lowEstimate_USD = item["lowEstimate"]
          highEstimate_USD = item["highEstimate"]
          price_USD = item["salePrice"]
          estimateCurrency = item["estimateCurrency"]
          url = item["url"]
          artist = item["artists"][0]
          end_date = unix2date(int(item["endDate"]))

          height = None 
          width = None
          full_text = item["fullText"]
          if full_text != None :
            pattern = r'(\d+(?:\.\d+)?)\s*(?:by|x)\s*(\d+(?:\.\d+)?)\s*cm'
            matches = re.findall(pattern, full_text)
            height = matches[0][0]
            width = matches[0][1]

        except IndexError:
            pass
        except AttributeError:
            end_date = None

        response = requests.get(url)
        if response.status_code == 200:
            html = response.text 
            soup = BeautifulSoup(html, 'html.parser')
            try : 
                text = soup.select_one("#LotDetails > div.css-1aw519d > p:nth-child(7)").text
                if not "cm" in text:
                    artwork_type = text
            except AttributeError:
                artwork_type = None
            
            p_tags = soup.find_all("p")
            
            year = None
            for p in p_tags:
                if "Executed" in p.text:
                    pattern = r'(?<=Executed in )\d{4}'
                    match = re.search(pattern, p.text)
                    year = match.group()

            if artwork_type == None :
                try : 
                  artwork_type = soup.find("li", "LotPage-medium").text 
                except :
                    pass
            
            if height == None : 
                try :
                  height_width = soup.find("li","LotPage-lotMeasurements").text 
                  pattern = r'(\d+(?:\.\d+)?)\s*(?:by|x)\s*(\d+(?:\.\d+)?)\s*cm'
                  matches = re.findall(pattern, height_width)
                  height = matches[0][0]
                  width = matches[0][1]
                except:
                    pass
              
            if year == None :
                try :
                    text = soup.find("li","LotPage-lotExecuted").text
                    pattern = r'(?<=Executed in )\d{4}'
                    match = re.search(pattern,text)
                    year = match.group()
                except :
                    pass

        auction_data.append({
            "artist" : artist,
            "title" : title,
            "end_date" : end_date,
            "low_estimate_USD" : lowEstimate_USD,
            "high_estimate_USD" : highEstimate_USD,
            "price_USD" : price_USD,
            "auction_site" : auction_site,
            "year" : year,
            "artwork_type" : artwork_type,
            "edition" : edition,
            "height_cm" : height,
            "width_cm" : width,
            "estimateCurrency" : estimateCurrency
        })

    json_fp = os.path.join(current_dir, "..", "data", "sothbys.csv")
    with open(json_fp, mode='w',newline='', encoding='utf-8') as file:
        fieldNames = auction_data[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldNames)
        writer.writeheader()
        writer.writerows(auction_data)

# if response.status_code == 200:
#     data = response.json()
#     with open(filename, 'w', encoding='utf-8') as f:
#         json.dump(data, f, indent=4, ensure_ascii=False)
#     extract_detail_sothebys(filename)

# CSV 파일 불러오기
current_dir = os.path.dirname(os.path.abspath(__file__))
json_fp = os.path.join(current_dir, "..", "data", "sothbys.csv")
df = pd.read_csv(json_fp)

# 날짜 컬럼을 datetime 형식으로 변환 (컬럼 이름에 맞게 수정)
df['date'] = pd.to_datetime(df['end_date'])

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
    

# USD 가격 계산
df['change_price_usd'] = df.apply(convert_to_usd, axis=1)

# 결과 저장
df.to_csv('converted_prices.csv', index=False)


# extract_detail_sothebys(filename)

