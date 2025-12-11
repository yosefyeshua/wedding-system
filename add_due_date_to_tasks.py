import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# הוסף עמודת due_date לטבלת tasks
c.execute('ALTER TABLE tasks ADD COLUMN due_date DATE')

conn.commit()
conn.close()

print("✅ עמודת due_date נוספה לטבלת Tasks!")