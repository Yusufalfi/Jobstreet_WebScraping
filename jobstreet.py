import asyncio
import csv
import json
import time
from playwright.async_api import async_playwright
# query='query', output_format='csv', max_pages= 5
async def scraping_jobstreet(query='query'):
    async with async_playwright() as p:
        try:
            open_browser = await p.chromium.launch(headless=False)
            page = await open_browser.new_page()
            await page.goto('https://id.jobstreet.com/en')
            print(await page.title())

            # selector input search
            input_search = await page.wait_for_selector('input[name="keywords"]')
            # fill input 
            fill_input = await page.fill('input[name="keywords"]', query)
            enter = await page.press('input[name="keywords"]', "Enter")
            
            await open_browser.close()

        except:
            pass
asyncio.run(scraping_jobstreet("Programmer"))
