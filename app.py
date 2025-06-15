import json
import logging
import os
import secrets
import sqlite3
import time
import threading
import pathlib
import shutil
import string
from datetime import datetime, timedelta
from functools import wraps
import bcrypt
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, Response, stream_with_context
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename

# Import your custom modules with error handling
try:
    from model.chatbot_model import generate_llm_response

    print("[IMPORT] ✅ Successfully imported chatbot_model")
except ImportError as e:
    print(f"[IMPORT] ❌ Failed to import chatbot_model: {e}")


    def generate_llm_response(query, **kwargs):
        return {"response": f"System in test mode. You said: {query}", "context": "", "document": ""}

try:
    from shared_utils import get_all_document_paths, semantic_search

    print("[IMPORT] ✅ Successfully imported shared_utils")
except ImportError as e:
    print(f"[IMPORT] ❌ Failed to import shared_utils: {e}")


    def get_all_document_paths():
        return []

# --- Enhanced Logging Configuration ---
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler("chatbot_backend.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

os.makedirs('logs', exist_ok=True)
chat_logger = logging.getLogger('CHAT')
auth_logger = logging.getLogger('AUTH')
admin_logger = logging.getLogger('ADMIN')

# --- Flask App Configuration ---
app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)
app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
    TEMPLATES_AUTO_RELOAD=True,
    UPLOAD_FOLDER='uploads/documents',
    MAX_CONTENT_LENGTH=16 * 1024 * 1024
)

csrf = CSRFProtect(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1000 per day", "200 per hour", "50 per minute"],
    storage_uri="memory://"
)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data/documents', exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_document_categories():
    try:
        categories = set()
        folders = []

        # Check multiple possible paths
        paths_to_check = [
            app.config['UPLOAD_FOLDER'],  # uploads/documents
            "data/documents",
            "hr",  # Direct hr folder
            os.path.join(os.getcwd(), "hr"),  # Current directory/hr
        ]

        for base_path in paths_to_check:
            if os.path.exists(base_path):
                print(f"✅ Found path: {base_path}")
                if os.path.isdir(base_path):
                    # If it's the hr folder directly
                    if base_path.endswith('hr'):
                        files = [f for f in os.listdir(base_path) if os.path.isfile(os.path.join(base_path, f))]
                        if files:
                            categories.add('hr')
                            print(f"📁 HR folder has {len(files)} files: {files[:3]}...")
                    else:
                        # Check for subfolders
                        for item in os.listdir(base_path):
                            folder_path = os.path.join(base_path, item)
                            if os.path.isdir(folder_path):
                                categories.add(item)
                                files = [f for f in os.listdir(folder_path) if
                                         os.path.isfile(os.path.join(folder_path, f))]
                                print(f"📁 {item} folder has {len(files)} files")

        print(f"🔍 Found categories: {list(categories)}")
        return sorted(list(categories)) if categories else ['general', 'hr', 'pgp']

    except Exception as e:
        print(f"❌ Error getting categories: {e}")
        return ['general', 'hr', 'pgp']


# --- Database Functions ---
def get_db_connection():
    conn = sqlite3.connect('chatbot.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        email TEXT UNIQUE NOT NULL, 
        password BLOB NOT NULL, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS account_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        email TEXT UNIQUE NOT NULL, 
        password BLOB NOT NULL, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS password_reset_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        email TEXT NOT NULL, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        admin_email = "anyashprasad768@gmail.com"
        admin_password = "admin123"
        admin_hashed = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())

        try:
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (admin_email, admin_hashed))
            chat_logger.info(f"Created admin user: {admin_email}")
            print(f"\n{'=' * 50}")
            print(f"ADMIN USER CREATED:")
            print(f"Email: {admin_email}")
            print(f"Password: {admin_password}")
            print(f"{'=' * 50}\n")
        except sqlite3.IntegrityError:
            chat_logger.info(f"Admin user already exists: {admin_email}")

    conn.commit()
    conn.close()


def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


init_db()


