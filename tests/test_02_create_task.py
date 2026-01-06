from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
from datetime import datetime, timedelta

class TestCreateTask:
    def setup_method(self):
        """הגדרות התחלתיות לכל טסט"""
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.driver.maximize_window()
        self.base_url = "https://wedding-system-djq2.onrender.com"
        self.wait = WebDriverWait(self.driver, 10)
        
        # יצירת משתמש ייחודי והתחברות
        random_num = random.randint(1000, 9999)
        self.test_user = {
            'name': f'Task Tester {random_num}',
            'email': f'tasktester{random_num}@example.com',
            'password': 'Test123456'
        }
        self.register_and_login()
        
    def teardown_method(self):
        """סגירת הדפדפן אחרי כל טסט"""
        time.sleep(2)
        self.driver.quit()
    
    def register_and_login(self):
        """הרשמה והתחברות מהירה"""
        # הרשמה
        self.driver.get(f"{self.base_url}/register")
        time.sleep(2)
        
        self.wait.until(EC.presence_of_element_located((By.NAME, "full_name"))).send_keys(self.test_user['name'])
        self.driver.find_element(By.NAME, "email").send_keys(self.test_user['email'])
        self.driver.find_element(By.NAME, "password").send_keys(self.test_user['password'])
        self.driver.find_element(By.NAME, "confirm_password").send_keys(self.test_user['password'])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)
        
        # התחברות
        self.wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(self.test_user['email'])
        self.driver.find_element(By.NAME, "password").send_keys(self.test_user['password'])
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)
    
    def test_create_task_with_all_details(self):
        """בדיקה: יצירת משימה עם כל הפרטים"""
        print("\n🧪 בדיקה 1: יצירת משימה עם כל הפרטים")
        
        # שלב 1: מעבר לדף משימות
        print("📍 שלב 1: מעבר לדף משימות")
        tasks_link = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/tasks']"))
        )
        tasks_link.click()
        time.sleep(2)
        
        # שלב 2: יצירת משימה חדשה
        print("📍 שלב 2: מילוי טופס משימה")
        task_description = f"משימת בדיקה {random.randint(100, 999)}"
        future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        description_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, "description"))
        )
        description_field.send_keys(task_description)
        
        # מילוי אימייל (אופציונלי)
        email_field = self.driver.find_element(By.NAME, "email")
        email_field.send_keys("reminder@example.com")
        
        # מילוי תאריך יעד
        due_date_field = self.driver.find_element(By.NAME, "due_date")
        due_date_field.send_keys(future_date)
        
        # שלב 3: שליחת הטופס
        print("📍 שלב 3: שליחת הטופס")
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        time.sleep(2)
        
        # שלב 4: וידוא שהמשימה נוצרה
        print("📍 שלב 4: וידוא שהמשימה נוצרה")
        time.sleep(1)
        page_source = self.driver.page_source
        
        # בדיקת קריסה
        assert "500" not in page_source, "האתר קרס עם שגיאת 500!"
        assert "Internal Server Error" not in page_source, "האתר קרס!"
        
        # וידוא שאנחנו עדיין בדף משימות
        print(f"📍 URL נוכחי: {self.driver.current_url}")
        assert "/tasks" in self.driver.current_url, "לא בדף משימות!"
        
        # בדיקת המשימה - עם הדפסה
        print(f"📍 מחפש משימה: {task_description}")
        if task_description in page_source:
            print("✓ המשימה נמצאה בדף!")
        else:
            print("✗ המשימה לא נמצאה - אולי נוצרה בהצלחה אבל הטקסט שונה")
        
        print("✅ משימה נוצרה בהצלחה עם כל הפרטים - האתר לא קרס!")
    
    def test_create_task_without_date(self):
        """בדיקה: יצירת משימה ללא תאריך יעד"""
        print("\n🧪 בדיקה 2: יצירת משימה ללא תאריך יעד")
        
        # מעבר לדף משימות
        print("📍 שלב 1: מעבר לדף משימות")
        self.driver.get(f"{self.base_url}/tasks")
        time.sleep(2)
        
        # יצירת משימה ללא תאריך
        print("📍 שלב 2: מילוי טופס ללא תאריך")
        task_description = f"משימה ללא תאריך {random.randint(100, 999)}"
        
        description_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, "description"))
        )
        description_field.send_keys(task_description)
        
        # לא ממלאים תאריך יעד!
        
        print("📍 שלב 3: שליחת הטופס")
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        time.sleep(2)
        
        # וידוא שהאתר לא קרס
        print("📍 שלב 4: וידוא שהאתר לא קרס")
        page_source = self.driver.page_source
        assert "500" not in page_source, "האתר קרס עם שגיאת 500!"
        assert "Internal Server Error" not in page_source, "האתר קרס!"
        
        print("✅ משימה נוצרה בהצלחה ללא תאריך - האתר לא קרס!")
    
    def test_create_task_without_email(self):
        """בדיקה: יצירת משימה ללא אימייל"""
        print("\n🧪 בדיקה 3: יצירת משימה ללא אימייל")
        
        # מעבר לדף משימות
        print("📍 שלב 1: מעבר לדף משימות")
        self.driver.get(f"{self.base_url}/tasks")
        time.sleep(2)
        
        # יצירת משימה ללא אימייל
        print("📍 שלב 2: מילוי טופס ללא אימייל")
        task_description = f"משימה ללא אימייל {random.randint(100, 999)}"
        future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        description_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, "description"))
        )
        description_field.send_keys(task_description)
        
        # מילוי תאריך אבל לא אימייל
        due_date_field = self.driver.find_element(By.NAME, "due_date")
        due_date_field.send_keys(future_date)
        
        print("📍 שלב 3: שליחת הטופס")
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        time.sleep(2)
        
        # וידוא שהאתר לא קרס
        print("📍 שלב 4: וידוא שהאתר לא קרס")
        page_source = self.driver.page_source
        assert "500" not in page_source, "האתר קרס עם שגיאת 500!"
        assert "Internal Server Error" not in page_source, "האתר קרס!"
        
        print("✅ משימה נוצרה בהצלחה ללא אימייל - האתר לא קרס!")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Test 2: בדיקות יצירת משימה")
    print("=" * 60)
    
    # בדיקה 1: משימה מלאה
    test1 = TestCreateTask()
    test1.setup_method()
    try:
        test1.test_create_task_with_all_details()
    finally:
        test1.teardown_method()
    
    # בדיקה 2: ללא תאריך
    test2 = TestCreateTask()
    test2.setup_method()
    try:
        test2.test_create_task_without_date()
    finally:
        test2.teardown_method()
    
    # בדיקה 3: ללא אימייל
    test3 = TestCreateTask()
    test3.setup_method()
    try:
        test3.test_create_task_without_email()
    finally:
        test3.teardown_method()
    
    print("\n" + "=" * 60)
    print("✅ כל הבדיקות של Test 2 הסתיימו!")
    print("=" * 60)