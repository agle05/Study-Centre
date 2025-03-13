from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3 as sql
import hashlib
from flask_session import Session

app = Flask(__name__)
app.secret_key = 'wggygPENIS'  # Replace this with a secure key in production
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
app = Flask(__name__, static_url_path='/static') #connection to styling folder

# Create a dictionary of users with their usernames and hashed passwords
def db_connect():
    global conn, cursor
    conn = sql.connect('database.db')
    cursor = conn.cursor()
    return conn, cursor

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        db_connect()
        username = request.form['id']
        password = request.form['password']
        cursor.execute("SELECT * FROM students")
        user_list = cursor.fetchall()
        print(user_list)
        if username in user_list:
            error = 'Username already taken. Please choose a different username.'
        else:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            conn.execute("INSERT INTO students (surname, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            session['username'] = username
            return redirect(url_for('dashboard'))
    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        db_connect()
        username = request.form['id']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("SELECT * FROM students")
        user_list = cursor.fetchall()
        print(user_list)
        if username in user_list and user_list[username] == hashed_password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid username or password. Please try again.'
    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        username = session['username']
        return render_template('dashboard.html', username=username)
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)