def handle_simple_messages(message):
    """Enhanced greeting detection with fuzzy matching and comprehensive patterns"""
    message_lower = message.lower().strip()

    # Enhanced greeting patterns with variations and fuzzy matching
    greeting_patterns = [
        "hi", "hii", "hiiii", "hello", "helo", "hellooo", "hey", "heyy",
        "good morning", "good afternoon", "good evening", "morning",
        "afternoon", "evening", "namaste", "greetings", "howdy", "sup",
        "what's up", "whatsup", "yo", "hola"
    ]

    # Check for exact matches first (fastest)
    if message_lower in greeting_patterns:
        return {
            "response": "Hello! I'm your Chatbot assistant. I can help you with:\n\n🔹 HR policies and procedures\n🔹 PGP guidelines and protocols\n🔹 Company policies and regulations\n🔹 Document searches\n🔹 Emergency procedures\n\nHow can I assist you today?",
            "context": "greeting_handled",
            "document": "chatbot"
        }

    # Check for partial matches (for variations like "hiii", "helloooo")
    for pattern in greeting_patterns:
        if pattern in message_lower or message_lower in pattern:
            # Additional check to avoid false positives
            if len(message_lower) <= len(pattern) + 3:  # Allow up to 3 extra characters
                return {
                    "response": "Hello! I'm your Chatbot assistant. I can help you with:\n\n🔹 HR policies and procedures\n🔹 PGP guidelines and protocols\n🔹 Company policies and regulations\n🔹 Document searches\n🔹 Emergency procedures\n\nHow can I assist you today?",
                    "context": "greeting_handled",
                    "document": "chatbot"
                }

    # Check for greeting-like patterns (starts with common greeting words)
    greeting_starts = ["hi", "hello", "hey", "good"]
    for start in greeting_starts:
        if message_lower.startswith(start) and len(message_lower) <= len(start) + 5:
            return {
                "response": "Hello! I'm your Chatbot assistant. I can help you with:\n\n🔹 HR policies and procedures\n🔹 PGP guidelines and protocols\n🔹 Company policies and regulations\n🔹 Document searches\n🔹 Emergency procedures\n\nHow can I assist you today?",
                "context": "greeting_handled",
                "document": "chatbot"
            }

    # Handle thanks responses (exact matches)
    exact_thanks = ["thanks", "thank you", "ty", "tysm", "thx", "appreciate"]
    if message_lower in exact_thanks:
        return {
            "response": "You're welcome! I'm here to help with any questions about documents and policies. Feel free to ask anything else!",
            "context": "thanks_handled",
            "document": "chatbot"
        }

    # Handle help requests (exact matches to avoid false positives)
    if message_lower in ["help", "assist", "support", "what can you do", "menu", "options"]:
        return {
            "response": "I'm here to help you with:\n\n🔹 HR policies and procedures\n🔹 PGP guidelines and protocols\n🔹 Company policies and regulations\n🔹 Emergency procedures\n🔹 Document searches\n🔹 Leave policies\n🔹 Compensation information\n🔹 Medical policies\n🔹 Travel guidelines\n\nWhat would you like to know about?",
            "context": "help_handled",
            "document": "chatbot"
        }

    # Handle goodbye responses
    goodbye_patterns = ["bye", "goodbye", "see you", "farewell", "exit", "quit", "cya", "later"]
    if message_lower in goodbye_patterns:
        return {
            "response": "Goodbye! Have a great day. Feel free to return if you have more questions about policies or procedures!",
            "context": "goodbye_handled",
            "document": "chatbot"
        }

    # Return None so complex questions go to LLM
    return None


def handle_dropdown_selection(selection):
    try:
        if selection == 'search_documents':
            return "What would you like to search for in the documents? Please type your query and select the appropriate category."
        elif selection == 'list_categories':
            categories = get_document_categories()
            if categories:
                return f"Available document categories: {', '.join([cat.title().replace('_', ' ') for cat in categories])}"
            else:
                return "No document categories found."
        elif selection == 'recent_updates':
            return "Here are the recent document updates... (You can ask about any recent changes or new documents uploaded to the system)"
        elif selection == 'purchase_guidelines':
            return "Here are the purchase guidelines:\n\n• Follow company procurement policies\n• Obtain proper approvals before purchasing\n• Use approved vendors when available\n• Keep receipts for all purchases\n• Submit expense reports within 30 days\n\nFor specific questions, please search our procurement documents or contact the finance team."
        else:
            return "I didn't understand that selection. Type 'menu' to see available options."
    except Exception as e:
        chat_logger.error(f"Error handling dropdown selection: {e}")
        return "Sorry, there was an error processing your selection."


