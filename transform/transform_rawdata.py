import json
import os
import csv
import re
from datetime import datetime


def unix2date(unix_time):
    if unix_time > 10**10: 
        unix_time = unix_time / 1000

    date_time = datetime.fromtimestamp(unix_time)
    return date_time.strftime("%Y-%m-%dT%H:%M:%S")

def transform_rawdata(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_fp = os.path.join(current_dir, "..", "data", filename)
    
    try:
        with open(json_fp, 'r', encoding='utf-8') as f:
            data = json.load(f)  
    except:
        print(f"파일을 찾을 수 없습니다: {json_fp}")

    auction_data = []
    for json_data in data:
        for index, item in enumerate(json_data["results"][0]["hits"]):
            if item["promoType"]=="lot" and ( item["artistName"] == "Pablo Picasso" or (len(item["artists"]) >= 1 and item["artists"][0] == "Pablo Picasso")):
                # try :
                edition = 1
                auction_site = "sotheby's"
                title = item["title"]
                lowEstimate_USD = item["lowEstimate"]
                highEstimate_USD = item["highEstimate"]
                price_USD = item["salePrice"]
                estimateCurrency = item["estimateCurrency"]
                artist = item["artists"][0]
                try :
                    end_date = unix2date(int(item["endDate"]))
                except : 
                    end_date = None

                height = None 
                width = None
                year = None
                artwork_type = None
                full_text = item["fullText"]
                if full_text != None :
                    pattern = r'(\d+(?:\.\d+)?)\s*(?:by|x)\s*(\d+(?:\.\d+)?)\s*cm'
                    matches = re.findall(pattern, full_text)
                    
                    if matches :
                        height = matches[0][0]
                        width = matches[0][1]

                    match = re.search(r'Executed.*?\b(18\d{2}|19\d{2})\b', full_text)
                    if match :
                        year = match.group(1)

                    keywords = r'oil|watercolour|watercolor|lithograph|screenprint|graphite|ink|silkscreen|gouache|acrylic|pencil|paper|board|panel|canvas|pastel|crayon|pen|linoleum|mixed media|tempera|charcoal|plate|ceramic|earthenware|Linocut|Aquatint|drypoint|Etching|Engraving'
                    match = re.search(r'\b(' + keywords + r')\b', full_text, re.IGNORECASE)

                    if match:
                        artwork_type = match.group(1)

                    if artwork_type is None and item["keywords"] != None:
                        match = re.search(r'\b(' + keywords + r')\b', item["keywords"], re.IGNORECASE)

                        if match:
                            artwork_type = match.group(1)


                # except IndexError:
                #     pass
                # except AttributeError:
                #     end_date = None

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

    json_fp = os.path.join(current_dir, "..", "data", "sothbys_picaaso_last.csv")
    with open(json_fp, mode='w',newline='', encoding='utf-8') as file:
        fieldNames = auction_data[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldNames)
        writer.writeheader()
        writer.writerows(auction_data)


transform_rawdata('pablo_picasso_data.json')

