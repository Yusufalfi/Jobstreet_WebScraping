import asyncio
import json
import os
from playwright.async_api import async_playwright

async def scrape_detail(page, job_url):
    print(f" Buka halaman detail: {job_url}")
    full_description = "N/A"
    work_type = "N/A"
    try:
        await page.goto(job_url, wait_until="domcontentloaded", timeout=15000)

        details_el = await page.query_selector('div[data-automation="jobAdDetails"]')
        if details_el:
            full_description = await details_el.inner_text()

        work_type_el = await page.query_selector('[data-automation="job-detail-work-type"] a')
        if work_type_el:
            work_type = await work_type_el.inner_text()

    except Exception as e:
        print(f"Gagal ambil detail: {job_url} | {e}")

    return full_description.strip(), work_type.strip()

def save_jobs_to_json(query, new_jobs):
    filename = f"{query}_jobs.json"
    all_jobs = []

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                all_jobs = json.load(f)
            except json.JSONDecodeError:
                all_jobs = []

    all_jobs.extend(new_jobs)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=4, ensure_ascii=False)

    print(f"Data tersimpan. Total sementara: {len(all_jobs)} job.")

async def scraping_jobstreet(query):
    async with async_playwright() as p:
        print("[MAIN] Mulai Playwright...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("[MAIN] Buka homepage JobStreet...")
        await page.goto("https://id.jobstreet.com/", wait_until="networkidle")
        print(f"[MAIN] Ketik keyword: {query}")
        await page.fill('input[name="keywords"]', query)
        await page.press('input[name="keywords"]', "Enter")
        await page.wait_for_selector('article[data-automation="normalJob"]')

        page_number = 1
        visited_urls = set()

        while True:
            print(f"\n[MAIN] === Halaman {page_number} ===")

            # Scroll untuk load semua job
            previous_height = 0
            while True:
                await page.evaluate("window.scrollBy(0, 500);")
                await page.wait_for_timeout(500)
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height == previous_height:
                    break
                previous_height = new_height

            job_cards = await page.query_selector_all('article[data-automation="normalJob"]')
            print(f"[MAIN] Semua job card termuat di halaman ini.")
            print(f"  Ditemukan {len(job_cards)} job di halaman ini.")

            detail_links = []
            # jan di hapus old
            # for card in job_cards:
            #     title_el = await card.query_selector('a[data-automation="jobTitle"]')
            #     link = await title_el.get_attribute('href') if title_el else None
            #     if not link:
            #         continue
            #     full_link = f"https://www.jobstreet.co.id{link}"
            #     if full_link in visited_urls:
            #         continue
            #     visited_urls.add(full_link)

            #     title = await title_el.inner_text() if title_el else "N/A"

            #     company_el = await card.query_selector('a[data-automation="jobCompany"]')
            #     company = await company_el.inner_text() if company_el else "N/A"

            #     salary_el = await card.query_selector('span[data-automation="jobSalary"]')
            #     salary = await salary_el.inner_text() if salary_el else "N/A"

            #     location_els = await card.query_selector_all('[data-automation="jobCardLocation"] [data-automation="jobLocation"]')
            #     locations = [await loc.inner_text() for loc in location_els]
            #     location = ", ".join(locations)

            #     desc_el = await card.query_selector('[data-testid="job-card-teaser"]')
            #     description = await desc_el.inner_text() if desc_el else "N/A"

            #     detail_links.append({
            #         "title": title.strip(),
            #         "link": full_link,
            #         "company": company.strip(),
            #         "salary": salary.strip(),
            #         "location": location.strip(),
            #         "short_description": description.strip()
            #     })

            for card in job_cards:
                job_id = await card.get_attribute("data-job-id")
                if not job_id:
                    continue

                # Build link 
                full_link = f"https://id.jobstreet.com/id/job/{job_id}?type=standard&ref=search-standalone&origin=card"

                if full_link in visited_urls:
                    continue
                visited_urls.add(full_link)

                title_el = await card.query_selector('a[data-automation="jobTitle"]')
                title = await title_el.inner_text() if title_el else "N/A"

                company_el = await card.query_selector('a[data-automation="jobCompany"]')
                company = await company_el.inner_text() if company_el else "N/A"

                salary_el = await card.query_selector('span[data-automation="jobSalary"]')
                salary = await salary_el.inner_text() if salary_el else "N/A"

                location_els = await card.query_selector_all('[data-automation="jobCardLocation"] [data-automation="jobLocation"]')
                locations = [await loc.inner_text() for loc in location_els]
                location = ", ".join(locations)

                desc_el = await card.query_selector('[data-testid="job-card-teaser"]')
                description = await desc_el.inner_text() if desc_el else "N/A"

                detail_links.append({
                    "title": title.strip(),
                    "link": full_link,
                    "company": company.strip(),
                    "salary": salary.strip(),
                    "location": location.strip(),
                    "short_description": description.strip()
                })




            # Ambil detail
            detail_page = await browser.new_page()
            for job in detail_links:
                full_description, work_type = await scrape_detail(detail_page, job["link"])
                job["full_description"] = full_description
                job["work_type"] = work_type
            await detail_page.close()

            # Save langsung per halaman
            save_jobs_to_json(query, detail_links)

            # Cek tombol next
            await page.evaluate("""document.querySelector('footer')?.remove()""")
            await page.evaluate("""window.scrollTo(0, document.body.scrollHeight - 800);""")
            await page.wait_for_timeout(800)

            next_button = await page.query_selector('a[rel~="next"], a[aria-label="Next"]')
            if not next_button:
                print("[MAIN] Tidak ada tombol Next. Selesai scraping.")
                break
            await next_button.click()
            await page.wait_for_load_state("networkidle")
            page_number += 1

        await browser.close()
        print("[MAIN] Selesai scraping.")

if __name__ == "__main__":
    keyword = input("Masukkan keyword pencarian: ")
    asyncio.run(scraping_jobstreet(keyword))
