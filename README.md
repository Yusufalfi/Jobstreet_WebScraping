# JobStreet Advanced Scraper Tool

Aplikasi otomasi pencarian dan ekstraksi data lowongan kerja dari **JobStreet Indonesia** menggunakan **Python**, **Playwright**, dan **Tkinter GUI**.

Tool ini dirancang untuk membantu mengubah proses pengumpulan data lowongan kerja yang repetitif menjadi proses yang lebih terstruktur, cepat, dan mudah digunakan. Hasil scraping dapat diekspor ke **Excel (.xlsx)** atau **JSON**.

> **Note:** Tool ini dibuat untuk tujuan pembelajaran, eksperimen automation, dan portfolio project. Pastikan penggunaan scraper sesuai dengan Terms of Service, robots.txt, kebijakan situs, serta ketentuan hukum yang berlaku. Gunakan secara bertanggung jawab dan hindari membebani website dengan request berlebihan.

---

## ✨ Features

- **GUI Desktop**
  - Antarmuka berbasis Tkinter.
  - User dapat menjalankan scraper tanpa perlu mengubah source code secara manual.

- **Search Filters**
  - Keyword / posisi pekerjaan.
  - Minimal gaji.
  - Tanggal posting.
  - Jumlah maksimum data yang ingin dikumpulkan.

- **Job Detail Extraction**
  - Mengambil informasi lowongan dari halaman hasil pencarian dan halaman detail pekerjaan.
  - Data dapat diproses secara terstruktur sebelum diekspor.

- **Multi-Tab Concurrency**
  - Menggunakan `asyncio` dan `asyncio.Semaphore`.
  - Maksimal **5 halaman/tab diproses secara concurrent** untuk meningkatkan efisiensi pengambilan data.

- **Fault-Tolerant Processing**
  - Error atau timeout pada satu halaman tidak langsung menghentikan keseluruhan proses.
  - Proses dapat melanjutkan pengambilan data dari halaman lainnya.

- **Excel Export**
  - Export hasil ke `.xlsx`.
  - Data disusun dalam format tabel agar mudah dianalisis atau digunakan kembali.

- **JSON Export**
  - Export data dalam format `.json`.
  - Cocok untuk diproses kembali oleh aplikasi atau workflow automation lainnya.

- **Real-Time Activity Log**
  - Menampilkan progress scraping secara langsung melalui GUI.
  - Membantu memantau proses dan error yang terjadi.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Playwright | Browser automation & web data extraction |
| Asyncio | Asynchronous processing |
| Tkinter | Desktop GUI |
| OpenPyXL | Excel `.xlsx` export |
| JSON | Structured data export |

---

## 📋 System Requirements

- **Python 3.9+**
- **Git**
- Internet connection
- Chromium browser installed through Playwright

Recommended:

- Windows 10/11
- Python 3.10+

---

## 📦 Installation

### 1. Clone Repository

```bash
git clone https://github.com/Yusufalfi/Jobstreet_WebScraping.git
cd Jobstreet_WebScraping
```

### 2. Create Virtual Environment

#### Windows

```bash
python -m venv .env
.env\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv .env
source .env/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browser

```bash
playwright install chromium
```

---

## 🚀 Usage

### Run GUI Application

```bash
python gui.py
```

Setelah aplikasi terbuka, gunakan form yang tersedia untuk menentukan parameter scraping.

### Input Parameters

**1. Position / Job Keyword**

Masukkan keyword pekerjaan yang ingin dicari.

Contoh:

```text
Python Developer
Data Analyst
RPA Developer
Software Engineer
```

**2. Minimum Salary**

Pilih batas minimum gaji sesuai kebutuhan pencarian.

**3. Posted Date**

Pilih rentang waktu posting lowongan yang ingin dikumpulkan.

**4. Maximum Data**

Tentukan jumlah maksimum lowongan yang ingin diproses.

Contoh:

```text
50
100
500
```

**5. Export Format**

Pilih format output:

- Excel (`.xlsx`)
- JSON (`.json`)

**6. Start Scraping**

Klik **Start Scraping** untuk menjalankan proses.

Progress dan aktivitas scraper akan ditampilkan pada activity log.

---

## 🔄 How It Works

Secara umum, workflow aplikasi adalah:

```text
User Input
    ↓
