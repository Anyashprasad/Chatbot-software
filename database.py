#databse.py
import sqlite3
import os
import chromadb
from chromadb.config import Settings
from datetime import datetime


def get_db_connection():
    conn = sqlite3.connect('sail_chatbot.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')

    # Create chat_logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_input TEXT NOT NULL,
        bot_response TEXT NOT NULL,
        used_general_knowledge BOOLEAN NOT NULL DEFAULT 0
    )
    ''')

    # Create voice_logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS voice_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        query TEXT NOT NULL,
        response TEXT NOT NULL,
        used_general_knowledge BOOLEAN NOT NULL DEFAULT 0
    )
    ''')

    # Create feedback table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        response_id INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        rating INTEGER NOT NULL,
        comments TEXT
    )
    ''')

    # Create account_requests table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS account_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create password_requests table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS password_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        token TEXT NOT NULL,
        request_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        expiry DATETIME NOT NULL,
        status TEXT DEFAULT 'Pending'
    )
    ''')

    # Create documents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        content TEXT NOT NULL,
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully!")


def log_chat_interaction(user_id, user_input, bot_response, used_general_knowledge=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_logs (user_id, user_input, bot_response, used_general_knowledge) VALUES (?, ?, ?, ?)",
        (user_id, user_input, bot_response, used_general_knowledge)
    )
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id


def log_voice_interaction(user_id, query, response, used_general_knowledge=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO voice_logs (user_id, query, response, used_general_knowledge) VALUES (?, ?, ?, ?)",
        (user_id, query, response, used_general_knowledge)
    )
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id


def save_feedback(user_id, response_id, rating, comments=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO feedback (user_id, response_id, rating, comments) VALUES (?, ?, ?, ?)",
        (user_id, response_id, rating, comments)
    )
    feedback_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return feedback_id


def get_chroma_client():
    """Get a persistent Chroma client"""
    import chromadb
    import os

    # Create the directory if it doesn't exist
    persist_directory = os.path.join("data", "chroma_db")
    os.makedirs(persist_directory, exist_ok=True)

    # Use PersistentClient to save embeddings to disk
    client = chromadb.PersistentClient(path=persist_directory)

    return client


def get_or_create_collection(client, collection_name):
    """Get or create a collection with the given name"""
    try:
        # Try to get the collection
        collection = client.get_collection(collection_name)
        print(f"Retrieved existing collection: {collection_name}")
    except Exception as e:
        # If it doesn't exist, create it
        print(f"Creating new collection: {collection_name}")
        collection = client.create_collection(collection_name)

    return collection


import redis

def get_redis_client():
    """Get a Redis client for caching"""
    try:
        client = redis.Redis(
            host='localhost',  # Change to your Redis server host
            port=6379,         # Default Redis port
            db=0,              # Default database
            decode_responses=False  # Keep binary responses for embeddings
        )
        # Test connection
        client.ping()
        return client
    except Exception as e:
        print(f"Redis connection failed: {str(e)}")
        return None
