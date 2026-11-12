"""Automated Release Packaging Script for ProductionReady Commercial Distribution.

Creates a clean, production-ready ZIP archive ready for upload to Gumroad,
Lemon Squeezy, Whop, or direct customer delivery.
"""
from __future__ import annotations
import os
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"
ARCHIVE_NAME = "productionready-agency-v0.2.0.zip"
TARGET_ARCHIVE = DIST_DIR / ARCHIVE_NAME

EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    ".next",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "dist",
    "reports",
    ".turbo",
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".log",
}


def build_release_archive():
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if TARGET_ARCHIVE.exists():
        TARGET_ARCHIVE.unlink()

    print(f"Packaging commercial distribution archive: {TARGET_ARCHIVE} ...")
    file_count = 0

    with zipfile.ZipFile(TARGET_ARCHIVE, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(ROOT_DIR):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            rel_dir = Path(root).relative_to(ROOT_DIR)

            # Skip dist directory
            if "dist" in rel_dir.parts:
                continue

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in EXCLUDE_EXTENSIONS:
                    continue
                if file == ".DS_Store" or file.startswith("~$"):
                    continue

                rel_file = file_path.relative_to(ROOT_DIR)
                # Store inside top-level folder 'productionready-agency/'
                archive_arcname = Path("productionready-agency") / rel_file
                zf.write(file_path, arcname=str(archive_arcname))
                file_count += 1

    archive_size_kb = round(TARGET_ARCHIVE.stat().st_size / 1024, 1)
    print(f"Archive successfully generated:")
    print(f"Path:  {TARGET_ARCHIVE}")
    print(f"Files: {file_count} files included")
    print(f"Size:  {archive_size_kb} KB")


if __name__ == "__main__":
    build_release_archive()
