from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3
import bcrypt
import secrets
from datetime import datetime, timedelta
from functools import wraps
import calendar

app = Flask(__name__)
app.secret_key = 'wedding-system-secret-key-2025'  # Change this in production

# ===== HELPER FUNCTIONS =====
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('עליך להתחבר כדי לגשת לדף זה', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
        user = c.fetchone()
        conn.close()
        return user
    return None

def get_daily_tip():
    """קבלת טיפ יומי - משתנה לפי תאריך"""
    import random
    from datetime import date
    today = date.today()
    seed = int(today.strftime('%Y%m%d'))
    random.seed(seed)
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT tip, category FROM daily_tips')
    tips = c.fetchall()
    conn.close()
    if tips:
        tip = random.choice(tips)
        return {'tip': tip['tip'], 'category': tip['category']}
    return {'tip': 'תכננו את החתונה שלכם בהנאה!', 'category': 'כללי'}

def get_dashboard_stats(user):
    """קבלת סטטיסטיקות לדשבורד"""
    conn = get_db()
    c = conn.cursor()
    
    # משתמש + שותף
    user_ids = (user['id'], user['partner_id']) if user['partner_id'] else (user['id'],)
    
    # ספירת משימות
    if user['partner_id']:
        c.execute('SELECT COUNT(*) FROM tasks WHERE (user_id = ? OR user_id = ?) AND status = ?',
                  (user['id'], user['partner_id'], 'חדש'))
        pending_tasks = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM tasks WHERE (user_id = ? OR user_id = ?) AND status = ?',
                  (user['id'], user['partner_id'], 'הושלם'))
        completed_tasks = c.fetchone()[0]
        
        # אירועים קרובים (7 ימים הקרובים)
        c.execute('''SELECT * FROM events 
                     WHERE (user_id = ? OR user_id = ?) 
                     AND event_date >= date('now') 
                     AND event_date <= date('now', '+7 days')
                     ORDER BY event_date ASC LIMIT 3''',
                  (user['id'], user['partner_id']))
        upcoming_events = c.fetchall()
        
        # תקציב
        c.execute('SELECT budget_limit FROM users WHERE id = ?', (user['id'],))
        budget_limit = c.fetchone()[0] or 0
        
        c.execute('SELECT SUM(amount) FROM expenses WHERE user_id = ? OR user_id = ?',
                  (user['id'], user['partner_id']))
        total_spent = c.fetchone()[0] or 0
        
        # ספקים
        c.execute('SELECT COUNT(*) FROM suppliers WHERE user_id = ? OR user_id = ?',
                  (user['id'], user['partner_id']))
        total_suppliers = c.fetchone()[0]
        
    else:
        c.execute('SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = ?',
                  (user['id'], 'חדש'))
        pending_tasks = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = ?',
                  (user['id'], 'הושלם'))
        completed_tasks = c.fetchone()[0]
        
        c.execute('''SELECT * FROM events 
                     WHERE user_id = ? 
                     AND event_date >= date('now') 
                     AND event_date <= date('now', '+7 days')
                     ORDER BY event_date ASC LIMIT 3''',
                  (user['id'],))
        upcoming_events = c.fetchall()
        
        c.execute('SELECT budget_limit FROM users WHERE id = ?', (user['id'],))
        budget_limit = c.fetchone()[0] or 0
        
        c.execute('SELECT SUM(amount) FROM expenses WHERE user_id = ?', (user['id'],))
        total_spent = c.fetchone()[0] or 0
        
        c.execute('SELECT COUNT(*) FROM suppliers WHERE user_id = ?', (user['id'],))
        total_suppliers = c.fetchone()[0]
    
    conn.close()
    
    # חישוב אחוזי תקציב
    budget_percentage = 0
    if budget_limit > 0:
        budget_percentage = min(int((total_spent / budget_limit) * 100), 100)
    
    # האם חורג מהתקציב?
    is_over_budget = total_spent > budget_limit if budget_limit > 0 else False
    
    return {
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
        'upcoming_events': upcoming_events,
        'budget_limit': budget_limit,
        'total_spent': total_spent,
        'budget_remaining': budget_limit - total_spent,
        'budget_percentage': budget_percentage,
        'is_over_budget': is_over_budget,
        'total_suppliers': total_suppliers
    }

