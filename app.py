from flask import Flask,render_template,request,redirect,url_for,session,jsonify
import sqlite3
from services.hr_service import evaluate_hr_answer
import json
from services.dsa_service import evaluate_dsa_solution
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

    print("DEBUG STATS FROM DATABASE:", stats)

    # ==========================
    # SAFELY HANDLE EMPTY DATA
    # ==========================

    # For a new user with no interviews,
    # SQLite returns:
    # (0, None, None, None)

    total_interviews = (
        stats[0] if stats[0] is not None else 0
    )

    average_score = (
        stats[1] if stats[1] is not None else 0
    )

    highest_score = (
        stats[2] if stats[2] is not None else 0
    )

    latest_interview = (
        stats[3]
        if stats[3] is not None
        else "No interviews yet"
    )

    # IMPORTANT:
    # Replace the original stats tuple with
    # safe values before sending it to dashboard.html.

    stats = (
        total_interviews,
        average_score,
        highest_score,
        latest_interview
    )

    print("DEBUG SAFE STATS:", stats)

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

        tip = (
            "Excellent work! Keep practicing "
            "to maintain your performance."
        )

    elif readiness >= 70:

        tip = (
            "Complete one more mock interview "
            "to become placement ready."
        )

    elif readiness >= 50:

        tip = (
            "Improve your interview performance "
            "and resume ATS score."
        )

    else:

        tip = (
            "Upload your resume and complete your "
            "first mock interview to start improving."
        )

    # ==========================
    # AI Career Coach
    # ==========================

    if readiness >= 85:

        ai_message = (
            "Excellent performance! You are almost "
            "placement-ready. Continue practicing "
            "company-specific interviews."
        )

        recommendation1 = (
            "Practice one advanced mock interview."
        )

        recommendation2 = (
            "Improve communication confidence."
        )

        recommendation3 = (
            "Apply for internships and placements."
        )

    elif readiness >= 70:

        ai_message = (
            "You're making great progress. A little "
            "more practice can significantly improve "
            "your placement chances."
        )

        recommendation1 = (
            "Complete two mock interviews."
        )

        recommendation2 = (
            "Improve ATS score above 80%."
        )

        recommendation3 = (
            "Practice HR interview questions."
        )

    elif readiness >= 50:

        ai_message = (
            "Your fundamentals are improving. Focus "
            "on technical concepts and communication."
        )

        recommendation1 = (
            "Upload your resume."
        )

        recommendation2 = (
            "Practice SQL and DSA."
        )

        recommendation3 = (
            "Complete one mock interview."
        )

    else:

        ai_message = (
            "Let's start building your placement journey. "
            "Small improvements every day will make a "
            "big difference."
        )

        recommendation1 = (
            "Upload your resume."
        )

        recommendation2 = (
            "Take your first mock interview."
        )

        recommendation3 = (
            "Build one real-world project."
        )

    # ==========================
    # Predicted Readiness
    # ==========================

    predicted_readiness = min(
        readiness + 10,
        100
    )

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
        other_skills = request.form.get("other_skills", "")

    # ===================================
    # Save Interview Configuration
    # ===================================

    session["job_role"] = job_role
    session["skills"] = skills
    session["other_skills"] = other_skills
    session["difficulty"] = difficulty

    # ===================================
    # Show Interview Setup
    # ===================================

    return render_template(
        "interview_setup.html",
        username=session["username"],
        job_role=job_role,
        skills=skills,
        other_skills=other_skills,
        difficulty=difficulty
    )
