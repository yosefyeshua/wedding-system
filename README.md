# Wedding System

מיני-אפליקציית Flask לניהול משימות והוצאות לחתונה.

כיצד להריץ (PowerShell):

1. ליצור את מסד הנתונים (רק בפעם הראשונה):

```powershell
cd "c:\Users\יוסף ישועה\Documents\פרוייקט הנדסת תוכנה\wedding system"
python .\create_db.py
```

2. להריץ את היישום:

```powershell
cd "c:\Users\יוסף ישועה\Documents\פרוייקט הנדסת תוכנה\wedding system"
python .\app.py
```

- האתר יפעל בכתובת: `http://localhost:5001`
- לשינויי קוד לפיתוח, השרת רץ ב־debug ויטען מחדש אוטומטית.

הערות:
- קובץ המסד `database.db` מנוהל מקומית; אין צורך לעקוב אחריו ב־git (מופיע ב־`.gitignore`).
- תלווה ב־Python ו־Flask מותקן (התקנה: `pip install Flask`).
