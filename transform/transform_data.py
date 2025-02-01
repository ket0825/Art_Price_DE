import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
import time

import yfinance as yf

def save_json(transformed_data: List, output_dir:str, artist:str):
    artist_dir = artist.replace(" ", "_")
    raw_dir = f"{output_dir}/{artist_dir}"
    os.makedirs(raw_dir, exist_ok=True)
    filename = f"{raw_dir}/{artist_dir}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(transformed_data, f, indent=4, ensure_ascii=False)

def convert_price_to_usd(price: str, end_date) -> float:
    """
    Convert price to USD at the exchange rate on the end date.
    현재 지원: EUR, GBP
    """
    if not price:
        return None
    
    currency, price_str = price.split(" ")
    price_int = int(price_str.replace(",", ""))
    if currency == "USD":
        return price_int

    date = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S")

    # 이전 날짜 계산 (1일 전)
    prev_date = date - timedelta(days=1)

    # 특정 형식으로 문자열 변환이 필요한 경우
    date_str = date.strftime("%Y-%m-%d")
    prev_date_str = prev_date.strftime("%Y-%m-%d")

    # MARK: 현재 지원: EUR, GBP
    for currency in ["EUR", "GBP"]:
        if currency in price:
            exchange_rate = yf.download([f"{currency}USD=X"], start=prev_date_str, end=date_str)
            
            # 데이터가 비어있는지 확인
            if exchange_rate.empty:
                # 이전 영업일의 데이터를 찾을 때까지 날짜를 하루씩 뒤로 이동
                current_date = datetime.strptime(prev_date_str, "%Y-%m-%d")
                while exchange_rate.empty:
                    current_date -= timedelta(days=1)
                    exchange_rate = yf.download([f"{currency}USD=X"], 
                                            start=current_date.strftime("%Y-%m-%d"), 
                                            end=date_str)
            
            price_usd = price_int * exchange_rate["Close"].values[0][0]  # [0][0] 대신 [0] 사용
            return int(price_usd)
            
            

def convert_to_cm(value: float, unit: str) -> float:
    """Convert measurements to centimeters."""
    if 'in' in unit.lower():
        return value * 2.54  # 1 inch = 2.54 cm
    return value  # Assume it's already in cm if not inches

def parse_title(desc: str) -> str:
    """Extract title from description."""
    # Look for patterns like "<i>Die Zeit</i>"
    title_pattern = r'<i>(.*?)</i>'
    match = re.search(title_pattern, desc)
    if match:
        return match.group(1)
    title_pattern = r'<b>(.*?)</b>'

    return "Untitled"

