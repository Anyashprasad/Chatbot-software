import os
import json
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Use the correct function name from our final shared_utils.py
from shared_utils import get_all_document_paths, extract_text_from_file

# --- CONFIGURATION ---
EMBEDDING_MODEL = "all-minilm"
CHROMA_PATH = "data/chroma_db"


def build_and_cache_embeddings(document_name):
    """
    Takes a document name, loads its OCR'd text, chunks it,
    and stores the embeddings in ChromaDB.
    """
    print(f"--- Building embeddings for: {document_name} ---")

    # 1. Find the file path
    docs = get_all_document_paths()
    file_path = None
    for doc in docs:
        if doc['filename'] == document_name:
            file_path = doc['path']
            break

    if not file_path:
        print(f"[ERROR] Could not find document path for {document_name}. Skipping.")
        return

    # 2. Extract the full text using our corrected function
    # This call will now work because 'extract_text_from_file' exists in the final shared_utils.py
    full_text = extract_text_from_file(file_path)

    if not full_text:
        print(f"[ERROR] No text found for {document_name}. Skipping.")
        return

    # 3. Split the text into manageable chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(full_text)

    if not chunks:
        print(f"[ERROR] Text splitting resulted in no chunks for {document_name}. Skipping.")
        return

    # 4. Generate and store embeddings in ChromaDB
    try:
        embedding_function = OllamaEmbeddings(model=EMBEDDING_MODEL)
        vector_store = Chroma.from_texts(
            texts=chunks,
            embedding=embedding_function,
            persist_directory=CHROMA_PATH,
            # Add metadata to know which document a chunk came from
            metadatas=[{"source": document_name} for _ in chunks]
        )

        print(f"[SUCCESS] Successfully built and cached {len(chunks)} embeddings for {document_name}.")
    except Exception as e:
        print(f"[FATAL ERROR] Failed to generate or store embeddings for {document_name}: {e}")

