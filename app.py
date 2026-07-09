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
if __name__ == '__main__':
    app.run(debug=True)
