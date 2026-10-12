from datetime import datetime
import hashlib
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    raise ValueError("DATABASE_URL couldn't find! Please check the file .env")

def get_connection():
    return psycopg2.connect(DB_URL)
def hashpassword(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_tables():
    connection = get_connection()
    cursor = connection.cursor()
    create_logs = """
    CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    user_info TEXT,      
    action TEXT,        
    timestamp TEXT,      
    details TEXT           
    )
    """

    create_students = """
    CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL,
    studentnumber INTEGER UNIQUE,
    classname TEXT,
    password TEXT NOT NULL
    )
    """

    create_teachers = """
    CREATE TABLE IF NOT EXISTS teachers (
    id SERIAL PRIMARY KEY,
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL,
    branch TEXT NOT NULL,
    password TEXT NOT NULL
    )
    """

    create_grades = """
    CREATE TABLE IF NOT EXISTS grades (
    id SERIAL PRIMARY KEY,
    studentnumber INTEGER,
    lessonname TEXT,
    grade1 INTEGER,
    grade2 INTEGER,
    performance INTEGER,
    FOREIGN KEY (studentnumber) REFERENCES students (studentnumber)
    )
    """

    cursor.execute(create_logs)
    cursor.execute(create_students)
    cursor.execute(create_teachers)
    cursor.execute(create_grades)
    connection.commit()
    connection.close()


def addlog(userinfo, action, details):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO logs (user_info, action, timestamp, details)
            VALUES (%s, %s, %s, %s)
        """, (userinfo, action, now, details))

        connection.commit()

    finally:
        connection.close()



def generate_student_number():
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT MAX(studentnumber) FROM students")
        result = cursor.fetchone()[0]

        if result is None:
            return 1000
        else:
            return result + 1
    finally:
        connection.close()

def signupasstudent(firstname, lastname, studentnumber, classname, password):
   try:
    encryptedpassword = hashpassword(password)
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
            INSERT INTO students (firstname, lastname, studentnumber, classname, password)
            VALUES (%s, %s, %s, %s, %s)
        """, (firstname, lastname, studentnumber, classname, encryptedpassword))
    connection.commit()
   except psycopg2.IntegrityError:
       print("Student already exists")
   finally:
    connection.close()



