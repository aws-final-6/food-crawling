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

    # 태그가 없으면 빈 리스트로 설정
    if not tags:
        tags = []

    json_ld_data['tags'] = tags
    parsed_li.append(json_ld_data)

    print(f"[INFO] Successfully parsed Recipe ID {recipe_id}")
    return parsed_li

async def CrawlingBetweenRanges(startRecipeId, numRecipes):
    connector = TCPConnector(ssl=False)  # SSL 인증서 검증 비활성화
    async with ClientSession(connector=connector) as session:
        tasks = []
        for i in range(startRecipeId, startRecipeId - numRecipes, -1):
            url = baseUrl + str(i)
            tasks.append(fetch(session, url, i))

        print(f"[INFO] Starting to fetch {numRecipes} recipes from ID {startRecipeId}")
        responses = await asyncio.gather(*tasks)
        all_recipes = []
        not_found_ids = []
        for page_source, recipe_id in responses:
            if page_source is None:
                print(f"[ERROR] Failed to fetch Recipe ID {recipe_id}")
                not_found_ids.append(recipe_id)
                continue
            if (startRecipeId - recipe_id + startRecipeId - 1) % 10 == 0:
                print(f"Processing Recipe ID {recipe_id}")
            res = await parsing_async(page_source, recipe_id)
            if res:
                all_recipes.extend(res)
            else:
                not_found_ids.append(recipe_id)
        return all_recipes, not_found_ids

def save_to_csv(data, filename):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Data saved to {filename}")

def main(startRecipeId, numRecipes, filename):
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
startRecipeId = 7028266
numRecipes = 10000
filename = "recipes.csv"

main(startRecipeId, numRecipes, filename)
