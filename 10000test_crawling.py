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

    json_ld_data['tags'] = tags
    parsed_li.append(json_ld_data)

    return parsed_li


async def crawl_async(recipe_id):
    global currBrowser

    url = base_url + str(recipe_id)
    try:
        currBrowser.get(url)
    except:
        print(f"[ERROR] getUrl failed at recipe ID {recipe_id}")
        raise Exception("browser.get(url) Failed")

    try:
        element = WebDriverWait(currBrowser, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".view_tag"))
        )
    except:
        print(f"[ERROR] 20s timeout at recipe ID {recipe_id}")
        raise Exception("WebDriverWait Timeout")

    page_source = currBrowser.page_source
    parsing_li = await parsing_async(page_source)

    return parsing_li


async def main_async():
    global datas_li
    global currBrowser

    datas_li = []
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_argument(f"user-agent={ua.random}")  # 랜덤 User-Agent 설정

    # options를 capabilities로 변환하여 병합
    caps.update(options.to_capabilities())

    currBrowser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    time.sleep(3)

    for recipe_id in range(7028222, 7028224):  # 1번부터 100번 레시피 ID까지 크롤링
        parsed_li = await crawl_async(recipe_id)
        print(f"Recipe ID {recipe_id} has {len(parsed_li)} items.")
        datas_li += parsed_li
        time.sleep(random.uniform(1, 3))  # 요청 사이에 랜덤 지연 시간 추가

    currBrowser.quit()


# Running Time Check
startTime = datetime.today()

asyncio.run(main_async())

# Running Time Check
endTime = datetime.today()

print(f"[Start Time] {startTime}\n")
print(f"[End Time] {endTime}\n")
print(f"[Running Time] : {endTime - startTime} (ms)\n")
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

# log 출력
log_fd = open("10000recipe_log.txt", "a", newline="")
log_fd.write(f"[Start Time] {startTime}\n")
log_fd.write(f"[End Time] {endTime}\n")
log_fd.write(f"[Running Time] : {endTime - startTime} (ms)\n")
log_fd.write(f"[File Length] {len(datas_li)} rows \n\n")
log_fd.close()

print("[LOGGED] time log.txt generated")
