import sqlite3

conn = sqlite3.connect('study_centre.db')
print ("Opened database successfully");

conn.execute('CREATE TABLE students (first TEXT, last TEXT, email TEXT, username TEXT, password TEXT)')
print ("Table created successfully");
conn.close()