def parse_dimensions(dim_text: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """Parse height and width dimensions from text and convert to cm."""
    # Find patterns like "15 5/8 x 11 3/8in." or "31.5 x 43cm."
    # TODO: mm도 있음.
    dim_pattern = r'(\d+(?:\s+\d+\/\d+)?(?:\.\d+)?)\s*x\s*(\d+(?:\s+\d+\/\d+)?(?:\.\d+)?)(?:\s*)((?:in|cm)\.*)'
    match = re.search(dim_pattern, dim_text)
    
    if not match:
        return None, None, None
        
    def convert_fraction(dim_str: str) -> float:
        # Handle cases like "15 5/8"
        parts = dim_str.strip().split()
        if len(parts) == 2:
            whole = float(parts[0])
            num, denom = map(float, parts[1].split('/'))
            return whole + (num/denom)
        return float(dim_str)
        
    height = convert_fraction(match.group(1))
    width = convert_fraction(match.group(2))
    unit = match.group(3)
    
    # Convert to cm if necessary
    height = convert_to_cm(height, unit)
    width = convert_to_cm(width, unit)
    
    return height, width, 'cm'

def parse_artwork_type(desc: str) -> str:
    """Extract artwork type from description."""
    # TODO: 더 추가하긴 해야 함. 이거 없으면 아예 제외해야 할듯.
    # 사실 여러 속성이 들어갈 수 있음.
    # 프랑스어인 경우도 존재함. 이후 추론해야 할 듯.
    types = re.findall(r'<br>\s*(.*?(?:oil|watercolour|watercolor|lithograph|screenprint|graphite|ink|silkscreen|gouache|acrylic|pencil|paper|board|panel|canvas|pastel|crayon|pen|linoleum).*?)<br>', desc, re.I)
    if types:
        return types[0].strip()
    french_types = re.findall(r'<br>\s*(.*?(?:huile|aquarelle|plume|encre|papier|toile|carton|panneau|pastel|crayon|stylo|linoléum).*?)<br>', desc, re.I)
    if french_types:
        return french_types[0].strip()
    print("NO artwork type: ", desc)
    return "Unknown"

def parse_edition_info(desc: str) -> Optional[str]:
    """
    # TODO: 어려움. 일단은 이렇게.
    Extract edition information from description.
    """
    edition_pattern = r'(\d+/\d+).*?(?:edition|édition)'
    match = re.search(edition_pattern, desc, re.I)
    if match:
        return match.group(1)
    return None

def parse_year(desc: str) -> Optional[str]:
    """Extract creation year from description."""
    # Look for patterns like "Executed in 1994" or "Painted in 2001"
    # 프랑스어 등 다른 언어도 존재함. 이러면 찾기 어려움
    year_pattern = r'(?:executed|painted|drawn)\s+[in|on](?:[,\s\w]+)?(\d{4})'
    match = re.search(year_pattern, desc)
    if match:
        return match.group(1)
        
    # Also check for year patterns in quotes with apostrophes
    alt_year_pattern = r"(\d{2})'" # ex 90'
    match = re.search(alt_year_pattern, desc)
    if match:
        year = int(match.group(1))
        # Convert 2-digit year to 4-digit
        if year < 50:  # Assuming years 00-49 are 2000s
            return f"20{year:02d}"
        return f"19{year:02d}"

    alt_year_pattern2 = r"(\d{4})'" # ex 1990'
    match = re.search(alt_year_pattern2, desc)
    if match:
        return match.group(1)
    
    circa_year_pattern = r'circa(?:\s*</i>)?\s*(\d{4})'
    match = re.search(circa_year_pattern, desc)
    if match:
        return match.group(1)
    
    space_year_pattern = r'(\d{4})\s*<br>'
    match = re.search(space_year_pattern, desc)
    if match:
        return match.group(1)
    
    print("연도를 찾을 수 없습니다: ", desc)
    return None

def parse_artwork_description(description: str) -> Dict:
    """Main function to parse artwork description."""

    # lowercase로 바꾼다.
    description = description.lower()

    result = {
        "title": parse_title(description),
        "year": parse_year(description),
        "artwork_type": parse_artwork_type(description),
        "edition": parse_edition_info(description),
        "dimensions": {"height": None, "width": None, "unit": "cm"}
    }
    
    height, width, unit = parse_dimensions(description)
    if height and width:
        result["dimensions"]["height"] = round(height, 2)
        result["dimensions"]["width"] = round(width, 2)
    else:
        print("높이와 너비를 찾을 수 없습니다.", description)
    
    return result

def load_json(base_dir, artist):
    artist_dir = artist.replace(" ", "_")
    # artist_dir = "luc_tuymans"
    raw_dir = f"{base_dir}/{artist_dir}"
    for filename in os.listdir(raw_dir):
        if filename.endswith(".json"):
            print(f"Loading {filename}")
            with open(f"{raw_dir}/{filename}", "r", encoding="utf-8") as f:
                data = json.load(f)
                yield data
    

def transform_data(artist, data: Dict) -> List:
    """
    작가명/ 작품명/ 제작일자/ 거래날짜/ 예상낙찰가/ 실제 낙찰가/ 경매사이트/ 세로/ 가로/ 부수/ 작품 종류
    """
    print(f"Transforming data for {artist}")
    transformed_data = []
    # TODO: 동명이인 체크 로직 추가해야 함.
    # get artists list
    # if 'Artists' in data['filters']['groups'][2]["title_txt"]: # Artists / Maker / Author
    #     for item in data['filters']['groups'][2]['filters']:
    #         # 여기에 모두 섞여있음.
    #         pass
    # TODO: artwork type도 여기서 확인하고 추가할 수 있음.

    # 데이터 파싱
    count = 0
    for lot in data["lots"]:
        # printing 제외
        description = lot['description_txt'].lower()
        if (
            "print" in description
            or 'linocut' in description
            or 'aquatint' in description
            or 'drypoint' in description
            or 'etching' in description
            or 'engraving' in description
            or 'engrave' in description
            or 'lithograph' in description
            or 'earthenware' in description
            or 'ceramic' in description
            or 'plate' in description
            or 'tile' in description
            or 'engobe' in description
            or 'slip' in description
            or 'plaque' in description  # 도자기 혹은 조각판
            or 'terracotta' in description # 구운 흙

            # 태피스트리
            or 'tapestry' in description
            or 'tapisserie' in description

            # 가죽
            or 'patina' in description

            # 프랑스어
            or 'gravure' in description      # print의 프랑스어
            or 'linogravure' in description  # linocut
            or 'aquatinte' in description    # aquatint
            or 'pointe sèche' in description # drypoint
            or 'eau-forte' in description    # etching
            or 'taille-douce' in description # engraving
            or 'lithographie' in description # lithograph
            or 'faïence' in description      # earthenware
            or 'céramique' in description    # ceramic
            or 'assiette' in description     # plate
            or 'carreau' in description      # tile
            or 'glisser' in description      # 도자기 기법
            or 'terre cuite' in description  # terracotta
            ):
            count += 1
            print("skip: ", count)
            continue

        # 작가명
        artist = artist
        # 거래 마감 날짜:
        end_date = lot["end_date"]
        # 예상 낙찰가
        estimate = lot["estimate_txt"]
        # 실제 낙찰가
        price = lot["price_realised_txt"] # 과거 데이터는 공백으로도 존재함.
        # 경매사이트
        auction_site = "Christies"
        # description_txt 파싱
        result = parse_artwork_description(lot["description_txt"])
        # 작품명
        title = lot['title_secondary_txt']
        if not title:
            title = result["title"]
            if not title:
                print("check here: ", lot)
        # 제작 (마감) 일자 Painted, Executed 뒤에 있는 년도
        year = result["year"]
        # 작품 종류
        artwork_type = result["artwork_type"]
        # 부수
        edition = result["edition"]
        # 세로
        height = result["dimensions"]["height"]
        # 가로
        width = result["dimensions"]["width"]

        transformed_data.append({
            "artist": artist, # 작가명
            "title": title, # 작품명
            "end_date": end_date, # 거래 마감 날짜
            "estimate_USD": estimate, # 예상 낙찰가
            "price_USD": convert_price_to_usd(price, end_date), # 실제 낙찰가
            "auction_site": auction_site, # 경매사이트
            "year": year, # 제작 (마감) 일자
            "artwork_type": artwork_type, # 작품 종류 (ex. oil, watercolour, lithograph, screenprint, graphite, ink)
            "edition": edition, # 부수
            "height_cm": height, # 세로
            "width_cm": width # 가로
        })

    return transformed_data

def transform_main(base_dir, artist):
    transformed_data = []
    for data in load_json(base_dir, artist): # 나중에 수정 필요. 작가 리스트에서 있으면 그 작가로 간주.
        transformed = transform_data(artist, data)
        transformed_data.extend(transformed)
        # print(transformed_data)
    return transformed_data

if __name__ == '__main__':
    # base_dir = "jsons"
    # artist = "Luc Tuymans"
    base_dir = "jsons"
    artist = "Pablo_Picasso"
    transformed_data = transform_main(base_dir, artist)

    output_dir = "transformed2"
    save_json(transformed_data, output_dir, artist)