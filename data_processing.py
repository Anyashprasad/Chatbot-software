import os
import pytesseract
from pdf2image import convert_from_path
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION ---
OCR_CACHE_DIR = "data/ocr_cache"


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# --- END OF FIX ---


def process_page_bilingual(img_tuple):
    """Processes a single page with both English and Hindi OCR."""
    i, img = img_tuple
    custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
    try:
        text = pytesseract.image_to_string(img, lang='eng+hin', config=custom_config)
        return f"\n--- Page {i + 1} ---\n" + text
    except pytesseract.TesseractNotFoundError:
        # This error will no longer happen because we set the command path above.
        # But we keep the check for safety.
        print(
            "[FATAL ERROR] Tesseract executable not found at the specified path. Please check the path in data_processing.py.")
        return None
    except Exception as e:
        print(f"[ERROR] OCR failed for page {i + 1}: {e}")
        return ""


def batch_process_document(doc_path, doc_filename):
    """
    Performs bilingual OCR on a PDF and saves the text to the cache.
    Returns True on success, False on failure.
    """
    if not doc_path.lower().endswith('.pdf'):
        print(f"'{doc_filename}' is not a PDF. Skipping OCR.")
        return False

    cache_file_path = os.path.join(OCR_CACHE_DIR, doc_filename + ".txt")

    if os.path.exists(cache_file_path):
        print(f"Cache exists for {doc_filename}. Skipping OCR.")
        return True

    try:
        print(f"Starting OCR for {doc_filename}...")
        images = convert_from_path(doc_path)

        with ThreadPoolExecutor() as executor:
            page_texts = list(executor.map(process_page_bilingual, enumerate(images)))

        if any(text is None for text in page_texts):
            return False

        full_text = "".join(page_texts)

        with open(cache_file_path, "w", encoding="utf-8") as f:
            f.write(full_text)

        print(f"Successfully saved OCR text for {doc_filename} to cache.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to process PDF {doc_filename}: {e}")
        return False
