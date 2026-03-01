from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3

students_bp = Blueprint("students", __name__, template_folder="../templates")

# --- Database Connection Helper ---
def get_db_connection():
    # Note: Ensure name is 'attendance.db' as used in your main file
    conn = sqlite3.connect('attendance.db') 
    conn.row_factory = sqlite3.Row
    return conn

# --- Route: List All Students ---
@students_bp.route("/list")
def list_students():
    if not session.get("user"):
        return redirect(url_for("login"))

    try:
        conn = get_db_connection()
        # Alphabetical order mein list dikhana professional hota hai
        students = conn.execute("SELECT * FROM students ORDER BY name ASC").fetchall()
        conn.close()
        return render_template("index.html", students=students)
    except Exception as e:
        flash(f"Data load nahi ho saka: {str(e)}", "danger")
        return render_template("index.html", students=[])

# --- Route: Add New Student ---
@students_bp.route("/add", methods=["GET", "POST"])
def add_student():
    if not session.get("user"):
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name").strip() # strip() space saaf karne ke liye
        
        if not name:
            flash("Kripya student ka naam bharein!", "warning")
            return redirect(url_for("students.add_student"))

        try:
            conn = get_db_connection()
            conn.execute("INSERT INTO students (name) VALUES (?)", (name,))
            conn.commit()
            conn.close()
            flash(f"Student '{name}' ko Balaji Krishna Coaching mein add kar diya gaya hai!", "success")
            return redirect(url_for("students.list_students"))
        except sqlite3.IntegrityError:
            flash("Ye student name pehle se hi exist karta hai!", "danger")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
            
    return render_template("add_student.html")

# --- Route: Delete Student (Additional Professional Feature) ---
@students_bp.route("/delete/<int:id>", methods=["POST"])
def delete_student(id):
    if session.get("role") != "admin":
        flash("Sirf Admin hi student delete kar sakta hai!", "danger")
        return redirect(url_for("students.list_students"))

    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM students WHERE id = ?", (id,))
        # Saath hi uski attendance bhi delete kar deni chahiye (Cleanup)
        conn.execute("DELETE FROM attendance WHERE student_id = ?", (id,))
        conn.commit()
        conn.close()
        flash("Student record aur attendance delete kar di gayi.", "info")
    except Exception as e:
        flash(f"Deletion error: {str(e)}", "danger")
        
    return redirect(url_for("students.list_students"))