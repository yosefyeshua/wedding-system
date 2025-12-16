import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

try:
    c.execute('ALTER TABLE users ADD COLUMN budget_limit REAL DEFAULT 0')
    conn.commit()
    print("✅ עמודת budget_limit נוספה בהצלחה!")
except sqlite3.OperationalError as e:
    print(f"⚠️ העמודה כבר קיימת או שגיאה: {e}")

conn.close()