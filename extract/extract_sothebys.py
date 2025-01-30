import requests
import json
import os
import csv
import requests
import datetime
from bs4 import BeautifulSoup

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
    return date_time

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
        except IndexError:
            pass
        except AttributeError:
            end_date = None

        response = requests.get(url)
        if response.status_code == 200:
            html = response.text 
            soup = BeautifulSoup(html, 'html.parser')
            try : 
                artwork_type = soup.select_one("#LotDetails > div.css-1aw519d > p:nth-child(7)").text
            except AttributeError:
                artwork_type = None
            
            p_tags = soup.find_all("p")
            height_width = None
            height = None 
            width = None
            for p in p_tags:
                if "cm" in p.text:
                    height_width = p.text.strip()
                    break  # 찾으면 루프 종료
            if height_width != None :
              height = height_width.split()[0]
              width = height_width.split()[2]
            
            year = None
            for p in p_tags:
                if "Executed" in p.text:
                    year = p.text.split()[2]

            if artwork_type == None :
                try : 
                  artwork_type = soup.find("li", "LotPage-medium").text 
                except :
                    pass
            
            if height_width == None : 
                try :
                  height_width = soup.find("li","LotPage-lotMeasurements").text 
                  height = height_width.split()[0]
                  width = height_width.split()[2]
                except:
                    pass
              
            if year == None :
                try :
                    year = soup.find("li","LotPage-lotExecuted").text.split()[2]
                except :
                    pass

        auction_data.append({
            "artist" : artist,
            "title" : title,
            "end_date" : end_date,
            "lowEstimate_USD" : lowEstimate_USD,
            "highEstimate_USD" : highEstimate_USD,
            "price_USD" : price_USD,
            "auction_site" : auction_site,
            "year" : year,
            "artwork_type" : artwork_type,
            "edition" : edition,
            "height_cm" : height,
            "width_cm" : width
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


extract_detail_sothebys(filename)