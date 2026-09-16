Set-Content -Path README.md -Value @'
# 🚀 JobStreet Advanced Scraper Tool

Aplikasi otomasi pencarian dan ekstraksi data lowongan kerja dari **JobStreet Indonesia** berbasis **Python**, **Playwright**, dan **Tkinter GUI**. Tool ini dirancang untuk mengumpulkan informasi pekerjaan secara cepat menggunakan konsep **Multi-Tab Concurrency** dan mengekspor hasilnya ke format **Excel (.xlsx)** atau **JSON**.

---

## 🛠️ Fitur Utama

- **GUI Intuitif**: Antarmuka desktop berbasis Tkinter yang mudah digunakan tanpa perlu mengubah script secara manual.
- **Multi-Tab Parallel Processing**: Menggunakan `asyncio.Semaphore` (5 concurrent tabs) untuk mempercepat ekstraksi detail pekerjaan hingga 5x lebih cepat.
- **Isolasi Error (Fault Tolerant)**: Kegagalan loading/timeout pada satu tab tidak akan menghentikan proses scraping tab lainnya.
- **Filter Pencarian Lengkap**: Dukungan filter berdasarkan keyword posisi, minimal gaji, tanggal posting, dan batasan jumlah data.
- **Export Data**: Menyimpan hasil ke dalam format **Excel (.xlsx)** dengan styling tabel otomatis atau **JSON**.
- **Real-Time Activity Log**: Monitoring progress pengerjaan langsung dari antarmuka GUI.

---

## 📋 Prasyarat System

- **Python**: Versi 3.9 atau yang lebih baru.
- **Git**: Terinstall di perangkat kamu.

---

## 📦 Panduan Instalasi

### 1. Clone Repository
Buka terminal / command prompt dan jalankan perintah berikut:

```bash
git clone [https://github.com/Yusufalfi/Jobstreet_WebScraping.git](https://github.com/Yusufalfi/Jobstreet_WebScraping.git)
cd Jobstreet_WebScraping