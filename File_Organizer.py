from pathlib import Path
import shutil

# The directory containing our test files
folder = Path("~/file_organizer_lab/opsflow_test").expanduser()

# File extension -> category
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

# Check that the directory exists
if not folder.is_dir():
    print(f"Directory not found: {folder}")
    raise SystemExit(1)

# Organize the files
for file in sorted(folder.iterdir()):
    if not file.is_file() or file.name.startswith("."):
        continue

    extension = file.suffix.lower()
    category = categories.get(extension, "Other")

    destination_folder = folder / category
    destination_folder.mkdir(exist_ok=True)

    # Avoid overwriting an existing file
    destination = destination_folder / file.name
    if destination.exists():
        print(f"Skipped (already exists): {file.name}")
        continue

    shutil.move(str(file), str(destination))
    print(f"{file.name} -> {category}")

print("\nOrganization complete!")
