import asyncio
import csv
import json
import time
from playwright.async_api import async_playwright
# query='query', output_format='csv', max_pages= 5


async def scraping_jobstreet(query='query', max_pages= 5):
    async with async_playwright() as p:
        try:
            open_browser = await p.chromium.launch(
                headless=False,
                args=["--window-size=1280,800","--window-position=1920,0"]
            )

            page = await open_browser.new_page()
            await page.goto("https://www.jobstreet.co.id/", wait_until="networkidle")
            # print(await page.title())
        
            # search element 'Masuk'
            btn = page.locator('a[data-automation="sign in"]').first

            # get attribut href
            href = await btn.get_attribute("href")
            print("Href:", href)

            if href:
                full_url = f"https://id.jobstreet.com{href}"
                print("Pindah ke:", full_url)
                # waiting until all request idle (wait_until="networkidle") 
                await page.goto(full_url, wait_until="networkidle")
                print(">>> REDIRECT PAGE LOGIN!")
            else:
                print(">>>  ATTRIBUT HREF NOTHING!")

            input_email = page.locator('#emailAddress')
            await input_email.fill("Yusufalfi91@gmail.com")
            btn_send_code = page.locator('button[data-cy="login"]')
            await btn_send_code.click()
          

            # human manual or later connect to api gmail to obtain an otp 
            otp_code = input("input OTP from email: ")
            print(f"otp_code", otp_code)
            await asyncio.sleep(20)
            await page.locator('input[aria-label="verification input"]').fill(otp_code)
            # await page.locator('button:has-text("Masuk")').click()
            await asyncio.sleep(5)
            # selector input search, fill input, prees  snter
            await page.wait_for_selector('input[name="keywords"]')
            await page.fill('input[name="keywords"]', query)
            print(f"success input keyword")
            await page.press('input[name="keywords"]', "Enter")
            print(f"sucess press enter")
         
            

            # wait selector card
            await page.wait_for_selector('article[data-automation="normalJob"]') 
            scroll_increment = 200
            previous_height = 0

            while True:
                await page.evaluate(f"window.scrollBy(0, {scroll_increment});")
                scroll_now = await page.evaluate("window.scrollY")
                print(f"Scrolled to Y: {scroll_now}")
                await page.wait_for_timeout(1500)
                new_height = await page.evaluate("document.body.scrollHeight")
                print(f"New height: {new_height} | Previous height: {previous_height}")
                if new_height == previous_height:
                    break
                previous_height = new_height
                print("Scrolling done.")

            # get all card
            job_cards = await page.query_selector_all('article[data-automation="normalJob"]')
            # print(f"Total job cards: {len(job_cards)}")

            job_list = []
            page_number = 1

            while page_number <= max_pages:
                print(f"on page {page_number}")
                for card in job_cards:
                    try:
                        title_el = await card.query_selector('a[data-automation="jobTitle"]')
                        title = await title_el.inner_text() if title_el else ""
                        link = await title_el.get_attribute('href') if title_el else ""
                        company_el = await card.query_selector('a[data-automation="jobCompany"]')
                        company = await company_el.inner_text()  if company_el else "Nothing" 
                        salary_el = await card.query_selector('span[data-automation="jobSalary"]')
                        salary = await salary_el.inner_text() if salary_el else "Nothing"
                        location_els = await card.query_selector_all('span[data-automation="jobLocation"]')
                        # locations = [await loc.inner_text() for loc in location_els]
                        locations = []
                        for loc in location_els:
                            text = await  loc.inner_text()
                            locations.append(text)
                        location = ", ".join(locations)
                        desc_el = await card.query_selector('[data-testid="job-card-teaser"]')
                        description = await desc_el.inner_text() if desc_el else ""
                    except Exception as e:
                        print(f"Error extracting  job: {e}")
                        continue

                    job_list.append({
                        'title': title.strip(),
                        'link': f"https://www.jobstreet.co.id{link}" if link else "",
                        'company': company.strip(),
                        'location': location.strip(),
                        'salary': salary.strip(),
                        'description': description.strip(),
                    })
                # next button paginate
                next_button = await page.wait_for_selector('a[aria-label="Next"]')
                if not next_button:
                    break
                
                # check disable button
                is_disabled = await next_button.get_attribute('aria-disabled')
                if is_disabled == 'true':
                    print("next button disabled")
                    break
                
                print(f"click next page {page_number}")
                await next_button.click()
                # await load card next page
                await page.query_selector_all('article[data-automation="normalJob"]')
                page_number +=1

            print(f"Total get data job cards: {len(job_list)}")
            await open_browser.close()
        except:
            pass
asyncio.run(scraping_jobstreet("Programmer", max_pages=3))
