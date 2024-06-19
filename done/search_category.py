import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from collections import defaultdict
import time
import random

# 카테고리별 value 값 저장
category_values = {
    "종류별": {
        63: "밑반찬",
        56: "메인반찬",
        54: "국/탕",
        55: "찌개",
        60: "디저트",
        53: "면/만두",
        52: "밥/죽/떡",
        61: "퓨전",
        57: "김치/젓갈/장류",
        58: "양념/소스/잼",
        65: "양식",
        64: "샐러드",
        68: "스프",
        66: "빵",
        69: "과자",
        59: "차/음료/술",
        62: "기타"
    },
    "상황별": {
        12: "일상",
        18: "초스피드",
        13: "손님접대",
        19: "술안주",
        21: "다이어트",
        15: "도시락",
        43: "영양식",
        17: "간식",
        45: "야식",
        46: "해장",
        44: "명절",
        14: "이유식",
        22: "기타"
    }
}

# 특정 레시피 ID 범위를 설정합니다.
min_recipe_id = 7018267  # 최소 레시피 ID
max_recipe_id = 7028266  # 최대 레시피 ID

# 지정된 selector
selector = "#contents_area_full > ul > ul > li > div.common_sp_thumb > a"

# 사용자 에이전트 설정
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# 크롤링 함수
def crawl_recipes(min_recipe_id, max_recipe_id):
    base_url = "https://www.10000recipe.com/recipe/list.html"
    recipe_ids = defaultdict(lambda: {'categories': []})

    cat4_values = category_values["종류별"]
    cat2_values = category_values["상황별"]

    for cat4_value, cat4_name in cat4_values.items():
        for cat2_value, cat2_name in cat2_values.items():
            page = 1
            while True:
                url = f"{base_url}?cat4={cat4_value}&cat2={cat2_value}&order=date&page={page}"

                response = requests.get(url, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')

                # selector를 사용하여 레시피 링크 추출
                links = soup.select(selector)
                if not links:
                    break  # 링크가 더 이상 없으면 종료

                stop_crawling = False
                current_page_recipe_count = 0
                for link in links:
                    # 레시피 ID 추출 (링크에서 ID를 추출하는 예제)
                    match = re.search(r'recipe/(\d+)', link['href'])
                    if match:
                        recipe_id = int(match.group(1))  # 레시피 ID를 정수로 변환
                        if recipe_id < min_recipe_id:  # 레시피 ID가 최소값보다 작으면 크롤링 중단
                            stop_crawling = True
                            break
                        if recipe_id <= max_recipe_id:  # 레시피 ID가 최대값보다 작거나 같으면 저장
                            category_combination = (cat4_value, cat2_value)
                            if category_combination not in recipe_ids[recipe_id]['categories']:
                                recipe_ids[recipe_id]['categories'].append(category_combination)
                            current_page_recipe_count += 1
                        # 7028266보다 큰 경우는 저장하지 않지만 계속 크롤링

                print(f"{cat4_name} - {cat2_name} 조합 - 페이지 {page}에서 {current_page_recipe_count}개의 데이터를 크롤링했습니다. 현재까지 수집된 레시피 수: {len(recipe_ids)}")

                if stop_crawling:
                    break

                page += 1


    return recipe_ids

# 크롤링 실행
recipe_ids = crawl_recipes(min_recipe_id, max_recipe_id)

# 수집된 데이터를 DataFrame으로 변환
data = []
for recipe_id, info in recipe_ids.items():
    for cat4_value, cat2_value in info['categories']:
        data.append({
            'RecipeID': recipe_id,
            'cat4': cat4_value,
            'cat2': cat2_value
        })

df = pd.DataFrame(data)

# CSV 파일로 저장
df.to_csv('./recipe_cat_ids.csv', index=False)

print("CSV 파일로 저장되었습니다.")