Search JobStreet
    ↓
Apply Search Filters
    ↓
Collect Job Listings
    ↓
Open Job Details
    ↓
Process Multiple Tabs Concurrently
    ↓
Handle Timeout / Errors
    ↓
Collect Structured Data
    ↓
Export
 ┌───────────────┐
 │ Excel / JSON  │
 └───────────────┘
```

### Multi-Tab Processing

Detail lowongan diproses menggunakan asynchronous execution dengan concurrency limit.

Contoh konsep:

```python
asyncio.Semaphore(5)
```

Artinya scraper membatasi jumlah halaman yang diproses secara bersamaan hingga **5 concurrent tasks**.

Jumlah concurrency dapat disesuaikan berdasarkan kebutuhan dan kondisi lingkungan eksekusi.

---

## 📊 Example Output

Contoh informasi yang dapat dikumpulkan:

| Field | Example |
|---|---|
| Job Title | Python Developer |
| Company | Example Company |
| Location | Jakarta |
| Salary | Rp10.000.000 - Rp15.000.000 |
| Posted Date | 2 days ago |
| Job Type | Full Time |
| Description | Job description... |
| Job URL | https://... |

> Field yang tersedia dapat berbeda tergantung implementasi scraper dan struktur halaman JobStreet.

---

## 🎯 Project Objective

Project ini dibuat sebagai contoh bagaimana proses **pengumpulan data lowongan kerja yang repetitif** dapat diubah menjadi automation yang lebih terstruktur.

Daripada membuka dan mengumpulkan informasi lowongan satu per satu, user dapat menentukan kriteria pencarian melalui GUI, menjalankan proses secara otomatis, kemudian mendapatkan hasil dalam format yang siap digunakan kembali.

Project ini juga mendemonstrasikan beberapa konsep penting dalam automation:

- Browser automation
- Web data extraction
- Asynchronous programming
- Concurrent processing
- Error handling
- Data transformation
- File export
- Desktop GUI

---

## ⚠️ Responsible Scraping

Gunakan tool ini secara bertanggung jawab.

Sebelum menjalankan scraper terhadap website pihak ketiga:

1. Periksa **Terms of Service** website.
2. Periksa kebijakan `robots.txt` jika relevan.
3. Pastikan aktivitas scraping tidak mengganggu atau membebani layanan.
4. Gunakan concurrency dan request rate yang wajar.
5. Jangan mencoba melewati authentication, access control, CAPTCHA, atau mekanisme keamanan.
6. Perhatikan aturan mengenai penggunaan, penyimpanan, dan distribusi data yang dikumpulkan.
7. Untuk penggunaan komersial, lakukan review legal/compliance yang sesuai.

Repository ini tidak dimaksudkan untuk menghindari atau melewati mekanisme perlindungan website.

---

## 🧪 Development Notes

Project ini menggunakan browser automation sehingga perubahan pada struktur atau behavior website dapat menyebabkan scraper perlu diperbarui.

Jika terjadi error setelah perubahan website, beberapa bagian yang mungkin perlu diperiksa:

- Selector halaman.
- Struktur HTML.
- URL atau parameter pencarian.
- Pagination.
- Loading behavior.
- Timeout.
- Data extraction logic.

---

## 📈 Possible Future Improvements

Beberapa pengembangan yang dapat ditambahkan:

- [ ] Proxy support
- [ ] Retry mechanism dengan exponential backoff
- [ ] Configurable concurrency
- [ ] Resume scraping setelah proses terhenti
- [ ] Duplicate detection
- [ ] More advanced search filters
- [ ] CSV export
- [ ] Database storage
- [ ] Scheduling / automatic scraping
- [ ] Scraping statistics and summary
- [ ] Improved logging
- [ ] Packaged executable (`.exe`)

---

## 👨‍💻 Author

**Yusuf Alfi**

Automation / RPA Developer

Focused on:

- RPA Automation
- UiPath
- Python
- Playwright
- Web Automation
- Web Scraping
- Process Automation

---
