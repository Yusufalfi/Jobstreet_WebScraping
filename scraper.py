
import asyncio
import re
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from config import BASE_URL, USER_AGENT, SELECTORS

class JobStreetScraper:
    def __init__(self, query: str, salary_code: str, date_code: str, max_limit: int, logger_func=print, max_concurrent_tabs: int = 5):
        self.query = query
        self.salary_code = salary_code
        self.date_code = date_code
        self.max_limit = max_limit
        self.log = logger_func
        self.visited_urls = set()
        self.max_concurrent_tabs = max_concurrent_tabs  # Fixed ke 5 tab

    def build_url(self) -> str:
        formatted_query = self.query.strip().replace(" ", "-")
        url_params = []

        if self.date_code:
            url_params.append(f"daterange={self.date_code}")
        if self.salary_code:
            url_params.append(f"salaryrange={self.salary_code}&salarytype=monthly")

        query_string = "&".join(url_params)
        target_url = f"{BASE_URL}/id/{formatted_query}-jobs"
        if query_string:
            target_url += f"?{query_string}"

        return target_url

    def parse_posted_date(self, date_text: str) -> str:
        if not date_text or date_text == "N/A":
            return datetime.now().strftime("%d-%m-%Y")

        text_lower = date_text.lower().strip()
        now = datetime.now()

        days_match = re.search(r'(\d+)\s*(hari|d\b|day)', text_lower)
        if days_match:
            days_ago = int(days_match.group(1))
            target_date = now - timedelta(days=days_ago)
            return target_date.strftime("%d-%m-%Y")

        if any(unit in text_lower for unit in ["jam", "j lalu", "menit", "m lalu", "hour", "min"]):
            return now.strftime("%d-%m-%Y")

        return now.strftime("%d-%m-%Y")

    async def scrape_detail_task(self, context, semaphore, job_item, index: int, total: int, progress_tracker: dict):
        """Worker task untuk mengekstrak detail dengan Error Handling independen & Log Progress."""
        async with semaphore:
            self.log(f"[START] Opening detail ({index}/{total}): {job_item['title'][:25]}...")
            
            page = None
            full_description, work_type, raw_posted_date = "N/A", "N/A", ""

            # ERROR HANDLING PER-TAB (catch failed agar tab lain tidak terpengaruh)
            try:
                page = await context.new_page()
                
                # Memblokir media/font berat agar load time  cepat
                # await page.route("**/*.{png,jpg,jpeg,svg,webp,woff,woff2,ttf}", lambda route: route.abort())
                await page.goto(job_item["link"], wait_until="domcontentloaded", timeout=12000)

                details_el = await page.query_selector(SELECTORS["detail_container"])
                if details_el:
                    full_description = await details_el.inner_text()

                work_type_el = await page.query_selector(SELECTORS["work_type"])
                if work_type_el:
                    work_type = await work_type_el.inner_text()

                date_el = await page.query_selector('span:has-text("Diposting"), span:has-text("Diiklankan")')
                if date_el:
                    raw_posted_date = await date_el.inner_text()

            except Exception as e:
                # Jika 1 tab timeout/error, catat error di log & tetap lanjut
                self.log(f" fail load tab ({index}/{total}) [{job_item['title'][:20]}]: {e}")
            finally:
                if page:
                    await page.close()  #  tutup tab meskipun error

            # Simpan hasil ekstraksi (atau fallback jika error)
            job_item["posted_date"] = self.parse_posted_date(raw_posted_date)
            job_item["full_description"] = full_description.strip()
            job_item["work_type"] = work_type.strip()

            # MONITORING PROGRESS
            progress_tracker["completed"] += 1
            self.log(f"[INFO] Completed tab {progress_tracker['completed']} of {total} | {job_item['title'][:25]}")

    async def _clean_modals(self, page):
        await page.evaluate("""
            () => {
                const modals = document.querySelectorAll('div[role="dialog"], [data-automation="auth-modal"]');
                modals.forEach(el => el.remove());
                const backdrops = document.querySelectorAll('div[class*="backdrop"], div[class*="overlay"]');
                backdrops.forEach(el => el.remove());
                document.body.style.overflow = 'unset';
            }
        """)

    async def run(self) -> list:
        all_scraped_jobs = []
        target_url = self.build_url()

        self.log(f"[SCRAPER] Target URL Filter: {target_url}")
        self.log(f"[SCRAPER] Limit kuota data: {self.max_limit}")
        self.log(f"[SCRAPER] Parallel Execution: Max {self.max_concurrent_tabs} tabs bersamaan")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                ignore_default_args=["--enable-automation"],
                args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
            )

            context = await browser.new_context(user_agent=USER_AGENT, viewport=None)
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
            page = await context.new_page()

            try:
                await page.goto(target_url, wait_until="domcontentloaded")
                await page.wait_for_timeout(1000)
                await self._clean_modals(page)

                await page.wait_for_selector(SELECTORS["job_card"])
                page_number = 1

                while True:
                    self.log(f"\n--- Halaman {page_number} ---")

                    previous_height = 0
                    while True:
                        await page.evaluate("window.scrollBy(0, 500);")
                        await page.wait_for_timeout(300)
                        new_height = await page.evaluate("document.body.scrollHeight")
                        if new_height == previous_height:
                            break
                        previous_height = new_height

                    job_cards = await page.query_selector_all(SELECTORS["job_card"])
                    self.log(f"[DEBUG] Ditemukan {len(job_cards)} kartu lowongan di halaman ini.")

                    page_jobs = []
                    for card in job_cards:
                        if len(all_scraped_jobs) + len(page_jobs) >= self.max_limit:
                            break

                        job_id = await card.get_attribute("data-job-id")
                        if not job_id:
                            continue

                        full_link = f"{BASE_URL}/id/job/{job_id}?type=standard&ref=search-standalone&origin=card"
                        if full_link in self.visited_urls:
                            continue
                        self.visited_urls.add(full_link)

                        title_el = await card.query_selector(SELECTORS["title"])
                        title = await title_el.inner_text() if title_el else "N/A"

                        company_el = await card.query_selector(SELECTORS["company"])
                        company = await company_el.inner_text() if company_el else "N/A"

                        salary_el = await card.query_selector(SELECTORS["salary"])
                        salary = await salary_el.inner_text() if salary_el else ""
                        salary_clean = salary.strip() if salary else "Salary Not Displayed"

                        location_els = await card.query_selector_all(SELECTORS["location"])
                        locations = [await loc.inner_text() for loc in location_els]

                        desc_el = await card.query_selector(SELECTORS["teaser"])
                        description = await desc_el.inner_text() if desc_el else "N/A"

                        page_jobs.append({
                            "title": title.strip(),
                            "company": company.strip(),
                            "salary": salary_clean,
                            "location": ", ".join(locations).strip(),
                            "short_description": description.strip(),
                            "link": full_link
                        })

                    # === PARALLEL SCRAPING DETAIL ===
                    if page_jobs:
                        semaphore = asyncio.Semaphore(self.max_concurrent_tabs)
                        progress_tracker = {"completed": 0}
                        total_jobs_in_page = len(page_jobs)

                        tasks = []
                        for idx, job in enumerate(page_jobs, 1):
                            task = self.scrape_detail_task(
                                context, semaphore, job, idx, total_jobs_in_page, progress_tracker
                            )
                            tasks.append(task)

                        await asyncio.gather(*tasks)
                        all_scraped_jobs.extend(page_jobs)


                    # Setelah selesai scraping detail di halaman saat ini
                    if page_jobs:
                        semaphore = asyncio.Semaphore(self.max_concurrent_tabs)
                        progress_tracker = {"completed": 0}
                        total_jobs_in_page = len(page_jobs)

                        tasks = []
                        for idx, job in enumerate(page_jobs, 1):
                            task = self.scrape_detail_task(
                                context, semaphore, job, idx, total_jobs_in_page, progress_tracker
                            )
                            tasks.append(task)

                        await asyncio.gather(*tasks)
                        all_scraped_jobs.extend(page_jobs)

                    if len(all_scraped_jobs) >= self.max_limit:
                        self.log(f"[STOP] Total target data tercapai ({len(all_scraped_jobs)} items).")
                        break

                    # Pagination
                    await page.evaluate("document.querySelector('footer')?.remove()")
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight - 800);")
                    await page.wait_for_timeout(800)

                    next_button = await page.query_selector(SELECTORS["next_button"])
                    if not next_button:
                        self.log("[INFO] Tombol Next tidak ditemukan. Halaman terakhir.")
                        break

                    await next_button.click()
                    await page.wait_for_load_state("networkidle")
                    page_number += 1

            except Exception as e:
                self.log(f"[CRITICAL ERROR] Error saat scraping: {e}")
            finally:
                await browser.close()

        return all_scraped_jobs