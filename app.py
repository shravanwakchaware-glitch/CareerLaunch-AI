from flask import Flask,render_template,request,redirect,url_for,session
import sqlite3
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
@app.route('/dashboard')
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        username=session["username"]
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

@app.route("/interview_setup", methods=["POST"])
def interview_setup():

    if "user_id" not in session:
        return redirect(url_for("login"))

    job_role = request.form.get("job_role")
    skills = request.form.getlist("skills")
    other_skills = request.form.get("other_skills")
    difficulty = request.form.get("difficulty", "Intermediate")

    # Save everything in session
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

    return render_template(
        "interview.html",

        username=session["username"],

        job_role=session.get("job_role"),

        skills=session.get("skills", []),

        other_skills=session.get("other_skills", ""),

        difficulty=session.get("difficulty"),

        question="Tell me about yourself.",

        current_question=1,

        total_questions=10,

        timer="15:00"
    )
@app.route("/ats")
def ats():

    if "user_id" not in session:
        return redirect(url_for("login"))

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
