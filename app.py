from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# ===== HOME =====
@app.route('/')
def index():
    return redirect('/tasks')

# ===== TASKS ROUTES =====
@app.route('/tasks')
def tasks():
    status_filter = request.args.get('status')
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if status_filter:
        c.execute('SELECT * FROM tasks WHERE status = ?', (status_filter,))
    else:
        c.execute('SELECT * FROM tasks')
    
    tasks = c.fetchall()
    conn.close()
    return render_template('tasks.html', tasks=tasks)

@app.route('/tasks/create', methods=['POST'])
def create_task():
    description = request.form['description']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO tasks (title, description, status) VALUES (?, ?, ?)', (description, description, 'חדש'))
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

if __name__ == '__main__':
    app.run(debug=True, port=5001)