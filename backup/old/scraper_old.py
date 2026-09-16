# scraper.py
import asyncio
import re
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from config import BASE_URL, USER_AGENT, SELECTORS

class JobStreetScraper:
    def __init__(self, query: str, salary_code: str, date_code: str, max_limit: int, logger_func=print):
        self.query = query
        self.salary_code = salary_code
        self.date_code = date_code
        self.max_limit = max_limit
        self.log = logger_func
        self.visited_urls = set()

    def build_url(self) -> str:
        # Menyusun URL berdasarkan filter input user.
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
        
        # Konversi teks waktu JobStreet ke tanggal absolut (DD-MM-YYYY).
        # Contoh input: 'Diposting 4 hari yang lalu', 'Diiklankan 2 hari lalu', '3 jam yang lalu'
        
        if not date_text or date_text == "N/A":
            return datetime.now().strftime("%d-%m-%Y")

        text_lower = date_text.lower().strip()
        now = datetime.now()

        # Cari angka hari (misal: "diposting 4 hari yang lalu", "2 hari lalu", "14d ago")
        days_match = re.search(r'(\d+)\s*(hari|d\b|day)', text_lower)
        if days_match:
            days_ago = int(days_match.group(1))
            target_date = now - timedelta(days=days_ago)
            return target_date.strftime("%d-%m-%Y")

        #  postingan jam/menit (Posting hari ini)
        if any(unit in text_lower for unit in ["jam", "j lalu", "menit", "m lalu", "hour", "min"]):
            return now.strftime("%d-%m-%Y")

        return now.strftime("%d-%m-%Y")

    async def scrape_detail(self, page, job_url: str):
        full_description, work_type, raw_posted_date = "N/A", "N/A", ""
        try:
            await page.goto(job_url, wait_until="domcontentloaded", timeout=15000)
            
            # Deskripsi Pekerjaan
            details_el = await page.query_selector(SELECTORS["detail_container"])
            if details_el:
                full_description = await details_el.inner_text()

            # Tipe Pekerjaan (Full time / Part time)
            work_type_el = await page.query_selector(SELECTORS["work_type"])
            if work_type_el:
                work_type = await work_type_el.inner_text()

            #  Waktu Diposting dari Halaman Detail 
            date_el = await page.query_selector('span:has-text("Diposting"), span:has-text("Diiklankan")')
            if date_el:
                raw_posted_date = await date_el.inner_text()

        except Exception as e:
            self.log(f"[DEBUG-ERROR] Gagal scrape detail URL {job_url}: {e}")

        return full_description.strip(), work_type.strip(), raw_posted_date.strip()

    async def _clean_modals(self, page):
        #Hapus dialog modal login bawaan JobStreet.
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

                    # Smooth scrolling
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
                            self.log(f"[INFO] Batas limit kuota ({self.max_limit}) sudah terpenuhi.")
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

                        # GAJI: Jika kosong/N/A diubah ke "Salary Not Displayed"
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

                    # Scrape Detail & Tanggal Posting
                    if page_jobs:
                        detail_page = await context.new_page()
                        for idx, job in enumerate(page_jobs, 1):
                            curr_count = len(all_scraped_jobs) + idx
                            self.log(f" [{curr_count}/{self.max_limit}] Scrape Detail: {job['title'][:30]}...")
                            full_desc, work_type, raw_posted_date = await self.scrape_detail(detail_page, job["link"])
                            
                            # Konversi teks tanggal dari detail page (misal: "Diposting 4 hari yang lalu" -> 07-09-2026)
                            job["posted_date"] = self.parse_posted_date(raw_posted_date)
                            job["full_description"] = full_desc
                            job["work_type"] = work_type
                        await detail_page.close()

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