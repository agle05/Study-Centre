from flask import Flask, render_template, request, redirect, session, make_response
import sqlite3
import calendar
from datetime import datetime, timedelta
import re
import bcrypt
from passlib.hash import sha256_crypt

app = Flask(__name__, static_url_path='/static')
app.secret_key = "qwerty"

#Establish database connection
def db_connect():
    global conn, cursor
    conn = sqlite3.connect('study_centre.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS students (first TEXT, last TEXT, email TEXT, username TEXT, password TEXT)')
    conn.commit()
    return conn, cursor

#First page that you land on
@app.route('/')
def index():
    session.pop('username', None)
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template("login.html")

#login post method
@app.route('/login', methods=['POST'])
def login_post():
    if request.method == 'POST':
        global username
        db_connect()

        #get login information from form
        username = request.form['username']
        password = request.form['password']
        
        cursor.execute('SELECT password FROM students WHERE username = ?', (username,))
        row = cursor.fetchone()

        if row:
            hashed_passw = row[0]
            password = password.encode('utf-8')
            if bcrypt.checkpw(password, hashed_passw):
                session['username'] = username
                return redirect('/book')
            else:
                return render_template("login.html", error1 = "Incorrect Password")
        else:
            return render_template("login.html", error2 = "No user found")

    else:
        return render_template("login.html")
            

@app.route('/register')
def register():
    return render_template('register.html')

#register post method
@app.route("/register", methods=['POST'])
def register_post():
    if request.method == 'POST':
        global username
        db_connect()

        #fetch form information
        first = request.form['first']
        last = request.form['last']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        password_confirm = request.form['password-confirm']

        cursor.execute('SELECT * FROM students WHERE username = ?', (username,))
        user = cursor.fetchone()

        #checks if user exists already
        if user:
            return render_template('register.html', user_exists='Username already exists.')
        else:

            #checks if password matches the confirm password entrance
            if password != password_confirm:
                return render_template('register.html', password_match='Passwords do not match.')
            else:
                #checks that the student id is in the form ab12345
                pattern = r'^[a-zA-Z]{2}\d{5}$'
                match = re.match(pattern, username)
                if match:
                    password = password.encode('utf-8')
                    hash_passw = bcrypt.hashpw(password, bcrypt.gensalt())
                    cursor.execute('INSERT INTO students (first, last, email, username, password) VALUES (?, ?, ?, ?, ?)', (first, last, email, username, hash_passw))
                    conn.commit()
                    session['username'] = username
                    return redirect('/book')
                else:
                    return render_template('register.html', invalid_username='Invalid username (e.g. ab12345)')
    
    return render_template('register.html')

#to be made <-- future update -->
@app.route('/about')
def about():
    return render_template('about.html')

#to be made <-- future update -->
@app.route('/tutors')
def tutors():
    return render_template('tutors.html')

#page that users can only reach when logged in, home page for users <-- major update to come -->
@app.route('/home')
def home():
    if 'username' in session:
        db_connect()
        cursor.execute('SELECT first FROM students WHERE username=?', (username,))
        result = cursor.fetchone()
        first = str(result).strip("()'',")
        return render_template('home.html', first=first)
    else:
        return redirect('/')   

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

#the bookings page
@app.route('/book')
def book():
    if 'username' in session:
        global schedule
        schedule = 0
        db_connect()

        #this is to give the users a way to select tutor in the drop down menu
        options = ['']
        cursor.execute('SELECT tutor FROM tutorList WHERE status = 1')
        results = cursor.fetchall()
        for tutor in results:
            for name in tutor:
                options.append(name)

        #get tutor name for schedule
        cursor.execute('SELECT tutor FROM tutorList ')
        name = cursor.fetchall()
        name1 = name[0][0]
        tutor_name = str(name1).strip("()'',")

        #form schedule together, get tutor availability
        getWeek = f'''SELECT monday, tuesday, wednesday, thursday, friday FROM [{tutor_name}]'''
        cursor.execute(getWeek)
        rows = cursor.fetchall()
        tutor_name = tutor_name.capitalize()

        return render_template('book.html', rows=rows, options=options, tutor_name=tutor_name)

    else:
        return redirect('/login')

