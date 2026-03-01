from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"
ADMIN_PASSWORD = "Rahul@3123"


# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE)''')

    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    date TEXT,
                    status TEXT)''')

    conn.commit()
    conn.close()


def get_connection():
    return sqlite3.connect("attendance.db")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/")
        return "Wrong Password"
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")


# ---------------- HOME ----------------
@app.route("/")
def index():
    if not session.get("admin"):
        return redirect("/login")

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    students = c.fetchall()
    conn.close()
    return render_template("index.html", students=students)


# ---------------- ADD STUDENT ----------------
@app.route("/add", methods=["POST"])
def add_student():
    name = request.form["name"]
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO students (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()
    return redirect("/")


# ---------------- EDIT STUDENT ----------------
@app.route("/edit/<int:id>", methods=["POST"])
def edit_student(id):
    new_name = request.form["name"]
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE students SET name=? WHERE id=?", (new_name, id))
    conn.commit()
    conn.close()
    return redirect("/")


# ---------------- DELETE STUDENT ----------------
@app.route("/delete/<int:id>")
def delete_student(id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM students WHERE id=?", (id,))
    c.execute("DELETE FROM attendance WHERE student_id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")


# ---------------- MARK ATTENDANCE ----------------
@app.route("/mark/<int:student_id>/<status>")
def mark_attendance(student_id, status):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    c = conn.cursor()

    c.execute("DELETE FROM attendance WHERE student_id=? AND date=?", (student_id, today))
    c.execute("INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)",
              (student_id, today, status))

    conn.commit()
    conn.close()
    return redirect("/")


# ---------------- STUDENT DETAIL ----------------
@app.route("/student/<int:id>")
def student_detail(id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT name FROM students WHERE id=?", (id,))
    name = c.fetchone()[0]

    c.execute("SELECT date, status FROM attendance WHERE student_id=?", (id,))
    records = c.fetchall()

    total = len(records)
    present = len([r for r in records if r[1] == "present"])
    percentage = round((present / total) * 100, 2) if total > 0 else 0

    conn.close()
    return render_template("student_detail.html",
                           name=name,
                           records=records,
                           percentage=percentage)


# ---------------- MONTHLY REPORT ----------------
@app.route("/report")
def report():
    month = datetime.now().strftime("%Y-%m")
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT students.name, COUNT(attendance.id)
        FROM students
        LEFT JOIN attendance
        ON students.id = attendance.student_id
        AND attendance.status='present'
        AND attendance.date LIKE ?
        GROUP BY students.name
    """, (month + "%",))

    data = c.fetchall()
    conn.close()
    return render_template("report.html", data=data, month=month)


# ---------------- PDF REPORT ----------------
@app.route("/report/pdf")
def pdf_report():
    month = datetime.now().strftime("%Y-%m")
    file_name = f"monthly_report_{month}.pdf"

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT students.name, COUNT(attendance.id)
        FROM students
        LEFT JOIN attendance
        ON students.id = attendance.student_id
        AND attendance.status='present'
        AND attendance.date LIKE ?
        GROUP BY students.name
    """, (month + "%",))
    data = c.fetchall()
    conn.close()

    doc = SimpleDocTemplate(file_name)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"Monthly Attendance Report ({month})", styles['Heading1']))
    elements.append(Spacer(1, 0.3 * inch))

    table_data = [["Student Name", "Days Present"]]
    for row in data:
        table_data.append([row[0], str(row[1])])

    table = Table(table_data)
    table.setStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])

    elements.append(table)
    doc.build(elements)

    return send_file(file_name, as_attachment=True)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)