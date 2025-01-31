import requests

# BASE_URL = f"https://api.phillips.com/api/maker/{MAKER_ID}/lots"
# url = "https://www.phillips.com/api/6740/makerlotsdetailed"
# url = "https://www.phillips.com/api/detail/luc-tuymans/NY010624/164"
url = "https://portalapi.phillips.com/api/lot/NY010624/detail"


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json"
}

response = requests.get(url, headers=headers)

print(f"HTTP Status Code: {response.status_code}")  # 상태 코드 출력
print(f"Response Text: {response.text}")  # 응답의 앞부분 500자만 출력
