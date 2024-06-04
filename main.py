from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
import json
import argparse
import os

def get_driver():
    """Sets a driver. Chrome by default."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    return driver

def scroll_down(driver, num_scrolls, scroll_pause_time = 1):
    """Scroll down the page num_scrolls times with a pause between scrolls, so it can load more results.
    It scrolls twice in a row with a little pause, so Feina Activa loads results properly.
    """
    for _ in range(num_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(0.5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)

def search(output_path : str, topic_str : str = None, province_str : str = None, results : int = 100):

    SEARCH_URL = "https://feinaactiva.gencat.cat/search/offers/list?"
    JOB_POSTS = "//div[contains(@class, 'list-item')]"
    COOKIES = "//div[@class='cookieConsent']//button"
    URL_BASE = "https://feinaactiva.gencat.cat"

    #Sets driver and scrolls
    driver = get_driver()
    wait = WebDriverWait(driver, 15)
    scrolls = (results // 20) - 1
    # There should be at least topic or province
    if topic_str is None and province_str is None:
        raise Exception('Topic and/or Province parameters should be passed.')

    # Match province with its respective URL code
    if province_str:
        if province_str.lower() == 'barcelona':
            SEARCH_URL += '&type=province&province=08&i=0'
        elif province_str.lower() == 'girona':
            SEARCH_URL += '&type=province&province=17&i=0'
        elif province_str.lower() == 'tarragona':
            SEARCH_URL += '&type=province&province=43&i=0'
        elif province_str.lower() == 'lleida':
            SEARCH_URL += '&type=province&province=25&i=0'

    # Spaces should be replaced with %20 to match URL standards.
    if topic_str:
        keywords = topic_str.replace(' ', '%20')
        SEARCH_URL += f'&keywords={keywords}'

    driver.get(SEARCH_URL)

    # Bypass cookies
    wait.until(EC.presence_of_element_located((By.XPATH, COOKIES)))
    cookies = driver.find_element(By.XPATH, COOKIES).click()
    time.sleep(1.25)

    # Makes sure some jobs are loaded, so we'll get the right output
    jobs_appear = wait.until(EC.presence_of_all_elements_located((By.XPATH, JOB_POSTS)))

    # Scroll for the results, once for each 20 results.
    scroll_down(driver, scrolls)

    # Get the results to parse.
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    jobs_list = soup.select('div[class*="list-item"]')
    jobs_dict = {}

    for i, job_div in enumerate(jobs_list):

        # Tags with different parameters
        job_tag = job_div.find('a')
        job_description = job_tag.get_text().strip().encode('utf-8')
        job_description = job_description.decode('utf-8')
        job_url = str(URL_BASE + job_tag['href'])
        time_post = job_div.find('span', class_='published')
        business = job_div.find('span', class_='business')
        location = job_div.find('span', class_='location')
        description = job_div.find('p', class_='description')
        second_paragraph = job_div.find_all('p')[1]

        jobs_dict[i] = {
            'job_description': job_description,
            'job_url': job_url,
            'time_post': time_post.get_text().strip() if time_post else None,
            'business': business.get_text().strip() if business else None,
            'location': location.get_text().strip() if location else None,
            'subtitle': description.get_text().strip().replace('\n','') if description else None,
            'description': second_paragraph.get_text().strip().replace('\n','') if second_paragraph else None,
        }

    # Prepare JSON output
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base_output_path = f'FA_search_{timestamp}.json'
    with open(os.path.join(output_path,base_output_path), 'w', encoding='utf-8') as file:
        json.dump(jobs_dict, file, ensure_ascii=False, indent=4)

    print('Search saved as JSON file.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Feina Activa job scraper')
    parser.add_argument('output_path', type=str, help='Output path for the JSON file')
    parser.add_argument('--province', type=str, help='Province to filter job postings. Options: Barcelona, Girona, Tarragona, Lleida')
    parser.add_argument('--topic', type=str, help='Topic to filter job postings')
    parser.add_argument('--results', type=int, help='Number of results')

    args = parser.parse_args()

    search(output_path=args.output_path, province_str=args.province, topic_str=args.topic, results=args.results)





