import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import requests
import zipfile
import io
import os
import sys
import threading
import subprocess
import psutil 

# --- THEME SETTINGS ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Color Palette (Dracula Theme inspired)
COLOR_BG = "#1e1e2e"       
COLOR_SIDEBAR = "#181825"
COLOR_ACCENT = "#cba6f7"    # Pastel Purple (Progress Bar)
COLOR_BTN_MAIN = "#a6e3a1"  # Green (Play tMod)
COLOR_BTN_SEC = "#89b4fa"   # Blue (Play Terraria)
COLOR_BTN_UPD = "#fab387"   # Orange (Update) - Distinct Color
FONT_MAIN = ("Segoe UI", 24, "bold")
FONT_BTN = ("Segoe UI", 14, "bold")
FONT_SUB = ("Segoe UI", 12)

GITHUB_REPO = "tModLoader/tModLoader"

class PremiumLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Launcher by MiyamGo")
        self.geometry("900x600") 
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)

        # Path Logic
        if getattr(sys, 'frozen', False):
            self.base_path = os.path.dirname(sys.executable)
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))

        icon_path = os.path.join(self.base_path, "app.ico")
        
        # Check if the file exists first, to prevent app crash if icon is missing
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.tmod_dir = os.path.join(self.base_path, "tModLoader")
        self.terraria_dir = os.path.join(self.base_path, "Terraria")
        self.target_tmod = None
        self.target_terraria = None

        # --- GRID LAYOUT ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0) 
        self.grid_rowconfigure(0, weight=1)

        # ================= LEFT: CONTROL PANEL =================
        self.pnl_left = ctk.CTkFrame(self, fg_color=COLOR_BG, corner_radius=0)
        self.pnl_left.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)

        # 1. Header Area
        self.lbl_title = ctk.CTkLabel(self.pnl_left, text="TMODLOADER\nLAUNCHER", 
                                      font=("Segoe UI", 32, "bold"), text_color="white", justify="left")
        self.lbl_title.pack(anchor="w", pady=(10, 5))

        self.lbl_ver = ctk.CTkLabel(self.pnl_left, text="Launcher v1.0 • MiyamGo", 
                                    font=("Segoe UI", 12, "bold"), text_color="gray")
        self.lbl_ver.pack(anchor="w", pady=(0, 20))

        # 2. Status & Progress Area (CLEAN, Info Only)
        self.status_frame = ctk.CTkFrame(self.pnl_left, fg_color="#313244", corner_radius=10)
        self.status_frame.pack(fill="x", pady=20, ipady=15)

        self.lbl_status = ctk.CTkLabel(self.status_frame, text="Status: Ready to Launch", font=FONT_BTN)
        self.lbl_status.pack(pady=(5, 5))

        # Percentage Label
        self.lbl_percent = ctk.CTkLabel(self.status_frame, text="0%", font=("Consolas", 12, "bold"), text_color=COLOR_ACCENT)
        self.lbl_percent.pack(anchor="e", padx=20)

        self.progress = ctk.CTkProgressBar(self.status_frame, height=15, corner_radius=8, progress_color=COLOR_ACCENT)
        self.progress.set(0)
        self.progress.pack(fill="x", padx=20, pady=(0, 10))

        # Spacer (Pushes buttons to the bottom)
        self.spacer = ctk.CTkLabel(self.pnl_left, text="", font=("Arial", 5))
        self.spacer.pack(expand=True)


        # 3. Action Buttons Group (ALL AT BOTTOM)
        
        # Update Button (Orange)
        self.btn_update = ctk.CTkButton(self.pnl_left, text="⟳ CHECK FOR UPDATES", 
                                        font=("Segoe UI", 12, "bold"), 
                                        fg_color=COLOR_BTN_UPD, text_color="#1e1e2e",
                                        height=40, hover_color="#f9e2af", 
                                        command=self.start_update_thread)
        self.btn_update.pack(fill="x", pady=(0, 10))

        # Vanilla Terraria Button (Blue)
        self.btn_play_terraria = ctk.CTkButton(self.pnl_left, text="▶ PLAY TERRARIA", 
                                               font=("Segoe UI", 20, "bold"), height=50, corner_radius=12,
                                               fg_color=COLOR_BTN_MAIN, hover_color="#94e2d5", text_color="#1e1e2e",
                                               command=lambda: self.launch_game(self.target_terraria, "Terraria"))
        self.btn_play_terraria.pack(fill="x", pady=(0, 10))

        # tModLoader Button (Green - MAIN)
        self.btn_play_tmod = ctk.CTkButton(self.pnl_left, text="▶ PLAY TMODLOADER", 
                                           font=("Segoe UI", 20, "bold"), height=50, corner_radius=12,
                                           fg_color=COLOR_BTN_MAIN, hover_color="#94e2d5", text_color="#1e1e2e",
                                           command=lambda: self.launch_game(self.target_tmod, "tModLoader"))
        self.btn_play_tmod.pack(fill="x", pady=(0, 10))


        # ================= RIGHT: IMAGE =================
        self.pnl_right = ctk.CTkFrame(self, fg_color="black", width=380, corner_radius=0)
        self.pnl_right.grid(row=0, column=1, sticky="nsew")
        
        self.load_image()
        self.scan_files()

    def load_image(self):
        img_path = os.path.join(self.base_path, "cover.png")
        try:
            if os.path.exists(img_path):
                pil_img = Image.open(img_path)
                my_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(380, 600))
                lbl_img = ctk.CTkLabel(self.pnl_right, text="", image=my_image)
                lbl_img.pack(fill="both", expand=True)
            else:
                self.pnl_right.configure(fg_color=COLOR_SIDEBAR)
                ctk.CTkLabel(self.pnl_right, text="PLACE\nCOVER.PNG\nHERE", 
                             font=("Segoe UI", 20, "bold"), text_color="#45475a").pack(expand=True)
        except Exception: pass

    # --- MAIN LOGIC (Remains the Same) ---
    def find_file_recursive(self, root_folder, valid_names):
        if not os.path.exists(root_folder): return None
        for root, dirs, files in os.walk(root_folder):
            for file in files:
                if file.lower() in [n.lower() for n in valid_names]:
                    return os.path.join(root, file)
        return None

    def scan_files(self):
        tmod_files = ["tModLoader.exe", "start-tmodloader.bat", "start-tmodloader.sh"]
        self.target_tmod = self.find_file_recursive(self.tmod_dir, tmod_files)
        
        if self.target_tmod:
            self.btn_play_tmod.configure(state="normal", text="▶ PLAY TMODLOADER")
            self.lbl_status.configure(text="Ready to Play", text_color=COLOR_BTN_MAIN)
        else:
            self.btn_play_tmod.configure(state="disabled", text="INSTALL TMODLOADER FIRST", fg_color="#45475a")
            self.lbl_status.configure(text="tModLoader Missing", text_color=COLOR_BTN_UPD)

        self.target_terraria = self.find_file_recursive(self.terraria_dir, ["Terraria.exe"])
        if self.target_terraria:
            self.btn_play_terraria.configure(state="normal")
        else:
            self.btn_play_terraria.configure(state="disabled", text="INSTALL TERRARIA FIRST", fg_color="#45475a")

    def is_running(self, path):
        exe = os.path.basename(path).lower()
        for p in psutil.process_iter(['name']):
            try:
                if p.info['name'] and exe in p.info['name'].lower(): return True
            except: pass
        return False

    def launch_game(self, path, name):
        if not path: return
        if self.is_running(path):
            messagebox.showwarning("Running", f"{name} is already active!")
            return
        try:
            subprocess.Popen([path], cwd=os.path.dirname(path))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def start_update_thread(self):
        self.btn_update.configure(state="disabled", text="CONNECTING...")
        self.btn_play_tmod.configure(state="disabled")
        threading.Thread(target=self.run_update).start()

    def run_update(self):
        try:
            self.lbl_status.configure(text="Fetching Release info...", text_color="white")
            api = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            data = requests.get(api, timeout=10).json()
            dl = next((a['browser_download_url'] for a in data['assets'] if "tModLoader.zip" in a['name']), None)
            
            if not dl: raise Exception("Zip not found")

            self.lbl_status.configure(text="Downloading...", text_color=COLOR_BTN_UPD)
            r = requests.get(dl, stream=True, timeout=15)
            total = int(r.headers.get('content-length', 0))
            done = 0
            buf = io.BytesIO()

            for chunk in r.iter_content(64*1024):
                buf.write(chunk)
                done += len(chunk)
                if total:
                    pct = done/total
                    self.progress.set(pct)
                    self.lbl_percent.configure(text=f"{int(pct*100)}%") 

            self.lbl_status.configure(text="Extracting Files...", text_color=COLOR_BTN_UPD)
            if not os.path.exists(self.tmod_dir): os.makedirs(self.tmod_dir)
            with zipfile.ZipFile(buf) as z: z.extractall(self.tmod_dir)

            self.progress.set(1.0)
            self.lbl_percent.configure(text="100%")
            self.lbl_status.configure(text="Update Success!", text_color=COLOR_BTN_MAIN)
            messagebox.showinfo("Success", "Update Completed!")

        except Exception as e:
            self.lbl_status.configure(text="Error", text_color="red")
            messagebox.showerror("Error", str(e))
        finally:
            self.btn_update.configure(state="normal", text="⟳ CHECK FOR UPDATES")
            self.scan_files()

if __name__ == "__main__":
    app = PremiumLauncher()
    app.mainloop()