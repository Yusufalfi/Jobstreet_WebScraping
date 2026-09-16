import asyncio
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
        print("[MAIN] Membuka browser dengan mode Anti-Detection...")

        # Launch browser tanpa flag automation bawaan
        browser = await p.chromium.launch(
            headless=False,
            ignore_default_args=["--enable-automation"],
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport=None
        )

        # Injeksi script anti-webdriver
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = await context.new_page()

        # Format URL pencarian langsung (misal: "python developer" -> "python-developer-jobs")
        formatted_query = query.strip().replace(" ", "-")
        search_url = f"https://id.jobstreet.com/id/{formatted_query}-jobs"

        print(f"[MAIN] Langsung menuju URL pencarian: {search_url}")
        await page.goto(search_url, wait_until="domcontentloaded")

        # Bersihkan modal login jika terdeteksi muncul
        await page.wait_for_timeout(1000)
        await page.evaluate("""
            () => {
                const modals = document.querySelectorAll('div[role="dialog"], [data-automation="auth-modal"]');
                modals.forEach(el => el.remove());
                const backdrops = document.querySelectorAll('div[class*="backdrop"], div[class*="overlay"]');
                backdrops.forEach(el => el.remove());
                document.body.style.overflow = 'unset';
            }
        """)

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
            print(f"[MAIN] Ditemukan {len(job_cards)} job di halaman ini.")

            detail_links = []

            for card in job_cards:
                job_id = await card.get_attribute("data-job-id")
                if not job_id:
                    continue

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

            # Ambil detail via context baru
            detail_page = await context.new_page()
            for job in detail_links:
                full_description, work_type = await scrape_detail(detail_page, job["link"])
                job["full_description"] = full_description
                job["work_type"] = work_type
            await detail_page.close()

            # Save per halaman
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
