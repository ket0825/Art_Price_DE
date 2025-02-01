import requests
import json
import requests

# 페이지 네이션 적용된 form-data
def create_requests(page):
    return {"requests":[{"indexName":"bsp_dotcom_prod_en","params":"highlightPreTag=%3Cais-highlight-0000000000%3E&highlightPostTag=%3C%2Fais-highlight-0000000000%3E&clickAnalytics=true&hitsPerPage=51&filters=type%3A%22Bid%22%20OR%20type%3A%22Buy%20Now%22%20OR%20type%3A%22Lot%22%20OR%20type%3A%22Private%20Sale%22%20OR%20type%3A%22Retail%22&query=pablo%20picasso&maxValuesPerFacet=9999&page={page}&facets=%5B%22type%22%2C%22endDate%22%2C%22lowEstimate%22%2C%22highEstimate%22%2C%22artists%22%2C%22departments%22%5D&tagFilters=&facetFilters=%5B%5B%22departments%3A19th%20Century%20European%20Paintings%22%2C%22departments%3AImpressionist%20%26%20Modern%20Art%22%2C%22departments%3AContemporary%20Art%22%2C%22departments%3AAfrican%20%26%20Oceanic%20Art%22%2C%22departments%3AOld%20Master%20Paintings%22%5D%5D"},{"indexName":"bsp_dotcom_prod_en","params":"highlightPreTag=%3Cais-highlight-0000000000%3E&highlightPostTag=%3C%2Fais-highlight-0000000000%3E&clickAnalytics=false&hitsPerPage=1&filters=type%3A%22Bid%22%20OR%20type%3A%22Buy%20Now%22%20OR%20type%3A%22Lot%22%20OR%20type%3A%22Private%20Sale%22%20OR%20type%3A%22Retail%22&query=pablo%20picasso&maxValuesPerFacet=9999&page={page2}&attributesToRetrieve=%5B%5D&attributesToHighlight=%5B%5D&attributesToSnippet=%5B%5D&tagFilters=&analytics=false&facets=departments".format(page=page,page2=page)}]}
    
# sotheby에서 raw 데이터 뽑아오는 함수
def extract_sothebys():
    all_responses = []
    query = "pablo picasso"
    for page in range(21, 30): 
        request_data = {"requests":[
            {
                "indexName": "bsp_dotcom_prod_en",
                "params": f"highlightPreTag=%3Cais-highlight-0000000000%3E&highlightPostTag=%3C%2Fais-highlight-0000000000%3E&clickAnalytics=true&hitsPerPage=51&filters=type%3A%22Bid%22%20OR%20type%3A%22Buy%20Now%22%20OR%20type%3A%22Lot%22%20OR%20type%3A%22Private%20Sale%22%20OR%20type%3A%22Retail%22&query=pablo%20picasso&maxValuesPerFacet=9999&page={page}&facets=%5B%22type%22%2C%22endDate%22%2C%22lowEstimate%22%2C%22highEstimate%22%2C%22artists%22%2C%22departments%22%5D&tagFilters=&facetFilters=%5B%5B%22departments%3A19th%20Century%20European%20Paintings%22%2C%22departments%3AImpressionist%20%26%20Modern%20Art%22%2C%22departments%3AContemporary%20Art%22%2C%22departments%3AAfrican%20%26%20Oceanic%20Art%22%2C%22departments%3AOld%20Master%20Paintings%22%5D%5D".format(page=page)
            },
            {
                "indexName": "bsp_dotcom_prod_en",
                "params": f"highlightPreTag=%3Cais-highlight-0000000000%3E&highlightPostTag=%3C%2Fais-highlight-0000000000%3E&clickAnalytics=false&hitsPerPage=1&filters=type%3A%22Bid%22%20OR%20type%3A%22Buy%20Now%22%20OR%20type%3A%22Lot%22%20OR%20type%3A%22Private%20Sale%22%20OR%20type%3A%22Retail%22&query=pablo%20picasso&maxValuesPerFacet=9999&page={page}&attributesToRetrieve=%5B%5D&attributesToHighlight=%5B%5D&attributesToSnippet=%5B%5D&tagFilters=&analytics=false&facets=departments".format(page=page)
            }
        ]}
        response = requests.post(
            "https://o28sy4q7wu-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.2.0)%3B%20Browser%20(lite)%3B%20react%20(16.13.1)%3B%20react-instantsearch%20(6.7.0)%3B%20JS%20Helper%20(3.2.2)&x-algolia-api-key=e732e65c70ebf8b51d4e2f922b536496&x-algolia-application-id=O28SY4Q7WU",
            json=request_data
        )

        if response.status_code == 200:
            print("{page} clear".format(page=page))
            all_responses.append(response.json())  
        else:
            print(f"Error with page {page}: {response.status_code}")
        
        # JSON 파일로 저장
        with open("{query}_data.json".format(query=query), 'w', encoding='utf-8') as f:
            json.dump(all_responses, f, ensure_ascii=False, indent=2)
   

extract_sothebys()