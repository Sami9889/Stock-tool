import bcrypt
import streamlit as st
from database import get_db_connection
import re

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def is_valid_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    return True, "Password meets requirements"

def is_valid_username(username):
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, "Username is valid"

def check_username_exists(username):
    """Check if username already exists"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = %s', (username,))
        count = cursor.fetchone()[0]
        return count > 0

def register_user(username, password):
    username_valid, username_msg = is_valid_username(username)
    if not username_valid:
        st.error(username_msg)
        return False

    password_valid, password_msg = is_valid_password(password)
    if not password_valid:
        st.error(password_msg)
        return False

    # Check for existing username before attempting to insert
    if check_username_exists(username):
        st.error("Username already exists. Please choose a different username.")
        return False

    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            password_hash = hash_password(password)
            cursor.execute(
                'INSERT INTO users (username, password_hash) VALUES (%s, %s)',
                (username, password_hash)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error registering user: {e}")
            st.error("An error occurred during registration. Please try again.")
            return False

def login_user(username, password):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, password_hash FROM users WHERE username = %s',
            (username,)
        )
        result = cursor.fetchone()

        if result and verify_password(password, result[1]):
            return result[0]  # Return user_id
        return None

def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None