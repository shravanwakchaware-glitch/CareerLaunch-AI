from flask import Flask,render_template,request,redirect,url_for,session
import sqlite3
import json
from services.interview_ai import InterviewAI, active_interviews, extract_skills
import os
from werkzeug.utils import secure_filename
from services.resume_parser import extract_resume_text
from services.ats_service import analyze_resume
app = Flask(__name__)
app.secret_key = "careerlaunch_secret_key"
@app.route('/')
def home():
    return render_template('index.html')
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        connection.close()

        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]
            session["email"] = user[2]
            return redirect(url_for("dashboard"))
        else:
            return "Invalid Email or Password"

    return render_template("login.html")
@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]

        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO users(fullname, email, password) VALUES(?,?,?)",
            (fullname, email, password)
        )

        connection.commit()
        connection.close()

        return redirect(url_for("login"))

    return render_template("signup.html")
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # ==========================
    # Dashboard Statistics
    # ==========================
    cursor.execute("""
        SELECT
            COUNT(*),
            AVG(overall_score),
            MAX(overall_score),
            MAX(interview_date)
        FROM interview_results
        WHERE user_id = ?
    """, (session["user_id"],))

    stats = cursor.fetchone()

    total_interviews = stats[0] or 0
    average_score = stats[1] or 0
    highest_score = stats[2] or 0
    latest_interview = stats[3]

    # ==========================
    # Placement Readiness
    # ==========================
    readiness = min(
        100,
        int(
            average_score * 0.7 +
            min(total_interviews, 10) * 3
        )
    )

    # ==========================
    # Readiness Status
    # ==========================
    if readiness >= 85:
        status = "🟢 Placement Ready"

    elif readiness >= 70:
        status = "🔵 Good Progress"

    elif readiness >= 50:
        status = "🟡 Improving"

    else:
        status = "🔴 Needs Improvement"

    # ==========================
    # AI Tip
    # ==========================
    if readiness >= 85:
        tip = "Excellent work! Keep practicing to maintain your performance."

    elif readiness >= 70:
        tip = "Complete one more mock interview to become placement ready."

    elif readiness >= 50:
        tip = "Improve your interview performance and resume ATS score."

    else:
        tip = "Upload your resume and complete your first mock interview to start improving."

    # ==========================
    # AI Career Coach
    # ==========================
    if readiness >= 85:

        ai_message = (
            "Excellent performance! You are almost placement-ready. "
            "Continue practicing company-specific interviews."
        )

        recommendation1 = "Practice one advanced mock interview."

        recommendation2 = "Improve communication confidence."

        recommendation3 = "Apply for internships and placements."

    elif readiness >= 70:

        ai_message = (
            "You're making great progress. A little more practice can "
            "significantly improve your placement chances."
        )

        recommendation1 = "Complete two mock interviews."

        recommendation2 = "Improve ATS score above 80%."

        recommendation3 = "Practice HR interview questions."

    elif readiness >= 50:

        ai_message = (
            "Your fundamentals are improving. Focus on technical concepts "
            "and communication."
        )

        recommendation1 = "Upload your resume."

        recommendation2 = "Practice SQL and DSA."

        recommendation3 = "Complete one mock interview."

    else:

        ai_message = (
            "Let's start building your placement journey. Small improvements "
            "every day will make a big difference."
        )

        recommendation1 = "Upload your resume."

        recommendation2 = "Take your first mock interview."

        recommendation3 = "Build one real-world project."

    predicted_readiness = min(readiness + 10, 100)

    # ==========================
    # Recent Activities
    # ==========================
    cursor.execute("""
        SELECT
            job_role,
            overall_score,
            interview_date
        FROM interview_results
        WHERE user_id = ?
        ORDER BY interview_date DESC
        LIMIT 5
    """, (session["user_id"],))

    recent_activities = cursor.fetchall()

    connection.close()

    # ==========================
    # Render Dashboard
    # ==========================
    return render_template(
        "dashboard.html",

        username=session["username"],

        stats=stats,

        recent_activities=recent_activities,

        readiness=readiness,

        status=status,

        tip=tip,

        ai_message=ai_message,

        recommendation1=recommendation1,

        recommendation2=recommendation2,

        recommendation3=recommendation3,

        predicted_readiness=predicted_readiness
    )
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("home"))
@app.route('/without_resume')
def without_resume():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("without_resume.html")