#POST method for the booking system
@app.route('/book', methods=['POST'])
def getInfo():
    #if the post request comes from the booknig form
    if request.method == 'POST' and request.form.get('action') == 'Query Booking':
        db_connect()

        #getting the information from the forms
        tutorName = request.form['tutor']
        day = request.form['day']
        time = request.form['time']
        startTime = request.form['startTime']

        #converting the start time into an integer to use in equations
        startTime = int(startTime.strip())

        #checking if the slot requested is available 
        avb = f'''SELECT [{day}] FROM [{tutorName}] WHERE slot = ?'''
        cursor.execute(avb, (str(startTime)))
        result = cursor.fetchone()
        slot = str(result).strip("()'',")

        #creating a list of tutors enrolled for the drop down menu
        options = ['']
        cursor.execute('SELECT tutor FROM tutorList WHERE status = 1')
        results = cursor.fetchall()
        for tutor in results:
            for name in tutor:
                options.append(name)

        #to have the drop down menu on the form of all the tutor names
        cursor.execute('SELECT tutor FROM tutorList ')
        name = cursor.fetchall()
        name1 = name[0][0]
        tutor_name = str(name1).strip("()'',")

        #to form the schedule, get tutor availability
        getWeek = f'''SELECT monday, tuesday, wednesday, thursday, friday FROM [{tutor_name}]'''
        cursor.execute(getWeek)
        rows = cursor.fetchall()
        tutor_name = tutor_name.capitalize()

        #to tell the user that slot is not available
        if slot == '1':
            return render_template('book.html', unavailable = "Tutor is not available for this slot", options = options, tutor_name = tutor_name, rows=rows)

        #covering the possible scenarios for when slot = 0
        elif slot == '0':

            #when time 15 and slot 0  booking will always be made
            if time == '15':
                booked = f'''UPDATE [{tutorName}] SET [{day}] = ? WHERE slot = ?'''
                cursor.execute(booked, (1, str(startTime),))
                conn.commit()

            #when time 30 and slot 0 there are three scenarios. The tutoring time may be invalid (goes overtime), the second 15 minute may be booked, or the 30 mins is available
            elif time == '30':
                if (startTime + 1) == 6:
                    return render_template('book.html', invalid = "Can't book the 30 minute slot. Try 15 minutes", options = options, tutor_name = tutor_name, rows=rows)
                else:
                    avb = f'''SELECT [{day}] FROM [{tutorName}] WHERE slot = ?'''
                    cursor.execute(avb, (str(startTime + 1)))
                    result = cursor.fetchone()
                    slot = str(result).strip("()'',")
                    if slot == '1':
                        return render_template('book.html', double = "Can't book the 30 minute slot. Try 15 minutes", options = options, tutor_name = tutor_name, rows=rows)
                    elif slot == '0':

                        #entering the booking into the system
                        booked = f'''UPDATE [{tutorName}] SET [{day}] = ? WHERE slot = ?'''
                        cursor.execute(booked, (1, str(startTime),))
                        cursor.execute(booked, (1, str(startTime + 1)))
                        conn.commit()

            #when time 45 and slot 0 there are 5 possible scenarios. Session goes two blocks overtime, session goes one block overtime, third session is booked, second session is booked, all three are available
            elif time == '45':

                #using equations to check if the triple 15 min session goes overtime
                if (startTime + 2) == 6:
                    return render_template('book.html', invalid1 = "Can't book the 45 minute slot. Try 30 minutes", options = options, tutor_name = tutor_name, rows=rows)
                elif (startTime + 2) == 7:
                    return render_template('book.html', invalid2 = "Can't book the 45 minute slot. Try 15 minutes", options = options, tutor_name = tutor_name, rows=rows)
                else:
                    avb = f'''SELECT [{day}] FROM [{tutorName}] WHERE slot = ?'''
                    cursor.execute(avb, (str(startTime + 1)))
                    result = cursor.fetchone()

                    #this is to check the slot one after the start time
                    slot1 = str(result).strip("()'',")
                    avb = f'''SELECT [{day}] FROM [{tutorName}] WHERE slot = ?'''
                    cursor.execute(avb, (str(startTime + 2)))
                    result = cursor.fetchone()

                    #this is to check the slot two after the start time
                    slot2 = str(result).strip("()'',")

                    #to cover scenario four
                    if slot1 == '1':
                        return render_template('book.html', triple = "Can't book the 45 minute slot. Try 15 minute slot", options= options, tutor_name = tutor_name, rows=rows)

                    #to cover scenario three
                    elif slot1 == '0' and slot2 == '1':
                        return render_template('book.html', triple1 = "Can't book the 45 minute slot. Try the 30 minute slot", options=options, tutor_name = tutor_name, rows=rows)

                    #if all three slots are available the booking is created
                    elif slot1 =='0' and slot2 == '0':
                        booked = f'''UPDATE [{tutorName}] SET [{day}] = ? WHERE slot = ?'''
                        cursor.execute(booked, (1, str(startTime),))
                        cursor.execute(booked, (1, str(startTime + 1)))
                        cursor.execute(booked, (1, str(startTime + 2)))
                        conn.commit()
            else:

                #if no time is selected from the form
                return render_template('book.html', message = "Please select how long you'd like.", options = options, tutor_name = tutor_name, rows=rows)

            return render_template('book.html')

        return render_template('book.html', options = options, tutor_name = tutor_name, rows=rows)

    if request.method == 'POST' and request.form.get('left') == 'left':
        global schedule

        db_connect()

        #creating a list of tutors to display for the tutor selection in the form
        options = ['']
        cursor.execute('SELECT tutor FROM tutorList WHERE status = 1')
        results = cursor.fetchall()
        for tutor in results:
            for name in tutor:
                options.append(name)

        schedule -= 1

        #if schedule is below 0 no tutor will be fetched, will reset "schedule" to the max number
        if schedule < 1:
            cursor.execute("SELECT id FROM tutorList ORDER BY id DESC LIMIT 1")
            schedule = cursor.fetchone()
            schedule = str(schedule).strip("()'',")
            schedule = int(schedule)
        else:

            #if the "schedule" variable is above 0
            print("safe")

        #to get the next schedule
        cursor.execute("SELECT tutor FROM tutorList WHERE id = ?", (schedule,))
        tutor = cursor.fetchone()
        tutor = str(tutor).strip("()'',")
        getWeek = f'''SELECT monday, tuesday, wednesday, thursday, friday FROM [{tutor}]'''
        cursor.execute(getWeek)
        rows = cursor.fetchall()
        cursor.close()
        tutor = tutor.capitalize()
        schedule = str(schedule).strip("()'',")
        schedule = int(schedule)


        return render_template('book.html', rows=rows, tutor_name=tutor, options=options)

    if request.method == 'POST' and request.form.get('right') == 'right':
        
        db_connect()

        #creating a list of tutors to display for the tutor selection in the form
        options = ['']
        cursor.execute('SELECT tutor FROM tutorList WHERE status = 1')
        results = cursor.fetchall()
        for tutor in results:
            for name in tutor:
                options.append(name)

        #creating a list of tutors' names  for the buttons to select which schedule to view
        tutors = []
        cursor.execute('SELECT tutor FROM tutorList WHERE status = 1')
        results = cursor.fetchall()
        for tutor in results:
            for name in tutor:
                tutors.append(name)

        schedule += 1

        cursor.execute("SELECT id FROM tutorList ORDER BY id DESC LIMIT 1")
        tutor_amount = cursor.fetchone()
        tutor_amount = str(tutor_amount).strip("()'',")
        tutor_amount = int(tutor_amount)

        #if "schedule" is larger than the max amount, no schedule will be fetched, so must reset to 1
        if schedule > int(tutor_amount):
            schedule = 1
        else:
            pass
        
        #fetch the new schedule
        cursor.execute("SELECT tutor FROM tutorList WHERE id = ?", (schedule,))
        tutor = cursor.fetchone()
        tutor = str(tutor).strip("()'',")
        getWeek = f'''SELECT monday, tuesday, wednesday, thursday, friday FROM [{tutor}]'''
        cursor.execute(getWeek)
        rows = cursor.fetchall()
        cursor.close()
        tutor = tutor.capitalize()

        return render_template('book.html', rows=rows, tutor_name=tutor, options=options)

