import requests
import json
import os
import uuid

headers = {
    'Accept': 'application/vnd.christies.v1+json',
    'Accept-Language': 'ko-KR,ko;q=0.9',
    'Origin': 'https://www.christies.com',
    'Referer': 'https://www.christies.com/',
    'correlation-id': str(uuid.uuid4()),
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15'
}

params = {
    'keyword': 'luc tuymans',
    'page': 1,
    'is_past_lots': 'True',
    'sortby': 'date',
    'language': 'en',
    'geocountrycode': 'KR',
    'show_on_loan': 'true',
    'datasourceId': '182f8bb2-d729-4a38-b539-7cf1a901cf2e'
}

response = requests.get(
    'https://apim.christies.com/search-client',
    headers=headers,
    params=params
)

json_fp = 'jsons/jsons/jsons/chriesties1.json'

if response.status_code == 200:
    data = response.json()
    dir_path = json_fp[:json_fp.rfind('/')]
    os.makedirs(dir_path, exist_ok=True)
    with open(json_fp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)