@app.route("/skills")
def skills():

    if "user_id" not in session:
        return redirect(url_for("login"))

    role = request.args.get("job_role")

    return render_template(
        "skills.html",
        username=session["username"],
        role=role
    )
@app.route("/resume_role", methods=["POST"])
def resume_role():

    if "user_id" not in session:
        return redirect(url_for("login"))

    file = request.files.get("resume")

    if not file or file.filename == "":
        return redirect(url_for("mock_interview"))

    # Create uploads folder
    upload_folder = "uploads"
    os.makedirs(upload_folder, exist_ok=True)

    # Save uploaded resume
    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)

    file.save(filepath)

    # Store resume information in session
    session["resume_path"] = filepath
    session["resume_mode"] = True

    # Open Resume Role page
    return render_template(
        "resume_role.html",
        username=session["username"]
    )

@app.route("/interview_setup", methods=["POST"])
def interview_setup():

    if "user_id" not in session:
        return redirect(url_for("login"))

    job_role = request.form.get("job_role")
    difficulty = request.form.get("difficulty", "Intermediate")

    # ===================================
    # Resume Interview
    # ===================================
    if session.get("resume_mode"):

        resume_path = session["resume_path"]

        # Extract Resume Text
        resume_text = extract_resume_text(resume_path)

        # Extract Skills using AI
        skills = extract_skills(resume_text)

        other_skills = ""

        # Clear Resume Session
        session.pop("resume_path", None)
        session.pop("resume_mode", None)

    # ===================================
    # Without Resume
    # ===================================
    else:

        skills = request.form.getlist("skills")
        other_skills = request.form.get("other_skills")

    # Save Everything
    session["job_role"] = job_role
    session["skills"] = skills
    session["other_skills"] = other_skills
    session["difficulty"] = difficulty

    return render_template(
        "interview_setup.html",
        username=session["username"],
        job_role=job_role,
        skills=skills,
        other_skills=other_skills,
        difficulty=difficulty
    )

@app.route("/interview")
def interview():

    if "user_id" not in session:
        return redirect(url_for("login"))

    interview = InterviewAI(
        username=session["username"],
        role=session["job_role"],
        skills=session.get("skills", []),
        difficulty=session["difficulty"]
    )

    first_question = interview.start_interview()

    # Save interview object
    active_interviews[interview.session_id] = interview

    # Save session id
    session["interview_session_id"] = interview.session_id

    return render_template(
        "interview.html",

        username=session["username"],

        job_role=session.get("job_role"),

        skills=session.get("skills", []),

        other_skills=session.get("other_skills", ""),

        difficulty=session.get("difficulty"),

        question=first_question["question"],

        current_question=1,

        total_questions=15,

        timer="15:00"
    )
@app.route("/submit_answer", methods=["POST"])
def submit_answer():

    if "user_id" not in session:
        return redirect(url_for("login"))

    answer = request.form.get("answer")

    interview_session_id = session.get("interview_session_id")

    interview = active_interviews.get(interview_session_id)

    if interview is None:
        return "Interview session expired. Please start a new interview."

    result = interview.submit_answer(answer)

    if result["finished"]:

        report = result["report"]

        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        # Save Interview Result
        cursor.execute("""
            INSERT INTO interview_results
            (
                user_id,
                job_role,
                interview_type,
                overall_score,
                technical_score,
                communication_score,
                strengths,
                weaknesses,
                suggestions
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            session.get("job_role"),
            "AI Mock Interview",
            report["overall_score"],
            report["technical_score"],
            report["communication_score"],
            "\n".join(report["strengths"]),
            "\n".join(report["weaknesses"]),
            "\n".join(report["recommendations"])
        ))

        interview_result_id = cursor.lastrowid

        # Save Questions & Answers
        for i in range(len(interview.questions)):

            cursor.execute("""
                INSERT INTO interview_answers
                (
                    interview_result_id,
                    question,
                    user_answer,
                    ai_feedback,
                    score
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                interview_result_id,
                interview.questions[i],
                interview.answers[i],
                "",
                0
            ))

        connection.commit()
        connection.close()

        active_interviews.pop(interview_session_id, None)

        return redirect(url_for("interview_results"))

    return render_template(
        "interview.html",
        username=session["username"],
        job_role=session.get("job_role"),
        skills=session.get("skills", []),
        other_skills=session.get("other_skills", ""),
        difficulty=session.get("difficulty"),
        question=result["question"],
        current_question=result["question_number"],
        total_questions=15,
        timer="15:00"
    )

    return render_template(
        "interview.html",

        username=session["username"],

        job_role=session.get("job_role"),

        skills=session.get("skills", []),

        other_skills=session.get("other_skills", ""),

        difficulty=session.get("difficulty"),

        question=result["question"],

        current_question=result["question_number"],

        total_questions=15,

        timer="15:00"
    )
