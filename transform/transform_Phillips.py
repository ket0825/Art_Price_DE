import pandas as pd
from datetime import datetime, timedelta
import json
import yfinance as yf


# JSON 파일 로드
json_filename = "./data/phillips_auction_results_6740.json"
with open(json_filename, "r", encoding="utf-8") as file:
    auction_data = json.load(file)

# 데이터를 DataFrame으로 변환
df = pd.DataFrame(auction_data)

# 통화 단위에 대한 환율 코드 매핑
CURRENCY_MAPPING = {
    "$": "USD",  # USD는 변환하지 않음
    "£": "GBPUSD=X",  # 영국 파운드 -> USD
    "HK$": "HKDUSD=X",  # 홍콩 달러 -> USD
    "€": "EURUSD=X",  # 유로 -> USD
    "C$": "CADUSD=X",  # 캐나다 달러 -> USD
    "A$": "AUDUSD=X",  # 호주 달러 -> USD
}

# 환율 데이터 캐싱
exchange_rate_cache = {}

def fetch_exchange_rates(ticker):
    """ 특정 통화의 전체 기간 환율 데이터를 가져와 캐싱 """
    try:
        history = yf.Ticker(ticker).history(period="max")  # 전체 기간 데이터 가져오기
        exchange_rate_cache[ticker] = history["Close"].dropna().tz_localize(None)  # 타임존 제거
        return True
    except Exception as e:
        print(f"⚠️ {ticker} 환율 데이터 가져오기 실패: {e}")
        return False

# 달러를 제외한 모든 필요한 통화의 환율 데이터 미리 가져오기
for currency_symbol, ticker in CURRENCY_MAPPING.items():
    if ticker != "USD":
        fetch_exchange_rates(ticker)



def get_usd_exchange_rate(date_str, currency):
    """ 특정 날짜의 USD 환율을 가져오는 함수 """

    # 지원하지 않는 통화
    if currency not in CURRENCY_MAPPING:
        print(f'There is no ticker information for this currency: {currency}')
        return None  

    # 통화 단위에 맞는 티커 가져오기
    ticker = CURRENCY_MAPPING[currency]
    date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S").date() # 문자열을 datetime객체로 변환

    # USD는 변환할 필요 없음
    if ticker == "USD":
        return 1.0 
    
    # 찾으려는 날짜가 2003년 이전이면 None 반환?
    # if date.year < 2003:
    #     print(f"⚠️ {date} is before 2003. No exchange rate available.")
    #     return None


    # 캐시에 데이터가 없으면 None 반환
    if ticker not in exchange_rate_cache:
        return None

    # 가장 가까운 날짜의 환율 찾기(df.index.get_indexer)
    rates = exchange_rate_cache[ticker]
    target_date = pd.Timestamp(date).tz_localize(None)  # 타임존 제거 
    closest_date = rates.index[rates.index.get_indexer([target_date], method="nearest")[0]]
    
    return rates.loc[closest_date]


#------------------날짜 형태 변환--------------------#
# 날짜 변환
df["start_date"] = pd.to_datetime(df["start_date"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%S")
df["end_date"] = pd.to_datetime(df["end_date"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%S")

#------------------통화 단위 변환--------------------#
# 환율 컬럼 추가, 통화에 맞는 해당 날짜 환율로 채움
df["exchange_rate"] = df["currency"].map(lambda c: 1.0 if c == "$" else None)
mask = df["exchange_rate"].isna()  
df.loc[mask, "exchange_rate"] = df.loc[mask].apply(
    lambda row: get_usd_exchange_rate(row["end_date"], row["currency"]), axis=1
)

# 환율 적용
df[["low_estimate_USD", "high_estimate_USD", "price_USD"]] = df[
    ["low_estimate", "high_estimate", "price"]
].mul(df["exchange_rate"], axis=0)

# 소수점 반올림
df[["low_estimate_USD", "high_estimate_USD", "price_USD"]] = df[
    ["low_estimate_USD", "high_estimate_USD", "price_USD"]
].round(2)

# 환율 컬럼 제거
df.drop(columns=["exchange_rate"], inplace=True)

#----------------Transform 데이터 저장----------------#
transformed_json_filename = "./data/phillips_auction_results_transformed_6740.json"
df.to_json(transformed_json_filename, orient="records", indent=4, force_ascii=False)


print(f"✅ Transform 완료, 저장된 파일: {transformed_json_filename}")
