import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# הוסף עמודת email לטבלת tasks
c.execute('ALTER TABLE tasks ADD COLUMN email TEXT')

conn.commit()
conn.close()

print("✅ עמודת Email נוספה לטבלת Tasks!")