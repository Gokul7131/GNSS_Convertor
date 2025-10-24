import os
import subprocess
import gzip
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta
import sys
import time
import psutil  # Used for process termination

CDDIS_URL = "https://cddis.nasa.gov/archive/gnss/data/daily"
STATION_MAP = {
    "DAGR": "DAGR00GBR",
    "POL2": "POL200KGZ",
    "PIMO": "PIMO00PHL",
    "HYDE": "HYDE00IND",
    "IISC": "IISC00IND",
    "LHAZ": "LHAZ00CHN",
    "CUSV": "CUSV00THA",
    "MAL2": "MAL200KEN",
    "COCO": "COCO00AUS",
    "KIT3": "KIT300UZB",
    "TEHN": "TEHN00IRN",
    "ADIS": "ADIS00ETH",
}
STATIONS = list(STATION_MAP.keys())

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def terminate_processes(process_name):
    """ Terminates all processes with a given name """
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        if process_name.lower() in proc.info['name'].lower():
            print(f"Terminating process {proc.info['name']} (PID {proc.info['pid']})")
            proc.terminate()
            proc.wait()

def safe_delete(file_path):
    """ Safely deletes a file, waiting for it to be closed before removal """
    if os.path.exists(file_path):
        try:
            # Check if file is being used by another process
            for _ in range(5):  # Try for 5 seconds
                if not file_in_use(file_path):
                    os.remove(file_path)
                    print(f"Deleted {file_path}")
                    return
                time.sleep(1)  # Wait a bit before checking again
            print(f"Failed to delete {file_path}, file might still be in use.")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

def file_in_use(file_path):
    """ Checks if a file is currently in use by another process """
    try:
        with open(file_path, 'r+'):
            return False  # File is not locked
    except IOError:
        return True  # File is locked by another process

def ensure_cookie_login(cookie_file, proxy_url, regenerate=False):
    """ Ensure the user is logged in and cookies are available """
    if regenerate or not os.path.exists(cookie_file):
        # If regenerate is True or no cookies exist, create a new session
        login_url = "https://urs.earthdata.nasa.gov"
        curl_cmd = [resource_path("curl.exe")]
        if proxy_url:
            curl_cmd += ["--proxy", proxy_url]
        curl_cmd += ["-n", "-c", cookie_file, "-L", "-o", os.devnull, login_url]
        subprocess.run(curl_cmd, check=True)
        print("Cookies have been regenerated.")
    else:
        print("Using existing cookies.")

def download_file(url, output_path, cookie_file, proxy_url):
    """ Downloads a file, ensuring it's complete and valid """
    try:
        curl_cmd = [resource_path("curl.exe")]
        if proxy_url:
            curl_cmd += ["--proxy", proxy_url]
        curl_cmd += [
            "-b", cookie_file,
            "-L", "-o", output_path,
            url
        ]
        subprocess.run(curl_cmd, check=True)

        # Validate the file (ensure it's not an HTML page)
        with open(output_path, 'rb') as f:
            head = f.read(10)
            if head.startswith(b'<!DOCTYPE') or head.startswith(b'<html'):
                print(f"Error: Received HTML instead of .gz for {output_path}.")
                os.remove(output_path)
                return False

        # Check if the file is large enough to be valid (not an empty file)
        if os.path.getsize(output_path) < 100:
            print(f"Error: File {output_path} is too small.")
            os.remove(output_path)
            return False

        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

class RinexDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RINEX Downloader")
        self.setup_gui()

    def setup_gui(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.grid()

        labels = ["Username", "Password", "Year", "Month"]
        self.entries = {}
        for i, label in enumerate(labels):
            ttk.Label(frm, text=label).grid(column=0, row=i, sticky="w")
            ent = ttk.Entry(frm, show="*" if label == "Password" else "")
            ent.grid(column=1, row=i)
            self.entries[label] = ent

        ttk.Label(frm, text="Output Folder").grid(column=0, row=len(labels), sticky="w")
        self.output_folder = tk.StringVar()
        ttk.Entry(frm, textvariable=self.output_folder, width=40).grid(column=1, row=len(labels))
        ttk.Button(frm, text="Browse", command=self.select_output_folder).grid(column=2, row=len(labels))

        self.use_proxy_var = tk.BooleanVar()
        self.use_proxy_check = ttk.Checkbutton(frm, text="Use Proxy", variable=self.use_proxy_var, command=self.toggle_proxy_fields)
        self.use_proxy_check.grid(column=0, row=5, columnspan=2, sticky="w")

        self.proxy_user_label = ttk.Label(frm, text="Proxy Username")
        self.proxy_user_entry = ttk.Entry(frm)
        self.proxy_pass_label = ttk.Label(frm, text="Proxy Password")
        self.proxy_pass_entry = ttk.Entry(frm, show="*")

        ttk.Button(frm, text="Start", command=self.run_process).grid(column=1, row=10, pady=10)
        self.progress = ttk.Progressbar(frm, length=300)
        self.progress.grid(column=0, row=11, columnspan=3, pady=5)

    def toggle_proxy_fields(self):
        if self.use_proxy_var.get():
            self.proxy_user_label.grid(column=0, row=6, sticky="w")
            self.proxy_user_entry.grid(column=1, row=6)
            self.proxy_pass_label.grid(column=0, row=7, sticky="w")
            self.proxy_pass_entry.grid(column=1, row=7)
        else:
            self.proxy_user_label.grid_remove()
            self.proxy_user_entry.grid_remove()
            self.proxy_pass_label.grid_remove()
            self.proxy_pass_entry.grid_remove()

    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)

    def run_process(self):
        output_dir = self.output_folder.get()
        log_path = os.path.join(output_dir, "rinex_download.log")

        def log(msg):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_path, "a") as log_file:
                log_file.write(f"{timestamp} - {msg}\n")
            print(f"{timestamp} - {msg}")

        creds = {key: entry.get() for key, entry in self.entries.items()}
        year = int(creds["Year"])
        month = int(creds["Month"])

        netrc_path = os.path.expanduser("~/_netrc")
        cookie_file = os.path.join(output_dir, ".urs_cookies")

        if not os.path.exists(output_dir):
            messagebox.showerror("Error", "Output directory does not exist.")
            return

        proxy_url = ""
        if self.use_proxy_var.get():
            proxy_user = self.proxy_user_entry.get()
            proxy_pass = self.proxy_pass_entry.get().replace("#", "%23").replace("@", "%40")
            proxy_url = f"http://{proxy_user}:{proxy_pass}@"Enter your proxy adress"

        # Ensure cookies and terminate any lingering processes
        ensure_cookie_login(cookie_file, proxy_url, regenerate=True)
        terminate_processes("curl.exe")
        terminate_processes("CRX2RNX.exe")
        terminate_processes("GFZRNX.exe")

        days_in_month = (datetime(year, month % 12 + 1, 1) - timedelta(days=1)).day
        total_tasks = days_in_month * len(STATIONS)
        current_task = 0

        log("Starting download and conversion process.")

        for day in range(1, days_in_month + 1):
            doy = datetime(year, month, day).timetuple().tm_yday
            for station in STATIONS:
                full_code = STATION_MAP[station]
                yyyy = str(year)
                yy = yyyy[2:]
                ddd = f"{doy:03}"
                base_url = f"{CDDIS_URL}/{yyyy}/{ddd}/{yy}d"
                filename = f"{full_code}_R_{yyyy}{ddd}0000_01D_30S_MO.crx.gz"
                gz_url = f"{base_url}/{filename}"
                gz_path = os.path.join(output_dir, filename)

                log(f"Starting download for {filename}...")

                if not download_file(gz_url, gz_path, cookie_file, proxy_url):
                    log(f"Skipping {filename}: download failed.")
                    continue

                crx_path = gz_path[:-3]
                with gzip.open(gz_path, 'rb') as f_in, open(crx_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                os.remove(gz_path)

                subprocess.run([resource_path("CRX2RNX.exe"), crx_path], check=True)
                rnx_path = crx_path.replace(".crx", ".rnx")
                os.remove(crx_path)

                short_doy = f"{doy:03}"
                final_name = f"{station.lower()}{short_doy}0.25o"
                final_path = os.path.join(output_dir, final_name)
                subprocess.run([resource_path("GFZRNX.exe"), "-finp", rnx_path, "-fout", final_path, "-v", "2.11"], check=True)
                os.remove(rnx_path)

                log(f"Successfully processed {filename} → {final_name}")

                current_task += 1
                self.progress["value"] = (current_task / total_tasks) * 100
                self.root.update_idletasks()

        log("Download and conversion completed.")
        messagebox.showinfo("Done", "Download and conversion completed.")

# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    app = RinexDownloaderApp(root)
    root.mainloop()