@app.route('/admin')
def viewAdmin():
    return render_template('admin.html')

@app.route('/admin', methods=['POST'])
def listImport():
    #to clear current student tutor list
    clearTable()

    #to form the list of new imputted tutors
    student_names = []
    for key, value in request.form.items():
        if key.startswith('student'):
            student_names.append(value)

    db_connect()

    id = 1

    #inserting the tutors names into the tutor list for the week
    for name in student_names:
        input = f'''INSERT INTO tutorList (tutor, status, id) VALUES (?, ?, ?)'''
        cursor.execute(input, (str(name).strip(),1,id))
        conn.commit()
        id+=1
    conn.commit()
    conn.close()
    db_connect()

    #creating tables for tutors and setting all the values to the basic set
    for tutor in student_names:
        table = f'''CREATE TABLE IF NOT EXISTS [{tutor.strip()}] (monday INTEGER NOT NULL, tuesday INTEGER NOT NULL, wednesday INTEGER NOT NULL, thursday INTEGER NOT NULL, friday INTEGER NOT NULL, slot INTEGER NOT NULL)'''
        cursor.execute(table)
        clear = f'''DELETE FROM [{tutor.strip()}]'''
        cursor.execute(clear)
        conn.commit()
        for i in range(5):
            set = f'''INSERT INTO [{tutor.strip()}] (monday, tuesday, wednesday, thursday, friday, slot) VALUES (?, ?, ?, ?, ?, ?)'''
            cursor.execute(set, (0, 0, 0, 0, 0, (i+1)))
            conn.commit()
    
    # Redirect or render a response
    return redirect('/book')

#function to clear the tutor list from te database
def clearTable():
    db_connect()
    cursor.execute('DELETE FROM tutorList')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    app.run(debug=True)