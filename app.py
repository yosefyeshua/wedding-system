from flask import Flask, render_template, request, redirect, session, flash, url_for
import os
import bcrypt
import secrets
from datetime import datetime, timedelta
from functools import wraps
import calendar
import psycopg
from psycopg.rows import dict_row
import sqlite3
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'wedding-system-secret-key-2025')

# ===== DATABASE CONNECTION =====
def get_db():
    """חיבור ל-PostgreSQL או SQLite (לפי סביבה)"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Production - PostgreSQL
        # Fix for Render.com - change postgres:// to postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        conn = psycopg.connect(database_url, row_factory=dict_row)
        return conn
    else:
        # Development - SQLite
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        return conn

def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """פונקציה עזר להרצת שאילתות"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if commit:
            conn.commit()
            result = cursor.rowcount
        elif fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = None
            
        return result
    finally:
        cursor.close()
        conn.close()

# ===== HELPER FUNCTIONS =====
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
        query = 'SELECT * FROM users WHERE id = %s' if os.environ.get('DATABASE_URL') else 'SELECT * FROM users WHERE id = ?'
        return execute_query(query, (session['user_id'],), fetch_one=True)
    return None

def get_daily_tip():
    """קבלת טיפ יומי - משתנה לפי תאריך"""
    import random
    from datetime import date
    today = date.today()
    seed = int(today.strftime('%Y%m%d'))
    random.seed(seed)
    
    tips = execute_query('SELECT tip, category FROM daily_tips', fetch_all=True)
    
    if tips:
        tip = random.choice(tips)
        return {'tip': tip['tip'], 'category': tip['category']}
    return {'tip': 'תכננו את החתונה שלכם בהנאה!', 'category': 'כללי'}

