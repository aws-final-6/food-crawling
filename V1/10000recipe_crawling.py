import asyncio
import csv
import json
import time
import random
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from fake_useragent import UserAgent
from datetime import datetime
import os

# User-Agent 설정을 위한 fake_useragent 사용
ua = UserAgent()

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")  # 헤드리스 모드 활성화
chrome_options.add_argument("--no-sandbox")  # 샌드박스 사용 안 함
chrome_options.add_argument("--disable-dev-shm-usage")  # /dev/shm 파티션 사용 안 함
chrome_options.add_argument(f"user-agent={ua.random}")  # 랜덤 User-Agent 설정

# Selenium 감지 방지 설정
caps = webdriver.DesiredCapabilities.CHROME.copy()
caps["pageLoadStrategy"] = "eager"  # 페이지가 완전히 로드되기 전에도 동작하도록 설정

base_url = "https://www.10000recipe.com/recipe/"

async def parsing_async(page_source):
    parsed_li = []
    soup = BeautifulSoup(page_source, "html.parser")

    # JSON-LD 데이터 추출
    try:
        json_ld_script = soup.find("script", type="application/ld+json")
        json_ld_data = json.loads(json_ld_script.string)
    except Exception as e:
        print(f"[ERROR] JSON-LD parsing failed: {e}")
        return []

    # 태그 데이터 추출
    try:
        tags = [tag.text.strip() for tag in soup.select(".view_tag a")]
    except Exception as e:
        print(f"[ERROR] Tag parsing failed: {e}")
        tags = []

    # 태그가 없으면 빈 리스트로 설정
    if not tags:
        tags = []

    json_ld_data['tags'] = tags
    parsed_li.append(json_ld_data)

    return parsed_li

async def crawl_async(recipe_id, browser, semaphore):
    async with semaphore:
        try:
            url = base_url + str(recipe_id)
            browser.get(url)

            # 레시피가 없을 때 alert 창 처리
            try:
                alert = WebDriverWait(browser, 3).until(EC.alert_is_present())
                alert.accept()
                print(f"Recipe ID {recipe_id} not found (alert present).")
                return [], recipe_id  # 레시피가 없는 경우
            except:
                pass

            element = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "script[type='application/ld+json']"))
            )
            page_source = browser.page_source
            parsing_li = await parsing_async(page_source)
            return parsing_li, None
        except Exception as e:
            print(f"[ERROR] Error at recipe ID {recipe_id}: {e}")
            return [], recipe_id

async def main_async(recipe_ids):
    global datas_li

    datas_li = []
    not_found_ids = []

    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_argument(f"user-agent={ua.random}")  # 랜덤 User-Agent 설정

    # options를 capabilities로 변환하여 병합
    caps.update(options.to_capabilities())

    # 더 많은 브라우저 인스턴스를 생성하여 병렬 처리
    num_browsers = 5  # 동시에 실행될 최대 브라우저 수
    browsers = [webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options) for _ in range(num_browsers)]
    time.sleep(3)

    semaphore = asyncio.Semaphore(num_browsers)  # 병렬로 실행될 최대 task 수

    tasks = []
    for i, recipe_id in enumerate(recipe_ids):
        browser = browsers[i % len(browsers)]
        task = asyncio.ensure_future(crawl_async(recipe_id, browser, semaphore))
        tasks.append(task)
        print(f"Task created for Recipe ID {recipe_id}")
        time.sleep(random.uniform(0.5, 1.5))  # 요청 사이에 랜덤 지연 시간 추가

    results = await asyncio.gather(*tasks)
    for i, result in enumerate(results):
        parsed_li, not_found_id = result
        if not_found_id:
            print(f"Recipe ID {not_found_id} not found.")
            not_found_ids.append(not_found_id)
        else:
            recipe_id = recipe_ids[i]
            print(f"Recipe ID {recipe_id} has {len(parsed_li)} items.")
            datas_li += parsed_li

    for browser in browsers:
        browser.quit()

    return not_found_ids

# 파일에서 레시피 ID 읽기
with open('./recipe_id.txt', 'r') as file:
    recipe_ids = [int(line.strip()) for line in file]

# ID 값을 큰 순서대로 정렬하고, 상위 1,000개 선택
recipe_ids = sorted(recipe_ids, reverse=True)[:1000]

# Running Time Check
startTime = datetime.today()
print(f"[Start Time] {startTime}")

not_found_ids = asyncio.run(main_async(recipe_ids))

# Running Time Check
endTime = datetime.today()
print(f"[End Time] {endTime}")
print(f"[Running Time] : {endTime - startTime} (ms)")
print(f"[File Length] {len(datas_li)} rows \n\n")

# CSV 출력
with open('10000recipe_results.csv', mode='w', newline='', encoding='utf-8') as fd:
    csvWriter = csv.writer(fd)
    # JSON-LD의 모든 키를 헤더로 사용
    if datas_li:
        # 첫 번째 데이터의 키를 사용하여 헤더를 설정
        headers = list(datas_li[0].keys())
        csvWriter.writerow(headers)
        # 크롤링 결과 작성
        for data in datas_li:
            csvWriter.writerow([data.get(header, "") for header in headers])

# 레시피가 없는 ID 로그 출력
with open('not_found_recipes.txt', mode='w', newline='', encoding='utf-8') as log_fd:
    for not_found_id in not_found_ids:
        log_fd.write(f"{not_found_id}\n")

# log 출력
with open("10000recipe_log.txt", "a", newline="") as log_fd:
    log_fd.write(f"[Start Time] {startTime}\n")
    log_fd.write(f"[End Time] {endTime}\n")
    log_fd.write(f"[Running Time] : {endTime - startTime} (ms)\n")
    log_fd.write(f"[File Length] {len(datas_li)} rows \n\n")

print("[LOGGED] time log.txt generated")
