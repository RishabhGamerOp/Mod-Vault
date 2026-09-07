import base64
import json
import os
import shutil
import sys
import threading
import subprocess
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from io import BytesIO
import customtkinter as ctk
import requests
from PIL import Image, ImageTk

# Current Application Version
CURRENT_VERSION = "1.0.0"
# GitHub repository configuration
GITHUB_REPO = "RishabhGamerOp/Mod-Vault" 

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class ModVaultApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        # Window Setup
        self.title(f"ModVault v{CURRENT_VERSION} — Minecraft Suite")
        self.geometry("1080x750")
        self.minsize(980, 680)

        # Instance Detection
        self.detected_instances = self.detect_minecraft_instances()
        self.save_directory = list(self.detected_instances.values())[0]

        # App State
        self.theme_mode = ctk.StringVar(value="Dark")
        self.accent_color = ctk.StringVar(value="blue")
        self.parallel_threads = ctk.IntVar(value=4)
        self.image_cache = {}

        self.setup_ui()
        
        # Check for updates automatically on startup in background
        threading.Thread(target=self.check_for_updates, args=(True,), daemon=True).start()

    def detect_minecraft_instances(self):
        """Detects standard launcher folders on the system."""
        home = os.path.expanduser("~")
        instances = {
            "Downloads Folder": os.path.join(home, "Downloads"),
            "Default .minecraft": (
                os.path.join(os.getenv("APPDATA", home), ".minecraft", "mods")
                if os.name == "nt"
                else os.path.join(home, ".minecraft", "mods")
            ),
        }

        prism_path = (
            os.path.join(os.getenv("APPDATA", home), "PrismLauncher", "instances")
            if os.name == "nt"
            else os.path.join(home, ".local", "share", "PrismLauncher", "instances")
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
        """Constructs sidebar, main content area, and status bar."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ==================== SIDEBAR NAVIGATION ====================
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        self.brand_title = ctk.CTkLabel(
            self.sidebar,
            text="⚡ MODVAULT",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#00d2ff",
        )
        self.brand_title.grid(row=0, column=0, padx=20, pady=(25, 5))

        self.brand_subtitle = ctk.CTkLabel(
            self.sidebar,
            text=f"v{CURRENT_VERSION} Pro Suite",
            font=ctk.CTkFont(size=11),
            text_color="#8a8a9e",
        )
        self.brand_subtitle.grid(row=1, column=0, padx=20, pady=(0, 20))

        self.btn_nav_downloader = ctk.CTkButton(
            self.sidebar,
            text="🔍 Mod Downloader",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            height=38,
            fg_color="#1f538d",
            command=self.show_downloader_view,
        )
        self.btn_nav_downloader.grid(row=2, column=0, padx=15, pady=8, sticky="ew")

        self.btn_nav_settings = ctk.CTkButton(
            self.sidebar,
            text="⚙ Settings & Tools",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            height=38,
            fg_color="transparent",
            text_color=("#333", "#ccc"),
            hover_color=("#e0e0e0", "#2b2b2b"),
            command=self.show_settings_view,
        )
        self.btn_nav_settings.grid(row=3, column=0, padx=15, pady=8, sticky="ew")

        # Directory Indicator Card
        self.sidebar_folder_card = ctk.CTkFrame(self.sidebar, corner_radius=8)
        self.sidebar_folder_card.grid(row=5, column=0, padx=15, pady=20, sticky="ew")

        ctk.CTkLabel(
            self.sidebar_folder_card,
            text="TARGET DIRECTORY",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#8a8a9e",
        ).pack(anchor="w", padx=10, pady=(8, 2))

        self.lbl_sidebar_path = ctk.CTkLabel(
            self.sidebar_folder_card,
            text=os.path.basename(self.save_directory),
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        )
        self.lbl_sidebar_path.pack(anchor="w", padx=10, pady=(0, 8))

        # ==================== MAIN CONTAINER ====================
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        self.view_downloader = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_settings = ctk.CTkFrame(self.main_container, fg_color="transparent")

        self.build_downloader_view()
        self.build_settings_view()

        self.show_downloader_view()

        # ==================== STATUS BAR ====================
        self.status_frame = ctk.CTkFrame(self, height=35, corner_radius=0)
        self.status_frame.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="● System Ready",
            font=ctk.CTkFont(size=12),
            text_color="#00d2ff",
        )
        self.status_label.pack(side="left", padx=15)

        self.progress_bar = ctk.CTkProgressBar(self.status_frame, width=250)
        self.progress_bar.pack(side="right", padx=15)
        self.progress_bar.set(0)

    # ==================== VIEW SWITCHING ====================
    def show_downloader_view(self):
        self.view_settings.grid_forget()
        self.view_downloader.grid(row=0, column=0, sticky="nsew")
        self.btn_nav_downloader.configure(fg_color="#1f538d", text_color="white")
        self.btn_nav_settings.configure(fg_color="transparent", text_color=("#333", "#ccc"))

    def show_settings_view(self):
        self.view_downloader.grid_forget()
        self.view_settings.grid(row=0, column=0, sticky="nsew")
        self.btn_nav_settings.configure(fg_color="#1f538d", text_color="white")
        self.btn_nav_downloader.configure(fg_color="transparent", text_color=("#333", "#ccc"))

    # ==================== BUILD DOWNLOADER VIEW ====================
    def build_downloader_view(self):
        parent = self.view_downloader

        control_card = ctk.CTkFrame(parent, corner_radius=10)
        control_card.pack(fill="x", pady=(0, 15))

        filters_grid = ctk.CTkFrame(control_card, fg_color="transparent")
        filters_grid.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(filters_grid, text="Type:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.type_dropdown = ctk.CTkOptionMenu(filters_grid, values=["Single Mod", "Modpack"], width=115)
        self.type_dropdown.grid(row=0, column=1, padx=(0, 15))

        ctk.CTkLabel(filters_grid, text="Platform:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=(0, 5), sticky="w")
        self.platform_dropdown = ctk.CTkOptionMenu(filters_grid, values=["Modrinth", "CurseForge"], width=115)
        self.platform_dropdown.grid(row=0, column=3, padx=(0, 15))

        ctk.CTkLabel(filters_grid, text="Loader:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=4, padx=(0, 5), sticky="w")
        self.loader_dropdown = ctk.CTkOptionMenu(filters_grid, values=["fabric", "forge", "neoforge", "quilt"], width=110)
        self.loader_dropdown.grid(row=0, column=5, padx=(0, 15))

        ctk.CTkLabel(filters_grid, text="Version:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=6, padx=(0, 5), sticky="w")
        self.version_entry = ctk.CTkEntry(filters_grid, width=80)
        self.version_entry.insert(0, "1.20.1")
        self.version_entry.grid(row=0, column=7)

        search_row = ctk.CTkFrame(control_card, fg_color="transparent")
        search_row.pack(fill="x", padx=15, pady=(0, 15))

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="Search mods or modpacks (e.g., Sodium, JEI, RLCraft)...",
            height=40,
            font=ctk.CTkFont(size=13),
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self.execute_search())

        search_btn = ctk.CTkButton(
            search_row,
            text="⚡ Search",
            width=120,
            height=40,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#007acc",
            hover_color="#005999",
            command=self.execute_search,
        )
        search_btn.pack(side="right")

        self.results_scrollable = ctk.CTkScrollableFrame(parent, corner_radius=10, label_text="SEARCH RESULTS")
        self.results_scrollable.pack(fill="both", expand=True, pady=(0, 15))
        self.results_scrollable.grid_columnconfigure((0, 1), weight=1)

        self.lbl_placeholder = ctk.CTkLabel(
            self.results_scrollable,
            text="Enter a query above to explore available mods and modpacks.",
            font=ctk.CTkFont(size=14),
            text_color="#666677",
        )
        self.lbl_placeholder.pack(pady=60)

    # ==================== BUILD SETTINGS VIEW ====================
    def build_settings_view(self):
        parent = self.view_settings

        # Software Update Section Card
        update_card = ctk.CTkFrame(parent, corner_radius=10)
        update_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            update_card,
            text="🚀 SOFTWARE UPDATES",
            font=ctk.CTkFont(weight="bold", size=12),
            text_color="#00d2ff",
        ).pack(anchor="w", padx=15, pady=(15, 5))

        update_row = ctk.CTkFrame(update_card, fg_color="transparent")
        update_row.pack(fill="x", padx=15, pady=(0, 15))

        self.lbl_update_status = ctk.CTkLabel(
            update_row,
            text=f"Current Version: v{CURRENT_VERSION}",
            font=ctk.CTkFont(size=13),
        )
        self.lbl_update_status.pack(side="left", padx=(0, 15))

        self.btn_check_update = ctk.CTkButton(
            update_row,
            text="Check for Updates",
            height=32,
            fg_color="#007acc",
            hover_color="#005999",
            command=lambda: threading.Thread(target=self.check_for_updates, args=(False,), daemon=True).start(),
        )
        self.btn_check_update.pack(side="right")

        # UI Theme Options
        ui_card = ctk.CTkFrame(parent, corner_radius=10)
        ui_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            ui_card,
            text="🎨 APPEARANCE & THEME",
            font=ctk.CTkFont(weight="bold", size=12),
            text_color="#00d2ff",
        ).pack(anchor="w", padx=15, pady=(15, 5))

        theme_row = ctk.CTkFrame(ui_card, fg_color="transparent")
        theme_row.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(theme_row, text="UI Appearance Mode:").pack(side="left", padx=(0, 10))
        self.theme_dropdown = ctk.CTkOptionMenu(
            theme_row,
            values=["Dark", "Light", "System"],
            variable=self.theme_mode,
            command=self.change_theme_mode,
        )
        self.theme_dropdown.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(theme_row, text="Accent Color Theme:").pack(side="left", padx=(0, 10))
        self.color_dropdown = ctk.CTkOptionMenu(
            theme_row,
            values=["blue", "green", "dark-blue"],
            variable=self.accent_color,
            command=self.change_accent_color,
        )
        self.color_dropdown.pack(side="left")

        # Minecraft Target Selection
        instance_card = ctk.CTkFrame(parent, corner_radius=10)
        instance_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            instance_card,
            text="📂 TARGET MINECRAFT DIRECTORY",
            font=ctk.CTkFont(weight="bold", size=12),
            text_color="#00d2ff",
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.instance_dropdown = ctk.CTkOptionMenu(
            instance_card,
            values=list(self.detected_instances.keys()),
            command=self.on_instance_selected,
        )
        self.instance_dropdown.pack(fill="x", padx=15, pady=(0, 10))

        path_row = ctk.CTkFrame(instance_card, fg_color="transparent")
        path_row.pack(fill="x", padx=15, pady=(0, 15))

        self.path_display = ctk.CTkEntry(path_row, height=36)
        self.path_display.insert(0, self.save_directory)
        self.path_display.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(path_row, text="Browse...", width=90, height=36, command=self.choose_folder)
        browse_btn.pack(side="right")

        # Performance Settings
        perf_card = ctk.CTkFrame(parent, corner_radius=10)
        perf_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            perf_card,
            text="⚡ PERFORMANCE & MULTITHREADING",
            font=ctk.CTkFont(weight="bold", size=12),
            text_color="#00d2ff",
        ).pack(anchor="w", padx=15, pady=(15, 5))

        threads_row = ctk.CTkFrame(perf_card, fg_color="transparent")
        threads_row.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(threads_row, text="Parallel Download Threads:").pack(side="left", padx=(0, 15))
        self.thread_slider = ctk.CTkSlider(
            threads_row,
            from_=1,
            to=12,
            number_of_steps=11,
            variable=self.parallel_threads,
        )
        self.thread_slider.pack(side="left", fill="x", expand=True, padx=(0, 15))

        self.thread_label = ctk.CTkLabel(
            threads_row,
            text=f"{self.parallel_threads.get()} Threads",
            font=ctk.CTkFont(weight="bold"),
        )
        self.thread_label.pack(side="right")
        self.thread_slider.configure(command=lambda val: self.thread_label.configure(text=f"{int(val)} Threads"))

    # ==================== AUTO-UPDATER LOGIC ====================
    def check_for_updates(self, silent=False):
        """Fetches the latest release tag from GitHub and handles updates."""
        try:
            if not silent:
                self.update_status("Checking for app updates...", 0.3)

            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            res = requests.get(api_url, timeout=5)

            if res.status_code != 200:
                if not silent:
                    self.lbl_update_status.configure(text="No update server release found.")
                return

            data = res.json()
            latest_version = data.get("tag_name", "").lstrip("v")
            assets = data.get("assets", [])

            if latest_version and latest_version != CURRENT_VERSION:
                # Find downloadable .exe asset
                download_url = None
                for asset in assets:
                    if asset.get("name", "").endswith(".exe"):
                        download_url = asset.get("browser_download_url")
                        break

                if download_url:
                    self.lbl_update_status.configure(text=f"🚀 New Version v{latest_version} Available!")
                    self.btn_check_update.configure(
                        text="Update Now",
                        fg_color="#00a859",
                        hover_color="#008043",
                        command=lambda: threading.Thread(
                            target=self.apply_update, args=(download_url,), daemon=True
                        ).start(),
                    )
                    self.update_status(f"Update Available: v{latest_version}", 1.0)
                else:
                    if not silent:
                        self.lbl_update_status.configure(text=f"v{latest_version} released (No .exe attached).")
            else:
                if not silent:
                    self.lbl_update_status.configure(text=f"You are up to date! (v{CURRENT_VERSION})")
                    self.update_status("App up to date", 1.0)

        except Exception as e:
            if not silent:
                self.lbl_update_status.configure(text="Update check failed.")

    def apply_update(self, download_url):
        """Downloads new executable and spawns a updater script to swap files."""
        try:
            self.update_status("Downloading software update...", 0.5)
            self.btn_check_update.configure(state="disabled", text="Downloading...")

            # Path locations
            current_exe = sys.executable
            exe_dir = os.path.dirname(current_exe)
            new_exe = os.path.join(exe_dir, "ModVault_new.exe")

            # Download new executable
            response = requests.get(download_url, stream=True)
            with open(new_exe, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.update_status("Applying update & restarting...", 0.9)

            # Create updater script to swap executables after closing app
            bat_path = os.path.join(exe_dir, "update_installer.bat")
            bat_script = f"""@echo off
timeout /t 2 /nobreak > nul
move /y "{new_exe}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
            with open(bat_path, "w") as f:
                f.write(bat_script)

            # Run batch updater and terminate app
            subprocess.Popen([bat_path], shell=True)
            self.destroy()

        except Exception as e:
            self.update_status(f"Update failed: {str(e)}", 0)
            self.btn_check_update.configure(state="normal", text="Update Failed")

    # ==================== UTILITY & SEARCH METHODS ====================
    def change_theme_mode(self, mode):
        ctk.set_appearance_mode(mode)

    def change_accent_color(self, color):
        ctk.set_default_color_theme(color)

    def on_instance_selected(self, choice):
        self.save_directory = self.detected_instances[choice]
        self.path_display.delete(0, "end")
        self.path_display.insert(0, self.save_directory)
        self.lbl_sidebar_path.configure(text=os.path.basename(self.save_directory))

    def choose_folder(self):
        chosen = ctk.filedialog.askdirectory(initialdir=self.save_directory)
        if chosen:
            self.save_directory = chosen
            self.path_display.delete(0, "end")
            self.path_display.insert(0, chosen)
            self.lbl_sidebar_path.configure(text=os.path.basename(self.save_directory))

    def update_status(self, text, progress_val=0):
        self.status_label.configure(text=f"● {text}")
        self.progress_bar.set(progress_val)

    def execute_search(self):
        query = self.search_entry.get().strip()
        version = self.version_entry.get().strip()
        loader = self.loader_dropdown.get().lower()
        platform = self.platform_dropdown.get()
        item_type = self.type_dropdown.get()

        if not query:
            return

        for child in self.results_scrollable.winfo_children():
            child.destroy()

        self.update_status("Fetching results...", 0.3)

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
            f"query={query}&limit=10&facets=[[\"project_type:{project_type}\"],[\"categories:{loader}\"],[\"versions:{version}\"]]"
        )

        try:
            res = requests.get(url, headers=headers, timeout=10).json()
            hits = res.get("hits", [])

            if not hits:
                self.after(0, lambda: self.render_empty_state("No matching mods found."))
                self.update_status("No Results", 0)
                return

            self.after(0, lambda: self.render_mod_cards(hits))
            self.update_status(f"Found {len(hits)} items for MC {version}", 1.0)

        except Exception as e:
            self.after(0, lambda: self.render_empty_state(f"API Error: {str(e)}"))
            self.update_status("Search Error", 0)

    def render_empty_state(self, message):
        lbl = ctk.CTkLabel(
            self.results_scrollable,
            text=message,
            font=ctk.CTkFont(size=14),
            text_color="#666677",
        )
        lbl.pack(pady=60)

    def render_mod_cards(self, hits):
        for idx, item in enumerate(hits):
            row = idx // 2
            col = idx % 2

            card = ctk.CTkFrame(self.results_scrollable, corner_radius=8, fg_color="#1e1e28")
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            top_frame = ctk.CTkFrame(card, fg_color="transparent")
            top_frame.pack(fill="x", padx=10, pady=(10, 5))

            icon_label = ctk.CTkLabel(
                top_frame,
                text="📦",
                width=48,
                height=48,
                fg_color="#2b2b38",
                corner_radius=6,
                font=ctk.CTkFont(size=20),
            )
            icon_label.pack(side="left", padx=(0, 10))

            if item.get("icon_url"):
                threading.Thread(
                    target=self.load_thumbnail,
                    args=(item["icon_url"], icon_label),
                    daemon=True,
                ).start()

            title_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
            title_frame.pack(side="left", fill="x", expand=True)

            title_lbl = ctk.CTkLabel(
                title_frame,
                text=item["title"],
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w",
            )
            title_lbl.pack(fill="x")

            author_lbl = ctk.CTkLabel(
                title_frame,
                text=f"by {item.get('author', 'Unknown')}",
                font=ctk.CTkFont(size=11),
                text_color="#8a8a9e",
                anchor="w",
            )
            author_lbl.pack(fill="x")

            desc_text = item.get("description", "No description available.")
            if len(desc_text) > 85:
                desc_text = desc_text[:82] + "..."

            desc_lbl = ctk.CTkLabel(
                card,
                text=desc_text,
                font=ctk.CTkFont(size=11),
                text_color="#cccccc",
                anchor="w",
                justify="left",
                wraplength=320,
            )
            desc_lbl.pack(fill="x", padx=10, pady=5)

            footer_frame = ctk.CTkFrame(card, fg_color="transparent")
            footer_frame.pack(fill="x", padx=10, pady=(5, 10))

            downloads_cnt = item.get("downloads", 0)
            dl_lbl = ctk.CTkLabel(
                footer_frame,
                text=f"📥 {downloads_cnt:,}",
                font=ctk.CTkFont(size=11),
                text_color="#8a8a9e",
            )
            dl_lbl.pack(side="left")

            install_btn = ctk.CTkButton(
                footer_frame,
                text="Install",
                width=80,
                height=28,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#00a859",
                hover_color="#008043",
                command=lambda p=item: self.start_single_download(p),
            )
            install_btn.pack(side="right")

    def load_thumbnail(self, url, label_widget):
        try:
            if url in self.image_cache:
                img = self.image_cache[url]
            else:
                raw_bytes = requests.get(url, timeout=5).content
                pil_img = Image.open(BytesIO(raw_bytes)).resize((48, 48))
                img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(48, 48))
                self.image_cache[url] = img

            self.after(0, lambda: label_widget.configure(image=img, text=""))
        except Exception:
            pass

    def start_single_download(self, project_item):
        threading.Thread(target=self.download_workflow, args=(project_item,), daemon=True).start()

    def download_workflow(self, project_item):
        item_type = self.type_dropdown.get()
        version = self.version_entry.get().strip()
        loader = self.loader_dropdown.get().lower()

        project_id = project_item["project_id"]
        title = project_item["title"]
        headers = {"User-Agent": "ModVault/1.0 (MinecraftModInstaller)"}

        self.update_status(f"Fetching download package for {title}...", 0.4)
        url = f"https://api.modrinth.com/v2/project/{project_id}/version?game_versions=[\"{version}\"]&loaders=[\"{loader}\"]"

        try:
            res = requests.get(url, headers=headers, timeout=10).json()

            if not res:
                self.update_status(f"No file found for {title} (MC {version} {loader})", 0)
                return

            file_info = res[0]["files"][0]
            download_url = file_info["url"]
            filename = file_info["filename"]
            out_path = os.path.join(self.save_directory, filename)

            self.update_status(f"Downloading {filename}...", 0.7)
            file_bytes = requests.get(download_url, headers=headers).content

            with open(out_path, "wb") as f:
                f.write(file_bytes)

            if item_type == "Modpack" and filename.endswith(".mrpack"):
                self.install_modpack_file(out_path)
            else:
                self.update_status(f"Installed {filename} successfully!", 1.0)

        except Exception as e:
            self.update_status(f"Installation failed: {str(e)}", 0)

    def install_modpack_file(self, mrpack_path):
        self.update_status("Extracting modpack manifest...", 0.5)

        extract_dir = os.path.join(self.save_directory, "temp_modpack")
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(mrpack_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        index_file = os.path.join(extract_dir, "modrinth.index.json")
        if not os.path.exists(index_file):
            self.update_status("Invalid .mrpack archive", 0)
            return

        with open(index_file, "r") as f:
            index_data = json.load(f)

        files = index_data.get("files", [])
        max_threads = self.parallel_threads.get()

        self.update_status(f"Downloading {len(files)} mods across threads...", 0.8)

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            executor.map(self.download_file_worker, files)

        shutil.rmtree(extract_dir, ignore_errors=True)
        self.update_status("Modpack installed successfully!", 1.0)

    def download_file_worker(self, file_data):
        headers = {"User-Agent": "ModVault/1.0 (MinecraftModInstaller)"}
        download_url = file_data["downloads"][0]

        file_bytes = requests.get(download_url, headers=headers).content
        out_path = os.path.join(self.save_directory, file_data["path"])
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        with open(out_path, "wb") as f:
            f.write(file_bytes)


if __name__ == "__main__":
    app = ModVaultApp()
    app.mainloop()