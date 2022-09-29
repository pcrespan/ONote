import psycopg2
from datetime import datetime

from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

# Configuring Flask
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Connection with database
def connection():
    conn = psycopg2.connect(
        host = 'localhost',
        database = 'onote',
        user = 'postgres',
        password = 'onote'
    )
    return conn

# Close connection with database
def close_con(connection, cursor):
    cursor.close()
    connection.close()


def conCommit(connection, cursor):
    connection.commit()
    cursor.close()
    connection.close()


# Checks if user is logged in
def require_login(f):
    @wraps(f)
    def logged(*args, **kwargs):
        if session.get("user_id"):
            return f(*args, **kwargs)
        return redirect("/login")
    return logged


@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        con = connection()
        cursor = con.cursor()

        username = request.form.get("username")
        password = request.form.get("password")
        confirmPass = request.form.get("confirmPass")
        
        cursor.execute("SELECT * FROM users WHERE username = %s;", (username, ))
        user_exists = cursor.fetchall()
        error = 'Username already in use'
        if user_exists or password != confirmPass:
            close_con(con, cursor)
            return render_template("register.html", error = error)
        else:
            hashPassword = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s);", (username, hashPassword))
            conCommit(con, cursor)
            return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        # Check if username and password match database
        con = connection()
        cursor = con.cursor()

        username = request.form.get("username")
        password = request.form.get("password")

        if username and password:
            pass
        else:
            redirect("/login")

        cursor.execute("SELECT * FROM users WHERE username = %s;", (username, ))
        user_data = cursor.fetchall()
        if user_data and check_password_hash(user_data[0][2], password):
            session["user_id"] = user_data[0][0]
            session["username"] = user_data[0][1]
            close_con(con, cursor)
            return redirect("/")
        else:
            error = 'Wrong username or password'
            close_con(con, cursor)
            return render_template("login.html", error = error)
    else:
        return render_template("login.html")


@app.route("/logout")
@require_login
def logout():
    session.clear()
    return redirect("/login")


@app.route("/")
@require_login
def index():
    con = connection()
    cursor = con.cursor()

    cursor.execute("SELECT noteid, title, text, TO_CHAR(date, 'MM/DD/YYYY'), TO_CHAR(hour, 'HH:MM') FROM notes WHERE uid = %s ORDER BY date;", (session["user_id"], ))
    user_notes = cursor.fetchall()
    close_con(con, cursor)
    return render_template("index.html", user_notes = user_notes)


@app.route("/add", methods = ["GET", "POST"])
@require_login
def add():

    title = request.form.get("title")
    text = request.form.get("text")
    today = datetime.now()
    date = today.date()
    hour = today.time()

    if request.method == "POST":
        if title and text:
            pass
        else:
            error = 'Fill every field before adding a note'
            return render_template("add.html", error = error)
        
        con = connection()
        cursor = con.cursor()

        cursor.execute("INSERT INTO notes (uid, title, text, date, hour) VALUES (%s, %s, %s, %s, %s);", (session["user_id"], title, text, date, hour))
        conCommit(con, cursor)
        return redirect("/")
    else:
        return render_template("add.html")


@app.route("/delete", methods=["POST"])
@require_login
def delete():
    if request.method == "POST":
        note_id = request.form.get("note_id")

        con = connection()
        cursor = con.cursor()

        cursor.execute("DELETE FROM notes WHERE noteid = %s", (note_id))
        close_con(con, cursor)
        # Might be cool to add a warning that the note was successfully deleted
        return redirect("/")
    else:
        return redirect("/")