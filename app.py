from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# ===== EMAIL SIMULATION =====
def send_email(to_email, task_description, task_status):
    """דמיית שליחת מייל תזכורת"""
    try:
        # הדפסה ב-Terminal במקום שליחה אמיתית
        print("\n" + "="*50)
        print("📧 מייל תזכורת (SIMULATION)")
        print("="*50)
        print(f"אל: {to_email}")
        print(f"נושא: תזכורת: {task_description}")
        print("-"*50)
        print(f"""
שלום,

תזכורת למשימה בחתונה:

📋 משימה: {task_description}
📊 סטטוס: {task_status}

בהצלחה!
מערכת ניהול החתונה
        """)
        print("="*50)
        print("✅ מייל נשלח בהצלחה! (simulation)\n")
        
        return True
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        return False

# ===== HOME =====
@app.route('/')
def index():
    return redirect('/tasks')

# ===== TASKS ROUTES =====
@app.route('/tasks')
def tasks():
    from datetime import datetime
    
    status_filter = request.args.get('status')
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if status_filter:
        c.execute('SELECT * FROM tasks WHERE status = ? ORDER BY due_date ASC, id DESC', (status_filter,))
    else:
        c.execute('SELECT * FROM tasks ORDER BY due_date ASC, id DESC')
    
    tasks_raw = c.fetchall()
    conn.close()
    
    # Format tasks with Hebrew dates
    tasks = []
    for task in tasks_raw:
        task_dict = dict(task)
        # Format date as DD/MM/YYYY
        if task['due_date']:
            date_obj = datetime.strptime(task['due_date'], '%Y-%m-%d')
            task_dict['due_date'] = date_obj.strftime('%d/%m/%Y')
        tasks.append(task_dict)
    
    return render_template('tasks.html', tasks=tasks)

@app.route('/tasks/create', methods=['POST'])
def create_task():
    description = request.form['description']
    email = request.form.get('email', '')
    due_date = request.form.get('due_date', '')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO tasks (title, description, status, email, due_date) VALUES (?, ?, ?, ?, ?)', 
              (description, description, 'חדש', email, due_date))
    conn.commit()
    conn.close()
    return redirect('/tasks')

@app.route('/tasks/status/<int:task_id>', methods=['POST'])
def update_task_status(task_id):
    new_status = request.form['new_status']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('UPDATE tasks SET status = ? WHERE id = ?', (new_status, task_id))
    conn.commit()
    conn.close()
    return redirect('/tasks')

@app.route('/tasks/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return redirect('/tasks')

@app.route('/tasks/remind/<int:task_id>', methods=['POST'])
def remind_task(task_id):
    """שליחת תזכורת במייל"""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    task = c.fetchone()
    conn.close()
    
    if task and task['email']:
        success = send_email(task['email'], task['description'], task['status'])
        if success:
            return redirect('/tasks?message=sent')
    
    return redirect('/tasks?message=error')

# ===== BUDGET ROUTES =====
@app.route('/budget')
def budget():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM expenses')
    expenses = c.fetchall()
    c.execute('SELECT SUM(amount) FROM expenses')
    total = c.fetchone()[0] or 0
    conn.close()
    return render_template('budget.html', expenses=expenses, total=total)

@app.route('/budget/add', methods=['POST'])
def add_expense():
    description = request.form['description']
    amount = float(request.form['amount'])
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO expenses (description, amount) VALUES (?, ?)', (description, amount))
    conn.commit()
    conn.close()
    return redirect('/budget')

# ===== SUPPLIERS ROUTES =====
@app.route('/suppliers')
def suppliers():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM suppliers')
    suppliers = c.fetchall()
    c.execute('SELECT SUM(price) FROM suppliers')
    total = c.fetchone()[0] or 0
    conn.close()
    return render_template('suppliers.html', suppliers=suppliers, total=total)

@app.route('/suppliers/add', methods=['POST'])
def add_supplier():
    name = request.form['name']
    phone = request.form.get('phone', '')
    category = request.form['category']
    price = float(request.form.get('price', 0))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO suppliers (name, phone, category, price) VALUES (?, ?, ?, ?)',
              (name, phone, category, price))
    conn.commit()
    conn.close()
    return redirect('/suppliers')

@app.route('/suppliers/delete/<int:supplier_id>', methods=['POST'])
def delete_supplier(supplier_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('DELETE FROM suppliers WHERE id = ?', (supplier_id,))
    conn.commit()
    conn.close()
    return redirect('/suppliers')

# ===== EVENTS ROUTES =====
@app.route('/events')
def events():
    from datetime import datetime
    import calendar
    
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM events ORDER BY event_date ASC')
    events_raw = c.fetchall()
    conn.close()
    
    # Format events with Hebrew dates
    events = []
    for event in events_raw:
        event_dict = dict(event)
        # Format date as DD/MM/YYYY
        date_obj = datetime.strptime(event['event_date'], '%Y-%m-%d')
        event_dict['event_date'] = date_obj.strftime('%d/%m/%Y')
        # Format time without seconds
        if event['event_time']:
            event_dict['event_time'] = event['event_time'][:5]  # HH:MM only
        events.append(event_dict)
    
    # Get current month and year
    now = datetime.now()
    year = now.year
    month = now.month
    
    # Hebrew month names
    month_names = {
        1: 'ינואר', 2: 'פברואר', 3: 'מרץ', 4: 'אפריל',
        5: 'מאי', 6: 'יוני', 7: 'יולי', 8: 'אוגוסט',
        9: 'ספטמבר', 10: 'אוקטובר', 11: 'נובמבר', 12: 'דצמבר'
    }
    month_name = month_names[month]
    
    # Get calendar days
    cal = calendar.monthcalendar(year, month)
    calendar_days = []
    
    # Get event dates for highlighting
    event_dates = set()
    for event in events_raw:
        event_date = datetime.strptime(event['event_date'], '%Y-%m-%d')
        if event_date.year == year and event_date.month == month:
            event_dates.add(event_date.day)
    
    # Build calendar
    for week in cal:
        for day in week:
            if day == 0:
                calendar_days.append({'day': '', 'has_event': False, 'is_today': False})
            else:
                is_today = (day == now.day and month == now.month and year == now.year)
                has_event = day in event_dates
                calendar_days.append({
                    'day': day,
                    'has_event': has_event,
                    'is_today': is_today
                })
    
    return render_template('events.html', 
                         events=events, 
                         calendar_days=calendar_days,
                         month_name=month_name,
                         year=year)

@app.route('/events/add', methods=['POST'])
def add_event():
    title = request.form['title']
    event_date = request.form['event_date']
    event_time = request.form.get('event_time', '')
    description = request.form.get('description', '')
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO events (title, event_date, event_time, description) VALUES (?, ?, ?, ?)',
              (title, event_date, event_time, description))
    conn.commit()
    conn.close()
    return redirect('/events')

@app.route('/events/delete/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('DELETE FROM events WHERE id = ?', (event_id,))
    conn.commit()
    conn.close()
    return redirect('/events')

if __name__ == '__main__':
    app.run(debug=True, port=5001)