@app.route("/interview-instructions", methods=["GET", "POST"])
def interview_instructions():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # ==========================================
    # RECEIVE DIFFICULTY FROM INTERVIEW SETUP
    # ==========================================

    if request.method == "POST":

        difficulty = request.form.get(
            "difficulty",
            "Intermediate"
        )

        session["difficulty"] = difficulty

        print("================================")
        print("INTERVIEW INSTRUCTIONS")
        print("Difficulty:", difficulty)
        print("================================")

    # ==========================================
    # SHOW INSTRUCTIONS PAGE
    # ==========================================

    return render_template(
        "interview_instructions.html",
        username=session.get("username", "Candidate"),
        job_role=session.get("job_role", ""),
        skills=session.get("skills", []),
        difficulty=session.get(
            "difficulty",
            "Intermediate"
        )
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

    answer = request.form.get("answer", "").strip()

    interview_session_id = session.get("interview_session_id")

    interview = active_interviews.get(interview_session_id)

    if interview is None:
        return "Interview session expired. Please start a new interview."


    # =========================================================
    # SUBMIT ANSWER TO AI
    # =========================================================

    result = interview.submit_answer(answer)


    # =========================================================
    # INTERVIEW FINISHED
    # =========================================================

    if result["finished"]:

        report = result.get("report", {})


        print()
        print("================================")
        print("FINAL REPORT RECEIVED BY APP.PY")
        print("================================")
        print(report)
        print("================================")
        print()


        # -----------------------------------------------------
        # Safely get every field
        # -----------------------------------------------------

        overall_score = report.get(
            "overall_score",
            0
        )

        technical_score = report.get(
            "technical_score",
            0
        )

        communication_score = report.get(
            "communication_score",
            0
        )

        strengths = report.get(
            "strengths",
            ["Unable to generate evaluation."]
        )

        weaknesses = report.get(
            "weaknesses",
            ["Unable to generate evaluation."]
        )

        recommendations = report.get(
            "recommendations",
            ["Please try the interview again."]
        )


        # -----------------------------------------------------
        # Make sure lists are actually lists
        # -----------------------------------------------------

        if not isinstance(strengths, list):
            strengths = [str(strengths)]

        if not isinstance(weaknesses, list):
            weaknesses = [str(weaknesses)]

        if not isinstance(recommendations, list):
            recommendations = [str(recommendations)]


        # =====================================================
        # SAVE INTERVIEW RESULT
        # =====================================================

        connection = sqlite3.connect(
            "database.db"
        )

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

            session.get(
                "job_role"
            ),

            "AI Mock Interview",

            overall_score,

            technical_score,

            communication_score,

            "\n".join(
                str(x) for x in strengths
            ),

            "\n".join(
                str(x) for x in weaknesses
            ),

            "\n".join(
                str(x) for x in recommendations
            )

        ))


        interview_result_id = cursor.lastrowid


        # =====================================================
        # SAVE QUESTIONS AND ANSWERS
        # =====================================================

        total_items = min(
            len(interview.questions),
            len(interview.answers)
        )


        for i in range(total_items):

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


        # =====================================================
        # REMOVE ACTIVE INTERVIEW
        # =====================================================

        active_interviews.pop(
            interview_session_id,
            None
        )


        # =====================================================
        # GO TO RESULT PAGE
        # =====================================================

        return redirect(
            url_for("interview_results")
        )


    # =========================================================
    # NEXT QUESTION
    # =========================================================

    return render_template(

        "interview.html",

        username=session["username"],

        job_role=session.get(
            "job_role"
        ),

        skills=session.get(
            "skills",
            []
        ),

        other_skills=session.get(
            "other_skills",
            ""
        ),

        difficulty=session.get(
            "difficulty"
        ),

        question=result["question"],

        current_question=result[
            "question_number"
        ],

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

# ============================================================
# HR PRACTICE
# ============================================================

@app.route("/hr")
def hr():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "hr.html",
        username=session.get(
            "username",
            "Candidate"
        )
    )


# ============================================================
# HR INTERVIEW
# ============================================================


