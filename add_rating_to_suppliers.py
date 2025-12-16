import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# הוסף עמודת rating לטבלת suppliers
c.execute('ALTER TABLE suppliers ADD COLUMN rating INTEGER DEFAULT 0')

conn.commit()
conn.close()

print("✅ עמודת rating נוספה לטבלת Suppliers!")