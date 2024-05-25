import requests
import os
from lxml import html
from playwright.sync_api import sync_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_request(url, homepage_url):
    try:
        headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'cookie': 'ak_cookieconsent_status=allow; nitroCachedPage=0',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'referer': 'https://franchisesuppliernetwork.com/resources/page/3/',
    'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}
        if not url.startswith(homepage_url):
            url = homepage_url+url
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            if url.endswith(('.jpg','.jpeg','.png','.svg','.webp')):
                logger.info(f"Image Request successful! :: {str(url)}")
                return response.content
            else:
                logger.info(f"URL Request successful! :: {str(url)}")
                return response.text
        else:
            logger.error(f"Request failed with status code:: {str(response.status_code)}")
            homepage_response = requests.get(homepage_url)
            cookies = homepage_response.cookies
            retry_response = requests.get(url, cookies=cookies,headers=headers)
            if retry_response.status_code == 200:
                logger.info("Retry request successful!")
                return retry_response.text
            else:
                print(f"Retry request failed with status code :: {str(retry_response.status_code)}")
                # Use Playwright to try the URL
                with sync_playwright() as p:
                    browser = p.chromium.launch()
                    page = browser.new_page()
                    page.set_extra_http_headers(cookies)
                    page.goto(url)
                    retry_response_playwright = page.content()
                    if retry_response_playwright:
                        logger.info(f"Playwright attempt successful! :: {str(url)}")
                        return retry_response_playwright
                    else:
                        logger.error("Playwright attempt failed.")
                        return None
    except Exception as e:
        logger.error(f"An error occured in requests: {str(e)}")
        return None

def scrape_categories(response):
    try:
        tree = html.fromstring(response)
        category_names = tree.xpath('//ul[@id="primary-menu"]//text()')
        category_links = tree.xpath('//ul[@id="primary-menu"]//@href')
        category_names = [name.strip() for name in category_names if name.strip()]
        categories = dict(zip(category_names, category_links))
        return categories
    except Exception as e:
        logger.error(f"An error occurred in categories: {str(e)}")
        return None

def scrape_resources(response,folder_path,homepage_url):
    try:
        tree = html.fromstring(response)
        resource_names = tree.xpath('//div[contains(@class,"single-news")]/h3/text()')
        resource_links = tree.xpath('//div[contains(@class,"single-news")]/a/@href')
        resource_images = tree.xpath('//div[contains(@class,"single-news")]/img/@src')
        resource_names = [name.strip() for name in resource_names if name.strip()]
        combined_links = zip(resource_links,resource_images)
        resources = dict(zip(resource_names, combined_links))
        for resource, link in resources.items():
            if link:
                resource_link_response = process_request(link[0], homepage_url)
                content_path = os.path.join(folder_path, f"{resource}_content.txt")
                with open(content_path, 'w', encoding = 'utf8') as outfile:
                    outfile.write(resource_link_response)
                resource_image_response = process_request(link[1], homepage_url)
                image_path = os.path.join(folder_path, f"{resource}_image.jpg")
                with open(image_path,'wb') as imagefile:
                    imagefile.write(resource_image_response)
        try:
            next_page_link = tree.xpath('//link[@rel="next"]/@href')
            if next_page_link:
                next_page_response = process_request(next_page_link[0], homepage_url)
            if next_page_response:
                scrape_resources(next_page_response,folder_path,homepage_url)
        except Exception as e:
            logger.error(f"An error occurred in resources next page: {str(e)}")
    except Exception as e:
        logger.error(f"An error occurred while saving resources content/image: {str(e)}")
        return None

def scrape_suppliers(response,folder_path,homepage_url):
    try:
        tree = html.fromstring(response)
        supplier_names = tree.xpath('//div[@class="fs-single"]/h3/text()')
        supplier_links = tree.xpath('//div[@class="fs-single"]/a/@href')
        supplier_images = tree.xpath('//div[@class="fs-single"]/img/@src')
        supplier_names = [name.strip() for name in supplier_names if name.strip()]
        combined_links = zip(supplier_links,supplier_images)
        suppliers = dict(zip(supplier_names,combined_links))
        for supplier,link in suppliers.items():
            if link:
                supplier_link_response = process_request(link[0], homepage_url)
                content_path = os.path.join(folder_path, f"{supplier}_content.txt")
                with open(content_path, 'w', encoding = 'utf8') as outfile:
                    outfile.write(supplier_link_response)
                supplier_image_response = process_request(link[1], homepage_url) 
                image_path = os.path.join(folder_path, f"{supplier}_image.jpg")   
                with open(image_path,'wb') as imagefile:
                    imagefile.write(supplier_image_response)
        try:
            next_page_link = tree.xpath('//a[@class="nextpostslink"]/@href')
            if next_page_link:
                next_page_response = process_request(next_page_link[0], homepage_url)
            if next_page_response:
                scrape_suppliers(next_page_response,folder_path,homepage_url)
        except Exception as e:
            logger.error(f"An error occurred in supplier next page: {str(e)}")
    except Exception as e:
        logger.error(f"An error occurred while saving supplier content/image: {str(e)}")


# Example usage:
def main():
    url = "https://franchisesuppliernetwork.com/"
    homepage_url = "https://franchisesuppliernetwork.com/"
    folder_path = "output"
    os.makedirs(folder_path, exist_ok=True)
    response_text = process_request(url, homepage_url)
    if response_text:
        categories = scrape_categories(response_text)
        if categories:
            for category, link in categories.items():
                if link:
                    category_link_response = process_request(link, homepage_url)
                    content_path = os.path.join(folder_path, f"{category}_content.txt")
                    with open(content_path, 'w', encoding = 'utf8') as outfile:
                        outfile.write(category_link_response)
                if category.lower() == 'resources':
                    scrape_resources(category_link_response,folder_path,homepage_url)
                if category.lower() == 'fsn suppliers':
                    scrape_suppliers(category_link_response,folder_path,homepage_url)
        else:
            logger.error("Scraping failed.")
    else:
        logger.error("Request processing failed.")


if __name__ == "__main__":
    main()