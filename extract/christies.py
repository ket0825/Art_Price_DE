import requests
import json
import os
import uuid
from typing import Optional

def christies_get_history_lots(base_path, artist, page:int, sortby, tab) -> Optional[int]:
    # 자동으로 저장할 파일 경로가 결정됩니다.
    # dir 만들기
    if base_path[-1] != '/':
        raise Exception('디렉토리 경로는 /로 끝나야 합니다.')
    
    tab_path = ''
    if tab == 'True':
        tab_path = 'sold_lots'
    elif tab == 'False':
        tab_path = 'available'
    else:
        raise Exception('tab은 True 또는 False여야 합니다.')

    artist_path = artist.replace(" ", "_")

    json_fp = f"{base_path}/{artist_path}/christies_{artist_path}_{page}_{sortby}_{tab_path}.json"
    dir_path = json_fp[:json_fp.rfind('/')]
    os.makedirs(dir_path, exist_ok=True) # 재귀적으로 디렉토리 생성하고, 있어도 에러 안나게 함
    
    headers = {
        'Accept': 'application/vnd.christies.v1+json',
        'Accept-Language': 'ko-KR,ko;q=0.9',
        'Origin': 'https://www.christies.com',
        'Referer': 'https://www.christies.com/',
        'correlation-id': str(uuid.uuid4()),
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15'
    }

    params = {
        'keyword': artist,
        'page': page,
        'is_past_lots': tab, # 아마 tab에 따라 다른데 available이면 False, sold_lots이면 True
        'sortby': sortby, # date, relevance.
        'language': 'en',
        'geocountrycode': 'KR',
        'show_on_loan': 'true',
        'datasourceId': '182f8bb2-d729-4a38-b539-7cf1a901cf2e',
        "filterids": "|CoaCategoryValues{Paintings}|CoaCategoryValues{Drawings+%26+Watercolors}|",
        # 추후에 filterids는 예술작품에 한하여 계속 추가해야 함.
    }

    response = requests.get(
        'https://apim.christies.com/search-client',
        headers=headers,
        params=params
    )

    if response.status_code == 200:
        data = response.json()
        with open(json_fp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        if page == 1:
            total_page = data['total_pages'] # int

            if not isinstance(total_page, int):
                raise Exception('total_pages가 int가 아닙니다.')
            
            print(f"총 페이지 수: {total_page}")
            return total_page
        else:
            return None
    
    raise Exception(f"status_code: {response.status_code}")

if __name__ == '__main__':
    base_path = 'jsons/'
    artist = 'luc tuymans'
    sortby = 'date'
    tab = 'True' # sold_lots라는 뜻. available이면 False

    # get search metadata 필요할수도.
    total_page = christies_get_history_lots(base_path, artist, 1, sortby, tab)

    for i in range(2, total_page+1):
        christies_get_history_lots(base_path, artist, i, sortby, tab)
    