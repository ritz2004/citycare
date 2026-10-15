import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = "citycare.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Create a default admin account if it does not exist.
    admin = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        ("admin@citycare.com",)
    ).fetchone()

    if admin is None:
        conn.execute("""
            INSERT INTO users (name, email, password, role)
            VALUES (?, ?, ?, ?)
        """, (
            "CityCare Admin",
            "admin@citycare.com",
            generate_password_hash("Admin@123"),
            "admin"
        ))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("CityCare database initialized successfully!")