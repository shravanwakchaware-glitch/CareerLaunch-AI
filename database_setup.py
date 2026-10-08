import sqlite3


# =========================================================
# DATABASE CONNECTION
# =========================================================

connection = sqlite3.connect("database.db")
cursor = connection.cursor()

print("=" * 60)
print("CAREERLAUNCH AI DATABASE SETUP")
print("=" * 60)


# =========================================================
# USERS TABLE
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")


# =========================================================
# INTERVIEW SESSIONS TABLE
# =========================================================

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


# =========================================================
# INTERVIEW MESSAGES TABLE
# =========================================================

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


# =========================================================
# ATS HISTORY TABLE
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS ats_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    resume_name TEXT NOT NULL,
    ats_score INTEGER,
    strengths TEXT,
    weaknesses TEXT,
    keywords TEXT,
    suggestions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")


# =========================================================
# RESUMES TABLE
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    resume_text TEXT,
    ats_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")


# =========================================================
# INTERVIEW RESULTS TABLE
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS interview_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    job_role TEXT,
    difficulty TEXT,
    overall_score REAL,
    technical_score REAL,
    communication_score REAL,
    confidence_score REAL,
    aptitude_score REAL,
    hr_score REAL,
    strengths TEXT,
    weaknesses TEXT,
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")


# =========================================================
# INTERVIEW ANSWERS TABLE
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS interview_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER NOT NULL,
    question_number INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT,
    score REAL,
    feedback TEXT,
    category TEXT,
    FOREIGN KEY(result_id) REFERENCES interview_results(id)
)
""")


# =========================================================
# JOB READINESS TABLE
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS job_readiness (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    readiness_score REAL,
    technical_score REAL,
    communication_score REAL,
    confidence_score REAL,
    aptitude_score REAL,
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")


# =========================================================
# APTITUDE QUESTIONS TABLE
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS aptitude_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    explanation TEXT
)
""")


# =========================================================
# DSA QUESTIONS TABLE
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS dsa_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    examples TEXT,
    constraints TEXT,
    expected_time_complexity TEXT,
    expected_space_complexity TEXT,
    starter_code_python TEXT,
    starter_code_java TEXT,
    starter_code_cpp TEXT,
    starter_code_javascript TEXT
)
""")


# =========================================================
# HR QUESTIONS TABLE
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS hr_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    category TEXT NOT NULL
)
""")


# =========================================================
# 50 HR QUESTIONS
# =========================================================

