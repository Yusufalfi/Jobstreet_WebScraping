import asyncio
import csv
import json
from playwright.async_api import async_playwright

async def main_scraping(query='query', output_format= 'csv', max_pages = 5):
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await page.goto("https://www.jumia.co.ke/")
            # take selector input attribute name
            await page.wait_for_selector('input[name="q"]')
            # fill input 
            await page.fill('input[name="q"]', query)
            # press key Enter
            await page.press('input[name="q"]', "Enter")
            # take selector card attribute class
            await page.wait_for_selector('article.prd')

            products = []
            page_number = 1
            while page_number <= max_pages:
                print(f"scraping Page {page_number}")
                await page.wait_for_selector('article.prd')
                # get all card Product List
                product_elements = await page.query_selector_all('article.prd')
                for product in product_elements:
                    try:
                        # get Selector title class name
                        title_element = await product.query_selector('.name')
                        price_element = await product.query_selector('.prc')
                        discount_element = await product.query_selector('.bdg._dsct')
                        link_element = await product.query_selector('a.core')
                        image_element = await product.query_selector('img.img')
                        if title_element:
                            title = await title_element.inner_text()
                        else:
                            title = 'not found'
                        # using ternary on python
                        price = await price_element.inner_text() if price_element else 'Not Found'
                        discount = await discount_element.inner_text() if discount_element else 'No discount'
                        link = await link_element.get_attribute('href') if link_element else 'No link detail'
                        image = await image_element.get_attribute('src') if image_element else 'No image'

                        # append all 
                        products.append({
                            'title' : title,
                            'price' : price,
                            'discount' : discount,
                            "link": f"https://www.jumia.co.ke{link}",
                            "image": image
                        })
                    except Exception as e:
                        print(f"Error extracting Product: {e}")
                        continue
                # next button paginate
                next_btn= await page.query_selector('a[aria-label="Next Page"]')
                if not next_btn:
                    break
                await next_btn.click()
                # wait for the page to load card
                await page.wait_for_selector('article.prd')
                page_number = page_number + 1
            await browser.close()

            if output_format == 'csv':
                with open(f"{query}_products.csv", "w", newline="", encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=["title","price","discount","link","image"])
                    writer.writeheader()
                    writer.writerows(products)
            elif output_format == 'json':
                with open(f"{query}_products.json", "w", encoding='utf-8') as file:
                    json.dump(products, file, indent=4)
            print(f"scraped {len(products)} product. Dta saved to {query}_products.{output_format}")

        except Exception as e:
            print({e})

# asyncio.run(main_scraping(query="gas cooker", output_format='csv', max_pages=5))    
asyncio.run(main_scraping(query="huawei", output_format='json', max_pages=5))    


