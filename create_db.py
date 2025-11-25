import sqlite3

# יצירת קובץ Database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# יצירת טבלת משימות
cursor.execute('''
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'חדש'
)
''')

# יצירת טבלת הוצאות
cursor.execute('''
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    amount REAL NOT NULL
)
''')

conn.commit()
conn.close()

print("✅ Database נוצר בהצלחה!")
print("✅ טבלאות נוצרו: tasks, expenses")