hr_questions = [

    # -----------------------------------------------------
    # INTRODUCTION
    # -----------------------------------------------------

    (
        "Tell me about yourself and briefly describe your background, skills, achievements, and career goals.",
        "Introduction"
    ),

    (
        "Walk me through your academic journey and the experiences that have shaped your career interests.",
        "Introduction"
    ),

    (
        "How would you describe yourself in three words, and why did you choose those words?",
        "Introduction"
    ),

    (
        "What motivates you to build a career in the technology industry?",
        "Motivation"
    ),

    (
        "What are your biggest strengths as a student or young professional?",
        "Strengths"
    ),

    # -----------------------------------------------------
    # STRENGTHS AND WEAKNESSES
    # -----------------------------------------------------

    (
        "What are your strongest qualities and how have they helped you in your academic or professional work?",
        "Strengths"
    ),

    (
        "What is one weakness you are currently working on, and what are you doing to improve it?",
        "Weaknesses"
    ),

    (
        "What is a skill you have improved significantly in the last year?",
        "Strengths"
    ),

    (
        "What is one area where you believe you still need significant improvement?",
        "Weaknesses"
    ),

    (
        "How do you handle situations where you realize that you have made a mistake?",
        "Self Awareness"
    ),

    # -----------------------------------------------------
    # TEAMWORK
    # -----------------------------------------------------

    (
        "Tell me about a time when you worked successfully as part of a team.",
        "Teamwork"
    ),

    (
        "Describe a situation where you disagreed with a teammate. How did you handle it?",
        "Teamwork"
    ),

    (
        "What role do you usually take when working in a team?",
        "Teamwork"
    ),

    (
        "How would you handle a teammate who is not contributing equally to a project?",
        "Teamwork"
    ),

    (
        "Tell me about a time when you helped a teammate solve a problem.",
        "Teamwork"
    ),

    # -----------------------------------------------------
    # PROBLEM SOLVING
    # -----------------------------------------------------

    (
        "Describe a difficult problem you faced and explain how you solved it.",
        "Problem Solving"
    ),

    (
        "Tell me about a challenging project you worked on and how you managed the difficulties.",
        "Problem Solving"
    ),

    (
        "What steps do you normally follow when you face a problem that you have never encountered before?",
        "Problem Solving"
    ),

    (
        "Tell me about a time when your first solution did not work. What did you do next?",
        "Problem Solving"
    ),

    (
        "How do you decide which problem should be solved first when you have multiple problems at the same time?",
        "Problem Solving"
    ),

    # -----------------------------------------------------
    # LEADERSHIP
    # -----------------------------------------------------

    (
        "Tell me about a time when you took leadership of a project or team.",
        "Leadership"
    ),

    (
        "What does good leadership mean to you?",
        "Leadership"
    ),

    (
        "Describe a situation where you had to take responsibility for a team.",
        "Leadership"
    ),

    (
        "How would you motivate a team member who has lost interest in a project?",
        "Leadership"
    ),

    (
        "Have you ever taken initiative without being asked to do something? Tell me about it.",
        "Leadership"
    ),

    # -----------------------------------------------------
    # FAILURE AND LEARNING
    # -----------------------------------------------------

    (
        "Tell me about a failure or mistake that taught you an important lesson.",
        "Failure"
    ),

    (
        "Describe a time when you received negative feedback. How did you respond?",
        "Feedback"
    ),

    (
        "What is the biggest lesson you have learned from your academic or project experience?",
        "Learning"
    ),

    (
        "Tell me about a time when you failed to meet your own expectations.",
        "Failure"
    ),

    (
        "How do you react when someone points out a mistake in your work?",
        "Feedback"
    ),

    # -----------------------------------------------------
    # WORK ETHIC
    # -----------------------------------------------------

    (
        "How do you manage your time when you have multiple deadlines?",
        "Work Ethic"
    ),

    (
        "How do you prioritize your work when everything seems important?",
        "Work Ethic"
    ),

    (
        "Tell me about a time when you had to work under pressure.",
        "Work Ethic"
    ),

    (
        "How do you stay productive when you are working on a task that you find boring?",
        "Work Ethic"
    ),

    (
        "What does professionalism mean to you?",
        "Professionalism"
    ),

    # -----------------------------------------------------
    # COMPANY AND JOB
    # -----------------------------------------------------

    (
        "Why do you think you would be a good fit for this role?",
        "Job Fit"
    ),

    (
        "Why should we hire you?",
        "Job Fit"
    ),

    (
        "What are you looking for in your first job?",
        "Career"
    ),

    (
        "What type of work environment helps you perform your best?",
        "Work Environment"
    ),

    (
        "What do you expect from your manager or team leader?",
        "Work Environment"
    ),

    # -----------------------------------------------------
    # CAREER GOALS
    # -----------------------------------------------------

    (
        "Where do you see yourself professionally in the next five years?",
        "Career Goals"
    ),

    (
        "What are your short-term and long-term career goals?",
        "Career Goals"
    ),

    (
        "What kind of professional do you want to become?",
        "Career Goals"
    ),

    (
        "What skills do you want to develop over the next few years?",
        "Career Goals"
    ),

    (
        "How does this job fit into your long-term career plans?",
        "Career Goals"
    ),

    # -----------------------------------------------------
    # SITUATIONAL HR
    # -----------------------------------------------------

    (
        "If you were given a task with a very short deadline, how would you approach it?",
        "Situational"
    ),

    (
        "If your manager gave you an assignment that you did not understand, what would you do?",
        "Situational"
    ),

    (
        "If two teammates were arguing during an important project, how would you handle the situation?",
        "Situational"
    ),

    (
        "If you discovered an important mistake just before a project deadline, what would you do?",
        "Situational"
    ),

    (
        "If you were assigned a task outside your current skill set, how would you handle it?",
        "Situational"
    )
]


# =========================================================
# INSERT HR QUESTIONS
# =========================================================

cursor.execute("SELECT COUNT(*) FROM hr_questions")
hr_count = cursor.fetchone()[0]

if hr_count == 0:

    cursor.executemany("""
        INSERT INTO hr_questions (
            question,
            category
        )
        VALUES (?, ?)
    """, hr_questions)

    print(f"{len(hr_questions)} HR questions inserted successfully! 🚀")

else:

    print(
        f"HR question bank already contains {hr_count} questions."
    )


# =========================================================
# SAVE DATABASE
# =========================================================

connection.commit()
connection.close()


# =========================================================
# COMPLETION MESSAGE
# =========================================================

print()
print("=" * 60)
print("DATABASE SETUP COMPLETED SUCCESSFULLY!")
print("=" * 60)

print()
print("Tables available:")
print("✓ users")
print("✓ interview_sessions")
print("✓ interview_messages")
print("✓ ats_history")
print("✓ resumes")
print("✓ interview_results")
print("✓ interview_answers")
print("✓ job_readiness")
print("✓ aptitude_questions")
print("✓ dsa_questions")
print("✓ hr_questions")

print()
print("HR question bank: 50 questions")
print("=" * 60)