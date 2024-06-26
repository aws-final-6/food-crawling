import asyncio
import aiohttp
from aiohttp import ClientSession, TCPConnector
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import datetime

baseUrl = 'http://www.10000recipe.com/recipe/'

async def fetch(session, url, recipe_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        async with session.get(url, headers=headers) as response:
            print(f"Fetching URL: {url}")
            page_source = await response.read()
            return page_source.decode('utf-8', errors='replace'), recipe_id
    except Exception as e:
        print(f"[ERROR] Fetching URL failed: {url}, error: {e}")
        return None, recipe_id

async def parsing_async(page_source, recipe_id):
    parsed_li = []
    soup = BeautifulSoup(page_source, "html.parser", from_encoding='utf-8')

    # 레시피가 없는 경우 alert 메시지 처리
    if soup.find("div", class_="alert"):
        print(f"[INFO] Recipe ID {recipe_id} not found.")
        return []

    # JSON-LD 데이터 추출
    try:
        json_ld_script = soup.find("script", type="application/ld+json")
        json_ld_data = json.loads(json_ld_script.string, strict=False)
        json_ld_data = {'recipe_id': recipe_id, **json_ld_data}  # Add recipe ID to the beginning of data
    except Exception as e:
        print(f"[ERROR] JSON-LD parsing failed for Recipe ID {recipe_id}: {e}")
        return []

    # 태그 데이터 추출
    try:
        tags = [tag.text.strip() for tag in soup.select(".view_tag a")]
    except Exception as e:
        print(f"[ERROR] Tag parsing failed for Recipe ID {recipe_id}: {e}")
        tags = []

    # 재료 데이터 추출
    ingredients = []
    try:
        material_area = soup.select('#divConfirmedMaterialArea > ul > li')
        for item in material_area:
            material_name = item.select_one('div').text.strip()
            material_amount = item.select_one('span').text.strip()
            ingredients.append({'name': material_name, 'amount': material_amount})
    except Exception as e:
        print(f"[ERROR] Material parsing failed for Recipe ID {recipe_id}: {e}")
        ingredients = []

    # 태그와 재료가 없으면 빈 리스트로 설정
    if not tags:
        tags = []
    if not ingredients:
        ingredients = []

    json_ld_data['tags'] = tags
    json_ld_data['ingredients'] = ingredients
    parsed_li.append(json_ld_data)

    print(f"[INFO] Successfully parsed Recipe ID {recipe_id}")
    return parsed_li

async def CrawlingBetweenRanges(startRecipeId, numRecipes):
    connector = TCPConnector(ssl=False)  # SSL 인증서 검증 비활성화
    async with ClientSession(connector=connector) as session:
        all_recipes = []
        not_found_ids = []
        consecutive_not_found = 0

        for i in range(startRecipeId, startRecipeId + numRecipes):
            if consecutive_not_found >= 20:
                print("[INFO] 20 consecutive recipes not found. Stopping crawling.")
                break

            url = baseUrl + str(i)
            page_source, recipe_id = await fetch(session, url, i)

            if page_source is None:
                print(f"[ERROR] Failed to fetch Recipe ID {recipe_id}")
                not_found_ids.append(recipe_id)
                consecutive_not_found += 1
                continue

            res = await parsing_async(page_source, recipe_id)
            if res:
                all_recipes.extend(res)
                consecutive_not_found = 0  # Reset counter if a valid recipe is found
            else:
                not_found_ids.append(recipe_id)
                consecutive_not_found += 1

        return all_recipes, not_found_ids

def save_to_csv(data, filename):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Data saved to {filename}")

def get_last_recipe_id(csv_filename):
    try:
        df = pd.read_csv(csv_filename)
        if df.empty:
            return None
        return df['RecipeID'].max()
    except FileNotFoundError:
        return None

def main(csv_filename, numRecipes, filename):
    last_recipe_id = get_last_recipe_id(csv_filename)
    if last_recipe_id is None:
        print("[INFO] No previous data found. Please set a startRecipeId manually.")
        return

    startRecipeId = last_recipe_id + 1

    # Running Time Check
    startTime = datetime.now()
    print(f"[Start Time] {startTime}")

    all_recipes, not_found_ids = asyncio.run(CrawlingBetweenRanges(startRecipeId, numRecipes))

    # Running Time Check
    endTime = datetime.now()
    print(f"[End Time] {endTime}")
    print(f"[Running Time] : {endTime - startTime} (ms)")

    save_to_csv(all_recipes, filename)

    # 레시피가 없는 ID 로그 출력
    with open('not_found_recipes.txt', mode='w', newline='', encoding='utf-8') as log_fd:
        for not_found_id in not_found_ids:
            log_fd.write(f"{not_found_id}\n")

    # log 출력
    with open("10000recipe_log.txt", "a", newline='', encoding='utf-8') as log_fd:
        log_fd.write(f"[Start Time] {startTime}\n")
        log_fd.write(f"[End Time] {endTime}\n")
        log_fd.write(f"[Running Time] : {endTime - startTime} (ms)\n")

    print("[LOGGED] time log.txt generated")

# 크롤링 범위와 저장할 파일명을 설정합니다.
csv_filename = "Recipe_data.csv"
numRecipes = 10000
filename = "recent_recipes.csv"

main(csv_filename, numRecipes, filename)