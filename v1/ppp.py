from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3 as sql
import os
from pickle import TRUE, FALSE
import random
import string

def get_random_string(length):
    global result_str
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))

get_random_string(8)

currentdirectory = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = result_str

def db_connect():
    global conn, cursor
    conn = sql.connect('database.db')
    cursor = conn.cursor()
    return conn, cursor

@app.route("/")
def home():
    if 'id' in session:
        return redirect("http://127.0.0.1:5000/home")
    return render_template("home.html")

@app.route("/account")
def account():
    return render_template("account.html")

@app.route("/booking")
def booking():
    return render_template("booking.html")

@app.route("/subject")
def subject():
    return render_template("subject.html")

#displaying the registration html
@app.route("/register")
def enter_details():
    return render_template("register.html")

#connecting to database and inputting new user.
@app.route("/register", methods =["POST"])
def add_user():
    db_connect()
    surname = request.form["surname"]
    first = request.form["first"]
    id = request.form["id"]
    pw = request.form["password"]
    if len(id) != 5:
        return render_template("register.html")
    else:
        conn.execute("INSERT INTO students (surname, first, id, password) VALUES (?, ?, ?, ?)",(surname, first, id, pw))
        conn.commit()
    return redirect("http://127.0.0.1:5000/home")

#displaying log in page
@app.route("/login")
def load():
    return render_template("login.html")

#taking inputted login information and checking it against the database
@app.route("/login", methods=["POST"])
def login():
    db_connect()
    error=""
    id=request.form["id"]
    pw=request.form["password"]
    if login_check(id, pw)==TRUE:
        session['id'] = id
        return redirect("http://127.0.0.1:5000/home")
    else:
        error="User does not exist"
        return render_template("login.html", error=error)
        
#function to check the login info
def login_check(id, pw):
    cursor.execute("SELECT * FROM students WHERE id LIKE ? and password LIKE ?", (id, pw))
    user=cursor.fetchall()
    if user:
        return TRUE
    else:
        return FALSE

@app.route("/home")
def welcome():
    return render_template("landing.html")

if __name__ == '__main__':    
    app.run(debug=True)

