import sqlite3
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash # pyright: ignore[reportMissingImports]
import os

# Database file path
DB_PATH = 'emotioncv.db'

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    
    # Users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    
    # Emergency contacts table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS emergency_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            relationship TEXT,
            is_primary BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Emotion sessions table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS emotion_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            text_input TEXT,
            ai_response TEXT,
            emotion_scores TEXT,  -- JSON string of emotion scores
            risk_assessment TEXT, -- JSON string of risk assessment
            emergency_triggered BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

class User:
    def __init__(self, id, username, email, password_hash, first_name, last_name, phone, created_at, is_active):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.created_at = created_at
        self.is_active = is_active
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'created_at': self.created_at
        }

class EmergencyContact:
    def __init__(self, id, user_id, name, phone, email, relationship, is_primary, created_at):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.phone = phone
        self.email = email
        self.relationship = relationship
        self.is_primary = is_primary
        self.created_at = created_at
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'relationship': self.relationship,
            'is_primary': self.is_primary
        }

class EmotionSession:
    def __init__(self, id, user_id, session_date, text_input, ai_response, emotion_scores, risk_assessment, emergency_triggered):
        self.id = id
        self.user_id = user_id
        self.session_date = session_date
        self.text_input = text_input
        self.ai_response = ai_response
        self.emotion_scores = json.loads(emotion_scores) if emotion_scores else {}
        self.risk_assessment = json.loads(risk_assessment) if risk_assessment else {}
        self.emergency_triggered = emergency_triggered
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_date': self.session_date,
            'text_input': self.text_input,
            'ai_response': self.ai_response,
            'emotion_scores': self.emotion_scores,
            'risk_assessment': self.risk_assessment,
            'emergency_triggered': self.emergency_triggered
        }

# Database Operations
def add_user(user_data):
    """Add new user to database"""
    conn = get_db_connection()
    
    password_hash = generate_password_hash(user_data['password'])
    
    cursor = conn.execute('''
        INSERT INTO users (username, email, password_hash, first_name, last_name, phone)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        user_data['username'],
        user_data['email'],
        password_hash,
        user_data['first_name'],
        user_data['last_name'],
        user_data.get('phone')
    ))
    
    user_id = cursor.lastrowid
    conn.commit()
    
    # Fetch the created user
    user_row = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    user = User(*user_row) if user_row else None
    
    conn.close()
    return user

def get_user_by_username(username):
    """Get user by username"""
    conn = get_db_connection()
    user_row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    user = User(*user_row) if user_row else None
    conn.close()
    return user

def get_user_by_id(user_id):
    """Get user by ID"""
    conn = get_db_connection()
    user_row = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    user = User(*user_row) if user_row else None
    conn.close()
    return user

def add_emergency_contact(user_id, contact_data):
    """Add emergency contact for user"""
    conn = get_db_connection()
    
    cursor = conn.execute('''
        INSERT INTO emergency_contacts (user_id, name, phone, email, relationship, is_primary)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        contact_data['name'],
        contact_data['phone'],
        contact_data.get('email'),
        contact_data.get('relationship'),
        contact_data.get('is_primary', False)
    ))
    
    contact_id = cursor.lastrowid
    conn.commit()
    
    # Fetch the created contact
    contact_row = conn.execute('SELECT * FROM emergency_contacts WHERE id = ?', (contact_id,)).fetchone()
    contact = EmergencyContact(*contact_row) if contact_row else None
    
    conn.close()
    return contact

def save_emotion_session(session_data):
    """Save emotion analysis session"""
    conn = get_db_connection()
    
    cursor = conn.execute('''
        INSERT INTO emotion_sessions (user_id, text_input, ai_response, emotion_scores, risk_assessment, emergency_triggered)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        session_data['user_id'],
        session_data.get('text_input'),
        session_data.get('ai_response'),
        json.dumps(session_data.get('emotion_scores', {})),
        json.dumps(session_data.get('risk_assessment', {})),
        session_data.get('emergency_triggered', False)
    ))
    
    session_id = cursor.lastrowid
    conn.commit()
    
    # Fetch the created session
    session_row = conn.execute('SELECT * FROM emotion_sessions WHERE id = ?', (session_id,)).fetchone()
    session = EmotionSession(*session_row) if session_row else None
    
    conn.close()
    return session

def get_user_sessions(user_id, limit=50):
    """Get recent emotion sessions for user"""
    conn = get_db_connection()
    
    sessions_rows = conn.execute('''
        SELECT * FROM emotion_sessions 
        WHERE user_id = ? 
        ORDER BY session_date DESC 
        LIMIT ?
    ''', (user_id, limit)).fetchall()
    
    sessions = [EmotionSession(*row) for row in sessions_rows]
    conn.close()
    return sessions

def get_user_emergency_contacts(user_id):
    """Get all emergency contacts for user"""
    conn = get_db_connection()
    contacts_rows = conn.execute('SELECT * FROM emergency_contacts WHERE user_id = ?', (user_id,)).fetchall()
    contacts = [EmergencyContact(*row) for row in contacts_rows]
    conn.close()
    return contacts
