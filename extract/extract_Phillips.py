import requests
import json
from bs4 import BeautifulSoup
import re
import time
import random

# Phillips API 기본 URL
MAKER_ID = 6740
BASE_URL = f"https://api.phillips.com/api/maker/{MAKER_ID}/lots"

# User-Agent 리스트 (랜덤 선택)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0",
]

HEADERS = {
    "User-Agent": random.choice(USER_AGENTS),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Referer": "https://www.phillips.com/browse",
    "Connection": "keep-alive",
}

# 세션 유지 (쿠키 확보)
session = requests.Session()
session.headers.update(HEADERS)

# Phillips 홈페이지 방문하여 쿠키 저장 (403 방지)
session.get("https://www.phillips.com/")
cookies = session.cookies.get_dict()  # 쿠키 확인

def fetch_detail_info(detail_url):
    """상세 페이지에서 추가 정보를 가져오는 함수"""
    if detail_url == "No URL":
        return {}

    # 요청 전에 일정한 딜레이 추가 (403 방지)
    time.sleep(random.uniform(2, 5))

    # User-Agent 변경
    session.headers.update({"User-Agent": random.choice(USER_AGENTS)})

    # 쿠키 포함하여 요청
    response = session.get(detail_url, cookies=cookies)

    if response.status_code == 403:
        print(f"⚠️ [403 Forbidden] Access denied to {detail_url}")
        return {}

    if response.status_code != 200:
        print(f"⚠️ Failed to fetch details from {detail_url}. Status: {response.status_code}")
        return {}

    soup = BeautifulSoup(response.text, "html.parser")

    detail_info = {
        "year": None,
        "artwork_type": None,
        "height_cm": None,
        "width_cm": None,
        "edition": None,
    }

    # 추가 정보 추출
    additional_info_elem = soup.select_one(".lot-page__lot__additional-info")
    
    if additional_info_elem:
        additional_info_text = additional_info_elem.get_text(separator=" ").strip()

        # 제작 연도 추출 (4자리 숫자 탐색)
        year_match = re.search(r"(\b\d{4}\b)", additional_info_text)
        if year_match:
            detail_info["year"] = int(year_match.group(1))

        # 매체 추출
        material_match = re.search(r"(oil|watercolour|lithograph|screenprint|graphite|ink|acrylic|mixed media|tempera|gouache|charcoal|pastel)", additional_info_text, re.IGNORECASE)
        if material_match:
            detail_info["artwork_type"] = material_match.group(0).strip()

        # 크기 정보 추출 (23.5 x 15.2 cm)
        size_match = re.search(r"(\d+(\.\d+)?)\s*x\s*(\d+(\.\d+)?)\s*cm", additional_info_text)
        if size_match:
            detail_info["height_cm"] = float(size_match.group(1))
            detail_info["width_cm"] = float(size_match.group(3))

        # 에디션 정보 추출 (예: Edition of 100)
        edition_match = re.search(r"edition of (\d+)", additional_info_text, re.IGNORECASE)
        if edition_match:
            detail_info["edition"] = int(edition_match.group(1))
        
    return detail_info

    
def fetch_lots():
    """경매 데이터를 가져오는 함수"""
    auction_site = "Phillips"
    # 크롤링한 데이터를 저장할 리스트
    auction_data = []

    # 페이지네이션을 처리하기 위한 변수
    page = 1  # 첫 페이지부터 시작
    total_pages = None  # 처음엔 전체 페이지 수를 모르므로 None으로 설정

    while True:
        # API 요청 시 필요한 쿼리 파라미터
        params = {
            "page": page,              # 현재 페이지 번호
            "resultsperpage": 24,       # 한 페이지에서 가져올 데이터 개수
            "lotStatus": "past"         # 과거 경매 데이터 (현재 진행 중은 'upcoming'으로 변경 가능)
        }

        # API 요청 보내기
        response = session.get(BASE_URL, headers=HEADERS, params=params)

        if response.status_code == 200:  
            data = response.json()  # 응답 데이터를 JSON 형식으로 변환

            # 전체 페이지 수 설정 (첫 요청에서만 가져옴), totalPages가 없으면 기본값 1로 설정
            if total_pages is None:
                total_pages = data.get("totalPages", 1)

            print(f"📌 Fetching page {page} of {total_pages}...")

            # 응답 JSON에서 'data' 키 안의 경매 리스트 가져오기
            for item in data.get("data", []):
                detail_url = item.get("detailLink", "No URL")

                # 비정상적 경매 종료 시간 처리
                auction_start = item.get("auctionStartDateTimeOffset", "0001-01-01T00:00:00")
                auction_end = item.get("auctionEndDateTimeOffset", "0001-01-01T00:00:00")
                if "0001" in auction_end:
                    if "0001" in auction_start:
                        continue  # 시작, 종료 모두 0001년이면 데이터 제외
                    auction_end = auction_start  # 비정상적인 종료 시간을 시작 시간으로 대체

                # 비정상적 경매가격 처리
                price = item.get("hammerPlusBP", 0)
                if price == 0.0:
                    price = None

                # 각 필드에서 필요한 데이터 추출
                # transform에서 거래 날자 형변환, 예상/실제 낙찰가 단위 변환 필요
                lot_info = {
                    "artist": item.get("makerName", "Unknown Artist"),
                    "title": item.get("description", "No Title"),
                    "start_date": auction_start,
                    "end_date": auction_end,
                    "low_estimate": item.get("lowEstimate", 0),
                    "high_estimate": item.get("highEstimate", 0),
                    "price": price,
                    "auction_site": auction_site,
                    "year": None,
                    "artwork_type": None,
                    "edition": None,
                    "height_cm": None,
                    "width_cm": None,
                    "currency": item.get("currencySign", ""), #화폐 단위
                }
                
                detail_data = fetch_detail_info(detail_url)
                lot_info.update(detail_data)

                auction_data.append(lot_info)

            page += 1
            if page > total_pages:
                break
        else:
            print(f"⚠️ Failed to fetch data on page {page}. Status code: {response.status_code}")
            break
    return auction_data

# 데이터 크롤링 실행
auction_results = fetch_lots()

# JSON 파일로 저장 (파일명에 작가 ID 포함)
json_filename = f"./data/phillips_auction_results_{MAKER_ID}.json"
with open(json_filename, "w", encoding="utf-8") as file:
    json.dump(auction_results, file, indent=4, ensure_ascii=False)  # JSON 저장 (가독성 위해 indent=4)

print(f"✅ 데이터 저장 완료: {json_filename}")