# --- Authentication Routes ---
@app.route('/login', methods=['GET', 'POST'])
@csrf.exempt
def login():
    if request.method == 'GET':
        if session.get('logged_in'):
            return redirect(url_for('index'))
        return render_template('login.html')

    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    if not email or not password:
        return render_template('login.html', error="Email and password are required.")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session.clear()
            session['email'] = email
            session['user_id'] = user['id']
            session['logged_in'] = True
            session['is_admin'] = (email == "anyashprasad768@gmail.com")
            session.permanent = True
            auth_logger.info(f"Successful login for user: {email}")
            return redirect(url_for('index'))
        else:
            auth_logger.warning(f"Failed login attempt for: {email}")
            return render_template('login.html', error="Invalid email or password.")
    except Exception as e:
        auth_logger.error(f"Database error during login: {e}")
        return render_template('login.html', error="A database error occurred.")


@app.route('/register', methods=['GET', 'POST'])
@csrf.exempt
def register():
    if request.method == 'GET':
        if session.get('logged_in'):
            return redirect(url_for('index'))
        return render_template('register.html')

    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not email or not password or not confirm_password:
        return render_template('register.html', error="All fields are required.")

    if password != confirm_password:
        return render_template('register.html', error="Passwords do not match.")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            return render_template('register.html', error="Email already registered.")

        cursor.execute("SELECT * FROM account_requests WHERE email=?", (email,))
        existing_request = cursor.fetchone()

        if existing_request:
            conn.close()
            return render_template('register.html',
                                   error="Account request already submitted. Please wait for admin approval.")

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("INSERT INTO account_requests (email, password) VALUES (?, ?)", (email, hashed_password))
        conn.commit()
        conn.close()

        auth_logger.info(f"Account request submitted for: {email}")
        return render_template('register.html',
                               success="Account request submitted successfully! Please wait for admin approval before you can login.")

    except Exception as e:
        auth_logger.error(f"Database error during registration: {e}")
        return render_template('register.html', error="A database error occurred during registration.")


# FIXED: Add missing forgot_password route
@app.route('/forgot_password', methods=['GET', 'POST'])
@csrf.exempt
def forgot_password():
    auth_logger.debug(f"Forgot password route accessed with method: {request.method}")

    if request.method == 'GET':
        return render_template('forgot_password.html')

    email = request.form.get('email', '').strip()
    auth_logger.debug(f"Password reset request for: {email}")

    if not email:
        return render_template('forgot_password.html', error="Email is required.")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        if user:
            # Check if request already exists
            cursor.execute("SELECT * FROM password_reset_requests WHERE email=?", (email,))
            existing_request = cursor.fetchone()

            if existing_request:
                conn.close()
                auth_logger.warning(f"Duplicate password reset request for: {email}")
                return render_template('forgot_password.html',
                                       error="Password reset request already submitted. Please wait for admin to process it.")

            # Add to password reset requests
            cursor.execute("INSERT INTO password_reset_requests (email) VALUES (?)", (email,))
            conn.commit()
            auth_logger.info(f"Password reset request created for: {email}")

        conn.close()

        return render_template('forgot_password.html',
                               success="Password reset request submitted to admin. You will be contacted once processed.")

    except Exception as e:
        auth_logger.error(f"Database error during password reset request: {e}")
        return render_template('forgot_password.html', error="A database error occurred.")


# FIXED: Add missing admin_login route
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    """Admin login route - redirects to main login"""
    auth_logger.debug("Admin login route accessed - redirecting to main login")
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    user_email = session.get('email', 'Unknown')
    session.clear()
    auth_logger.info(f"User logged out: {user_email}")
    return redirect(url_for('login'))


@app.route('/')
@app.route('/index')
@require_login
def index():
    user_email = session.get('email', 'Unknown')

    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))

    return render_template('index.html')


