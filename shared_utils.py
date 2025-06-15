import os
import re
import json
import pytesseract
from pdf2image import convert_from_path
from concurrent.futures import ThreadPoolExecutor

# --- FIX: Updated imports to resolve deprecation warnings ---
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

# --- CONFIGURATION (Unchanged) ---
EMBEDDING_MODEL = "all-minilm"
CHROMA_PATH = "data/chroma_db"
DOCUMENT_DIRECTORIES = ["data/documents", "data/uploads"]
OCR_CACHE_DIR = "data/ocr_cache"

# --- DYNAMIC DOCUMENT DISCOVERY (Robust Version) ---
def get_all_document_paths():
    """
    Dynamically scans document directories to find all files and their categories.
    This version is more robust and correctly identifies categories from folder paths.
    """
    all_docs = []
    for directory in DOCUMENT_DIRECTORIES:
        if not os.path.exists(directory):
            continue
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.pdf'):
                    full_path = os.path.join(root, file)
                    try:
                        # This new logic is more reliable. It gets the path relative
                        # to the base 'documents' or 'uploads' directory.
                        relative_path = os.path.relpath(root, directory)
                        # The category is the first part of the relative path.
                        # e.g., 'hr/policies' -> 'hr'
                        category = relative_path.split(os.sep)[0]
                        # Handle cases where file is in the root of 'documents'
                        if category == '.':
                            category = 'general'
                    except (ValueError, IndexError):
                        category = "general" # Fallback

                    all_docs.append({
                        "filename": file,
                        "path": full_path,
                        "category": category.lower()
                    })
    return all_docs

# --- CORE TEXT EXTRACTION (Unchanged) ---
def extract_text_from_file(file_path):
    """Loads text for a given file path from the OCR cache."""
    cache_filename = os.path.basename(file_path) + ".txt"
    cache_path = os.path.join(OCR_CACHE_DIR, cache_filename)
    if os.path.exists(cache_path):
        with open(cache_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return ""

# --- CLAUSE AND PREPROCESSING LOGIC (Unchanged) ---
def preprocess_query(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def find_document_by_name(doc_name):
    for doc in get_all_document_paths():
        if doc['filename'] == doc_name:
            return doc['path']
    return None

def extract_clause_section(document_name=None, clause_ref=None, category=None):
    """Extracts a clause by finding its start and a flexible end boundary."""
    if not clause_ref or not category: return []
    target_docs = [doc for doc in get_all_document_paths() if doc['category'] == category]
    if not target_docs: return []
    results = []
    for doc in target_docs:
        full_text = extract_text_from_file(doc['path'])
        if not full_text: continue
        start_pattern_str = r"^\s*" + re.escape(clause_ref) + r"\.?\s+.*"
        start_match = re.search(start_pattern_str, full_text, re.MULTILINE | re.IGNORECASE)
        if not start_match: continue
        start_index = start_match.start()
        end_index = len(full_text)
        generic_end_pattern = re.compile(r"^\s*(\d{1,2}\.)\s+[A-Z\s/]+$", re.MULTILINE)
        for match in generic_end_pattern.finditer(full_text, pos=start_match.end()):
            end_index = match.start()
            break
        extracted_text = full_text[start_index:end_index].strip()
        if extracted_text:
            results.append({"document": doc['filename'], "text": extracted_text})
    return results

# --- SEMANTIC SEARCH FUNCTION (Unchanged Logic, Uses Correct Imports) ---
def semantic_search(query, document_name=None, top_k=3, category=None):
    """Performs semantic search using ChromaDB on a specific category of documents."""
    if not category:
        print("[ERROR] Semantic search requires a category.")
        return []
    try:
        embedding_function = OllamaEmbeddings(model=EMBEDDING_MODEL)
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
        all_docs = get_all_document_paths()
        docs_in_cat = [doc['filename'] for doc in all_docs if doc['category'] == category]
        if not docs_in_cat:
            print(f"[WARN] No documents found in category '{category}' for semantic search.")
            return []
        results = db.similarity_search(query, k=top_k, filter={"source": {"$in": docs_in_cat}})
        if not results: return []
        return [doc.page_content for doc in results]
    except Exception as e:
        print(f"[FATAL ERROR] An error occurred during semantic search: {e}")
        return []
