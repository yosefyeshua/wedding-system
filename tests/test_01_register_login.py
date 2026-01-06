from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import random

class TestRegisterLogin:
    def setup_method(self):
        """הגדרות התחלתיות לכל טסט"""
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.driver.maximize_window()
        self.base_url = "https://wedding-system-djq2.onrender.com"
        self.wait = WebDriverWait(self.driver, 10)
        
    def teardown_method(self):
        """סגירת הדפדפן אחרי כל טסט"""
        time.sleep(2)
        self.driver.quit()
    
    def test_register_and_login(self):
        """בדיקה: הרשמה והתחברות למערכת"""
        print("\n🧪 מתחיל בדיקה: הרשמה והתחברות")
        
        # יצירת משתמש אקראי
        random_num = random.randint(1000, 9999)
        test_user = {
            'name': f'Test User {random_num}',
            'email': f'test{random_num}@example.com',
            'password': 'Test123456'
        }
        
        # שלב 1: כניסה לדף הרשמה
        print("📍 שלב 1: כניסה לדף הרשמה")
        self.driver.get(f"{self.base_url}/register")
        time.sleep(2)
        
        # שלב 2: מילוי טופס הרשמה - עם המתנה לטעינת השדות
        print("📍 שלב 2: מילוי טופס הרשמה")
        
        full_name_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, "full_name"))
        )
        full_name_field.send_keys(test_user['name'])
        
        email_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_field.send_keys(test_user['email'])
        
        password_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_field.send_keys(test_user['password'])
        
        confirm_password_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, "confirm_password"))
        )
        confirm_password_field.send_keys(test_user['password'])
        
        # שלב 3: שליחת הטופס
        print("📍 שלב 3: שליחת הטופס")
        submit_button = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        submit_button.click()
        time.sleep(3)
        
        # שלב 4: התחברות עם המשתמש החדש
        print("📍 שלב 4: התחברות עם המשתמש החדש")
        
        email_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_field.send_keys(test_user['email'])
        
        password_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_field.send_keys(test_user['password'])
        
        submit_button = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        submit_button.click()
        time.sleep(3)
        
        # שלב 5: וידוא שהגענו לדשבורד
        print("📍 שלב 5: וידוא שהגענו לדשבורד")
        assert "wedding-system" in self.driver.current_url
        assert self.driver.title != ""
        
        # שלב 6: וידוא שיש כפתור התנתקות - חיפוש לפי href
        print("📍 שלב 6: וידוא שיש כפתור יציאה")
        logout_link = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href='/logout']"))
        )
        assert logout_link is not None
        print("✓ כפתור יציאה נמצא!")
        
        # שלב 7: התנתקות
        print("📍 שלב 7: יציאה מהמערכת")
        logout_link.click()
        time.sleep(2)
        
        # וידוא שחזרנו לדף התחברות
        print("📍 שלב 8: וידוא שחזרנו לדף התחברות")
        assert "/login" in self.driver.current_url
        print("✓ חזרנו לדף התחברות!")
        
        print("\n✅ הבדיקה עברה בהצלחה!")
        print(f"✅ משתמש נוצר: {test_user['email']}")
        print(f"✅ התחברות הצליחה")
        print(f"✅ יציאה הצליחה")

if __name__ == "__main__":
    test = TestRegisterLogin()
    test.setup_method()
    try:
        test.test_register_and_login()
    finally:
        test.teardown_method()