@app.route('/admin_dashboard')
@require_login
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('index'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM account_requests ORDER BY created_at DESC")
        account_requests = cursor.fetchall()
        cursor.execute("SELECT * FROM password_reset_requests ORDER BY created_at DESC")
        password_requests = cursor.fetchall()
        cursor.execute("SELECT email, created_at FROM users ORDER BY created_at DESC")
        registered_users = cursor.fetchall()
        conn.close()

        # FIXED: Get folder information with recursive file counting
        folders = []

        def count_files_recursively(folder_path):
            """Count all files in folder and subfolders"""
            total_files = []
            if not os.path.exists(folder_path):
                return total_files

            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    # Skip hidden files and system files
                    if not file.startswith('.'):
                        total_files.append(os.path.join(root, file))
            return total_files

        # Check HR folder (with subdirectories)
        hr_folder_path = os.path.join(os.getcwd(), "hr")
        if os.path.exists(hr_folder_path) and os.path.isdir(hr_folder_path):
            all_hr_files = count_files_recursively(hr_folder_path)
            # Get just filenames for display (first 10)
            display_files = [os.path.basename(f) for f in all_hr_files[:10]]
            folders.append({
                'name': 'hr',
                'file_count': len(all_hr_files),
                'files': display_files
            })
            print(f"✅ HR folder found with {len(all_hr_files)} files (including subdirectories)")

        # Check PGP folder (with subdirectories)
        pgp_folder_path = os.path.join(os.getcwd(), "pgp")
        if os.path.exists(pgp_folder_path) and os.path.isdir(pgp_folder_path):
            all_pgp_files = count_files_recursively(pgp_folder_path)
            display_files = [os.path.basename(f) for f in all_pgp_files[:10]]
            folders.append({
                'name': 'pgp',
                'file_count': len(all_pgp_files),
                'files': display_files
            })
            print(f"✅ PGP folder found with {len(all_pgp_files)} files (including subdirectories)")

        # Check upload folder
        upload_path = app.config['UPLOAD_FOLDER']
        if os.path.exists(upload_path):
            for item in os.listdir(upload_path):
                folder_path = os.path.join(upload_path, item)
                if os.path.isdir(folder_path):
                    all_files = count_files_recursively(folder_path)
                    display_files = [os.path.basename(f) for f in all_files[:10]]
                    folders.append({
                        'name': item,
                        'file_count': len(all_files),
                        'files': display_files
                    })

        # Check data/documents folder
        data_path = "data/documents"
        if os.path.exists(data_path):
            for item in os.listdir(data_path):
                folder_path = os.path.join(data_path, item)
                if os.path.isdir(folder_path):
                    all_files = count_files_recursively(folder_path)
                    display_files = [os.path.basename(f) for f in all_files[:10]]

                    # Check if folder already exists (avoid duplicates)
                    existing_folder = next((f for f in folders if f['name'] == item), None)
                    if existing_folder:
                        existing_folder['files'].extend(display_files)
                        existing_folder['file_count'] += len(all_files)
                    else:
                        folders.append({
                            'name': item,
                            'file_count': len(all_files),
                            'files': display_files
                        })

        print(f"📊 Total folders found: {len(folders)}")
        for folder in folders:
            print(f"📁 {folder['name']}: {folder['file_count']} files")

        return render_template('admin_dashboard.html',
                               account_requests=account_requests,
                               password_requests=password_requests,
                               registered_users=registered_users,
                               folders=folders)

    except Exception as e:
        admin_logger.error(f"Error loading admin dashboard: {e}")
        print(f"❌ Admin dashboard error: {e}")
        return render_template('admin_dashboard.html',
                               account_requests=[],
                               password_requests=[],
                               registered_users=[],
                               folders=[])


@app.route('/admin/view_folder/<folder_name>', methods=['GET'])
@require_login
def view_folder_details(folder_name):
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        folder_details = {
            'name': folder_name,
            'files': [],
            'total_size': 0,
            'last_modified': None
        }

        # Check multiple possible paths for the folder
        possible_paths = [
            os.path.join(os.getcwd(), folder_name),
            os.path.join(app.config['UPLOAD_FOLDER'], folder_name),
            os.path.join("data/documents", folder_name)
        ]

        folder_path = None
        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                folder_path = path
                break

        if folder_path:
            # Get all files recursively
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if not file.startswith('.'):  # Skip hidden files
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, folder_path)

                        try:
                            stat = os.stat(file_path)
                            folder_details['files'].append({
                                'name': file,
                                'path': relative_path,
                                'size': stat.st_size,
                                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                                'type': os.path.splitext(file)[1].lower()
                            })
                            folder_details['total_size'] += stat.st_size
                        except OSError:
                            continue

            # Sort files by name
            folder_details['files'].sort(key=lambda x: x['name'])

            # Get folder last modified time
            try:
                folder_stat = os.stat(folder_path)
                folder_details['last_modified'] = datetime.fromtimestamp(folder_stat.st_mtime).strftime(
                    '%Y-%m-%d %H:%M:%S')
            except OSError:
                folder_details['last_modified'] = 'Unknown'

        return jsonify({
            'success': True,
            'folder': folder_details
        })

    except Exception as e:
        admin_logger.error(f"Error viewing folder {folder_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# FIXED: Add missing admin routes
@app.route('/approve_request/<int:request_id>', methods=['POST'])
@require_login
@csrf.exempt
def approve_request(request_id):
    if not session.get('is_admin'):
        return "Unauthorized", 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM account_requests WHERE id = ?", (request_id,))
        request_data = cursor.fetchone()

        if request_data:
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)",
                           (request_data['email'], request_data['password']))
            cursor.execute("DELETE FROM account_requests WHERE id = ?", (request_id,))
            conn.commit()
            admin_logger.info(f"Account approved: {request_data['email']}")

        conn.close()
    except Exception as e:
        admin_logger.error(f"Error approving request: {e}")

    return redirect(url_for('admin_dashboard'))


