import tkinter as tk
from tkinter import messagebox, filedialog
from threading import Thread, Event
from concurrent.futures import ThreadPoolExecutor
import time
import random
import os
import zipfile
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

# ------------------ LICENSE KEY (NO LONGER ENFORCED) ------------------
LICENSE_KEY = "NED-1234-VALID"  # kept for compatibility; NOT used

# Global counters
successful_views = 0
stop_event = Event()

# ------------------ START VIEWER ------------------
def start_viewer():
    root = tk.Tk()
    app = YouTubeViewBotUI(root)
    root.mainloop()

def logout():
    import auth
    import sys
    sys.modules.pop("main")
    auth.signup_window()

# ------------------ UI CLASS ------------------
class YouTubeViewBotUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔥 Auto feed x")
        self.root.geometry("600x600")
        self.root.configure(bg="#1e1e2f")

        # Variables
        self.url = tk.StringVar()
        self.keywords = tk.StringVar()
        self.proxy_file_path = ""
        self.loop_minutes = tk.StringVar(value="0")
        self.min_watch = tk.StringVar(value="35")
        self.max_watch = tk.StringVar(value="60")

        # Logout button
        tk.Button(self.root, text="🚪 Logout", command=self.logout_and_exit, bg="#d63031", fg="white").pack(pady=5)
        tk.Label(root, text="🎥 Auto feed x", font=("Segoe UI", 16, "bold"), bg="#1e1e2f", fg="#00ffcc").pack(pady=15)

        # URL field
        tk.Label(root, text="Enter YouTube URL:", font=("Segoe UI", 11), bg="#1e1e2f", fg="white").pack()
        tk.Entry(root, textvariable=self.url, font=("Segoe UI", 10), width=50, bg="#2c2c3c", fg="white").pack(pady=5)

        # Keyword field
        tk.Label(root, text="Enter Keywords (comma separated):", font=("Segoe UI", 11), bg="#1e1e2f", fg="white").pack()
        tk.Entry(root, textvariable=self.keywords, font=("Segoe UI", 10), width=50, bg="#2c2c3c", fg="white").pack(pady=5)

        # Proxy file chooser
        tk.Button(root, text="📂 Choose Proxy File", command=self.select_proxy_file, font=("Segoe UI", 11), bg="#00b894", fg="white").pack(pady=10)

        # Test Proxy button
        tk.Button(root, text="🔍 Test Proxy", command=self.test_proxy, font=("Segoe UI", 11),
                  bg="#0984e3", fg="white").pack(pady=5)

        # Loop interval
        frame = tk.Frame(root, bg="#1e1e2f")
        frame.pack()
        tk.Label(frame, text="Repeat every (min):", font=("Segoe UI", 11), bg="#1e1e2f", fg="white").pack(side=tk.LEFT)
        tk.Entry(frame, textvariable=self.loop_minutes, font=("Segoe UI", 10), width=5, bg="#2c2c3c", fg="white").pack(side=tk.LEFT, padx=5)

        # Watch time range
        tk.Label(root, text="Watch time range (sec):", font=("Segoe UI", 11), bg="#1e1e2f", fg="white").pack(pady=(10, 0))
        watch_frame = tk.Frame(root, bg="#1e1e2f")
        watch_frame.pack()
        tk.Entry(watch_frame, textvariable=self.min_watch, width=5).pack(side=tk.LEFT)
        tk.Label(watch_frame, text="to", bg="#1e1e2f", fg="white").pack(side=tk.LEFT)
        tk.Entry(watch_frame, textvariable=self.max_watch, width=5).pack(side=tk.LEFT)

        # Start & Stop buttons
        tk.Button(root, text="🚀 Start Bot", command=self.start_bot_thread, font=("Segoe UI", 11), bg="#6c5ce7", fg="white").pack(pady=15)
        tk.Button(root, text="🛑 Stop Bot", command=self.stop_bot, font=("Segoe UI", 11), bg="#d63031", fg="white").pack(pady=(5, 15))

        # Status
        self.status_label = tk.Label(root, text="", font=("Segoe UI", 10), bg="#1e1e2f", fg="#00ffcc")
        self.status_label.pack()

        self.views_label = tk.Label(root, text="👁️ Views Simulated: 0", font=("Segoe UI", 10, "bold"), bg="#1e1e2f", fg="#fd79a8")
        self.views_label.pack(pady=5)

        self.proxy_result_label = tk.Label(root, text="", font=("Segoe UI", 9), bg="#1e1e2f", fg="#ffeaa7")
        self.proxy_result_label.pack(pady=5)

    # ------------------ UI METHODS ------------------
    def logout_and_exit(self):
        self.root.destroy()
        logout()

    def select_proxy_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            self.proxy_file_path = file_path
            messagebox.showinfo("File Selected", f"Using proxies from:\n{file_path}")

    def test_proxy(self):
        """Test first proxy in file using httpbin.org/ip"""
        if not self.proxy_file_path:
            messagebox.showerror("Error", "Please select a proxy file first.")
            return

        try:
            with open(self.proxy_file_path, 'r') as f:
                lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            if not lines:
                messagebox.showerror("Error", "Proxy file is empty or invalid.")
                return

            # Take first proxy for quick test
            test_line = lines[0]
            parts = test_line.split(":")
            if len(parts) == 2:
                proxy = {"ip": parts[0], "port": parts[1], "auth": None}
            elif len(parts) == 4:
                proxy = {"ip": parts[0], "port": parts[1],
                         "auth": {"username": parts[2], "password": parts[3]}}
            else:
                messagebox.showerror("Error", f"Invalid proxy format: {test_line}")
                return

            # Run test
            if watch_video_with_proxy("https://httpbin.org/ip", proxy, 5, 5):
                messagebox.showinfo("Proxy Test", "Proxy is working!")
            else:
                messagebox.showerror("Proxy Test", "Proxy failed. Check IP or credentials.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not test proxy:\n{e}")

    def start_bot_thread(self):
        stop_event.clear()
        url = self.url.get().strip()
        proxy_file = self.proxy_file_path
        try:
            loop_delay = int(self.loop_minutes.get())
        except:
            messagebox.showerror("Error", "Loop interval must be a number.")
            return

        if not url or not proxy_file:
            messagebox.showerror("Error", "Enter URL and select proxy file.")
            return

        # Keywords available via self.keywords.get() if needed later
        t = Thread(target=self.looping_bot, args=(url, proxy_file, loop_delay))
        t.start()

    def stop_bot(self):
        stop_event.set()
        self.status_label.config(text="❌ Stop signal sent. Waiting for threads to finish...")

    def looping_bot(self, url, proxy_file, loop_delay):
        while not stop_event.is_set():
            self.start_bot(url, proxy_file)
            if loop_delay <= 0:
                break
            time.sleep(loop_delay * 60)

    def start_bot(self, url, proxy_file_path):
        global successful_views
        try:
            with open(proxy_file_path, 'r') as f:
                proxies = []
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue  # Skip blank or comment lines

                    parts = line.split(":")
                    if len(parts) == 2:  # IP:PORT
                        proxies.append({"ip": parts[0], "port": parts[1], "auth": None})
                    elif len(parts) == 4:  # IP:PORT:USER:PASS
                        proxies.append({"ip": parts[0], "port": parts[1],
                                        "auth": {"username": parts[2], "password": parts[3]}})
                    else:
                        print(f"[!] Invalid proxy format (skipped): {line}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not read proxies:\n{e}")
            return

        min_watch = int(self.min_watch.get())
        max_watch = int(self.max_watch.get())

        # Single window default
        with ThreadPoolExecutor(max_workers=1) as executor:
            for proxy in proxies:
                if stop_event.is_set():
                    break
                executor.submit(self.watch_and_count, url, proxy, min_watch, max_watch)

    def watch_and_count(self, url, proxy, min_watch, max_watch):
        global successful_views
        if stop_event.is_set():
            return
        if watch_video_with_proxy(url, proxy, min_watch, max_watch):
            if not stop_event.is_set():
                successful_views += 1
                self.views_label.config(text=f"👁️ Views Simulated: {successful_views}")
                self.root.update_idletasks()  # Force GUI refresh

