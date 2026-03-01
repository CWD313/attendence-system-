from flask import Blueprint, render_template, session, redirect, url_for, flash
import sqlite3

reports_bp = Blueprint("reports", __name__, template_folder="../templates")

# Helper function for DB connection
def get_db_connection():
    conn = sqlite3.connect("attendance.db")
    conn.row_factory = sqlite3.Row
    return conn

@reports_bp.route("/")
def report():
    # 1. Security Check: Sirf logged-in users hi report dekh sakein
    if not session.get("user"):
        flash("Please login to view reports.", "warning")
        return redirect(url_for("login"))

    report_data = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 2. Professional SQL Query: 
        # Hum 'attendance' aur 'students' table ko join kar rahe hain 
        # taaki student_id ki jagah uska real name dikhe.
        query = '''
            SELECT 
                attendance.date, 
                students.name AS student_name, 
                attendance.status, 
                attendance.marked_by
            FROM attendance
            JOIN students ON attendance.student_id = students.id
            ORDER BY attendance.date DESC, students.name ASC
        '''
        
        cursor.execute(query)
        report_data = cursor.fetchall()
        conn.close()

    except Exception as e:
        flash(f"Error generating report: {str(e)}", "danger")

    # 3. Data ko template mein pass karna
    return render_template("report.html", report=report_data)