@app.route("/hr-interview")
def hr_interview():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # --------------------------------------------------------
    # CONNECT TO DATABASE
    # --------------------------------------------------------

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # --------------------------------------------------------
    # GET 5 RANDOM HR QUESTIONS
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            question,
            category
        FROM hr_questions
        ORDER BY RANDOM()
        LIMIT 5
    """)

    rows = cursor.fetchall()

    connection.close()

    # --------------------------------------------------------
    # CHECK QUESTIONS
    # --------------------------------------------------------

    if not rows:

        return (
            "No HR questions found in database. "
            "Please run database_setup.py first."
        )

    # --------------------------------------------------------
    # CONVERT DATABASE DATA
    # --------------------------------------------------------

    questions = []

    for row in rows:

        questions.append({

            "id": row[0],

            "question": row[1],

            "category": row[2]

        })

    # --------------------------------------------------------
    # START FRESH HR SESSION
    # --------------------------------------------------------

    session["hr_questions"] = questions

    session["hr_results"] = []

    session["hr_saved_to_db"] = False

    session.modified = True

    # --------------------------------------------------------
    # RENDER HR INTERVIEW
    # --------------------------------------------------------

    return render_template(

        "hr_interview.html",

        username=session.get(
            "username",
            "Candidate"
        ),

        questions=questions

    )
# ============================================================
# HR SUBMIT ANSWER
# ============================================================

@app.route("/hr-submit", methods=["POST"])
def hr_submit():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "Please login first."
        }), 401

    try:

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({
                "success": False,
                "error": "Invalid request."
            }), 400


        question_index = data.get(
            "question_index"
        )

        question = data.get(
            "question",
            ""
        )

        answer = data.get(
            "answer",
            ""
        ).strip()


        if question_index is None:

            return jsonify({
                "success": False,
                "error": "Question index missing."
            }), 400


        if not answer:

            return jsonify({
                "success": False,
                "error": "Answer cannot be empty."
            }), 400


        try:

            question_index = int(
                question_index
            )

        except Exception:

            return jsonify({
                "success": False,
                "error": "Invalid question index."
            }), 400


        # ----------------------------------------------------
        # Make sure question belongs to this HR session
        # ----------------------------------------------------

        hr_questions = session.get(
            "hr_questions",
            []
        )


        if (
            question_index < 0 or
            question_index >= len(hr_questions)
        ):

            return jsonify({
                "success": False,
                "error": "Invalid HR question."
            }), 400


        # Use server-side question
        question = hr_questions[
            question_index
        ]["question"]


        print()
        print("=" * 60)
        print("HR ANSWER SUBMISSION")
        print("=" * 60)
        print("Question:", question_index + 1)
        print("Answer:", answer)
        print("=" * 60)


        # ----------------------------------------------------
        # AI EVALUATION
        # ----------------------------------------------------

        evaluation = evaluate_hr_answer(
            question,
            answer
        )


        # ----------------------------------------------------
        # Store result
        # ----------------------------------------------------

        hr_results = session.get(
            "hr_results",
            []
        )


        # Remove old result for same question
        hr_results = [
            item
            for item in hr_results
            if item.get("question_index")
            != question_index
        ]


        hr_results.append({

            "question_index":
                question_index,

            "question":
                question,

            "answer":
                answer,

            "skipped":
                False,

            "score":
                evaluation.get(
                    "score",
                    0
                ),

            "communication":
                evaluation.get(
                    "communication",
                    0
                ),

            "relevance":
                evaluation.get(
                    "relevance",
                    0
                ),

            "confidence":
                evaluation.get(
                    "confidence",
                    0
                ),

            "answer_quality":
                evaluation.get(
                    "answer_quality",
                    0
                ),

            "feedback":
                evaluation.get(
                    "feedback",
                    ""
                ),

            "strengths":
                evaluation.get(
                    "strengths",
                    []
                ),

            "improvements":
                evaluation.get(
                    "improvements",
                    []
                )

        })


        session["hr_results"] = hr_results

        session.modified = True


        return jsonify({

            "success": True,

            "question_index":
                question_index

        })


    except Exception as e:

        print()
        print("=" * 60)
        print("HR SUBMIT ERROR")
        print("=" * 60)
        print(str(e))
        print("=" * 60)


        return jsonify({

            "success": False,

            "error":
                "Unable to evaluate this answer. Please try again."

        }), 500
    # ============================================================
# HR SKIP
# ============================================================

@app.route("/hr-skip", methods=["POST"])
def hr_skip():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "error": "Please login first."
        }), 401


    try:

        data = request.get_json(
            silent=True
        )


        if not data:

            return jsonify({
                "success": False,
                "error": "Invalid request."
            }), 400


        question_index = data.get(
            "question_index"
        )


        try:

            question_index = int(
                question_index
            )

        except Exception:

            return jsonify({
                "success": False,
                "error": "Invalid question index."
            }), 400


        hr_questions = session.get(
            "hr_questions",
            []
        )


        if (
            question_index < 0 or
            question_index >= len(hr_questions)
        ):

            return jsonify({
                "success": False,
                "error": "Invalid HR question."
            }), 400


        question = hr_questions[
            question_index
        ]["question"]


        hr_results = session.get(
            "hr_results",
            []
        )


        # Remove previous answer
        hr_results = [
            item
            for item in hr_results
            if item.get("question_index")
            != question_index
        ]


        # Store skipped question
        hr_results.append({

            "question_index":
                question_index,

            "question":
                question,

            "answer":
                "",

            "skipped":
                True,

            "score":
                0,

            "communication":
                0,

            "relevance":
                0,

            "confidence":
                0,

            "answer_quality":
                0,

            "feedback":
                "You skipped this question.",

            "strengths":
                [],

            "improvements":
                []

        })


        session["hr_results"] = hr_results

        session.modified = True


        print(
            f"HR Question {question_index + 1} skipped."
        )


        # IMPORTANT:
        # Always return JSON.
        # This prevents:
        # Unexpected token '<'

        return jsonify({

            "success": True,

            "skipped": True,

            "question_index":
                question_index

        })


    except Exception as e:

        print()
        print("=" * 60)
        print("HR SKIP ERROR")
        print("=" * 60)
        print(str(e))
        print("=" * 60)


        return jsonify({

            "success": False,

            "error":
                "Unable to skip question."

        }), 500
# ============================================================
# HR RESULT
# ============================================================

@app.route("/hr-result")
def hr_result():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # --------------------------------------------------------
    # Get HR results from session
    # --------------------------------------------------------

    results = session.get("hr_results", [])

    questions = session.get("hr_questions", [])

    total = len(questions)

    # Fallback in case questions are not available
    if total == 0:
        total = 5

    # --------------------------------------------------------
    # Calculate statistics
    # --------------------------------------------------------

    attempted = 0
    skipped = 0

    total_score = 0
    total_communication = 0
    total_relevance = 0
    total_confidence = 0
    total_answer_quality = 0

    for result in results:

        if result.get("skipped", False):

            skipped += 1

            continue

        attempted += 1

        total_score += int(
            result.get("score", 0) or 0
        )

        total_communication += int(
            result.get("communication", 0) or 0
        )

        total_relevance += int(
            result.get("relevance", 0) or 0
        )

        total_confidence += int(
            result.get("confidence", 0) or 0
        )

        total_answer_quality += int(
            result.get("answer_quality", 0) or 0
        )

    # --------------------------------------------------------
    # Calculate averages
    # --------------------------------------------------------

    if attempted > 0:

        average_score = round(
            total_score / attempted
        )

        communication = round(
            total_communication / attempted
        )

        relevance = round(
            total_relevance / attempted
        )

        confidence = round(
            total_confidence / attempted
        )

        answer_quality = round(
            total_answer_quality / attempted
        )

    else:

        average_score = 0
        communication = 0
        relevance = 0
        confidence = 0
        answer_quality = 0

    # --------------------------------------------------------
    # Overall HR score
    #
    # Score is calculated out of ALL 5 questions.
    # Example:
    # 1 correct/high-quality answer + 4 skipped
    # will NOT become 100%.
    # --------------------------------------------------------

    if total > 0:

        score = round(
            total_score / (total * 100) * 100
        )

    else:

        score = 0

    # --------------------------------------------------------
    # Make sure score stays between 0 and 100
    # --------------------------------------------------------

    score = max(
        0,
        min(100, score)
    )

    # --------------------------------------------------------
    # Store final result in session
    # --------------------------------------------------------

    session["hr_final_result"] = {

        "score": score,

        "total": total,

        "attempted": attempted,

        "skipped": skipped,

        "average_score": average_score,

        "communication": communication,

        "relevance": relevance,

        "confidence": confidence,

        "answer_quality": answer_quality,

        "results": results

    }

    session.modified = True

    # --------------------------------------------------------
    # Debug information
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("HR INTERVIEW RESULT")
    print("=" * 60)

    print("Total Questions :", total)
    print("Attempted       :", attempted)
    print("Skipped         :", skipped)
    print("Overall Score   :", score)
    print("Communication   :", communication)
    print("Relevance       :", relevance)
    print("Confidence      :", confidence)
    print("Answer Quality  :", answer_quality)

    print("=" * 60)
    print()

    # --------------------------------------------------------
    # Render result page
    # --------------------------------------------------------

    return render_template(

        "hr_result.html",

        username=session.get(
            "username",
            "Candidate"
        ),

        score=score,

        total=total,

        attempted=attempted,

        skipped=skipped,

        average_score=average_score,

        communication=communication,

        relevance=relevance,

        confidence=confidence,

        answer_quality=answer_quality,

        results=results

    )
# ============================================================
# DSA PRACTICE
# ============================================================

@app.route("/dsa")
def dsa():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dsa.html",
        username=session.get("username", "Candidate")
    )


# ============================================================
# START DSA INTERVIEW
# ============================================================

@app.route("/dsa-interview")
def dsa_interview():

    if "user_id" not in session:
        return redirect(url_for("login"))

    try:

        # ====================================================
        # GET 5 RANDOM QUESTIONS FROM DATABASE
        # ====================================================

        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                title,
                description,
                examples,
                constraints,
                expected_time_complexity,
                expected_space_complexity,
                starter_code_python,
                starter_code_java,
                starter_code_cpp,
                starter_code_javascript
            FROM dsa_questions
            ORDER BY RANDOM()
            LIMIT 5
        """)

        rows = cursor.fetchall()

        connection.close()

        # ====================================================
        # CHECK QUESTION BANK
        # ====================================================

        if len(rows) < 5:

            print()
            print("=" * 60)
            print("❌ DSA QUESTION BANK ERROR")
            print("=" * 60)
            print("Only", len(rows), "questions found.")
            print("At least 5 DSA questions are required.")
            print("=" * 60)

            return "Not enough DSA questions in database.", 500

        # ====================================================
        # FORMAT QUESTIONS FOR FRONTEND
        # ====================================================

        questions = []

        for row in rows:

            questions.append({

                "id": row[0],

                "title": row[1],

                "description": row[2],

                "examples": row[3],

                "constraints": row[4],

                "expected_time_complexity":
                    row[5] or "",

                "expected_space_complexity":
                    row[6] or "",

                "starter_code_python":
                    row[7] or "",

                "starter_code_java":
                    row[8] or "",

                "starter_code_cpp":
                    row[9] or "",

                "starter_code_javascript":
                    row[10] or ""
            })

        # ====================================================
        # SAVE SELECTED QUESTIONS IN SESSION
        # ====================================================

        session["dsa_questions"] = questions

        # Start a fresh practice
        session["dsa_results"] = []

        session.modified = True

        # ====================================================
        # DEBUG
        # ====================================================

        print()
        print("=" * 60)
        print("DSA INTERVIEW STARTED")
        print("=" * 60)

        for index, question in enumerate(questions, start=1):

            print(
                f"{index}. "
                f"[ID {question['id']}] "
                f"{question['title']}"
            )

        print("=" * 60)

        # ====================================================
        # SEND QUESTIONS TO FRONTEND
        # ====================================================

        return render_template(
            "dsa_interview.html",
            username=session.get(
                "username",
                "Candidate"
            ),
            questions=questions
        )

    except Exception as e:

        print()
        print("=" * 60)
        print("❌ DSA INTERVIEW START ERROR")
        print("=" * 60)
        print(str(e))
        print("=" * 60)

        return "Unable to start DSA interview.", 500


