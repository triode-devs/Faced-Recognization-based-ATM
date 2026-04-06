"""database.py — SQLite database operations"""
import sqlite3, os, hashlib
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "atm_biometric.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number     TEXT UNIQUE NOT NULL,
            holder_name     TEXT NOT NULL,
            phone           TEXT,
            email           TEXT,
            balance         REAL DEFAULT 5000.0,
            face_image      TEXT,
            face_encoding   BLOB,
            failed_attempts INTEGER DEFAULT 0,
            is_locked       INTEGER DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number TEXT,
            action      TEXT,
            amount      REAL,
            timestamp   TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS unknown_faces (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number TEXT,
            image_file  TEXT,
            status      TEXT DEFAULT 'pending',
            action      TEXT,
            timestamp   TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    conn.commit()
    conn.close()


def _hash(pw): return hashlib.sha256(pw.encode()).hexdigest()


def create_admin(username, password):
    conn = get_conn()
    try:
        conn.execute("INSERT OR IGNORE INTO admins (username, password) VALUES (?,?)",
                     (username, _hash(password)))
        conn.commit()
    finally:
        conn.close()


def get_admin(username, password):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM admins WHERE username=? AND password=?",
        (username, _hash(password))
    ).fetchone()
    conn.close()
    return row


def get_account(card_number):
    conn = get_conn()
    row = conn.execute("SELECT * FROM accounts WHERE card_number=?", (card_number,)).fetchone()
    conn.close()
    return row


def get_all_accounts():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM accounts ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


def create_account(card, name, phone, email, balance):
    conn = get_conn()
    conn.execute("""
        INSERT INTO accounts (card_number, holder_name, phone, email, balance)
        VALUES (?,?,?,?,?)
    """, (card, name, phone, email, balance))
    conn.commit()
    conn.close()


def update_face_encoding(card, image_file, encoding_blob):
    conn = get_conn()
    conn.execute("""
        UPDATE accounts SET face_image=?, face_encoding=? WHERE card_number=?
    """, (image_file, encoding_blob, card))
    conn.commit()
    conn.close()


def update_balance(card, new_balance):
    conn = get_conn()
    conn.execute("UPDATE accounts SET balance=? WHERE card_number=?", (new_balance, card))
    conn.commit()
    conn.close()


def log_transaction(card, action, amount):
    conn = get_conn()
    conn.execute("INSERT INTO transactions (card_number, action, amount) VALUES (?,?,?)",
                 (card, action, amount))
    conn.commit()
    conn.close()


def get_transactions(card, limit=10):
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM transactions WHERE card_number=?
        ORDER BY timestamp DESC LIMIT ?
    """, (card, limit)).fetchall()
    conn.close()
    return rows


def update_failed_attempts(card, attempts, lock):
    conn = get_conn()
    conn.execute("""
        UPDATE accounts SET failed_attempts=?, is_locked=? WHERE card_number=?
    """, (attempts, 1 if lock else 0, card))
    conn.commit()
    conn.close()


def reset_failed_attempts(card):
    conn = get_conn()
    conn.execute("UPDATE accounts SET failed_attempts=0, is_locked=0 WHERE card_number=?", (card,))
    conn.commit()
    conn.close()


def add_unknown_face(card, image_file):
    conn = get_conn()
    conn.execute("INSERT INTO unknown_faces (card_number, image_file) VALUES (?,?)",
                 (card, image_file))
    conn.commit()
    conn.close()


def get_unknown_faces(card=None, pending_only=False):
    conn = get_conn()
    if card and pending_only:
        rows = conn.execute("""
            SELECT * FROM unknown_faces WHERE card_number=? AND status='pending'
            ORDER BY timestamp DESC
        """, (card,)).fetchall()
    elif card:
        rows = conn.execute("""
            SELECT * FROM unknown_faces WHERE card_number=?
            ORDER BY timestamp DESC
        """, (card,)).fetchall()
    elif pending_only:
        rows = conn.execute("""
            SELECT uf.*, a.holder_name FROM unknown_faces uf
            LEFT JOIN accounts a ON uf.card_number = a.card_number
            WHERE uf.status='pending' ORDER BY uf.timestamp DESC
        """).fetchall()
    else:
        rows = conn.execute("""
            SELECT uf.*, a.holder_name FROM unknown_faces uf
            LEFT JOIN accounts a ON uf.card_number = a.card_number
            ORDER BY uf.timestamp DESC
        """).fetchall()
    conn.close()
    return rows


def resolve_unknown_face(face_id, action):
    conn = get_conn()
    conn.execute("""
        UPDATE unknown_faces SET status='resolved', action=? WHERE id=?
    """, (action, face_id))
    conn.commit()
    conn.close()
