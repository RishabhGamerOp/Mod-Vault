import os
import subprocess
import sys
import customtkinter

# Programmatically locate CustomTkinter assets directory
ctk_path = os.path.dirname(customtkinter.__file__)

# Build command including icon flag
build_cmd = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--noconfirm",
    "--onedir",  # Folder output for Inno Setup bundling
    "--windowed",
    f"--add-data={ctk_path}{os.path.pathsep}customtkinter/",
    "--icon=app_icon.ico",  # App icon flag
    "--name=ModVault",
    "app.py",
]

print("Building ModVault folder inside Visual Studio Code...")
subprocess.run(build_cmd)
print("\nSuccess! Output generated inside the 'dist/ModVault' directory.")