@app.route("/ats", methods=["GET", "POST"])
def ats():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        file = request.files.get("resume")

        if not file or file.filename == "":
            return render_template(
                "ats_analyzer.html",
                username=session["username"]
            )

        upload_folder = "uploads"
        os.makedirs(upload_folder, exist_ok=True)

        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_folder, filename)

        # Save Resume
        file.save(filepath)
        print("Resume Saved:", filepath)

        # Extract Resume Text
        resume_text = extract_resume_text(filepath)
        print("Resume extracted successfully.")

        # Analyze Resume using Gemini
        analysis = analyze_resume(resume_text)
        print("Gemini analysis completed.")

        # Save Analysis to Database
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO ats_history (
            user_id,
            resume_name,
            ats_score,
            strengths,
            weaknesses,
            keywords,
            suggestions
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            file.filename,
            analysis["ats_score"],
            json.dumps(analysis["strengths"]),
            json.dumps(analysis["weaknesses"]),
            json.dumps(analysis["keywords"]),
            json.dumps(analysis["suggestions"])
        ))

        conn.commit()
        conn.close()

        return render_template(
            "ats_analyzer.html",
            username=session["username"],
            ats_score=analysis["ats_score"],
            strengths=analysis["strengths"],
            weaknesses=analysis["weaknesses"],
            keywords=analysis["keywords"],
            suggestions=analysis["suggestions"]
        )

    return render_template(
        "ats_analyzer.html",
        username=session["username"]
    )

    return render_template(
        "ats_analyzer.html",
        username=session["username"]
    )
@app.route("/mock_interview")
def mock_interview():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "mock_interview.html",
        username=session["username"]
    )

@app.route("/interview_results")
def interview_results():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM interview_results
        WHERE user_id = ?
        ORDER BY interview_date DESC
        LIMIT 1
    """, (session["user_id"],))

    result = cursor.fetchone()

    connection.close()

    return render_template(
        "interview_results.html",
        result=result
    )
@app.route("/finish_interview", methods=["POST"])
def finish_interview():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO interview_results
        (
            user_id,
            job_role,
            interview_type,
            overall_score,
            technical_score,
            communication_score,
            strengths,
            weaknesses,
            suggestions
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        "Python Developer",
        "Mock Interview",
        88,
        90,
        85,
        "Python, Flask",
        "Communication, SQL",
        "Practice SQL joins and improve communication."
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("interview_results"))
@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM interview_results
        WHERE user_id=?
        ORDER BY interview_date DESC
    """, (session["user_id"],))

    interviews = cursor.fetchall()

    connection.close()

    return render_template(
        "history.html",
        interviews=interviews
    )
@app.route("/progress")
def progress():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            COUNT(*),
            AVG(overall_score),
            MAX(overall_score),
            AVG(technical_score),
            AVG(communication_score)
        FROM interview_results
        WHERE user_id=?
    """, (session["user_id"],))

    stats = cursor.fetchone()

    connection.close()

    return render_template(
        "progress.html",
        stats=stats
    )
if __name__ == '__main__':
    app.run(debug=True)
