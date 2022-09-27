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
        database = 'ONote',
        user = 'ONote',
        password = 'onote'
    )
    return conn


# Checks if user is logged in
def require_login(f):
    @wraps
    def logged(*args, **kwargs):
        if session["user_id"]:
            return f(*args, **kwargs)
        else:
            return redirect("/login")
    return logged