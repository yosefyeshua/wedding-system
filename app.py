from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# פונקציה לחיבור ל-Database
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # מאפשר גישה לעמודות בשם
    return conn

@app.route("/")
def home():
    # דף הבית יעביר אוטומטית למסך המשימות
    return redirect(url_for("tasks_page"))

@app.route("/tasks", methods=["GET"])
def tasks_page():
    """
    מסך ניהול משימות:
    - מציג רשימת משימות
    - מאפשר סינון לפי סטטוס (חדש/בתהליך/בוצע)
    """
    status_filter = request.args.get("status")
    
    conn = get_db_connection()
    
    if status_filter:
        tasks = conn.execute('SELECT * FROM tasks WHERE status = ?', (status_filter,)).fetchall()
    else:
        tasks = conn.execute('SELECT * FROM tasks').fetchall()
    
    conn.close()
    
    return render_template("tasks.html", tasks=tasks, current_status=status_filter)

@app.route("/tasks/create", methods=["POST"])
def create_task():
    """
    יצירת משימה חדשה (User Story: יצירת משימה)
    """
    title = request.form.get("title")
    
    if title:
        conn = get_db_connection()
        conn.execute('INSERT INTO tasks (title, status) VALUES (?, ?)', 
                     (title, 'חדש'))
        conn.commit()
        conn.close()
    
    return redirect(url_for("tasks_page"))

@app.route("/tasks/<int:task_id>/edit", methods=["POST"])
def edit_task(task_id):
    """
    עריכת משימה קיימת (User Story: עריכת משימה)
    """
    new_title = request.form.get("title")
    new_status = request.form.get("status")
    
    conn = get_db_connection()
    
    if new_title and new_status:
        conn.execute('UPDATE tasks SET title = ?, status = ? WHERE id = ?',
                     (new_title, new_status, task_id))
    elif new_title:
        conn.execute('UPDATE tasks SET title = ? WHERE id = ?',
                     (new_title, task_id))
    elif new_status:
        conn.execute('UPDATE tasks SET status = ? WHERE id = ?',
                     (new_status, task_id))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for("tasks_page"))

@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    """
    מחיקת משימה (User Story: מחיקת משימה)
    """
    conn = get_db_connection()
    conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for("tasks_page"))

@app.route("/budget", methods=["GET"])
def budget_page():
    """
    מסך הוצאות + סיכום (User Stories: הוספת הוצאה, סיכום הוצאות)
    """
    conn = get_db_connection()
    expenses = conn.execute('SELECT * FROM expenses').fetchall()
    
    # חישוב סכום כולל
    total = sum(expense['amount'] for expense in expenses)
    
    conn.close()
    
    return render_template("budget.html", expenses=expenses, total=total)

@app.route("/budget/add", methods=["POST"])
def add_expense():
    """
    הוספת הוצאה (User Story: הוספת הוצאה)
    """
    description = request.form.get("description")
    amount_str = request.form.get("amount")
    
    try:
        amount = float(amount_str)
    except (TypeError, ValueError):
        amount = 0
    
    if description and amount > 0:
        conn = get_db_connection()
        conn.execute('INSERT INTO expenses (description, amount) VALUES (?, ?)',
                     (description, amount))
        conn.commit()
        conn.close()
    
    return redirect(url_for("budget_page"))

if __name__ == "__main__":
    app.run(debug=True, port=5001)