# ============================================================
# SUBMIT DSA SOLUTION
# ============================================================

@app.route("/dsa-submit", methods=["POST"])
def dsa_submit():

    if "user_id" not in session:

        return jsonify({
            "error": "Please login first."
        }), 401

    try:

        # ====================================================
        # GET REQUEST DATA
        # ====================================================

        data = request.get_json()

        if not data:

            return jsonify({
                "error": "No submission received."
            }), 400

        question_id = data.get("question_id")

        language = data.get(
            "language",
            "python"
        )

        code = data.get(
            "code",
            ""
        )

        # ====================================================
        # VALIDATE QUESTION ID
        # ====================================================

        try:

            question_id = int(question_id)

        except Exception:

            return jsonify({
                "error": "Invalid question ID."
            }), 400

        # ====================================================
        # VALIDATE CODE
        # ====================================================

        if not code or not code.strip():

            return jsonify({
                "error": "Code cannot be empty."
            }), 400

        # ====================================================
        # GET CURRENT 5 QUESTIONS
        # ====================================================

        selected_questions = session.get(
            "dsa_questions",
            []
        )

        if not selected_questions:

            return jsonify({
                "error":
                    "DSA interview session expired. "
                    "Please start a new interview."
            }), 400

        # ====================================================
        # MAKE SURE QUESTION BELONGS TO CURRENT INTERVIEW
        # ====================================================

        selected_question_ids = [

            int(question["id"])

            for question in selected_questions
        ]

        if question_id not in selected_question_ids:

            return jsonify({
                "error":
                    "This question does not belong "
                    "to the current DSA interview."
            }), 403

        # ====================================================
        # GET ACTUAL QUESTION FROM DATABASE
        # ====================================================

        connection = sqlite3.connect(
            "database.db"
        )

        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                title,
                description,
                examples,
                constraints,
                expected_time_complexity,
                expected_space_complexity
            FROM dsa_questions
            WHERE id = ?
        """, (question_id,))

        row = cursor.fetchone()

        connection.close()

        # ====================================================
        # QUESTION NOT FOUND
        # ====================================================

        if not row:

            return jsonify({
                "error":
                    "Question not found in database."
            }), 404

        # ====================================================
        # BUILD QUESTION
        # ====================================================

        question = {

            "id": row[0],

            "title": row[1],

            "description": row[2],

            "examples": row[3],

            "constraints": row[4],

            "time": row[5] or "",

            "space": row[6] or ""
        }

        # ====================================================
        # DEBUG INFORMATION
        # ====================================================

        print()
        print("=" * 60)
        print("SENDING DSA SOLUTION TO AI")
        print("=" * 60)

        print("Question ID:", question_id)

        print(
            "Question:",
            question["title"]
        )

        print(
            "Language:",
            language
        )

        print(
            "Code length:",
            len(code)
        )

        print("=" * 60)

        # ====================================================
        # AI EVALUATION
        # ====================================================

        from services.dsa_service import (
            evaluate_dsa_solution
        )

        result = evaluate_dsa_solution(

            title=question["title"],

            problem_statement=
                question["description"],

            constraints=
                question["constraints"],

            expected_time=
                question["time"],

            expected_space=
                question["space"],

            language=language,

            code=code
        )

        # ====================================================
        # SAFETY CHECK
        # ====================================================

        if not isinstance(result, dict):

            raise Exception(
                "AI evaluator returned invalid data."
            )

        # ====================================================
        # GET EXISTING RESULTS
        # ====================================================

        dsa_results = session.get(
            "dsa_results",
            []
        )

        # ====================================================
        # REMOVE OLD RESULT
        # FOR SAME QUESTION
        # ====================================================

        dsa_results = [

            item

            for item in dsa_results

            if int(
                item.get(
                    "question_id",
                    -1
                )
            ) != question_id
        ]

        # ====================================================
        # SAVE NEW RESULT
        # ====================================================

        dsa_results.append({

            "question_id":
                question_id,

            "title":
                question["title"],

            "language":
                language,

            "code":
                code,

            "correct":
                bool(
                    result.get(
                        "correct",
                        False
                    )
                ),

            "skipped":
                False,

            "feedback":
                result.get(
                    "feedback",
                    "No feedback provided."
                ),

            "time_complexity":
                result.get(
                    "time_complexity",
                    "Not evaluated"
                ),

            "space_complexity":
                result.get(
                    "space_complexity",
                    "Not evaluated"
                ),

            "correct_approach":
                result.get(
                    "correct_approach",
                    ""
                )
        })

        session["dsa_results"] = dsa_results

        session.modified = True

        # ====================================================
        # SEND SUCCESS RESPONSE
        # ====================================================

        return jsonify({

            "success":
                True,

            "correct":
                bool(
                    result.get(
                        "correct",
                        False
                    )
                ),

            "feedback":
                result.get(
                    "feedback",
                    ""
                ),

            "time_complexity":
                result.get(
                    "time_complexity",
                    "Not evaluated"
                ),

            "space_complexity":
                result.get(
                    "space_complexity",
                    "Not evaluated"
                ),

            "correct_approach":
                result.get(
                    "correct_approach",
                    ""
                )
        })

    except Exception as e:

        print()
        print("=" * 60)
        print("❌ DSA SUBMIT ROUTE ERROR")
        print("=" * 60)
        print(str(e))
        print("=" * 60)

        return jsonify({

            "error":
                f"AI evaluation failed: {str(e)}"

        }), 500


# ============================================================
# DSA RESULT
# ============================================================

@app.route("/dsa-result")
def dsa_result():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    # ========================================================
    # DSA INTERVIEW ALWAYS HAS 5 QUESTIONS
    # ========================================================

    total_questions = 5

    # ========================================================
    # GET RESULTS
    # ========================================================

    results = session.get(
        "dsa_results",
        []
    )

    # ========================================================
    # COUNT ATTEMPTED
    # ========================================================

    attempted_results = [

        item

        for item in results

        if not item.get(
            "skipped",
            False
        )
    ]

    attempted = len(
        attempted_results
    )

    # ========================================================
    # COUNT CORRECT
    # ========================================================

    correct = sum(

        1

        for item in attempted_results

        if item.get(
            "correct",
            False
        )
    )

    # ========================================================
    # COUNT INCORRECT
    # ========================================================

    incorrect = sum(

        1

        for item in attempted_results

        if not item.get(
            "correct",
            False
        )
    )

    # ========================================================
    # COUNT SKIPPED
    # ========================================================

    skipped = sum(

        1

        for item in results

        if item.get(
            "skipped",
            False
        )
    )

    # ========================================================
    # SCORE
    #
    # Score is calculated out of ALL 5 questions.
    #
    # Example:
    # 1 correct + 4 skipped = 20%
    # 3 correct + 1 incorrect + 1 skipped = 60%
    # ========================================================

    score = round(

        (
            correct /
            total_questions
        ) * 100

    )

    # ========================================================
    # DEBUG
    # ========================================================

    print()
    print("=" * 60)
    print("DSA RESULT")
    print("=" * 60)

    print(
        "Total:",
        total_questions
    )

    print(
        "Attempted:",
        attempted
    )

    print(
        "Correct:",
        correct
    )

    print(
        "Incorrect:",
        incorrect
    )

    print(
        "Skipped:",
        skipped
    )

    print(
        "Score:",
        score,
        "%"
    )

    print("=" * 60)

    # ========================================================
    # RENDER RESULT PAGE
    # ========================================================

    return render_template(

        "dsa_result.html",

        username=session.get(
            "username",
            "Candidate"
        ),

        results=results,

        total=total_questions,

        attempted=attempted,

        correct=correct,

        incorrect=incorrect,

        skipped=skipped,

        score=score
    )


# ============================================================
# SKIP DSA QUESTION
# ============================================================

@app.route("/dsa-skip", methods=["POST"])
def dsa_skip():

    if "user_id" not in session:

        return jsonify({

            "error":
                "Please login first."

        }), 401

    try:

        # ====================================================
        # GET REQUEST DATA
        # ====================================================

        data = request.get_json()

        if not data:

            return jsonify({

                "error":
                    "No skip information received."

            }), 400

        question_id = data.get(
            "question_id"
        )

        title = data.get(
            "title",
            "DSA Question"
        )

        # ====================================================
        # VALIDATE QUESTION ID
        # ====================================================

        try:

            question_id = int(
                question_id
            )

        except Exception:

            return jsonify({

                "error":
                    "Invalid question ID."

            }), 400

        # ====================================================
        # CHECK CURRENT INTERVIEW QUESTIONS
        # ====================================================

        selected_questions = session.get(
            "dsa_questions",
            []
        )

        if not selected_questions:

            return jsonify({

                "error":
                    "DSA interview session expired."

            }), 400

        selected_question_ids = [

            int(question["id"])

            for question in selected_questions
        ]

        if question_id not in selected_question_ids:

            return jsonify({

                "error":
                    "This question does not belong "
                    "to the current interview."

            }), 403

        # ====================================================
        # GET EXISTING RESULTS
        # ====================================================

        dsa_results = session.get(
            "dsa_results",
            []
        )

        # ====================================================
        # REMOVE OLD RESULT
        # ====================================================

        dsa_results = [

            item

            for item in dsa_results

            if int(
                item.get(
                    "question_id",
                    -1
                )
            ) != question_id
        ]

        # ====================================================
        # ADD SKIPPED RESULT
        # ====================================================

        dsa_results.append({

            "question_id":
                question_id,

            "title":
                title,

            "language":
                "",

            "code":
                "",

            "correct":
                False,

            "skipped":
                True,

            "feedback":
                "You skipped this question. "
                "It was not evaluated by AI.",

            "time_complexity":
                "Not evaluated",

            "space_complexity":
                "Not evaluated",

            "correct_approach":
                ""
        })

        # ====================================================
        # SAVE SESSION
        # ====================================================

        session["dsa_results"] = dsa_results

        session.modified = True

        # ====================================================
        # RESPONSE
        # ====================================================

        return jsonify({

            "success":
                True,

            "skipped":
                True
        })

    except Exception as e:

        print()
        print("=" * 60)
        print("❌ DSA SKIP ERROR")
        print("=" * 60)

        print(str(e))

        print("=" * 60)

        return jsonify({

            "error":
                "Unable to skip question."

        }), 500

# =========================================================
# APTITUDE PRACTICE
# =========================================================

@app.route("/aptitude")
def aptitude():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "aptitude.html",
        username=session.get(
            "username",
            "Candidate"
        )
    )


# =========================================================
# APTITUDE INTERVIEW
# =========================================================


@app.route("/aptitude-interview")
def aptitude_interview():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # -----------------------------------------------------
    # Get 5 random questions from SQLite
    # -----------------------------------------------------

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            question,
            option_a,
            option_b,
            option_c,
            option_d
        FROM aptitude_questions
        ORDER BY RANDOM()
        LIMIT 5
    """)

    rows = cursor.fetchall()

    connection.close()

    # -----------------------------------------------------
    # Make sure questions are available
    # -----------------------------------------------------

    if not rows:
        return "No aptitude questions found in database. Please run database_setup.py first."

    # -----------------------------------------------------
    # Convert database rows to frontend format
    # IMPORTANT:
    # correct_answer is NOT sent to browser
    # -----------------------------------------------------

    questions = []

    for row in rows:

        questions.append({
            "id": row[0],
            "question": row[1],
            "options": [
                row[2],
                row[3],
                row[4],
                row[5]
            ]
        })

    # -----------------------------------------------------
    # Start fresh attempt
    # -----------------------------------------------------

    session["aptitude_questions"] = questions
    session["aptitude_answers"] = {}

    session.modified = True

    # -----------------------------------------------------
    # Render Aptitude Interview
    # -----------------------------------------------------

    return render_template(
        "aptitude_interview.html",
        username=session.get(
            "username",
            "Candidate"
        ),
        questions=questions
    )