def get_dashboard_stats(user):
    """קבלת סטטיסטיקות לדשבורד"""
    if not user:
        return {
            'pending_tasks': 0,
            'completed_tasks': 0,
            'upcoming_events': [],
            'budget_limit': 0,
            'total_spent': 0,
            'budget_remaining': 0,
            'budget_percentage': 0,
            'is_over_budget': False,
            'total_suppliers': 0
        }
    
    placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'
    
    # ספירת משימות
    if user['partner_id']:
        pending_query = f'SELECT COUNT(*) as count FROM tasks WHERE (user_id = {placeholder} OR user_id = {placeholder}) AND status = {placeholder}'
        pending_tasks = execute_query(pending_query, (user['id'], user['partner_id'], 'חדש'), fetch_one=True)['count']
        
        completed_query = f'SELECT COUNT(*) as count FROM tasks WHERE (user_id = {placeholder} OR user_id = {placeholder}) AND status = {placeholder}'
        completed_tasks = execute_query(completed_query, (user['id'], user['partner_id'], 'הושלם'), fetch_one=True)['count']
        
        # אירועים קרובים
        events_query = f'''SELECT * FROM events 
                          WHERE (user_id = {placeholder} OR user_id = {placeholder}) 
                          AND event_date >= CURRENT_DATE 
                          AND event_date <= CURRENT_DATE + INTERVAL '7 days'
                          ORDER BY event_date ASC LIMIT 3''' if os.environ.get('DATABASE_URL') else \
                       f'''SELECT * FROM events 
                          WHERE (user_id = {placeholder} OR user_id = {placeholder}) 
                          AND event_date >= date('now') 
                          AND event_date <= date('now', '+7 days')
                          ORDER BY event_date ASC LIMIT 3'''
        upcoming_events = execute_query(events_query, (user['id'], user['partner_id']), fetch_all=True)
        
        # תקציב
        budget_query = f'SELECT budget_limit FROM users WHERE id = {placeholder}'
        budget_limit = execute_query(budget_query, (user['id'],), fetch_one=True)['budget_limit'] or 0
        
        spent_query = f'SELECT SUM(amount) as total FROM expenses WHERE user_id = {placeholder} OR user_id = {placeholder}'
        total_spent = execute_query(spent_query, (user['id'], user['partner_id']), fetch_one=True)['total'] or 0
        
        # ספקים
        suppliers_query = f'SELECT COUNT(*) as count FROM suppliers WHERE user_id = {placeholder} OR user_id = {placeholder}'
        total_suppliers = execute_query(suppliers_query, (user['id'], user['partner_id']), fetch_one=True)['count']
    else:
        pending_query = f'SELECT COUNT(*) as count FROM tasks WHERE user_id = {placeholder} AND status = {placeholder}'
        pending_tasks = execute_query(pending_query, (user['id'], 'חדש'), fetch_one=True)['count']
        
        completed_query = f'SELECT COUNT(*) as count FROM tasks WHERE user_id = {placeholder} AND status = {placeholder}'
        completed_tasks = execute_query(completed_query, (user['id'], 'הושלם'), fetch_one=True)['count']
        
        events_query = f'''SELECT * FROM events 
                          WHERE user_id = {placeholder} 
                          AND event_date >= CURRENT_DATE 
                          AND event_date <= CURRENT_DATE + INTERVAL '7 days'
                          ORDER BY event_date ASC LIMIT 3''' if os.environ.get('DATABASE_URL') else \
                       f'''SELECT * FROM events 
                          WHERE user_id = {placeholder} 
                          AND event_date >= date('now') 
                          AND event_date <= date('now', '+7 days')
                          ORDER BY event_date ASC LIMIT 3'''
        upcoming_events = execute_query(events_query, (user['id'],), fetch_all=True)
        
        budget_query = f'SELECT budget_limit FROM users WHERE id = {placeholder}'
        budget_limit = execute_query(budget_query, (user['id'],), fetch_one=True)['budget_limit'] or 0
        
        spent_query = f'SELECT SUM(amount) as total FROM expenses WHERE user_id = {placeholder}'
        total_spent = execute_query(spent_query, (user['id'],), fetch_one=True)['total'] or 0
        
        suppliers_query = f'SELECT COUNT(*) as count FROM suppliers WHERE user_id = {placeholder}'
        total_suppliers = execute_query(suppliers_query, (user['id'],), fetch_one=True)['count']
    
    # חישוב אחוזי תקציב
    budget_percentage = 0
    if budget_limit > 0:
        budget_percentage = min(int((total_spent / budget_limit) * 100), 100)
    
    is_over_budget = total_spent > budget_limit if budget_limit > 0 else False
    
    return {
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
        'upcoming_events': upcoming_events or [],
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

# ===== שאר ה-ROUTES נשארים אותו דבר =====
# (המשך הקוד בהודעה הבאה...)# ===== AUTHENTICATION ROUTES =====
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

        placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'
        check_query = f'SELECT id FROM users WHERE email = {placeholder}'
        existing_user = execute_query(check_query, (email,), fetch_one=True)

        if existing_user:
            flash('האימייל כבר רשום במערכת', 'error')
            return redirect(url_for('register'))

        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        insert_query = f'INSERT INTO users (full_name, email, password_hash) VALUES ({placeholder}, {placeholder}, {placeholder})'
        execute_query(insert_query, (full_name, email, password_hash), commit=True)

        flash('הרשמה הושלמה בהצלחה! כעת תוכל להתחבר', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']

        placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'
        query = f'SELECT * FROM users WHERE email = {placeholder}'
        user = execute_query(query, (email,), fetch_one=True)

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
        placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'
        
        query = f'SELECT id, full_name FROM users WHERE email = {placeholder}'
        user = execute_query(query, (email,), fetch_one=True)

        if user:
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=1)
            
            insert_query = f'INSERT INTO reset_tokens (user_id, token, expires_at) VALUES ({placeholder}, {placeholder}, {placeholder})'
            execute_query(insert_query, (user['id'], token, expires_at), commit=True)

            reset_link = f"{request.url_root}reset-password/{token}"
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

    placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'
    now_placeholder = 'NOW()' if os.environ.get('DATABASE_URL') else "datetime('now')"
    
    query = f'''SELECT user_id FROM reset_tokens 
                WHERE token = {placeholder} AND used = 0 AND expires_at > {now_placeholder}'''
    reset_token = execute_query(query, (token,), fetch_one=True)

    if not reset_token:
        flash('קוד איפוס לא תקין או פג תוקף', 'error')
        return redirect(url_for('reset_password_form'))

    password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    
    update_user = f'UPDATE users SET password_hash = {placeholder} WHERE id = {placeholder}'
    execute_query(update_user, (password_hash, reset_token['user_id']), commit=True)
    
    update_token = f'UPDATE reset_tokens SET used = 1 WHERE token = {placeholder}'
    execute_query(update_token, (token,), commit=True)

    flash('הסיסמה שונתה בהצלחה! כעת תוכל להתחבר', 'success')
    return redirect(url_for('login'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user = get_current_user()
    placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'share':
            partner_email = request.form['partner_email'].lower()
            
            query = f'SELECT id, full_name FROM users WHERE email = {placeholder}'
            partner = execute_query(query, (partner_email,), fetch_one=True)

            if not partner:
                flash('לא נמצא משתמש עם האימייל הזה', 'error')
                return redirect(url_for('settings'))

            if partner['id'] == user['id']:
                flash('לא ניתן לשתף עם עצמך', 'error')
                return redirect(url_for('settings'))

            update1 = f'UPDATE users SET partner_id = {placeholder}, partner_name = {placeholder} WHERE id = {placeholder}'
            execute_query(update1, (partner['id'], partner['full_name'], user['id']), commit=True)
            
            update2 = f'UPDATE users SET partner_id = {placeholder}, partner_name = {placeholder} WHERE id = {placeholder}'
            execute_query(update2, (user['id'], user['full_name'], partner['id']), commit=True)

            flash(f'החשבון שותף עם {partner["full_name"]}', 'success')
            return redirect(url_for('settings'))

        elif action == 'unshare':
            if user['partner_id']:
                update1 = f'UPDATE users SET partner_id = NULL, partner_name = NULL WHERE id = {placeholder}'
                execute_query(update1, (user['partner_id'],), commit=True)
            
            update2 = f'UPDATE users SET partner_id = NULL, partner_name = NULL WHERE id = {placeholder}'
            execute_query(update2, (user['id'],), commit=True)

            flash('השיתוף הוסר בהצלחה', 'success')
            return redirect(url_for('settings'))
        
        elif action == 'set_budget':
            budget_limit = float(request.form.get('budget_limit', 0))
            
            update = f'UPDATE users SET budget_limit = {placeholder} WHERE id = {placeholder}'
            execute_query(update, (budget_limit, user['id']), commit=True)
            
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
    
    return render_template('index.html', stats=stats, daily_tip=tip, user=user)# ===== TASKS ROUTES =====
@app.route('/tasks')
@login_required
def tasks():
    user = get_current_user()
    status_filter = request.args.get('status')
    placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'

    if user['partner_id']:
        if status_filter:
            query = f'SELECT * FROM tasks WHERE (user_id = {placeholder} OR user_id = {placeholder}) AND status = {placeholder} ORDER BY due_date ASC, id DESC'
            tasks_raw = execute_query(query, (user['id'], user['partner_id'], status_filter), fetch_all=True)
        else:
            query = f'SELECT * FROM tasks WHERE (user_id = {placeholder} OR user_id = {placeholder}) ORDER BY due_date ASC, id DESC'
            tasks_raw = execute_query(query, (user['id'], user['partner_id']), fetch_all=True)
    else:
        if status_filter:
            query = f'SELECT * FROM tasks WHERE user_id = {placeholder} AND status = {placeholder} ORDER BY due_date ASC, id DESC'
            tasks_raw = execute_query(query, (user['id'], status_filter), fetch_all=True)
        else:
            query = f'SELECT * FROM tasks WHERE user_id = {placeholder} ORDER BY due_date ASC, id DESC'
            tasks_raw = execute_query(query, (user['id'],), fetch_all=True)

    tasks = []
    for task in tasks_raw:
        task_dict = dict(task)
        if task['due_date']:
            date_obj = datetime.strptime(str(task['due_date']), '%Y-%m-%d')
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
    placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'

    query = f'INSERT INTO tasks (title, description, status, email, due_date, user_id) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})'
    execute_query(query, (description, description, 'חדש', email, due_date, session['user_id']), commit=True)

    return redirect('/tasks')

@app.route('/tasks/status/<int:task_id>', methods=['POST'])
@login_required
def update_task_status(task_id):
    new_status = request.form['new_status']
    placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'
    
    query = f'UPDATE tasks SET status = {placeholder} WHERE id = {placeholder}'
    execute_query(query, (new_status, task_id), commit=True)

    return redirect('/tasks')

@app.route('/tasks/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'
    
    query = f'DELETE FROM tasks WHERE id = {placeholder}'
    execute_query(query, (task_id,), commit=True)

    return redirect('/tasks')

@app.route('/tasks/remind/<int:task_id>', methods=['POST'])
@login_required
def remind_task(task_id):
    placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'
    
    query = f'SELECT * FROM tasks WHERE id = {placeholder}'
    task = execute_query(query, (task_id,), fetch_one=True)

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
    placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'

    budget_query = f'SELECT budget_limit FROM users WHERE id = {placeholder}'
    budget_limit = execute_query(budget_query, (user['id'],), fetch_one=True)['budget_limit'] or 0

    if user['partner_id']:
        expenses_query = f'SELECT * FROM expenses WHERE user_id = {placeholder} OR user_id = {placeholder} ORDER BY created_at DESC'
        expenses = execute_query(expenses_query, (user['id'], user['partner_id']), fetch_all=True)
        
        total_query = f'SELECT SUM(amount) as total FROM expenses WHERE user_id = {placeholder} OR user_id = {placeholder}'
        total = execute_query(total_query, (user['id'], user['partner_id']), fetch_one=True)['total'] or 0
    else:
        expenses_query = f'SELECT * FROM expenses WHERE user_id = {placeholder} ORDER BY created_at DESC'
        expenses = execute_query(expenses_query, (user['id'],), fetch_all=True)
        
        total_query = f'SELECT SUM(amount) as total FROM expenses WHERE user_id = {placeholder}'
        total = execute_query(total_query, (user['id'],), fetch_one=True)['total'] or 0

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
    placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'

    insert_query = f'INSERT INTO expenses (description, amount, user_id) VALUES ({placeholder}, {placeholder}, {placeholder})'
    execute_query(insert_query, (description, amount, session['user_id']), commit=True)
    
    user = get_current_user()
    
    if user['partner_id']:
        total_query = f'SELECT SUM(amount) as total FROM expenses WHERE user_id = {placeholder} OR user_id = {placeholder}'
        total_spent = execute_query(total_query, (user['id'], user['partner_id']), fetch_one=True)['total'] or 0
    else:
        total_query = f'SELECT SUM(amount) as total FROM expenses WHERE user_id = {placeholder}'
        total_spent = execute_query(total_query, (user['id'],), fetch_one=True)['total'] or 0
    
    budget_limit = user['budget_limit'] or 0
    
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
    placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'

    if user['partner_id']:
        if category_filter:
            query = f'SELECT * FROM suppliers WHERE (user_id = {placeholder} OR user_id = {placeholder}) AND category = {placeholder}'
            suppliers = execute_query(query, (user['id'], user['partner_id'], category_filter), fetch_all=True)
        else:
            query = f'SELECT * FROM suppliers WHERE user_id = {placeholder} OR user_id = {placeholder}'
            suppliers = execute_query(query, (user['id'], user['partner_id']), fetch_all=True)
        
        total_query = f'SELECT SUM(price) as total FROM suppliers WHERE user_id = {placeholder} OR user_id = {placeholder}'
        total = execute_query(total_query, (user['id'], user['partner_id']), fetch_one=True)['total'] or 0
        
        category_query = f'SELECT category, COUNT(*) as count FROM suppliers WHERE user_id = {placeholder} OR user_id = {placeholder} GROUP BY category'
        categories = execute_query(category_query, (user['id'], user['partner_id']), fetch_all=True)
    else:
        if category_filter:
            query = f'SELECT * FROM suppliers WHERE user_id = {placeholder} AND category = {placeholder}'
            suppliers = execute_query(query, (user['id'], category_filter), fetch_all=True)
        else:
            query = f'SELECT * FROM suppliers WHERE user_id = {placeholder}'
            suppliers = execute_query(query, (user['id'],), fetch_all=True)
        
        total_query = f'SELECT SUM(price) as total FROM suppliers WHERE user_id = {placeholder}'
        total = execute_query(total_query, (user['id'],), fetch_one=True)['total'] or 0
        
        category_query = f'SELECT category, COUNT(*) as count FROM suppliers WHERE user_id = {placeholder} GROUP BY category'
        categories = execute_query(category_query, (user['id'],), fetch_all=True)

    category_counts = {row['category']: row['count'] for row in categories}

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
    placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'

    query = f'INSERT INTO suppliers (name, phone, category, price, user_id) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})'
    execute_query(query, (name, phone, category, price, session['user_id']), commit=True)

    return redirect('/suppliers')

@app.route('/suppliers/edit/<int:supplier_id>', methods=['GET', 'POST'])
@login_required
def edit_supplier(supplier_id):
    placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form.get('phone', '')
        if request.form.get('category') == 'custom':
            category = request.form.get('custom_category', 'אחר')
        else:
            category = request.form['category']
        price = float(request.form.get('price', 0))

        query = f'UPDATE suppliers SET name = {placeholder}, phone = {placeholder}, category = {placeholder}, price = {placeholder} WHERE id = {placeholder}'
        execute_query(query, (name, phone, category, price, supplier_id), commit=True)
        
        return redirect('/suppliers')
    else:
        query = f'SELECT * FROM suppliers WHERE id = {placeholder}'
        supplier = execute_query(query, (supplier_id,), fetch_one=True)
        
        return render_template('suppliers_edit.html', supplier=supplier)

@app.route('/suppliers/delete/<int:supplier_id>', methods=['POST'])
@login_required
def delete_supplier(supplier_id):
    placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'
    
    query = f'DELETE FROM suppliers WHERE id = {placeholder}'
    execute_query(query, (supplier_id,), commit=True)

    return redirect('/suppliers')

@app.route('/suppliers/rate/<int:supplier_id>', methods=['POST'])
@login_required
def rate_supplier(supplier_id):
    rating = int(request.form.get('rating', 0))
    placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'
    
    query = f'UPDATE suppliers SET rating = {placeholder} WHERE id = {placeholder}'
    execute_query(query, (rating, supplier_id), commit=True)

    return redirect('/suppliers')# ===== EVENTS ROUTES =====
@app.route('/events')
@login_required
def events():
    user = get_current_user()
    placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'
    
    view_type = request.args.get('view', 'month')
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))

    if user['partner_id']:
        query = f'SELECT * FROM events WHERE user_id = {placeholder} OR user_id = {placeholder} ORDER BY event_date ASC'
        events_raw = execute_query(query, (user['id'], user['partner_id']), fetch_all=True)
    else:
        query = f'SELECT * FROM events WHERE user_id = {placeholder} ORDER BY event_date ASC'
        events_raw = execute_query(query, (user['id'],), fetch_all=True)

    events = []
    for event in events_raw:
        event_dict = dict(event)
        date_obj = datetime.strptime(str(event['event_date']), '%Y-%m-%d')
        event_dict['event_date'] = date_obj.strftime('%d/%m/%Y')
        event_dict['event_date_raw'] = str(event['event_date'])
        if event['event_time']:
            event_dict['event_time'] = str(event['event_time'])[:5]
        events.append(event_dict)

    month_names = {
        1: 'ינואר', 2: 'פברואר', 3: 'מרץ', 4: 'אפריל',
        5: 'מאי', 6: 'יוני', 7: 'יולי', 8: 'אוגוסט',
        9: 'ספטמבר', 10: 'אוקטובר', 11: 'נובמבר', 12: 'דצמבר'
    }
    
    day_names = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת']
    month_name = month_names[month]
    
    cal = calendar.monthcalendar(year, month)
    calendar_days = []
    event_dates = {}
    
    for event in events_raw:
        event_date = datetime.strptime(str(event['event_date']), '%Y-%m-%d')
        if event_date.year == year and event_date.month == month:
            day = event_date.day
            if day not in event_dates:
                event_dates[day] = []
            event_dates[day].append({
                'title': event['title'],
                'time': str(event['event_time'])[:5] if event['event_time'] else None
            })
    
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
    
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    week_dates = []
    if view_type == 'week':
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        
        for i in range(7):
            day_date = start_of_week + timedelta(days=i)
            day_events = []
            
            for event in events_raw:
                event_date = datetime.strptime(str(event['event_date']), '%Y-%m-%d').date()
                if event_date == day_date.date():
                    day_events.append({
                        'title': event['title'],
                        'time': str(event['event_time'])[:5] if event['event_time'] else None,
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
    placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'

    query = f'INSERT INTO events (title, event_date, event_time, description, user_id) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})'
    execute_query(query, (title, event_date, event_time, description, session['user_id']), commit=True)

    return redirect('/events')

@app.route('/events/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    placeholder = '%s' if os.environ.get('DATABASE_URL') else '?'
    
    query = f'DELETE FROM events WHERE id = {placeholder}'
    execute_query(query, (event_id,), commit=True)

    return redirect('/events')

# ===== ABOUT PAGE =====
@app.route('/about')
def about():
    """דף אודות המערכת"""
    
    system_info = {
        'name': 'מערכת ניהול חתונה',
        'version': '0.01.55',
        'release_date': 'דצמבר 2025',
        'description': 'תכנון חתונה לא חייב להיות מסובך! מערכת ניהול החתונה שלנו כאן כדי לעזור לכם להפוך את התהליך לפשוט, מאורגן ומהנה.'
    }
    
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
    
    features = [
        {'icon': '📋', 'title': 'ניהול משימות', 'description': 'עקוב אחרי כל המשימות עם סטטוסים, תזכורות ותאריכי יעד'},
        {'icon': '💰', 'title': 'ניהול תקציב חכם', 'description': 'שלוט בהוצאות עם תקציב כולל, התראות חריגה ומעקב בזמן אמת'},
        {'icon': '🏢', 'title': 'ניהול ספקים', 'description': 'ארגן את כל הספקים שלך עם דירוגים, מחירים וקטגוריות'},
        {'icon': '📅', 'title': 'לוח שנה אינטראקטיבי', 'description': 'תצוגות חודש ושבוע עם כל האירועים והפגישות החשובים'},
        {'icon': '🤝', 'title': 'שיתוף עם בן/בת זוג', 'description': 'עבדו ביחד על התכנון עם גישה משותפת לכל המידע'},
        {'icon': '🏠', 'title': 'דשבורד מקיף', 'description': 'קבל תמונת מצב מלאה במבט אחד עם סטטיסטיקות וטיפים'}
    ]
    
    technologies = [
        {'name': 'Python 3.9', 'icon': '🐍'},
        {'name': 'Flask', 'icon': '⚡'},
        {'name': 'PostgreSQL', 'icon': '🐘'},
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
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)