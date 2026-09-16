# main.py
import asyncio
from scraper import JobStreetScraper

def main():
    keyword = input("Masukkan keyword pencarian (misal: python developer): ")
    if not keyword.strip():
        print("Keyword tidak boleh kosong!")
        return

    scraper = JobStreetScraper(query=keyword)
    asyncio.run(scraper.run())

if __name__ == "__main__":
    main()