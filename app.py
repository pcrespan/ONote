import psycopg2

from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

# Configuring Flask
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Connection with database
def connection():
    conn = psycopg2.connect(
        host = 'localhost',
        database = 'onote',
        user = 'postgres',
        password = 'postgres'
    )
    return conn

def closeCon(connection, cursor):
    connection.close()
    cursor.close()


# Checks if user is logged in
def require_login(f):
    @wraps
    def logged(*args, **kwargs):
        if session["user_id"]:
            return f(*args, **kwargs)
        else:
            return redirect("/login")
    return logged


@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        con = connection()
        cursor = con.cursor()

        username = request.form.get("username")
        password = request.form.get("password")
        
        user_exists = cursor.execute("SELECT id FROM users WHERE username = %s", (username, )).fetchall()
        error = 'Username already in use'
        if user_exists:
            closeCon(con, cursor)
            return render_template("/register", error = error)
        else:
            hashPassword = generate_password_hash(password, "sha256")
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashPassword))
            closeCon(con, cursor)
    else:
        return render_template("/register")


@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        # Check if username and password match database
        con = connection()
        cursor = con.cursor()

        username = request.form.get("username")
        password = request.form.get("password")

        user_data = cursor.execute("SELECT * FROM users WHERE username = %s", (username, ))

        if user_data and check_password_hash(user_data[0][2], password):
            session["user_id"] = user_data[0][0]
            return render_template("/index")
        else:
            error = 'Wrong username or password'
            return render_template("/login", error = error)
    else:
        return render_template("/login")
