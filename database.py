import sqlite3

# Connect to SQLite database
connection = sqlite3.connect("database.db")
cursor = connection.cursor()

# ==========================
# Users Table
# ==========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    fullname TEXT NOT NULL,

    email TEXT UNIQUE NOT NULL,

    password TEXT NOT NULL

)
""")

# ==========================
# Interview Sessions Table
# ==========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS interview_sessions (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    role TEXT NOT NULL,

    skills TEXT NOT NULL,

    difficulty TEXT NOT NULL,

    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    completed INTEGER DEFAULT 0,

    overall_score INTEGER,

    aptitude_score INTEGER,

    technical_score INTEGER,

    hr_score INTEGER,

    communication_score INTEGER,

    confidence_score INTEGER,

    strengths TEXT,

    weaknesses TEXT,

    recommendations TEXT,

    FOREIGN KEY(user_id) REFERENCES users(id)

)
""")

# ==========================
# Interview Messages Table
# ==========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS interview_messages (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER NOT NULL,

    question_number INTEGER NOT NULL,

    question TEXT NOT NULL,

    answer TEXT,

    FOREIGN KEY(session_id) REFERENCES interview_sessions(id)

)
""")

connection.commit()
connection.close()

print("Database Created Successfully!")