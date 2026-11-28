import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_DIR = ROOT / "build"
DIST_DIR = ROOT / "dist"
OUTPUT_DIR = DIST_DIR / "uci"

for folder in (BUILD_DIR, DIST_DIR):
    if folder.exists():
        shutil.rmtree(folder)

subprocess.run(
    [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onedir",
        "-y",
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--specpath", str(BUILD_DIR),
        str(ROOT / "uci.py"),
    ],
    check=True,
)

# copy runtime assets right next to the executable so users can edit them
shutil.copytree(ROOT / "openings", OUTPUT_DIR / "openings", dirs_exist_ok=True)
shutil.copy2(ROOT / "settings.json", OUTPUT_DIR / "settings.json")

print(f"Build complete: {OUTPUT_DIR}")