@app.route('/deny_request/<int:request_id>', methods=['POST'])
@require_login
@csrf.exempt
def deny_request(request_id):
    if not session.get('is_admin'):
        return "Unauthorized", 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM account_requests WHERE id = ?", (request_id,))
        conn.commit()
        conn.close()
        admin_logger.info(f"Account request denied: {request_id}")
    except Exception as e:
        admin_logger.error(f"Error denying request: {e}")

    return redirect(url_for('admin_dashboard'))


# --- Chat Routes ---
@app.route('/get_dropdown_options', methods=['GET'])
@require_login
def get_dropdown_options():
    try:
        categories = get_document_categories()
        CATEGORY_LABELS = {
            'hr': 'HR',
            'pgp': 'PCP',
            'general': 'General'
        }
        options = []
        if categories:
            for category in categories:
                label = CATEGORY_LABELS.get(category, category.title().replace('_', ' '))
                options.append({
                    'value': category,
                    'label': label
                })

        if not options:
            options.append({
                'value': 'general',
                'label': 'General Questions'
            })

        return jsonify({
            'success': True,
            'options': options
        })

    except Exception as e:
        chat_logger.error(f"Error getting dropdown options: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load options'
        }), 500


@app.route('/chat_stream_integrated', methods=['POST'])
@require_login
@csrf.exempt
def chat_stream_integrated():
    user_email = session.get('email', 'Unknown')
    user_id = session.get('user_id', 'Unknown')

    chat_logger.info(f"Chat request from: {user_email}")

    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data received'}), 400

        user_message = data.get('message', '').strip()
        selected_category = data.get('category', 'general')
        chat_type = data.get('type', 'text')

        chat_logger.info(f"Message: '{user_message}', Category: '{selected_category}'")

        if not user_message:
            return jsonify({'error': 'Message is required'}), 400

        # Handle simple messages first
        simple_response = handle_simple_messages(user_message)
        if simple_response:
            chat_logger.info(f"Simple message handled: {user_message}")
            return jsonify({
                'response': simple_response['response'],
                'type': 'text',
                'category': selected_category,
                'context_length': len(simple_response.get('context', '')),
                'document': simple_response['document'],
                'timestamp': datetime.now().isoformat()
            })

        # Handle dropdown commands
        if user_message.lower() in ['menu', 'options']:
            return jsonify({
                'response': 'Please select an option:',
                'type': 'dropdown',
                'options': [
                    {'label': 'Document Search', 'value': 'search_documents'},
                    {'label': 'Category List', 'value': 'list_categories'},
                    {'label': 'Recent Updates', 'value': 'recent_updates'},
                    {'label': 'Purchase Guidelines', 'value': 'purchase_guidelines'}
                ]
            })

        # Handle dropdown selections
        if chat_type == 'dropdown':
            response = handle_dropdown_selection(user_message)
            return jsonify({'response': response, 'type': 'text'})

        # Generate complex response
        session_id = session.get('user_id', 'anonymous')

        try:
            result = generate_llm_response(
                query=user_message,
                category=selected_category if selected_category != 'general' else None,
                session_id=session_id
            )

            response_text = result.get('response', 'Sorry, I could not generate a response.')
            context_used = result.get('context', '')
            document_used = result.get('document', selected_category)

            chat_logger.info(f"LLM response generated successfully")

            return jsonify({
                'response': response_text,
                'type': 'text',
                'category': selected_category,
                'context_length': len(context_used),
                'document': document_used,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as llm_error:
            chat_logger.error(f"LLM Error: {llm_error}")
            return jsonify({
                'response': f"I encountered an error while processing your request. Please try rephrasing your question.",
                'type': 'text',
                'category': selected_category,
                'error': str(llm_error)
            })

    except Exception as e:
        chat_logger.error(f"Chat request failed: {e}")
        return jsonify({'error': 'Failed to generate response', 'details': str(e)}), 500


@app.route('/admin/process_folder/<folder_name>', methods=['POST'])
@require_login
def process_folder(folder_name):
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        # Call your processing scripts here
        # subprocess.run(['python', 'batch_process_documents.py', folder_name])

        return jsonify({
            'success': True,
            'message': f'Folder {folder_name} processed successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/rebuild_embeddings', methods=['POST'])
@require_login
def rebuild_embeddings():
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        # Call your embedding rebuild script
        # subprocess.run(['python', 'rebuild_embeddings_and_paragraphs.py'])

        return jsonify({
            'success': True,
            'message': 'Embeddings rebuilt successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- Voice Route ---
@app.route('/voice', methods=['POST'])
@require_login
@csrf.exempt
def voice_chat():
    user_email = session.get('email', 'Unknown')
    chat_logger.debug(f"Voice chat requested by: {user_email}")

    try:
        data = request.get_json()
        category = data.get('category', 'general')

        # Simple voice responses based on category
        if 'hr' in category.lower():
            responses = [
                {"query": "HR leave policy",
                 "response": "HR Leave Policy: Employees are entitled to annual leave as per company policy. Please check the employee handbook for specific entitlements."},
                {"query": "Salary information",
                 "response": "For salary queries, please contact HR department. All compensation details are handled by HR."}
            ]
        elif 'pgp' in category.lower():
            responses = [
                {"query": "EMO procedures",
                 "response": "EMO (Emergency Management Officer) handles emergency response procedures and safety protocols."},
                {"query": "Safety guidelines",
                 "response": "Safety is our priority. Always use PPE and follow safety protocols."}
            ]
        else:
            responses = [
                {"query": " information",
                 "response": " is India's largest steel-making company. How can I help you with specific policies?"},
                {"query": "General help",
                 "response": "I can assist with HR policies, PGP guidelines, and company information."}
            ]

        import random
        response = random.choice(responses)

        chat_logger.info(f"Voice response generated for {user_email}")
        return jsonify(response)

    except Exception as e:
        chat_logger.error(f"Voice chat error: {e}")
        return jsonify({
            "query": "",
            "response": "Voice processing failed. Please try again or use text input."
        }), 500


# FIXED: Add error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print(f"\n{'=' * 60}")
    print(" CHATBOT STARTING")
    print(f"{'=' * 60}")
    print(f"Admin Dashboard: http://localhost:5000/admin_dashboard")
    print(f"User Interface: http://localhost:5000/")
    print(f"Available Categories: {', '.join(get_document_categories())}")
    print(f"{'=' * 60}\n")

    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
