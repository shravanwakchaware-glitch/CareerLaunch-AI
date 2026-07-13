import sqlite3

connection = sqlite3.connect("database.db")
cursor = connection.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS resumes (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    file_name TEXT NOT NULL,

    file_path TEXT NOT NULL,

    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(user_id) REFERENCES users(id)

)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS interview_results (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    resume_id INTEGER,

    job_role TEXT,

    interview_type TEXT,

    overall_score INTEGER,

    technical_score INTEGER,

    communication_score INTEGER,

    strengths TEXT,

    weaknesses TEXT,

    suggestions TEXT,

    interview_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(user_id) REFERENCES users(id),

    FOREIGN KEY(resume_id) REFERENCES resumes(id)

)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS interview_answers (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    interview_result_id INTEGER NOT NULL,

    question TEXT,

    user_answer TEXT,

    ai_feedback TEXT,

    score INTEGER,

    FOREIGN KEY(interview_result_id) REFERENCES interview_results(id)

)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS job_readiness (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER UNIQUE,

    ats_score INTEGER,

    average_interview_score INTEGER,

    readiness_score INTEGER,

    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(user_id) REFERENCES users(id)

)
""")
connection.commit()
connection.close()

print("All tables created successfully! 🚀")