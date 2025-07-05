from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3
import os
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

DB_NAME = "feedback.db"

# Admin credentials (in a real app, use hashed passwords and store in database)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def init_db():
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Create teachers table
        c.execute('''CREATE TABLE teachers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    department TEXT NOT NULL,
                    joining_date DATE NOT NULL
                )''')
        
        # Create students table
        c.execute('''CREATE TABLE students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    department TEXT NOT NULL,
                    enrollment_date DATE NOT NULL
                )''')
        
        # Create semesters table
        c.execute('''CREATE TABLE semesters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL
                )''')
        
        # Create feedback table with foreign keys to teachers, students, and semesters
        c.execute('''CREATE TABLE feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER NOT NULL,
                    student_id INTEGER NOT NULL,
                    semester_id INTEGER NOT NULL,
                    rating INTEGER,
                    comments TEXT,
                    submission_date DATE DEFAULT CURRENT_DATE,
                    FOREIGN KEY (teacher_id) REFERENCES teachers(id),
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    FOREIGN KEY (semester_id) REFERENCES semesters(id)
                )''')
        
        conn.commit()
        conn.close()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Welcome, Admin!', 'success')
            return redirect(url_for('view_feedback'))
        else:
            flash('Invalid credentials', 'error')
            
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/admin/lecturers', methods=['GET', 'POST'])
@login_required
def manage_lecturers():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        department = request.form['department']
        joining_date = request.form['joining_date']
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO teachers (name, email, department, joining_date) VALUES (?, ?, ?, ?)",
                     (name, email, department, joining_date))
            conn.commit()
            flash('Teacher added successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Email already exists!', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('manage_lecturers'))
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM teachers ORDER BY name")
    teachers = c.fetchall()
    conn.close()
    
    return render_template('manage_lecturers.html', teachers=teachers)

@app.route('/admin/lecturers/delete/<int:id>')
@login_required
def delete_lecturer(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM teachers WHERE id = ?", (id,))
        conn.commit()
        flash('Teacher deleted successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Cannot delete teacher with existing feedback!', 'error')
    finally:
        conn.close()
    return redirect(url_for('manage_lecturers'))

@app.route('/admin/students', methods=['GET', 'POST'])
@login_required
def manage_students():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        department = request.form['department']
        enrollment_date = request.form['enrollment_date']
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO students (name, email, department, enrollment_date) VALUES (?, ?, ?, ?)",
                     (name, email, department, enrollment_date))
            conn.commit()
            flash('Student added successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Email already exists!', 'error')
        finally:
            conn.close()
        return redirect(url_for('manage_students'))
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY name")
    students = c.fetchall()
    conn.close()
    return render_template('manage_students.html', students=students)

@app.route('/admin/students/delete/<int:id>')
@login_required
def delete_student(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM students WHERE id = ?", (id,))
        conn.commit()
        flash('Student deleted successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Cannot delete student with existing feedback!', 'error')
    finally:
        conn.close()
    return redirect(url_for('manage_students'))

@app.route('/admin/semesters', methods=['GET', 'POST'])
@login_required
def manage_semesters():
    if request.method == 'POST':
        name = request.form['name']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO semesters (name, start_date, end_date) VALUES (?, ?, ?)",
                     (name, start_date, end_date))
            conn.commit()
            flash('Semester added successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Semester already exists!', 'error')
        finally:
            conn.close()
        return redirect(url_for('manage_semesters'))
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM semesters ORDER BY start_date DESC")
    semesters = c.fetchall()
    conn.close()
    return render_template('manage_semesters.html', semesters=semesters)

@app.route('/admin/semesters/delete/<int:id>')
@login_required
def delete_semester(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM semesters WHERE id = ?", (id,))
        conn.commit()
        flash('Semester deleted successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Cannot delete semester with existing feedback!', 'error')
    finally:
        conn.close()
    return redirect(url_for('manage_semesters'))

@app.route('/submit_feedback', methods=['GET', 'POST'])
def submit_feedback():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name, department FROM teachers ORDER BY name")
    teachers = c.fetchall()
    c.execute("SELECT id, name, department FROM students ORDER BY name")
    students = c.fetchall()
    c.execute("SELECT id, name, start_date, end_date FROM semesters ORDER BY start_date DESC")
    semesters = c.fetchall()
    
    if request.method == 'POST':
        try:
            teacher_id = request.form.get('teacher_id')
            student_id = request.form.get('student_id')
            semester_id = request.form.get('semester_id')
            rating = request.form.get('rating')
            comments = request.form.get('comments', '').strip()
            
            # Validate required fields
            if not teacher_id or not student_id or not semester_id or not rating or not comments:
                flash('Please fill in all required fields', 'error')
                return render_template('feedback.html', teachers=teachers, students=students, semesters=semesters)
            
            # Convert to integers with validation
            try:
                teacher_id = int(teacher_id)
                student_id = int(student_id)
                semester_id = int(semester_id)
                rating = int(rating)
                if not (1 <= rating <= 5):
                    flash('Invalid rating value', 'error')
                    return render_template('feedback.html', teachers=teachers, students=students, semesters=semesters)
            except ValueError:
                flash('Invalid input values', 'error')
                return render_template('feedback.html', teachers=teachers, students=students, semesters=semesters)

            c.execute("INSERT INTO feedback (teacher_id, student_id, semester_id, rating, comments) VALUES (?, ?, ?, ?, ?)",
                     (teacher_id, student_id, semester_id, rating, comments))
            conn.commit()
            conn.close()
            return redirect('/thanks')
        except Exception as e:
            flash('An error occurred while submitting feedback', 'error')
            return render_template('feedback.html', teachers=teachers, students=students, semesters=semesters)
    conn.close()
    return render_template('feedback.html', teachers=teachers, students=students, semesters=semesters)

@app.route('/thanks')
def thanks():
    return render_template('thanks.html')

@app.route('/view_feedback')
@login_required
def view_feedback():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT f.id, t.name, s.name, sem.name, f.rating, f.comments, f.submission_date
        FROM feedback f
        JOIN teachers t ON f.teacher_id = t.id
        JOIN students s ON f.student_id = s.id
        JOIN semesters sem ON f.semester_id = sem.id
        ORDER BY f.submission_date DESC
    ''')
    data = c.fetchall()
    conn.close()
    return render_template('view_feedback.html', feedbacks=data)

@app.route('/performance_report')
@login_required
def performance_report():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Get overall statistics for each student
    c.execute("""
        SELECT 
            s.id,
            s.name,
            s.department,
            COUNT(f.id) as total_feedback,
            ROUND(AVG(f.rating), 2) as avg_rating,
            (SELECT COUNT(*) FROM feedback f2 
             WHERE f2.student_id = s.id AND f2.rating >= 4) as high_ratings,
            (SELECT COUNT(*) FROM feedback f3
             WHERE f3.student_id = s.id AND f3.rating <= 2) as low_ratings
        FROM students s
        LEFT JOIN feedback f ON s.id = f.student_id
        GROUP BY s.id
        ORDER BY avg_rating DESC
    """)
    performance_data = c.fetchall()
    
    # Get monthly trends for each student
    c.execute("""
        SELECT 
            s.name,
            strftime('%Y-%m', f.submission_date) as month,
            ROUND(AVG(f.rating), 2) as monthly_avg
        FROM students s
        JOIN feedback f ON s.id = f.student_id
        GROUP BY s.id, month
        ORDER BY s.name, month DESC
    """)
    monthly_trends = c.fetchall()
    
    conn.close()
    return render_template('performance_report.html', 
                         performance_data=performance_data,
                         monthly_trends=monthly_trends)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