# ===== EMAIL SIMULATION =====
def send_email(to_email, subject, body):
    """דמיית שליחת מייל"""
    try:
        print("\n" + "="*50)
        print("📧 מייל (SIMULATION)")
        print("="*50)
        print(f"אל: {to_email}")
        print(f"נושא: {subject}")
        print("-"*50)
        print(body)
        print("="*50)
        print("✅ מייל נשלח בהצלחה! (simulation)\n")
        return True
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        return False

# ===== AUTHENTICATION ROUTES =====
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email'].lower()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('הסיסמאות לא תואמות', 'error')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('הסיסמה חייבת להיות לפחות 6 תווים', 'error')
            return redirect(url_for('register'))

        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE email = ?', (email,))
        existing_user = c.fetchone()

        if existing_user:
            conn.close()
            flash('האימייל כבר רשום במערכת', 'error')
            return redirect(url_for('register'))

        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        c.execute('INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)',
                  (full_name, email, password_hash))
        conn.commit()
        conn.close()

        flash('הרשמה הושלמה בהצלחה! כעת תוכל להתחבר', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']

        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            flash(f'ברוך הבא, {user["full_name"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('אימייל או סיסמה שגויים', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('התנתקת בהצלחה', 'success')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].lower()
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id, full_name FROM users WHERE email = ?', (email,))
        user = c.fetchone()

        if user:
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=1)
            c.execute('INSERT INTO reset_tokens (user_id, token, expires_at) VALUES (?, ?, ?)',
                      (user['id'], token, expires_at))
            conn.commit()

            reset_link = f"http://localhost:5001/reset-password/{token}"
            body = f"""
שלום {user['full_name']},
קיבלנו בקשה לאיפוס הסיסמה שלך.
קוד איפוס: {token}
או לחץ על הקישור:
{reset_link}
הקוד תקף לשעה אחת.
אם לא ביקשת איפוס סיסמה, התעלם ממייל זה.
בברכה,
מערכת ניהול החתונה
            """
            send_email(email, "איפוס סיסמה", body)
            flash(f'קוד איפוס נשלח לכתובת {email}', 'success')
        else:
            flash(f'אם האימייל קיים במערכת, נשלח קוד איפוס', 'info')

        conn.close()
        return redirect(url_for('reset_password_form'))

    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET'])
@app.route('/reset-password/<token>', methods=['GET'])
def reset_password_form(token=None):
    return render_template('reset_password.html', token=token)

@app.route('/reset-password-submit', methods=['POST'])
def reset_password_submit():
    token = request.form['token']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    if new_password != confirm_password:
        flash('הסיסמאות לא תואמות', 'error')
        return redirect(url_for('reset_password_form'))

    if len(new_password) < 6:
        flash('הסיסמה חייבת להיות לפחות 6 תווים', 'error')
        return redirect(url_for('reset_password_form'))

    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT user_id FROM reset_tokens 
                 WHERE token = ? AND used = 0 AND expires_at > ?''',
              (token, datetime.now()))
    reset_token = c.fetchone()

    if not reset_token:
        conn.close()
        flash('קוד איפוס לא תקין או פג תוקף', 'error')
        return redirect(url_for('reset_password_form'))

    password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    c.execute('UPDATE users SET password_hash = ? WHERE id = ?',
              (password_hash, reset_token['user_id']))
    c.execute('UPDATE reset_tokens SET used = 1 WHERE token = ?', (token,))
    conn.commit()
    conn.close()

    flash('הסיסמה שונתה בהצלחה! כעת תוכל להתחבר', 'success')
    return redirect(url_for('login'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user = get_current_user()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'share':
            partner_email = request.form['partner_email'].lower()
            conn = get_db()
            c = conn.cursor()
            c.execute('SELECT id, full_name FROM users WHERE email = ?', (partner_email,))
            partner = c.fetchone()

            if not partner:
                flash('לא נמצא משתמש עם האימייל הזה', 'error')
                conn.close()
                return redirect(url_for('settings'))

            if partner['id'] == user['id']:
                flash('לא ניתן לשתף עם עצמך', 'error')
                conn.close()
                return redirect(url_for('settings'))

            c.execute('UPDATE users SET partner_id = ?, partner_name = ? WHERE id = ?',
                      (partner['id'], partner['full_name'], user['id']))
            c.execute('UPDATE users SET partner_id = ?, partner_name = ? WHERE id = ?',
                      (user['id'], user['full_name'], partner['id']))
            conn.commit()
            conn.close()

            flash(f'החשבון שותף עם {partner["full_name"]}', 'success')
            return redirect(url_for('settings'))

        elif action == 'unshare':
            conn = get_db()
            c = conn.cursor()
            if user['partner_id']:
                c.execute('UPDATE users SET partner_id = NULL, partner_name = NULL WHERE id = ?',
                          (user['partner_id'],))
            c.execute('UPDATE users SET partner_id = NULL, partner_name = NULL WHERE id = ?',
                      (user['id'],))
            conn.commit()
            conn.close()

            flash('השיתוף הוסר בהצלחה', 'success')
            return redirect(url_for('settings'))
        
        elif action == 'set_budget':
            budget_limit = float(request.form.get('budget_limit', 0))
            conn = get_db()
            c = conn.cursor()
            c.execute('UPDATE users SET budget_limit = ? WHERE id = ?', (budget_limit, user['id']))
            conn.commit()
            conn.close()
            
            flash(f'תקציב כולל עודכן ל-₪{budget_limit:,.0f}', 'success')
            return redirect(url_for('settings'))

    return render_template('settings.html', user=user)

# ===== HOME / DASHBOARD =====
@app.route('/')
@login_required
def index():
    user = get_current_user()
    stats = get_dashboard_stats(user)
    tip = get_daily_tip()
    
    return render_template('index.html', stats=stats, daily_tip=tip, user=user)

# ===== TASKS ROUTES =====
@app.route('/tasks')
@login_required
def tasks():
    user = get_current_user()
    status_filter = request.args.get('status')
    conn = get_db()
    c = conn.cursor()

    if user['partner_id']:
        if status_filter:
            c.execute('SELECT * FROM tasks WHERE (user_id = ? OR user_id = ?) AND status = ? ORDER BY due_date ASC, id DESC',
                      (user['id'], user['partner_id'], status_filter))
        else:
            c.execute('SELECT * FROM tasks WHERE (user_id = ? OR user_id = ?) ORDER BY due_date ASC, id DESC',
                      (user['id'], user['partner_id']))
    else:
        if status_filter:
            c.execute('SELECT * FROM tasks WHERE user_id = ? AND status = ? ORDER BY due_date ASC, id DESC',
                      (user['id'], status_filter))
        else:
            c.execute('SELECT * FROM tasks WHERE user_id = ? ORDER BY due_date ASC, id DESC',
                      (user['id'],))

    tasks_raw = c.fetchall()
    conn.close()

    tasks = []
    for task in tasks_raw:
        task_dict = dict(task)
        if task['due_date']:
            date_obj = datetime.strptime(task['due_date'], '%Y-%m-%d')
            task_dict['due_date'] = date_obj.strftime('%d/%m/%Y')
        tasks.append(task_dict)

    tip = get_daily_tip()
    return render_template('tasks.html', tasks=tasks, daily_tip=tip)

@app.route('/tasks/create', methods=['POST'])
@login_required
def create_task():
    description = request.form['description']
    email = request.form.get('email', '')
    due_date = request.form.get('due_date', '')

    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO tasks (title, description, status, email, due_date, user_id) VALUES (?, ?, ?, ?, ?, ?)',
              (description, description, 'חדש', email, due_date, session['user_id']))
    conn.commit()
    conn.close()

    return redirect('/tasks')

@app.route('/tasks/status/<int:task_id>', methods=['POST'])
@login_required
def update_task_status(task_id):
    new_status = request.form['new_status']
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE tasks SET status = ? WHERE id = ?', (new_status, task_id))
    conn.commit()
    conn.close()

    return redirect('/tasks')

@app.route('/tasks/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

    return redirect('/tasks')

@app.route('/tasks/remind/<int:task_id>', methods=['POST'])
@login_required
def remind_task(task_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    task = c.fetchone()
    conn.close()

    if task and task['email']:
        body = f"""
שלום,
תזכורת למשימה בחתונה:
📋 משימה: {task['description']}
📊 סטטוס: {task['status']}
בהצלחה!
מערכת ניהול החתונה
        """
        success = send_email(task['email'], f"תזכורת: {task['description']}", body)
        if success:
            flash('תזכורת נשלחה בהצלחה!', 'success')
            return redirect('/tasks')

    flash('שגיאה בשליחת תזכורת', 'error')
    return redirect('/tasks')

# ===== BUDGET ROUTES =====
@app.route('/budget')
@login_required
def budget():
    user = get_current_user()
    conn = get_db()
    c = conn.cursor()

    # קבלת תקציב כולל
    c.execute('SELECT budget_limit FROM users WHERE id = ?', (user['id'],))
    budget_limit = c.fetchone()[0] or 0

    if user['partner_id']:
        c.execute('SELECT * FROM expenses WHERE user_id = ? OR user_id = ? ORDER BY created_at DESC',
                  (user['id'], user['partner_id']))
        expenses = c.fetchall()
        c.execute('SELECT SUM(amount) FROM expenses WHERE user_id = ? OR user_id = ?',
                  (user['id'], user['partner_id']))
    else:
        c.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY created_at DESC', (user['id'],))
        expenses = c.fetchall()
        c.execute('SELECT SUM(amount) FROM expenses WHERE user_id = ?', (user['id'],))

    total = c.fetchone()[0] or 0
    conn.close()

    # חישוב אחוזים וסטטוס
    budget_percentage = 0
    remaining = budget_limit - total
    is_over_budget = False
    
    if budget_limit > 0:
        budget_percentage = min(int((total / budget_limit) * 100), 100)
        is_over_budget = total > budget_limit

    tip = get_daily_tip()
    return render_template('budget.html', 
                           expenses=expenses, 
                           total=total,
                           budget_limit=budget_limit,
                           remaining=remaining,
                           budget_percentage=budget_percentage,
                           is_over_budget=is_over_budget,
                           daily_tip=tip)

@app.route('/budget/add', methods=['POST'])
@login_required
def add_expense():
    description = request.form['description']
    amount = float(request.form['amount'])

    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO expenses (description, amount, user_id) VALUES (?, ?, ?)',
              (description, amount, session['user_id']))
    conn.commit()
    
    # בדיקה אם חרגנו מהתקציב
    user = get_current_user()
    if user['partner_id']:
        c.execute('SELECT SUM(amount) FROM expenses WHERE user_id = ? OR user_id = ?',
                  (user['id'], user['partner_id']))
    else:
        c.execute('SELECT SUM(amount) FROM expenses WHERE user_id = ?', (user['id'],))
    
    total_spent = c.fetchone()[0] or 0
    budget_limit = user['budget_limit'] or 0
    
    conn.close()
    
    if budget_limit > 0 and total_spent > budget_limit:
        flash(f'⚠️ שים לב! חרגת מהתקציב ב-₪{total_spent - budget_limit:,.0f}', 'warning')
    else:
        flash('הוצאה נוספה בהצלחה', 'success')

    return redirect('/budget')

# ===== SUPPLIERS ROUTES =====
@app.route('/suppliers')
@login_required
def suppliers():
    user = get_current_user()
    category_filter = request.args.get('category')
    conn = get_db()
    c = conn.cursor()

    if user['partner_id']:
        if category_filter:
            c.execute('SELECT * FROM suppliers WHERE (user_id = ? OR user_id = ?) AND category = ?',
                      (user['id'], user['partner_id'], category_filter))
        else:
            c.execute('SELECT * FROM suppliers WHERE user_id = ? OR user_id = ?',
                      (user['id'], user['partner_id']))
        suppliers = c.fetchall()
        c.execute('SELECT SUM(price) FROM suppliers WHERE user_id = ? OR user_id = ?',
                  (user['id'], user['partner_id']))
        total = c.fetchone()[0] or 0
        c.execute('SELECT category, COUNT(*) as count FROM suppliers WHERE user_id = ? OR user_id = ? GROUP BY category',
                  (user['id'], user['partner_id']))
    else:
        if category_filter:
            c.execute('SELECT * FROM suppliers WHERE user_id = ? AND category = ?',
                      (user['id'], category_filter))
        else:
            c.execute('SELECT * FROM suppliers WHERE user_id = ?', (user['id'],))
        suppliers = c.fetchall()
        c.execute('SELECT SUM(price) FROM suppliers WHERE user_id = ?', (user['id'],))
        total = c.fetchone()[0] or 0
        c.execute('SELECT category, COUNT(*) as count FROM suppliers WHERE user_id = ? GROUP BY category',
                  (user['id'],))

    category_counts = {row['category']: row['count'] for row in c.fetchall()}
    conn.close()

    tip = get_daily_tip()
    return render_template('suppliers.html', suppliers=suppliers, total=total,
                           category_counts=category_counts, daily_tip=tip)

@app.route('/suppliers/add', methods=['POST'])
@login_required
def add_supplier():
    name = request.form['name']
    phone = request.form.get('phone', '')
    if request.form.get('category') == 'custom':
        category = request.form.get('custom_category', 'אחר')
    else:
        category = request.form['category']
    price = float(request.form.get('price', 0))

    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO suppliers (name, phone, category, price, user_id) VALUES (?, ?, ?, ?, ?)',
              (name, phone, category, price, session['user_id']))
    conn.commit()
    conn.close()

    return redirect('/suppliers')

@app.route('/suppliers/edit/<int:supplier_id>', methods=['GET', 'POST'])
@login_required
def edit_supplier(supplier_id):
    conn = get_db()
    c = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form.get('phone', '')
        if request.form.get('category') == 'custom':
            category = request.form.get('custom_category', 'אחר')
        else:
            category = request.form['category']
        price = float(request.form.get('price', 0))

        c.execute('UPDATE suppliers SET name = ?, phone = ?, category = ?, price = ? WHERE id = ?',
                  (name, phone, category, price, supplier_id))
        conn.commit()
        conn.close()
        return redirect('/suppliers')
    else:
        c.execute('SELECT * FROM suppliers WHERE id = ?', (supplier_id,))
        supplier = c.fetchone()
        conn.close()
        return render_template('suppliers_edit.html', supplier=supplier)

@app.route('/suppliers/delete/<int:supplier_id>', methods=['POST'])
@login_required
def delete_supplier(supplier_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM suppliers WHERE id = ?', (supplier_id,))
    conn.commit()
    conn.close()

    return redirect('/suppliers')

@app.route('/suppliers/rate/<int:supplier_id>', methods=['POST'])
@login_required
def rate_supplier(supplier_id):
    rating = int(request.form.get('rating', 0))
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE suppliers SET rating = ? WHERE id = ?', (rating, supplier_id))
    conn.commit()
    conn.close()

    return redirect('/suppliers')

# ===== EVENTS ROUTES =====
@app.route('/events')
@login_required
def events():
    user = get_current_user()
    
    # קבלת פרמטרים לתצוגה
    view_type = request.args.get('view', 'month')  # month או week
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))
    
    conn = get_db()
    c = conn.cursor()

    if user['partner_id']:
        c.execute('SELECT * FROM events WHERE user_id = ? OR user_id = ? ORDER BY event_date ASC',
                  (user['id'], user['partner_id']))
    else:
        c.execute('SELECT * FROM events WHERE user_id = ? ORDER BY event_date ASC', (user['id'],))

    events_raw = c.fetchall()
    conn.close()

    # Format events
    events = []
    for event in events_raw:
        event_dict = dict(event)
        date_obj = datetime.strptime(event['event_date'], '%Y-%m-%d')
        event_dict['event_date'] = date_obj.strftime('%d/%m/%Y')
        event_dict['event_date_raw'] = event['event_date']
        if event['event_time']:
            event_dict['event_time'] = event['event_time'][:5]
        events.append(event_dict)

    # Calendar generation
    month_names = {
        1: 'ינואר', 2: 'פברואר', 3: 'מרץ', 4: 'אפריל',
        5: 'מאי', 6: 'יוני', 7: 'יולי', 8: 'אוגוסט',
        9: 'ספטמבר', 10: 'אוקטובר', 11: 'נובמבר', 12: 'דצמבר'
    }
    
    day_names = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת']
    
    month_name = month_names[month]
    
    # יצירת לוח שנה
    cal = calendar.monthcalendar(year, month)
    calendar_days = []
    event_dates = {}
    
    # מיפוי אירועים לפי תאריך
    for event in events_raw:
        event_date = datetime.strptime(event['event_date'], '%Y-%m-%d')
        if event_date.year == year and event_date.month == month:
            day = event_date.day
            if day not in event_dates:
                event_dates[day] = []
            event_dates[day].append({
                'title': event['title'],
                'time': event['event_time'][:5] if event['event_time'] else None
            })
    
    # בניית לוח החודש
    today = datetime.now()
    for week in cal:
        week_days = []
        for day in week:
            if day == 0:
                week_days.append({'day': '', 'has_event': False, 'is_today': False, 'events': []})
            else:
                is_today = (day == today.day and month == today.month and year == today.year)
                has_event = day in event_dates
                day_events = event_dates.get(day, [])
                week_days.append({
                    'day': day,
                    'has_event': has_event,
                    'is_today': is_today,
                    'events': day_events
                })
        calendar_days.append(week_days)
    
    # חישוב חודש קודם ואחרי
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    # תצוגת שבוע
    week_dates = []
    if view_type == 'week':
        # מצא את השבוע הנוכחי
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())  # יום ראשון
        
        for i in range(7):
            day_date = start_of_week + timedelta(days=i)
            day_events = []
            
            for event in events_raw:
                event_date = datetime.strptime(event['event_date'], '%Y-%m-%d').date()
                if event_date == day_date.date():
                    day_events.append({
                        'title': event['title'],
                        'time': event['event_time'][:5] if event['event_time'] else None,
                        'description': event['description']
                    })
            
            week_dates.append({
                'date': day_date,
                'day_name': day_names[i],
                'is_today': day_date.date() == today.date(),
                'events': day_events
            })

    tip = get_daily_tip()
    
    return render_template('events.html',
                           events=events,
                           calendar_days=calendar_days,
                           month_name=month_name,
                           year=year,
                           month=month,
                           prev_year=prev_year,
                           prev_month=prev_month,
                           next_year=next_year,
                           next_month=next_month,
                           view_type=view_type,
                           week_dates=week_dates,
                           daily_tip=tip)

@app.route('/events/add', methods=['POST'])
@login_required
def add_event():
    title = request.form['title']
    event_date = request.form['event_date']
    event_time = request.form.get('event_time', '')
    description = request.form.get('description', '')

    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO events (title, event_date, event_time, description, user_id) VALUES (?, ?, ?, ?, ?)',
              (title, event_date, event_time, description, session['user_id']))
    conn.commit()
    conn.close()

    return redirect('/events')

@app.route('/events/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM events WHERE id = ?', (event_id,))
    conn.commit()
    conn.close()

    return redirect('/events')
# ===== ABOUT PAGE =====
@app.route('/about')
def about():
    """דף אודות המערכת"""
    
    # מידע על המערכת
    system_info = {
        'name': 'מערכת ניהול חתונה',
        'version': '0.01.55',
        'release_date': 'דצמבר 2025',
        'description': 'תכנון חתונה לא חייב להיות מסובך! מערכת ניהול החתונה שלנו כאן כדי לעזור לכם להפוך את התהליך לפשוט, מאורגן ומהנה.'
    }
    
    # הצוות המפתח
    team_members = [
        {
            'name': 'רועי שם טוב',
            'role': 'Product Owner & Full Stack Developer',
            'icon': '👨‍💻',
            'description': 'מוביל את הפרויקט ומפתח Backend ו-Frontend',
            'color': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        },
        {
            'name': 'דניאל ששון',
            'role': 'Backend Developer',
            'icon': '⚙️',
            'description': 'מומחה במסדי נתונים ולוגיקה עסקית',
            'color': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
        },
        {
            'name': 'יאיר ספנוב',
            'role': 'Frontend Developer',
            'icon': '🎨',
            'description': 'יוצר חוויות משתמש מרשימות ומעוצבות',
            'color': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
        },
        {
            'name': 'יהושוע יוסף',
            'role': 'QA & Database Specialist',
            'icon': '✅',
            'description': 'מבטיח איכות ויציבות של המערכת',
            'color': 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
        }
    ]
    
    # תכונות עיקריות
    features = [
        {
            'icon': '📋',
            'title': 'ניהול משימות',
            'description': 'עקוב אחרי כל המשימות עם סטטוסים, תזכורות ותאריכי יעד'
        },
        {
            'icon': '💰',
            'title': 'ניהול תקציב חכם',
            'description': 'שלוט בהוצאות עם תקציב כולל, התראות חריגה ומעקב בזמן אמת'
        },
        {
            'icon': '🏢',
            'title': 'ניהול ספקים',
            'description': 'ארגן את כל הספקים שלך עם דירוגים, מחירים וקטגוריות'
        },
        {
            'icon': '📅',
            'title': 'לוח שנה אינטראקטיבי',
            'description': 'תצוגות חודש ושבוע עם כל האירועים והפגישות החשובים'
        },
        {
            'icon': '🤝',
            'title': 'שיתוף עם בן/בת זוג',
            'description': 'עבדו ביחד על התכנון עם גישה משותפת לכל המידע'
        },
        {
            'icon': '🏠',
            'title': 'דשבורד מקיף',
            'description': 'קבל תמונת מצב מלאה במבט אחד עם סטטיסטיקות וטיפים'
        }
    ]
    
    # טכנולוגיות
    technologies = [
        {'name': 'Python 3.9', 'icon': '🐍'},
        {'name': 'Flask', 'icon': '⚡'},
        {'name': 'SQLite', 'icon': '🗄️'},
        {'name': 'HTML/CSS', 'icon': '🎨'},
        {'name': 'Flask-Login', 'icon': '🔐'},
        {'name': 'Jinja2', 'icon': '📄'}
    ]
    
    return render_template('about.html',
                         system_info=system_info,
                         team_members=team_members,
                         features=features,
                         technologies=technologies)
if __name__ == '__main__':
    app.run(debug=True, port=5001)