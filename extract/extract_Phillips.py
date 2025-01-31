import requests
import json
from bs4 import BeautifulSoup
import re
import time
import random
import concurrent.futures  # 병렬 처리 모듈

# Phillips API 기본 URL
MAKER_ID = 10800  # 6740
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
    #time.sleep(random.uniform(2, 5))

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
        material_match = re.search(r"(oil|watercolour|lithograph|screenprint|graphite|ink|acrylic|mixed media|tempera|gouache|charcoal|pastel|crayon|pencil|\
                                   plate|ceramic|earthenware|Linocut|Aquatint|drypoint|Etching|Engraving)", additional_info_text, re.IGNORECASE)
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
    auction_data = []
    detail_urls = []

    # 페이지네이션을 처리하기 위한 변수
    page = 1
    total_pages = None  

    while True:
        # API 요청 시 필요한 쿼리 파라미터
        params = {
            "page": page, #현재 페이지 번호
            "resultsperpage": 24, #한 페이지에서 가져올 데이터 개수
            "lotStatus": "past" #과거 경매 데이터
        }

        # API 요청 보내기
        response = session.get(BASE_URL, headers=HEADERS, params=params)

        if response.status_code == 200:
            data = response.json() # 응답 데이터를 JSON형식으로 변환

            # 전체 페이지 수 설정 (첫 요청에서만 가져옴), totalPages가 없으면 기본값 1로 설정
            if total_pages is None:
                total_pages = data.get("totalPages", 1)
                print(f"total page is {total_pages}")

            print(f"📌 Fetching page {page} of {total_pages}...")

            for item in data.get("data", []):
                detail_url = item.get("detailLink", "No URL")

                # 비정상적 경매 종료 시간 처리
                auction_start = item.get("auctionStartDateTimeOffset", "0001-01-01T00:00:00")
                auction_end = item.get("auctionEndDateTimeOffset", "0001-01-01T00:00:00")
                if "0001" in auction_end:
                    if "0001" in auction_start:
                        continue
                    auction_end = auction_start

                # 비정상적 경매가격 처리
                price = item.get("hammerPlusBP", 0)
                if price is None or price == 0:
                    continue

                # 기본 정보 저장
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
                    "currency": item.get("currencySign", ""),
                }

                detail_urls.append((lot_info, detail_url))

            page += 1
            if page > total_pages:
                break
        else:
            print(f"⚠️ Failed to fetch data on page {page}. Status code: {response.status_code}")
            break

    # 병렬로 상세 정보 가져오기
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        future_to_lot = {executor.submit(fetch_detail_info, detail_url): lot_info for lot_info, detail_url in detail_urls}

        extracted = 1
        results = []
        for future in concurrent.futures.as_completed(future_to_lot):
            lot_info = future_to_lot[future]
            try:
                detail_data = future.result()
                lot_info.update(detail_data)
                results.append(lot_info)
                print(extracted)
                extracted += 1
            except Exception as e:
                print(f"⚠️ Error fetching details: {e}")

    # 병렬 처리 결과 병합
    for i, detail_data in enumerate(results):
        detail_urls[i][0].update(detail_data)
        auction_data.append(detail_urls[i][0])

    return auction_data

# 데이터 크롤링 실행
auction_results = fetch_lots()

# JSON 파일로 저장
json_filename = f"./data/phillips_auction_results_{MAKER_ID}.json"
with open(json_filename, "w", encoding="utf-8") as file:
    json.dump(auction_results, file, indent=4, ensure_ascii=False)

print(f"✅ 데이터 저장 완료: {json_filename}")
