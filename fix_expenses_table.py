import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

try:
    # הוסף עמודת created_at ללא default
    c.execute('ALTER TABLE expenses ADD COLUMN created_at TIMESTAMP')
    conn.commit()
    print("✅ עמודת created_at נוספה לטבלת expenses!")
    
    # עדכן את כל השורות הקיימות עם תאריך נוכחי
    c.execute("UPDATE expenses SET created_at = datetime('now') WHERE created_at IS NULL")
    conn.commit()
    print("✅ תאריכים עודכנו לכל ההוצאות הקיימות!")
    
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e).lower():
        print("⚠️ העמודה כבר קיימת")
    else:
        print(f"❌ שגיאה: {e}")

conn.close()