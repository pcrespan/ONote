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


class Connection:

    # Creates an instance of Connection class
    @staticmethod
    def get_con():
        conn = psycopg2.connect(
        host = 'localhost',
        database = 'onote',
        user = 'postgres',
        password = 'onote'
        )

        cursor = conn.cursor()
        return conn, cursor
    
    # Close connection
    @staticmethod
    def close_all(cursor, conn):
        cursor.close()
        conn.close()

    # Commiting changes and closing connection
    @staticmethod
    def commit_all(cursor, conn):
        conn.commit()
        Connection.close_all(cursor, conn)


# Checks if user is logged in
def require_login(f):
    @wraps(f)
    def logged(*args, **kwargs):
        if session.get("user_id"):
            return f(*args, **kwargs)
        return redirect("/login")
    return logged

# Register function
@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        con,cursor = Connection.get_con()

        username = request.form.get("username")
        password = request.form.get("password")
        confirmPass = request.form.get("confirmPass")

        # Checks if input fields are not empty
        if username and password and confirmPass:
            pass
        else:
            Connection.close_all(cursor, con)
            return render_template("register.html");

        # Checking if username already exists
        cursor.execute("SELECT * FROM users WHERE username = %s;", (username, ))
        user_exists = cursor.fetchall()
        error = 'Username already in use or passwords do not match'

        if user_exists or password != confirmPass:
            Connection.close_all(cursor, con)
            return render_template("register.html", error = error)
        else:
            # Hashing password and inserting on database
            hashPassword = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s);", (username, hashPassword))
            Connection.commit_all(cursor, con)
            return redirect("/login")
    else:
        return render_template("register.html")

# Login function
@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        con,cursor = Connection.get_con()

        username = request.form.get("username")
        password = request.form.get("password")

        # Checks if input fields are not empty
        if username and password:
            pass
        else:
            redirect("/login")

        # Check if username and password match database
        cursor.execute("SELECT * FROM users WHERE username = %s;", (username, ))
        user_data = cursor.fetchall()
        if user_data and check_password_hash(user_data[0][2], password):
            session["user_id"] = user_data[0][0]
            session["username"] = user_data[0][1]
            Connection.close_all(cursor, con)
            return redirect("/")
        else:
            error = 'Wrong username or password'
            Connection.close_all(cursor, con)
            return render_template("login.html", error = error)
    else:
        return render_template("login.html")


# Logout function, clears session
@app.route("/logout")
@require_login
def logout():
    session.clear()
    return redirect("/login")


# Index page
@app.route("/")
@require_login
def index():
    con,cursor = Connection.get_con()

    # Gathering information from database
    cursor.execute("SELECT noteid, title, text FROM notes WHERE uid = %s ORDER BY date;", (session["user_id"], ))
    user_notes = cursor.fetchall()
    Connection.close_all(cursor, con)
    # Rendering template with all information
    return render_template("index.html", user_notes = user_notes)


# Add notes function
@app.route("/add", methods = ["POST"])
@require_login
def add():

    title = request.form.get("title")
    text = request.form.get("text")
    today = datetime.now()
    date = today.date()
    hour = today.time()

    if request.method == "POST":
        # Checking if input fields are not empty
        if title and text:
            pass
        else:
            return redirect("/")
        
        con,cursor = Connection.get_con()

        # Inserting note on database
        cursor.execute("INSERT INTO notes (uid, title, text, date, hour) VALUES (%s, %s, %s, %s, %s);", (session["user_id"], title, text, date, hour))
        Connection.commit_all(cursor, con)
        return redirect("/")
    else:
        pass


# Delete function
@app.route("/delete", methods=["POST"])
@require_login
def delete():
    if request.method == "POST":
        note_id = request.form.get("note_id")

        con,cursor = Connection.get_con()

        # Deleting row containing note from database
        cursor.execute("DELETE FROM notes WHERE noteid = %s", (note_id, ))
        Connection.commit_all(cursor, con)
        
        return redirect("/")
    else:
        return redirect("/")