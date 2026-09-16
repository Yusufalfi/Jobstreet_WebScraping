import asyncio
import csv
import json
from playwright.async_api import async_playwright


async def scraping_jobstreet(query="Programmer", max_pages=3):
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(
                headless=False,
                args=["--window-size=1280,800","--window-position=1920,0"]
            )
            page = await browser.new_page()
            await page.goto("https://www.jobstreet.co.id/", wait_until="networkidle")

            # Cari input keyword → ketik & Enter
            await page.wait_for_selector('input[name="keywords"]')
            await page.fill('input[name="keywords"]', query)
            await page.press('input[name="keywords"]', "Enter")
            print("Keyword input & search OK!")

            await page.wait_for_selector('article[data-automation="normalJob"]')
            print("Job cards loaded!")

            # Lazy load scroll di page pertama
            scroll_increment = 500
            previous_height = 0

            while True:
                await page.evaluate(f"window.scrollBy(0, {scroll_increment});")
                await page.wait_for_timeout(800)
                new_height = await page.evaluate("document.body.scrollHeight")
                print(f"New height: {new_height} | Previous: {previous_height}")
                if new_height == previous_height:
                    break
                previous_height = new_height

            print("Initial scroll done.")

            job_list = []
            page_number = 1

            while page_number <= max_pages:
                print(f"\n=== SCRAPING PAGE {page_number} ===")

                # Ambil semua job cards
                job_cards = await page.query_selector_all('article[data-automation="normalJob"]')
                print(f"Cards found: {len(job_cards)}")

                for card in job_cards:
                    try:
                        title_el = await card.query_selector('a[data-automation="jobTitle"]')
                        title = await title_el.inner_text() if title_el else ""
                        link = await title_el.get_attribute('href') if title_el else ""

                        company_el = await card.query_selector('a[data-automation="jobCompany"]')
                        company = await company_el.inner_text() if company_el else "N/A"

                        salary_el = await card.query_selector('span[data-automation="jobSalary"]')
                        salary = await salary_el.inner_text() if salary_el else "N/A"

                        location_els = await card.query_selector_all('[data-automation="jobCardLocation"] [data-automation="jobLocation"]')
                        locations = []
                        for loc in location_els:
                            loc_text = await loc.inner_text()
                            locations.append(loc_text)
                        location = ", ".join(locations)

                        desc_el = await card.query_selector('[data-testid="job-card-teaser"]')
                        print(f"desc_el", desc_el)
                        description = await desc_el.inner_text() if desc_el else "N/A"
                        print(f"description", description)

                         # ======== DETAIL PAGE ========
                        full_description = "N/A"
                        if link:
                            job_url = f"https://www.jobstreet.co.id{link}"
                            detail_page = await browser.new_page()
                            await detail_page.goto(job_url, wait_until="networkidle")
                            try:
                                work_type_el = await detail_page.query_selector('[data-automation="job-detail-work-type"] a')
                                work_type = await work_type_el.inner_text() if work_type_el else "N/A"
                                print("work_type: " + work_type)

                                await detail_page.wait_for_selector('div[data-automation="jobAdDetails"]', timeout=10000)
                                details_el = await detail_page.query_selector('div[data-automation="jobAdDetails"]')
                                full_description = await details_el.inner_text() if details_el else "N/A"
                                print(f"full_description" + full_description)
                            except:
                                print(f"Gagal ambil deskripsi detail: {job_url}")
                            await detail_page.close()

                        job_list.append({
                            "title": title.strip(),
                            "link": f"https://www.jobstreet.co.id{link}" if link else "",
                            "company": company.strip(),
                            "salary": salary.strip(),
                            "location": location.strip(),
                            "work_type": work_type.strip(),
                            "description": description.strip(),
                            "full_description": full_description.strip()
                        })

                    except Exception as e:
                        print(f"Error parsing card: {e}")
                        continue

                print(f"Collected jobs so far: {len(job_list)}")

                # === PAGINATION LOGIC ===
                # Matikan footer agar nggak nutup tombol
                await page.evaluate("""document.querySelector('footer')?.remove()""")

                # Scroll ke bawah → bantu biar tombol next muncul
                await page.evaluate("""window.scrollTo(0, document.body.scrollHeight - 800);""")
                await page.wait_for_timeout(800)

                # coba simulasi code bawah comment duluSSS untuk mengetahui posisi scroll height

                # 1. Cari Next by rel/aria
                next_buttons = await page.query_selector_all('a[rel~="next"]')
                if not next_buttons:
                    next_buttons = await page.query_selector_all('a[aria-label="Next"]')

                # 2. Fallback: cari page number
                if not next_buttons:
                    next_buttons = await page.query_selector_all(f'a[data-automation="page-{page_number + 1}"]')
                    print(f"next_buutons", next_buttons)

                print(f"Next button candidates: {len(next_buttons)}")

                next_button = None
                for btn in next_buttons:
                    href = await btn.get_attribute('href')
                    is_disabled = await btn.get_attribute('aria-disabled')
                    text = await btn.inner_text()
                    print(f"Candidate: href={href}, disabled={is_disabled}, text={text.strip()}")
                    if href and href != "#" and is_disabled != "true":
                        next_button = btn
                        break

                if not next_button:
                    print("Next not found → scraping done!")
                    break

                await next_button.scroll_into_view_if_needed()
                await next_button.hover()
                await page.wait_for_timeout(300)

                print(f"Clicking page {page_number + 1}")
                await next_button.click()
                await page.wait_for_load_state("networkidle")

                page_number += 1

            await browser.close()

            print(f"\n=== FINISHED: {len(job_list)} JOBS ===")

            # Save ke JSON
            with open(f"{query}_jobs.json", "w", encoding="utf-8") as f:
                json.dump(job_list, f, indent=4, ensure_ascii=False)
            print(f"Saved to {query}_jobs.json")

        except Exception as e:
            print(f"Fatal error: {e}")

asyncio.run(scraping_jobstreet())
