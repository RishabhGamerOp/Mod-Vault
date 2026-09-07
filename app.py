import base64
import json
import os
import shutil
import threading
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from io import BytesIO
import customtkinter as ctk
import requests
from PIL import Image, ImageTk

# Set default theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class ModVaultApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        # Main Window Configuration
        self.title("ModVault — Minecraft Mod & Modpack Suite")
        self.geometry("880x700")
        self.resizable(False, False)

        self.set_app_icon()

        # Detect Minecraft instances on launch
        self.detected_instances = self.detect_minecraft_instances()
        self.save_directory = list(self.detected_instances.values())[0]
        self.found_results = []

        # App State Variables
        self.theme_mode = ctk.StringVar(value="Dark")
        self.accent_color = ctk.StringVar(value="Blue")
        self.curseforge_api_key = ctk.StringVar(value="")
        self.parallel_threads = ctk.IntVar(value=4)

        self.setup_ui()

    def set_app_icon(self):
        """Sets embedded window icon."""
        try:
            icon_data = base64.b64decode(
                "iVBORw0KGgoAAAANsu..."  # Embedded icon payload
            )
            img = Image.open(BytesIO(icon_data))
            self.icon_photo = ImageTk.PhotoImage(img)
            self.iconphoto(False, self.icon_photo)
        except Exception:
            pass

    def detect_minecraft_instances(self):
        """Auto-detects default .minecraft and launcher instance paths."""
        home = os.path.expanduser("~")
        instances = {
            "Downloads Folder": os.path.join(home, "Downloads"),
            "Default .minecraft": (
                os.path.join(
                    os.getenv("APPDATA", home), ".minecraft", "mods"
                )
                if os.name == "nt"
                else os.path.join(home, ".minecraft", "mods")
            ),
        }

        # Check for Prism Launcher instances
        prism_path = (
            os.path.join(
                os.getenv("APPDATA", home), "PrismLauncher", "instances"
            )
            if os.name == "nt"
            else os.path.join(
                home, ".local", "share", "PrismLauncher", "instances"
            )
        )
        if os.path.exists(prism_path):
            try:
                for folder in os.listdir(prism_path):
                    mod_path = os.path.join(prism_path, folder, ".minecraft")
                    if os.path.exists(mod_path):
                        instances[f"Prism: {folder}"] = mod_path
            except Exception:
                pass

        return instances

    def setup_ui(self):
        """Constructs the grid layout and navigation tabs."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top Header Banner
        self.header_frame = ctk.CTkFrame(
            self, corner_radius=0, fg_color="#1a1a2e", height=60
        )
        self.header_frame.grid(row=0, column=0, sticky="ew")

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="⚡ MODVAULT",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#00d2ff",
        )
        self.title_label.pack(side="left", padx=20, pady=15)

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Mods & Modpacks Management Engine",
            font=ctk.CTkFont(size=12),
            text_color="#8a8a9e",
        )
        self.subtitle_label.pack(side="left", pady=15)

        # Tab Navigation System
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=1, column=0, padx=15, pady=(5, 10), sticky="nsew")

        self.tab_installer = self.tabview.add("Downloader")
        self.tab_settings = self.tabview.add("Settings & Customization")

        self.build_installer_tab()
        self.build_settings_tab()

        # Bottom Progress Bar
        self.status_frame = ctk.CTkFrame(self, height=35, corner_radius=0)
        self.status_frame.grid(row=2, column=0, sticky="ew")

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready.",
            font=ctk.CTkFont(size=12),
            text_color="#aaaaaa",
        )
        self.status_label.pack(side="left", padx=15)

        self.progress_bar = ctk.CTkProgressBar(self.status_frame, width=220)
        self.progress_bar.pack(side="right", padx=15)
        self.progress_bar.set(0)

    def build_installer_tab(self):
        parent = self.tab_installer

        filter_frame = ctk.CTkFrame(parent)
        filter_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            filter_frame, text="Type:", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, padx=6, pady=10)
        self.type_dropdown = ctk.CTkOptionMenu(
            filter_frame, values=["Single Mod", "Modpack"], width=110
        )
        self.type_dropdown.grid(row=0, column=1, padx=4)

        ctk.CTkLabel(
            filter_frame, text="Platform:", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=2, padx=6, pady=10)
        self.platform_dropdown = ctk.CTkOptionMenu(
            filter_frame, values=["Modrinth", "CurseForge"], width=105
        )
        self.platform_dropdown.grid(row=0, column=3, padx=4)

        ctk.CTkLabel(
            filter_frame, text="Loader:", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=4, padx=6, pady=10)
        self.loader_dropdown = ctk.CTkOptionMenu(
            filter_frame,
            values=["fabric", "forge", "neoforge", "quilt"],
            width=100,
        )
        self.loader_dropdown.grid(row=0, column=5, padx=4)

        ctk.CTkLabel(
            filter_frame, text="Version:", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=6, padx=6, pady=10)
        self.version_entry = ctk.CTkEntry(filter_frame, width=75)
        self.version_entry.insert(0, "1.20.1")
        self.version_entry.grid(row=0, column=7, padx=4)

        search_frame = ctk.CTkFrame(parent)
        search_frame.pack(fill="x", padx=10, pady=5)

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Enter mod or modpack name (e.g., Sodium, JEI, RLCraft)...",
        )
        self.search_entry.pack(
            side="left", fill="x", expand=True, padx=10, pady=10
        )

        search_btn = ctk.CTkButton(
            search_frame,
            text="Search",
            width=100,
            fg_color="#007acc",
            command=self.execute_search,
        )
        search_btn.pack(side="right", padx=10)

        self.console_output = ctk.CTkTextbox(
            parent, font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.console_output.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.install_btn = ctk.CTkButton(
            btn_frame,
            text="⬇ Install Selected Item",
            fg_color="#009944",
            hover_color="#007733",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.start_download_thread,
        )
        self.install_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        backup_btn = ctk.CTkButton(
            btn_frame,
            text="📦 Backup /mods Folder",
            fg_color="#333344",
            hover_color="#444455",
            height=42,
            command=self.create_folder_backup,
        )
        backup_btn.pack(side="right", padx=(5, 0))

    def build_settings_tab(self):
        parent = self.tab_settings

        ui_card = ctk.CTkFrame(parent)
        ui_card.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            ui_card,
            text="🎨 Interface & Theme Settings",
            font=ctk.CTkFont(weight="bold", size=14),
        ).pack(anchor="w", padx=10, pady=(10, 5))

        theme_row = ctk.CTkFrame(ui_card, fg_color="transparent")
        theme_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(theme_row, text="UI Theme Mode:").pack(side="left", padx=5)
        self.theme_dropdown = ctk.CTkOptionMenu(
            theme_row,
            values=["Dark", "Light", "System"],
            variable=self.theme_mode,
            command=self.change_theme_mode,
        )
        self.theme_dropdown.pack(side="left", padx=10)

        ctk.CTkLabel(theme_row, text="Accent Color:").pack(
            side="left", padx=(20, 5)
        )
        self.color_dropdown = ctk.CTkOptionMenu(
            theme_row,
            values=["blue", "green", "dark-blue"],
            variable=self.accent_color,
            command=self.change_accent_color,
        )
        self.color_dropdown.pack(side="left", padx=10)

        instance_card = ctk.CTkFrame(parent)
        instance_card.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            instance_card,
            text="📂 Target Installation Directory",
            font=ctk.CTkFont(weight="bold", size=14),
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self.instance_dropdown = ctk.CTkOptionMenu(
            instance_card,
            values=list(self.detected_instances.keys()),
            command=self.on_instance_selected,
        )
        self.instance_dropdown.pack(fill="x", padx=10, pady=5)

        self.path_display = ctk.CTkEntry(instance_card)
        self.path_display.insert(0, self.save_directory)
        self.path_display.pack(
            side="left", fill="x", expand=True, padx=(10, 5), pady=10
        )

        browse_btn = ctk.CTkButton(
            instance_card, text="Browse", width=80, command=self.choose_folder
        )
        browse_btn.pack(side="right", padx=(5, 10), pady=10)

        perf_card = ctk.CTkFrame(parent)
        perf_card.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            perf_card,
            text="⚡ Download & Performance Tuning",
            font=ctk.CTkFont(weight="bold", size=14),
        ).pack(anchor="w", padx=10, pady=(10, 5))

        threads_row = ctk.CTkFrame(perf_card, fg_color="transparent")
        threads_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            threads_row, text="Parallel Modpack Downloads (Threads):"
        ).pack(side="left", padx=5)
        self.thread_slider = ctk.CTkSlider(
            threads_row,
            from_=1,
            to=12,
            number_of_steps=11,
            variable=self.parallel_threads,
        )
        self.thread_slider.pack(side="left", padx=10, fill="x", expand=True)

        self.thread_label = ctk.CTkLabel(
            threads_row, text=f"{self.parallel_threads.get()} Threads"
        )
        self.thread_label.pack(side="right", padx=10)
        self.thread_slider.configure(
            command=lambda val: self.thread_label.configure(
                text=f"{int(val)} Threads"
            )
        )

        maint_card = ctk.CTkFrame(parent)
        maint_card.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            maint_card,
            text="🛠 Storage Maintenance & Credentials",
            font=ctk.CTkFont(weight="bold", size=14),
        ).pack(anchor="w", padx=10, pady=(10, 5))

        clean_btn = ctk.CTkButton(
            maint_card,
            text="🧹 Clean Active Mods Directory",
            fg_color="#a83232",
            hover_color="#822020",
            command=self.clear_mods_folder,
        )
        clean_btn.pack(side="left", padx=10, pady=10)

        cf_entry = ctk.CTkEntry(
            maint_card,
            placeholder_text="Paste CurseForge API Key...",
            textvariable=self.curseforge_api_key,
            show="*",
        )
        cf_entry.pack(side="right", fill="x", expand=True, padx=10, pady=10)

    def change_theme_mode(self, mode):
        ctk.set_appearance_mode(mode)

    def change_accent_color(self, color):
        ctk.set_default_color_theme(color)

    def on_instance_selected(self, choice):
        self.save_directory = self.detected_instances[choice]
        self.path_display.delete(0, "end")
        self.path_display.insert(0, self.save_directory)

    def choose_folder(self):
        chosen = ctk.filedialog.askdirectory(initialdir=self.save_directory)
        if chosen:
            self.save_directory = chosen
            self.path_display.delete(0, "end")
            self.path_display.insert(0, chosen)

    def clear_mods_folder(self):
        if not os.path.exists(self.save_directory):
            return

        jars = [
            f
            for f in os.listdir(self.save_directory)
            if f.endswith(".jar") or f.endswith(".disabled")
        ]
        if not jars:
            self.log("ℹ No .jar files to clean in target folder.")
            return

        for jar in jars:
            try:
                os.remove(os.path.join(self.save_directory, jar))
            except Exception:
                pass

        self.log(
            f"🧹 Cleaned {len(jars)} old mod file(s) from {self.save_directory}."
        )

    def create_folder_backup(self):
        if not os.path.exists(self.save_directory):
            self.log("❌ Target directory does not exist to back up.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"Mods_Backup_{timestamp}"
        backup_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        out_zip = os.path.join(backup_dir, backup_name)

        shutil.make_archive(out_zip, "zip", self.save_directory)
        self.log(f"📦 Backup created successfully:\n{out_zip}.zip")

    def update_status(self, text, progress_val=0):
        self.status_label.configure(text=text)
        self.progress_bar.set(progress_val)

    def log(self, text):
        self.console_output.insert("end", text + "\n")
        self.console_output.see("end")

    def execute_search(self):
        query = self.search_entry.get().strip()
        version = self.version_entry.get().strip()
        loader = self.loader_dropdown.get().lower()
        platform = self.platform_dropdown.get()
        item_type = self.type_dropdown.get()

        if not query:
            return

        self.console_output.delete("1.0", "end")
        self.update_status("Searching...", 0.3)
        self.log(
            f"🔎 Searching {platform} for {item_type} '{query}' | MC {version} ({loader})...\n"
        )

        if platform == "Modrinth":
            threading.Thread(
                target=self.search_modrinth,
                args=(query, version, loader, item_type),
                daemon=True,
            ).start()

    def search_modrinth(self, query, version, loader, item_type):
        headers = {"User-Agent": "ModVault/1.0 (MinecraftModInstaller)"}
        project_type = "modpack" if item_type == "Modpack" else "mod"

        url = (
            f"https://api.modrinth.com/v2/search?"
            f"query={query}&facets=[[\"project_type:{project_type}\"],[\"categories:{loader}\"],[\"versions:{version}\"]]"
        )

        try:
            res = requests.get(url, headers=headers, timeout=10).json()
            hits = res.get("hits", [])
            self.found_results = hits

            if not hits:
                self.log("❌ No matching results found.")
                self.update_status("Idle", 0)
                return

            top = hits[0]
            self.log(f"✔ Found: {top['title']}")
            self.log(f"  Author: {top['author']}")
            self.log(f"  Summary: {top['description']}\n")
            self.update_status("Item selected and ready to download.", 1.0)

        except Exception as e:
            self.log(f"❌ Error fetching from Modrinth: {e}")
            self.update_status("Search Failed", 0)

    def start_download_thread(self):
        if not self.found_results:
            return
        threading.Thread(target=self.download_workflow, daemon=True).start()

    def download_file_worker(self, file_data):
        headers = {"User-Agent": "ModVault/1.0 (MinecraftModInstaller)"}
        download_url = file_data["downloads"][0]
        filename = os.path.basename(file_data["path"])

        file_bytes = requests.get(download_url, headers=headers).content
        out_path = os.path.join(self.save_directory, file_data["path"])
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        with open(out_path, "wb") as f:
            f.write(file_bytes)

        self.log(f"  ✔ Downloaded: {filename}")

    def install_modpack_file(self, mrpack_path):
        self.log("📦 Unpacking .mrpack archive...")

        extract_dir = os.path.join(self.save_directory, "temp_modpack")
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(mrpack_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        index_file = os.path.join(extract_dir, "modrinth.index.json")
        if not os.path.exists(index_file):
            self.log("❌ Invalid modpack archive: Missing index file.")
            return

        with open(index_file, "r") as f:
            index_data = json.load(f)

        files = index_data.get("files", [])
        total_files = len(files)
        max_threads = self.parallel_threads.get()

        self.log(
            f"🚀 Downloading {total_files} mods using {max_threads} parallel threads...\n"
        )

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            executor.map(self.download_file_worker, files)

        self.log("\n🎉 Modpack construction complete!")

    def download_workflow(self):
        item_type = self.type_dropdown.get()
        version = self.version_entry.get().strip()
        loader = self.loader_dropdown.get().lower()

        project_id = self.found_results[0]["project_id"]
        headers = {"User-Agent": "ModVault/1.0 (MinecraftModInstaller)"}

        url = f"https://api.modrinth.com/v2/project/{project_id}/version?game_versions=[\"{version}\"]&loaders=[\"{loader}\"]"
        res = requests.get(url, headers=headers, timeout=10).json()

        if not res:
            self.log("❌ No download found for this version/loader combination.")
            self.update_status("Error", 0)
            return

        file_info = res[0]["files"][0]
        download_url = file_info["url"]
        filename = file_info["filename"]

        mrpack_path = os.path.join(self.save_directory, filename)

        self.log(f"⬇ Downloading package {filename}...")
        file_bytes = requests.get(download_url, headers=headers).content

        with open(mrpack_path, "wb") as f:
            f.write(file_bytes)

        if item_type == "Modpack" and filename.endswith(".mrpack"):
            self.install_modpack_file(mrpack_path)


if __name__ == "__main__":
    app = ModVaultApp()
    app.mainloop()