# =========================================================
# APTITUDE SUBMIT ALL
# =========================================================

@app.route("/aptitude-submit-all", methods=["POST"])
def aptitude_submit_all():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    try:

        # -------------------------------------------------
        # Get answers from frontend
        # -------------------------------------------------

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No answers received."
            }), 400

        answers = data.get("answers", [])

        # -------------------------------------------------
        # Get the 5 questions stored for this attempt
        # -------------------------------------------------

        questions = session.get(
            "aptitude_questions",
            []
        )

        if not questions:
            return jsonify({
                "success": False,
                "message": "Aptitude questions not found. Please restart the test."
            }), 400

        # -------------------------------------------------
        # Get question IDs
        # -------------------------------------------------

        question_ids = []

        for question in questions:
            question_ids.append(question["id"])

        # -------------------------------------------------
        # Get correct answers from DATABASE
        # -------------------------------------------------

        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        placeholders = ",".join(
            ["?"] * len(question_ids)
        )

        cursor.execute(
            f"""
            SELECT
                id,
                correct_answer,
                explanation
            FROM aptitude_questions
            WHERE id IN ({placeholders})
            """,
            question_ids
        )

        database_answers = cursor.fetchall()

        connection.close()

        # -------------------------------------------------
        # Convert database results into dictionary
        # -------------------------------------------------

        answer_key = {}

        for row in database_answers:

            answer_key[row[0]] = {
                "correct_answer": row[1],
                "explanation": row[2] or ""
            }

        # -------------------------------------------------
        # Evaluate all questions
        # -------------------------------------------------

        results = []

        correct = 0
        attempted = 0
        skipped = 0

        for index, question in enumerate(questions):

            question_id = question["id"]

            user_answer = None

            if index < len(answers):
                user_answer = answers[index]

            # -------------------------------------------------
            # Question skipped
            # -------------------------------------------------

            if (
                user_answer is None
                or str(user_answer).strip() == ""
            ):

                skipped += 1

                results.append({
                    "question": question["question"],
                    "user_answer": "Not Attempted",
                    "correct_answer": answer_key[question_id]["correct_answer"],
                    "correct": False,
                    "skipped": True,
                    "explanation": answer_key[question_id]["explanation"]
                })

                continue

            # -------------------------------------------------
            # Question attempted
            # -------------------------------------------------

            attempted += 1

            correct_answer = answer_key[question_id]["correct_answer"]

            is_correct = (
                str(user_answer).strip().lower()
                ==
                str(correct_answer).strip().lower()
            )

            if is_correct:
                correct += 1

            results.append({
                "question": question["question"],
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "correct": is_correct,
                "skipped": False,
                "explanation": answer_key[question_id]["explanation"]
            })

        # -------------------------------------------------
        # Calculate result
        # -------------------------------------------------

        total = len(questions)

        incorrect = attempted - correct

        skipped = total - attempted

        # -------------------------------------------------
        # Score is out of ALL 5 questions
        # -------------------------------------------------

        if total > 0:

            score = round(
                (correct / total) * 100
            )

        else:

            score = 0

        # -------------------------------------------------
        # Save result in session
        # -------------------------------------------------

        session["aptitude_result"] = {

            "score": score,

            "total": total,

            "attempted": attempted,

            "correct": correct,

            "incorrect": incorrect,

            "skipped": skipped,

            "results": results
        }

        session.modified = True

        # -------------------------------------------------
        # Return result URL
        # -------------------------------------------------

        return jsonify({

            "success": True,

            "redirect": "/aptitude-result"

        })

    except Exception as e:

        print()
        print("=" * 60)
        print("APTITUDE SUBMIT ALL ERROR")
        print("=" * 60)
        print(str(e))
        print("=" * 60)
        print()

        return jsonify({

            "success": False,

            "message": "Unable to submit aptitude test."

        }), 500

#aptitude result
@app.route("/aptitude-result")
def aptitude_result():

    if "user_id" not in session:
        return redirect(url_for("login"))

    result = session.get(
        "aptitude_result"
    )

    # -----------------------------------------------------
    # If there is no result
    # -----------------------------------------------------

    if not result:

        return redirect(
            url_for("aptitude")
        )

    return render_template(

        "aptitude_result.html",

        username=session.get(
            "username",
            "Candidate"
        ),

        score=result.get(
            "score",
            0
        ),

        total=result.get(
            "total",
            0
        ),

        attempted=result.get(
            "attempted",
            0
        ),

        correct=result.get(
            "correct",
            0
        ),

        incorrect=result.get(
            "incorrect",
            0
        ),

        skipped=result.get(
            "skipped",
            0
        ),

        results=result.get(
            "results",
            []
        )

    )
if __name__ == '__main__':
    app.run(debug=True)
