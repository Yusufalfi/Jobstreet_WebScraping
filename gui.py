# gui.py
import asyncio
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from config import DATE_RANGE_MAP, SALARY_MAP, LIMIT_MAP
from scraper import JobStreetScraper
from utils import save_data

class JobStreetGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("JobStreet Advanced Scraper Tool")
        self.root.geometry("580x680")
        self.root.resizable(False, False)

        self._build_ui()

    def _build_ui(self):
        # Container Form Input
        form_frame = ttk.LabelFrame(self.root, text=" Parameter & Filter Pencarian ", padding=15)
        form_frame.pack(fill="x", padx=15, pady=10)

        # Keyword Position
        ttk.Label(form_frame, text="Posisi / Keyword Pekerjaan:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_keyword = ttk.Entry(form_frame, width=35)
        self.entry_keyword.insert(0, "programmer")
        self.entry_keyword.grid(row=0, column=1, sticky="w", pady=5)

        # Dropdown Minimal Gaji
        ttk.Label(form_frame, text="Minimal Gaji (Bulanan):").grid(row=1, column=0, sticky="w", pady=5)
        self.combo_salary = ttk.Combobox(form_frame, values=list(SALARY_MAP.keys()), state="readonly", width=32)
        self.combo_salary.set("Rp 6.000.000")
        self.combo_salary.grid(row=1, column=1, sticky="w", pady=5)

        # Dropdown Tanggal Posting
        ttk.Label(form_frame, text="Tanggal Posting Pekerjaan:").grid(row=2, column=0, sticky="w", pady=5)
        self.combo_date = ttk.Combobox(form_frame, values=list(DATE_RANGE_MAP.keys()), state="readonly", width=32)
        self.combo_date.set("30 Hari Terakhir")
        self.combo_date.grid(row=2, column=1, sticky="w", pady=5)

        # Dropdown Limit Data
        ttk.Label(form_frame, text="Maksimal Jumlah Data:").grid(row=3, column=0, sticky="w", pady=5)
        self.combo_limit = ttk.Combobox(form_frame, values=list(LIMIT_MAP.keys()), state="readonly", width=32)
        self.combo_limit.set("50 Data")
        self.combo_limit.grid(row=3, column=1, sticky="w", pady=5)

        # Format Export (Radio Button)
        ttk.Label(form_frame, text="Format Export File:").grid(row=4, column=0, sticky="w", pady=5)
        self.export_format = tk.StringVar(value="excel")
        export_box = ttk.Frame(form_frame)
        export_box.grid(row=4, column=1, sticky="w", pady=5)
        ttk.Radiobutton(export_box, text="JSON", value="json", variable=self.export_format).pack(side="left", padx=5)
        ttk.Radiobutton(export_box, text="Excel (.xlsx)", value="excel", variable=self.export_format).pack(side="left", padx=5)

        # Tombol Start Scraping
        self.btn_start = ttk.Button(self.root, text="Start Scraping", command=self.on_start_click)
        self.btn_start.pack(pady=10, ipadx=20, ipady=4)

        # Text Log Viewer
        log_frame = ttk.LabelFrame(self.root, text=" Activity Log ", padding=10)
        log_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.log_widget = tk.Text(log_frame, state="disabled", wrap="word", bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9))
        self.log_widget.pack(fill="both", expand=True)

    def write_log(self, text: str):
        self.log_widget.config(state="normal")
        self.log_widget.insert(tk.END, text + "\n")
        self.log_widget.see(tk.END)
        self.log_widget.config(state="disabled")

    def on_start_click(self):
        keyword = self.entry_keyword.get().strip()
        if not keyword:
            messagebox.showwarning("Peringatan", "Keyword pekerjaan wajib diisi!")
            return

        self.btn_start.config(state="disabled")
        threading.Thread(target=self._run_async_process, daemon=True).start()

    def _run_async_process(self):
        asyncio.run(self._execute_scraping())

    async def _execute_scraping(self):
        query = self.entry_keyword.get().strip()
        salary_code = SALARY_MAP[self.combo_salary.get()]
        date_code = DATE_RANGE_MAP[self.combo_date.get()]
        max_limit = LIMIT_MAP[self.combo_limit.get()]
        fmt = self.export_format.get()

        self.write_log("==========================================")
        self.write_log(f"[START] Memulai Scraping Keyword: '{query}'")

        # Otomatis menggunakan 5 tab concurrent
        scraper = JobStreetScraper(
            query=query,
            salary_code=salary_code,
            date_code=date_code,
            max_limit=max_limit,
            max_concurrent_tabs=5,
            logger_func=self.write_log
        )

        results = await scraper.run()

        if results:
            save_data(query, results, fmt, logger_func=self.write_log)
            self.write_log(f"[SUCCESS] Berhasil mengumpulkan {len(results)} data!")
        else:
            self.write_log("[WARNING] Tidak ada data lowongan yang ditemukan/diekstrak.")

        self.write_log("==========================================\n")
        self.btn_start.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = JobStreetGUI(root)
    root.mainloop()