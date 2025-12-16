import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# טבלת Users
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    partner_id INTEGER,
    partner_name TEXT,
    FOREIGN KEY (partner_id) REFERENCES users(id)
)
''')

# טבלת Password Reset Tokens
c.execute('''
CREATE TABLE IF NOT EXISTS reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

# טבלת Tips
c.execute('''
CREATE TABLE IF NOT EXISTS daily_tips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tip TEXT NOT NULL,
    category TEXT
)
''')

# הוספת טיפים ראשוניים
tips = [
    ("התחילו לתכנן לפחות 6 חודשים לפני המועד - זה יחסוך לכם הרבה לחץ!", "כללי"),
    ("הכינו תקציב מפורט ועקבו אחריו - זה ימנע הפתעות לא נעימות", "תקציב"),
    ("פגשו לפחות 3 ספקים לכל קטגוריה לפני שתחליטו", "ספקים"),
    ("אל תשכחו לשריין מועד גיבוי לאולם - למקרה שהמועד הראשון לא יתאפשר", "אולם"),
    ("הזמינו צלם לפחות 6 חודשים מראש - הטובים נתפסים מהר!", "צלם"),
    ("בדקו ביקורות באינטרנט על כל ספק לפני החתימה", "ספקים"),
    ("תכננו את רשימת האורחים מוקדם - זה ישפיע על בחירת האולם", "אורחים"),
    ("אל תשכחו לשריין מלון לאורחים מחוץ לעיר", "אירוח"),
    ("הכינו Timeline מפורט ליום החתונה", "ארגון"),
    ("זכרו לאכול ולשתות ביום החתונה - זה קורה לכולם!", "יום החתונה"),
    ("שקלו ביטוח לאירוע - להרגעת הנפש", "ביטוח"),
    ("תכננו פינת ילדים אם יש הרבה משפחות עם ילדים", "אורחים"),
    ("אל תשכחו להכין רשימת השמעה לדי.ג'יי מראש", "מוזיקה"),
    ("שריינו חדר להחלפת בגדים ביום החתונה", "יום החתונה"),
    ("הכינו ערכת חירום: תפר, פלסטרים, כאבים", "הכנות"),
    ("תאמו עם הצלם צילומי 'First Look' - מומלץ מאוד!", "צלם"),
    ("בדקו מזג אוויר ושקלו פתרון גיבוי לאירוע בחוץ", "אירוע"),
    ("הכינו פינת מתנות וספר ברכות", "קישוטים"),
    ("אל תשכחו לאכול ארוחה טובה לפני האירוע", "יום החתונה"),
    ("תכננו הסעות לאורחים אם האולם רחוק", "הסעות"),
]

for tip, category in tips:
    c.execute('INSERT OR IGNORE INTO daily_tips (tip, category) VALUES (?, ?)', (tip, category))

# הוספת user_id לטבלאות קיימות
try:
    c.execute('ALTER TABLE tasks ADD COLUMN user_id INTEGER')
except:
    pass

try:
    c.execute('ALTER TABLE expenses ADD COLUMN user_id INTEGER')
except:
    pass

try:
    c.execute('ALTER TABLE suppliers ADD COLUMN user_id INTEGER')
except:
    pass

try:
    c.execute('ALTER TABLE events ADD COLUMN user_id INTEGER')
except:
    pass

conn.commit()
conn.close()

print("✅ טבלאות Users, Reset Tokens ו-Daily Tips נוצרו בהצלחה!")
print("✅ עמודת user_id נוספה לכל הטבלאות!")