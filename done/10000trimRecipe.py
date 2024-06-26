import asyncio
import csv
import time
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from datetime import datetime

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless") # 헤드리스 모드 활성화
chrome_options.add_argument("--no-sandbox") # 샌드박스 사용 안 함
chrome_options.add_argument("--disable-dev-shm-usage") # /dev/shm 파티션 사용 안 함

base_url = "https://www.10000recipe.com/profile/recipe.html?uid=10000know&qs=손질&page="

async def parsing_async(crawledHtml_li):
    parsed_li = []
    for result in crawledHtml_li:
        try:
            href = result.find("a")["href"]
            title = result.find("h4").text
            trim = "손질" in title
            storage = "보관" in title
            parsed_li.append([href, title, trim, storage])
        except:
            pass
    return parsed_li

async def crawl_async(page):
    global currBrowser

    url = base_url + str(page)
    try:
        currBrowser.get(url)
    except:
        print("[ERROR] getUrl failed at page ", page)
        raise Exception("browser.get(url) Failed")

    try:
        element = WebDriverWait(currBrowser, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#contents_area > div.brand_cont.mag_t_10 > ul > li"))
        )
    except:
        print("[ERROR] 20s timeout at page ", page)
        raise Exception("WebDriverWait Timeout")

    soup = BeautifulSoup(currBrowser.page_source, "html.parser")
    crawledHtml_li = soup.select("#contents_area > div.brand_cont.mag_t_10 > ul > li")
    parsing_li = await parsing_async(crawledHtml_li)

    return parsing_li

async def main_async():
    global datas_li
    global currBrowser

    datas_li = []
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    currBrowser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    time.sleep(3)

    for page in range(1, 10):
        parsed_li = await crawl_async(page)
        print(f"Page {page} has {len(parsed_li)} items.")
        datas_li += parsed_li

    currBrowser.quit()

# Running Time Check
startTime = datetime.today()

asyncio.run(main_async())

# Running Time Check
endTime = datetime.today()

print(f"[Start Time] {startTime}\n")
print(f"[End Time] {endTime}\n")
print(f"[Running Time] : { endTime - startTime} (ms)\n")
print(f"[File Length] {len(datas_li)} rows \n\n")

# csv 출력
with open('../10000recipe_results.csv', mode='w', newline='', encoding='utf-8') as fd:
    csvWriter = csv.writer(fd)
    # 컬럼 헤더 작성
    csvWriter.writerow(['URL', 'Title', 'Trim', 'Storage'])
    # 크롤링 결과 작성
    csvWriter.writerows(datas_li)

# log 출력
log_fd = open("10000recipe_log.txt", "a", newline="")
log_fd.write(f"[Start Time] {startTime}\n")
log_fd.write(f"[End Time] {endTime}\n")
log_fd.write(f"[Running Time] : { endTime - startTime} (ms)\n")
log_fd.write(f"[File Length] {len(datas_li)} rows \n\n")
log_fd.close()

print("[LOGGED] time log.txt generated")
