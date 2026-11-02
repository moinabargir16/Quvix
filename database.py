
import sqlite3

DB_NAME = "quvix.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def register_user(username):

    username = username.strip()

    if not username:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO users (username)
        VALUES (?)
    """, (username,))

    cursor.execute("""
        SELECT user_id FROM users
        WHERE username = ?
    """, (username,))

    result = cursor.fetchone()

    conn.commit()
    conn.close()

    return result[0] if result else None


def create_table():

    conn = get_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE COLLATE NOCASE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create quiz history table if it does not exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            topic TEXT,
            score INTEGER,
            total_questions INTEGER,
            accuracy REAL,
            performance_level TEXT,
            quiz_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Check existing columns
    cursor.execute("PRAGMA table_info(quiz_history)")
    columns = [row[1] for row in cursor.fetchall()]

    # Add user_id to an older database if necessary
    if "user_id" not in columns:
        cursor.execute("""
            ALTER TABLE quiz_history
            ADD COLUMN user_id INTEGER
        """)

    # Connect old quiz records to their users
    cursor.execute("""
        SELECT DISTINCT username
        FROM quiz_history
        WHERE username IS NOT NULL AND TRIM(username) != ''
    """)

    old_users = cursor.fetchall()

    for user in old_users:
        register_user(user[0])

    cursor.execute("""
        UPDATE quiz_history
        SET user_id = (
            SELECT user_id
            FROM users
            WHERE users.username = quiz_history.username COLLATE NOCASE
        )
        WHERE user_id IS NULL
    """)

    conn.commit()
    conn.close()


def save_result(username, topic, score, total, accuracy, level):

    user_id = register_user(username)

    if user_id is None:
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO quiz_history
        (user_id, username, topic, score, total_questions,
         accuracy, performance_level)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, username, topic, score, total, accuracy, level
    ))

    conn.commit()
    conn.close()


def get_history(username):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT topic, score, total_questions,
               accuracy, performance_level, quiz_date
        FROM quiz_history
        WHERE user_id = (
            SELECT user_id FROM users
            WHERE username = ? COLLATE NOCASE
        )
        ORDER BY quiz_date DESC, id DESC
    """, (username.strip(),))

    records = cursor.fetchall()

    conn.close()

    return records


def get_user_stats(username):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*),
            COALESCE(SUM(score), 0),
            COALESCE(SUM(total_questions), 0),
            COALESCE(AVG(accuracy), 0)
        FROM quiz_history
        WHERE user_id = (
            SELECT user_id FROM users
            WHERE username = ? COLLATE NOCASE
        )
    """, (username.strip(),))

    stats = cursor.fetchone()

    conn.close()

    return stats


def get_all_users():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username, created_at
        FROM users
        ORDER BY username
    """)

    users = cursor.fetchall()

    conn.close()

    return users
