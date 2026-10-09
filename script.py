import os
import re
import zipfile
from urllib.parse import urljoin, unquote
import requests
from bs4 import BeautifulSoup

# Updated URL and output names for Primary/Grade 6
PORTAL_URL = "https://education.gov.pg/components/primary.js"
BASE_URL = "https://education.gov.pg/"
OUTPUT_DIR = "png_primary_grade6_syllabuses"
ZIP_FILENAME = "PNG_Primary_Grade6_Syllabuses.zip"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Fetching links from {PORTAL_URL}...")
response = requests.get(PORTAL_URL, headers=headers)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

downloaded_files = []

for a_tag in soup.find_all("a", href=True):
    href = a_tag["href"]
    text = a_tag.get_text(strip=True).lower()
    text_and_url = f"{text} {href.lower()}"

    is_pdf = ".pdf" in href.lower()

    # We want syllabus documents (excluding teacher guides)
    is_syllabus = "syllabus" in text_and_url or "syllabi" in text_and_url
    is_tg = "teacher" in text_and_url or "guide" in text_and_url or "-tg" in text_and_url

    if is_pdf and is_syllabus and not is_tg:

        # PNG Primary syllabuses are either grade-specific or shared (Grades 6-8 / Senior Primary).
        # We want to skip documents strictly meant for other single grades (3, 4, 5, 7, 8).
        has_strictly_other_grade = bool(re.search(r'(grade|gr)[_ -]?(3|4|5|7|8)\b', text_and_url))
        has_grade_6 = bool(re.search(r'(grade|gr)[_ -]?6\b', text_and_url)) or bool(re.search(r'4-6', text_and_url)) or bool(re.search(r'6-8', text_and_url))
        has_shared = bool(re.search(r'senior|sp|upper', text_and_url))
        has_junior = bool(re.search(r'junior|jp|lower', text_and_url))

        if has_strictly_other_grade and not has_grade_6:
            continue
        elif has_junior and not (has_grade_6 or has_shared):
            continue

        full_url = urljoin(BASE_URL, href)
        filename = unquote(os.path.basename(full_url.split("?")[0]))

        if not filename.endswith(".pdf"):
            # Create a safe filename if the URL path doesn't end cleanly in .pdf
            clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', a_tag.get_text(strip=True))
            filename = f"{clean_name}.pdf"

        file_path = os.path.join(OUTPUT_DIR, filename)

        if not os.path.exists(file_path):
            print(f"Downloading: {filename}")
            try:
                r = requests.get(full_url, headers=headers, timeout=30)
                if r.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(r.content)
                    downloaded_files.append(file_path)
            except Exception as e:
                print(f"Failed to download {filename}: {e}")
        else:
            downloaded_files.append(file_path)

if downloaded_files:
    print(f"\nCompressing {len(downloaded_files)} files into {ZIP_FILENAME}...")
    with zipfile.ZipFile(ZIP_FILENAME, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in downloaded_files:
            zipf.write(file, arcname=os.path.basename(file))
    print(f"Done! Created {ZIP_FILENAME}")
else:
    print("\nNo Grade 6 syllabus files were found or downloaded.")

# Auto-download for Google Colab users
try:
    from google.colab import files
    if os.path.exists(ZIP_FILENAME):
        print("Pushing ZIP file to your browser downloads...")
        files.download(ZIP_FILENAME)
except ImportError:
    pass # Script is running locally, no action needed