import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# צור טבלת suppliers
c.execute('''
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    category TEXT,
    price REAL
)
''')

conn.commit()
conn.close()

print("✅ טבלת Suppliers נוצרה בהצלחה!")