from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

attendance_bp = Blueprint("attendance", __name__, template_folder="../templates")

# Helper function to get DB connection
def get_db_connection():
    conn = sqlite3.connect("attendance.db")
    conn.row_factory = sqlite3.Row  # Isse hum data ko dictionary format mein access kar sakte hain
    return conn

@attendance_bp.route("/mark", methods=["GET", "POST"])
def mark_attendance():
    # 1. Security Check: Agar user login nahi hai toh login page pe bhejo
    if not session.get("user"):
        flash("Please login first!", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        student_id = request.form.get("student_id")
        status = request.form.get("status")
        marked_by = session.get("user")
        today = datetime.now().strftime("%Y-%m-%d")

        # 2. Validation
        if not student_id or not status:
            flash("All fields are required!", "warning")
            return redirect(url_for("attendance.mark_attendance"))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 3. Duplicate Check: Aaj ki attendance pehle se toh nahi lagi?
            # Agar lagi hai toh update karein, nahi toh insert karein.
            cursor.execute('''
                INSERT INTO attendance (student_id, date, status, marked_by)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(student_id, date) DO UPDATE SET status=excluded.status
            ''', (student_id, today, status, marked_by))

            conn.commit()
            conn.close()
            
            flash(f"Attendance marked successfully for Student ID {student_id}!", "success")
            
        except Exception as e:
            flash(f"Database Error: {str(e)}", "danger")
            return redirect(url_for("attendance.mark_attendance"))

        return redirect(url_for("attendance.mark_attendance"))

    # GET request: Students ki list fetch karna taaki dropdown mein dikha saken
    students = []
    try:
        conn = get_db_connection()
        students = conn.execute('SELECT * FROM students').fetchall()
        conn.close()
    except Exception as e:
        flash("Could not fetch students list.", "danger")

    return render_template("mark_attendance.html", students=students)