def signupasteacher(firstname, lastname, branch, password):
   try:
    encryptedpassword = hashpassword(password)
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
            INSERT INTO teachers (firstname, lastname, branch, password)
            VALUES (%s, %s, %s, %s)
        """, (firstname, lastname, branch, encryptedpassword))
    connection.commit()
   except psycopg2.IntegrityError:
       print("teacher already exists")
   finally:
    connection.close()

def loginasteacher(firstname, lastname, branch, password):
   try:
       encryptedpassword = hashpassword(password)
       connection = get_connection()
       cursor = connection.cursor()
       cursor.execute("""SELECT * FROM teachers WHERE firstname = %s AND lastname = %s AND branch = %s AND password = %s""", (firstname, lastname, branch, encryptedpassword))

       result = cursor.fetchone()

       if result:
           addlog(f"Teacher {firstname} {lastname}", "Login Successfull", "Logged In")
           print("Login successful")
           return result
       else:
           addlog(f"Teacher {firstname} {lastname}", "Login Failed", "Wrong credentials")
           print("Login unsuccessful")
           return None
   finally:
    connection.close()


def loginasstudent(firstname, lastname, password):
    try:
        encryptedpassword = hashpassword(password)
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """SELECT * FROM students WHERE firstname = %s AND lastname = %s AND password = %s""",
            (firstname, lastname, encryptedpassword))

        result = cursor.fetchone()

        if result:
            print("Login successful")
            addlog(f"Student {firstname} {lastname}", "Login", "Successfully logged into the system")
            return result
        else:
            print("Login unsuccessful")
            addlog(f"Student {firstname} {lastname}", "Login Failed", "Wrong credentials")
            return None
    finally:
        connection.close()


#teacherpanel

def getstudentsbyclass(classname):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT firstname, lastname, studentnumber FROM students WHERE classname = %s", (classname,))
        students = cursor.fetchall()
        return students
    finally:
        connection.close()


def updategrade(studentnumber, lessonname, exam_type, new_score):
    if exam_type not in ["grade1", "grade2", "performance"]:
        return "Invalid exam type"

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM grades WHERE studentnumber = %s AND lessonname = %s", (studentnumber, lessonname))
        result = cursor.fetchone()

        if result:
            query = f"UPDATE grades SET {exam_type} = %s WHERE studentnumber = %s AND lessonname = %s"
            cursor.execute(query, (new_score, studentnumber, lessonname))
        else:
            grade1 = new_score if exam_type == "grade1" else 0
            grade2 = new_score if exam_type == "grade2" else 0
            performance = new_score if exam_type == "performance" else 0
            cursor.execute("""
                INSERT INTO grades (studentnumber, lessonname, grade1, grade2, performance)
                VALUES (%s, %s, %s, %s, %s)
            """, (studentnumber, lessonname, grade1, grade2, performance))

        connection.commit()
    finally:
        connection.close()
        addlog("Teacher", "Grade Update", f"Student {studentnumber} {exam_type} updated for {lessonname}")


def deletestudent(studentnumber):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM grades WHERE studentnumber = %s", (studentnumber,))
        cursor.execute("DELETE FROM students WHERE studentnumber = %s", (studentnumber,))
        connection.commit()
    finally:
        connection.close()
        addlog("Teacher", "Delete Student", f"Student {studentnumber} deleted")

def getstudentreports(studentnumber):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT lessonname, grade1, grade2, performance FROM grades WHERE studentnumber = %s", (studentnumber,))
        grades = cursor.fetchall()

        report = []
        for grade in grades:
            g1, g2, perf = grade[1], grade[2], grade[3]
            grades = [g for g in [g1, g2, perf] if g is not None]
            average = sum(grades) / len(grades) if grades else 0
            status = "Passed" if average >= 50 else "Failed"
            report.append({
                "Lesson:": grade[0],
                "Average:": round(average, 2),
                "Status:": status
            })
        return report
    finally:
        connection.close()

def addgrade(studentnumber, lessonname, grade1, grade2, performance):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO grades (studentnumber, lessonname, grade1, grade2, performance)
            VALUES (%s, %s, %s, %s, %s)
        """, (studentnumber, lessonname, grade1, grade2, performance))
        connection.commit()
    finally:
        connection.close()


#studentpanel


def getstudentprofile(studentnumber):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT firstname, lastname, classname FROM students WHERE studentnumber = %s", (studentnumber,))
        return cursor.fetchone()
    finally:
        connection.close()


def changepassword(studentnumber, oldpassword, newpassword):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT password FROM students WHERE studentnumber = %s", (studentnumber,))
        result = cursor.fetchone()
        if not result:
            print("Student not found")
            return False
        current_password = result[0]
        if current_password == hashpassword(oldpassword):
            newhashedpassword = hashpassword(newpassword)
            cursor.execute("UPDATE students SET password = %s WHERE studentnumber = %s", (newhashedpassword, studentnumber,))
            connection.commit()
            return True
        else:
            print("Old Password is incorrect")
            return False
    finally:
        connection.close()

def getclassmates(classname):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT firstname, lastname FROM students WHERE classname = %s ORDER BY firstname ASC", (classname,))
        return cursor.fetchall()
    finally:
        connection.close()

def getmygrades(studentnumber):
    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
                SELECT lessonname, grade1, grade2, performance 
                FROM grades 
                WHERE studentnumber = %s
            """, (studentnumber,))

        mygrades = cursor.fetchall()

        if not mygrades:
            return "No grades found yet"

        return mygrades
    finally:
        connection.close()