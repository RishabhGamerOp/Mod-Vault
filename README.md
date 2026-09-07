# ⚡ ModVault — Minecraft Mod & Modpack Suite

ModVault is a modern, lightweight desktop application built with Python and CustomTkinter. It simplifies searching, downloading, and managing Minecraft mods and modpacks directly from Modrinth across various game versions and mod loaders.

## ✨ Key Features

* 🔍 Multi-Platform Search: Seamlessly search mods and modpacks using the Modrinth API.
* 📦 Modpack Auto-Installer: Download, extract, and auto-install all required mods from .mrpack archives.
* ⚡ Multithreaded Downloads: Parallel downloading powered by customizable thread pools for maximum speed.
* 🚀 Integrated Auto-Updater: Checks for new version tags on GitHub Releases and updates the executable in-place.
* 📂 Launcher Auto-Detection: Automatically detects mod folders for default .minecraft and Prism Launcher instances.
* 🎨 Modern Dark UI: Responsive grid layout with high-resolution thumbnails, tags, and theme customization.

## 🛠 Tech Stack

* Language: Python 3.10+
* GUI Framework: CustomTkinter (https://github.com/TomSchimansky/CustomTkinter)
* Imaging: Pillow (PIL)
* Networking: Requests
* Packaging: PyInstaller

## 🚀 Getting Started

### Option 1: Standalone Executable (Recommended)

Go to the Releases page (https://github.com/RishabhGamerOp/Mod-Vault/releases).

Download ModVault.exe from the latest release.

Double-click to launch—no installation required!

### Option 2: Run From Source

Clone the repository:
git clone https://github.com/RishabhGamerOp/Mod-Vault.git
cd Mod-Vault

Install required dependencies:
pip install -r requirements.txt

Launch the application:
python app.py

## 📦 Building from Source

To build your own standalone .exe bundle using PyInstaller:

python -m PyInstaller --noconfirm --onefile --windowed --add-data "$(python -c 'import customtkinter, os; print(os.path.dirname(customtkinter.file))');customtkinter/" --name "ModVault" app.py

## 🛡️ Security & Antivirus Disclaimers

ModVault is 100% open-source, and all source code is available in this repository for review.

Because the app is bundled using PyInstaller and is not digitally signed with a commercial certificate, some antivirus software (and VirusTotal heuristics) may flag ModVault.exe as a generic false positive (e.g., Trojan or Dropper labels).

* Why does this happen? PyInstaller bundles the Python runtime and the self-updating batch script logic into a single binary, which matches generic patterns used by automated scanner heuristics.
* Is it safe? Yes. You can inspect app.py directly or compile the .exe yourself using the instructions above.

## 📄 License

This project is licensed under the MIT License.