# ------------------ PROXY EXTENSION ------------------
def create_proxy_auth_extension(proxy_host, proxy_port, proxy_username, proxy_password):
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy", "tabs", "unlimitedStorage", "storage", "<all_urls>", "webRequest", "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        }
    }
    """
    background_js = f"""
    var config = {{
        mode: "fixed_servers",
        rules: {{
            singleProxy: {{
                scheme: "http",
                host: "{proxy_host}",
                port: parseInt({proxy_port})
            }},
            bypassList: ["localhost"]
        }}
    }};
    chrome.proxy.settings.set({{value: config, scope: "regular"}}, function(){{}});
    chrome.webRequest.onAuthRequired.addListener(
        function(details) {{
            return {{
                authCredentials: {{
                    username: "{proxy_username}",
                    password: "{proxy_password}"
                }}
            }};
        }},
        {{urls: ["<all_urls>"]}},
        ["blocking"]
    );
    """

    plugin_path = os.path.join(os.getcwd(), "proxy_auth_plugin.zip")
    with zipfile.ZipFile(plugin_path, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    return plugin_path

# ------------------ WATCH VIDEO FUNCTION ------------------
def watch_video_with_proxy(url, proxy, min_watch, max_watch):
    # Lazy import so the whole app doesn't crash if UC is missing
    try:
        import undetected_chromedriver as uc
    except ModuleNotFoundError as e:
        msg = str(e)
        if "distutils" in msg:
            messagebox.showerror(
                "Missing dependency",
                "undetected-chromedriver requires 'setuptools' (distutils).\n\n"
                "Run:\n  pip install setuptools packaging undetected-chromedriver"
            )
        else:
            messagebox.showerror(
                "Missing dependency",
                "undetected-chromedriver is not installed.\n\n"
                "Run:\n  pip install undetected-chromedriver"
            )
        return False

    try:
        options = uc.ChromeOptions()
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")

        proxy_address = f"{proxy['ip']}:{proxy['port']}"
        options.add_argument(f"--proxy-server=http://{proxy_address}")

        # Add proxy auth extension if needed
        if proxy["auth"]:
            plugin_path = create_proxy_auth_extension(
                proxy["ip"], proxy["port"],
                proxy["auth"]["username"], proxy["auth"]["password"]
            )
            options.add_extension(plugin_path)

        driver = uc.Chrome(options=options)
        driver.get(url)
        time.sleep(2)

        # Handle consent buttons
        try:
            consent_btn = driver.find_element(By.XPATH, '//button[contains(text(),"I agree") or contains(text(),"Accept all")]')
            consent_btn.click()
            time.sleep(1)
        except:
            pass

        # Auto play video muted
        driver.execute_script("""
            const video = document.querySelector('video');
            if (video) {
                video.muted = true;
                video.play();
            }
        """)
        driver.execute_script("window.scrollBy(0, 500);")

        actions = ActionChains(driver)
        actions.move_by_offset(random.randint(50, 300), random.randint(50, 300)).perform()

        # Random watch time
        time.sleep(random.randint(min_watch, max_watch))
        driver.quit()
        return True
    except Exception as e:
        try:
            proxy_address = f"{proxy['ip']}:{proxy['port']}"
        except Exception:
            proxy_address = "<unknown>"
        print(f"[!] Failed with {proxy_address}: {e}")
        return False

# ------------------ ENTRY POINT ------------------
def launch_viewer(user_info=None):
    # License enforcement removed; keep signature unchanged
    start_viewer()
