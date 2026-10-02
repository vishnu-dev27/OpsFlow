#!/usr/bin/env python3

import argparse
import shutil
import sys
from pathlib import Path


categories = {
    ".pdf": "Documents",
    ".docx": "Documents",
    ".txt": "Text",
    ".md": "Text",
    ".jpg": "Images",
    ".png": "Images",
    ".svg": "Images",
    ".csv": "Spreadsheets",
    ".xlsx": "Spreadsheets",
    ".pptx": "Presentations",
    ".mp3": "Audio",
    ".mp4": "Video",
    ".zip": "Archives",
    ".py": "Code",
    ".html": "Code",
    ".css": "Code",
}


parser = argparse.ArgumentParser(
    description="Organize files into category folders."
)

parser.add_argument(
    "folder",
    help="Path to the folder you want to organize"
)

parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Preview file movements without moving files"
)

args = parser.parse_args()
folder = Path(args.folder).expanduser()

# Validate the target directory.
if not folder.exists() or not folder.is_dir():
    print(f"Directory not found: {folder}")
    sys.exit(1)

for file in sorted(folder.iterdir()):
    # Skip directories and hidden files.
    if not file.is_file() or file.name.startswith("."):
        continue

    # Skip this script if it is inside the target folder.
    if file.resolve() == Path(__file__).resolve():
        continue

    extension = file.suffix.lower()
    category = categories.get(extension, "Other")

    destination_folder = folder / category
    destination = destination_folder / file.name

    # Avoid overwriting an existing file.
    if destination.exists():
        print(f"Skipped (already exists): {file.name}")
        continue

    if args.dry_run:
        print(f"[DRY RUN] {file.name} -> {category}")
    else:
        try:
            destination_folder.mkdir(exist_ok=True)
            shutil.move(str(file), str(destination))
            print(f"{file.name} -> {category}")
        except OSError as error:
            print(f"Could not move {file.name}: {error}")

print("Organization complete!")
