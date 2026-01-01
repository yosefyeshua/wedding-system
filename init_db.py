import os
import psycopg2

# קבלת DATABASE_URL מהסביבה
database_url = os.environ.get('DATABASE_URL')

if not database_url:
    print("❌ DATABASE_URL לא מוגדר!")
    exit(1)

# תיקון URL של Render
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

print("🔧 מתחבר למסד הנתונים...")

conn = psycopg2.connect(database_url)
cursor = conn.cursor()

print("✅ התחברות הצליחה!")
print("📋 יוצר טבלאות...")

# יצירת טבלאות
tables = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        full_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash BYTEA NOT NULL,
        partner_id INTEGER,
        partner_name VARCHAR(255),
        budget_limit DECIMAL(10,2) DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        status VARCHAR(50) DEFAULT 'חדש',
        email VARCHAR(255),
        due_date DATE,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS expenses (
        id SERIAL PRIMARY KEY,
        description VARCHAR(255) NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS suppliers (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        phone VARCHAR(50),
        category VARCHAR(100),
        price DECIMAL(10,2) DEFAULT 0,
        rating INTEGER DEFAULT 0,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS events (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        event_date DATE NOT NULL,
        event_time TIME,
        description TEXT,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reset_tokens (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        token VARCHAR(255) UNIQUE NOT NULL,
        used INTEGER DEFAULT 0,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_tips (
        id SERIAL PRIMARY KEY,
        tip TEXT NOT NULL,
        category VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
]

for table_sql in tables:
    cursor.execute(table_sql)
    print("✅ טבלה נוצרה")

# הוספת טיפים יומיים
tips = [
    ("התחילו לתכנן לפחות שנה מראש", "תכנון"),
    ("הגדירו תקציב ברור מההתחלה", "תקציב"),
    ("השתמשו בספרדשיט למעקב אחר הוצאות", "תקציב"),
    ("קבעו פגישות עם ספקים מוקדם ככל האפשר", "ספקים"),
    ("שמרו על תקשורת פתוחה עם בן/בת הזוג", "זוגיות"),
]

cursor.execute("SELECT COUNT(*) FROM daily_tips")
if cursor.fetchone()[0] == 0:
    for tip, category in tips:
        cursor.execute("INSERT INTO daily_tips (tip, category) VALUES (%s, %s)", (tip, category))
    print("✅ טיפים יומיים נוספו")

conn.commit()
cursor.close()
conn.close()

print("🎉 מסד הנתונים מוכן!")