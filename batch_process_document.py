import os
import shutil
from shared_utils import get_all_document_paths
from data_processing import batch_process_document  # We will create this file next
from rebuild_embeddings_and_paragraphs import build_and_cache_embeddings

# --- CONFIGURATION ---
OCR_CACHE_DIR = "data/ocr_cache"
CHROMA_PATH = "data/chroma_db"
DOCUMENT_DIRECTORIES = ["data/documents", "data/uploads"]


def main():
    # 1. Clean up old data for a fresh start
    print("--- Clearing old cache and database ---")
    if os.path.exists(OCR_CACHE_DIR):
        shutil.rmtree(OCR_CACHE_DIR)
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    os.makedirs(OCR_CACHE_DIR, exist_ok=True)
    os.makedirs(CHROMA_PATH, exist_ok=True)
    print("Old data cleared successfully.")

    # 2. Get all documents to be processed
    all_docs = get_all_document_paths()
    if not all_docs:
        print("No documents found to process. Exiting.")
        return

    print(f"\nFound {len(all_docs)} documents to process.")

    # 3. Process each document
    for doc in all_docs:
        filename = doc['filename']
        filepath = doc['path']

        print(f"\n--- Processing Document: {filename} ---")

        # Step A: Perform bilingual OCR and save to cache
        success = batch_process_document(filepath, filename)

        if success:
            # Step B: Build and cache embeddings for the newly OCR'd text
            build_and_cache_embeddings(filename)
        else:
            print(f"[SKIPPING] Could not perform OCR on {filename}. Skipping embedding generation.")

    print("\n\n--- Batch processing complete. ---")


if __name__ == "__main__":
    main()
