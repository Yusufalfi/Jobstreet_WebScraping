# config.py

BASE_URL = "https://id.jobstreet.com"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)

#  MAP FILTER UNTUK URL JOBSTREET
DATE_RANGE_MAP = {
    "Hari ini": "1",
    "3 Hari Terakhir": "3",
    "7 Hari Terakhir": "7",
    "14 Hari Terakhir": "14",
    "30 Hari Terakhir": "31"
}

SALARY_MAP = {
    "Tanpa Filter": "",
    "Rp 5.000.000": "5000000-",
    "Rp 6.000.000": "6000000-",
    "Rp 7.000.000": "7000000-",
    "Rp 9.000.000": "9000000-",
    "Rp 10.000.000": "10000000-",
    "Rp 15.000.000": "15000000-",
    "Rp 20.000.000": "20000000-"
}

LIMIT_MAP = {
    "30 Data": 30,
    "50 Data": 50,
    "100 Data": 100,
    "Semua Data": 500
}

# SELECTOR CSS (Ubah di sini jika HTML JobStreet berubah) 
SELECTORS = {
    "job_card": 'article[data-automation="normalJob"]',
    "title": 'a[data-automation="jobTitle"]',
    "company": 'a[data-automation="jobCompany"]',
    "salary": 'span[data-automation="jobSalary"]',
    "location": '[data-automation="jobCardLocation"] [data-automation="jobLocation"]',
    "teaser": '[data-testid="job-card-teaser"]',
    "detail_container": 'div[data-automation="jobAdDetails"]',
    "work_type": '[data-automation="job-detail-work-type"] a',
    "next_button": 'a[rel~="next"], a[aria-label="Next"]'
}