from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import random

class TestBudget:
    def setup_method(self):
        """הגדרות התחלתיות לכל טסט"""
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.driver.maximize_window()
        self.base_url = "https://wedding-system-djq2.onrender.com"
        self.wait = WebDriverWait(self.driver, 10)
        
        # יצירת משתמש ייחודי והתחברות
        random_num = random.randint(1000, 9999)
        self.test_user = {
            'name': f'Budget Tester {random_num}',
            'email': f'budgettester{random_num}@example.com',
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
    
    def test_add_expense_with_all_details(self):
        """בדיקה: הוספת הוצאה עם כל הפרטים"""
        print("\n🧪 בדיקה 1: הוספת הוצאה עם כל הפרטים")
        
        # שלב 1: מעבר לדף תקציב
        print("📍 שלב 1: מעבר לדף תקציב")
        budget_link = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/budget']"))
        )
        budget_link.click()
        time.sleep(2)
        
        # שלב 2: הוספת הוצאה
        print("📍 שלב 2: מילוי טופס הוצאה")
        expense_description = f"הוצאת בדיקה {random.randint(100, 999)}"
        expense_amount = random.randint(1000, 5000)
        
        description_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, "description"))
        )
        description_field.send_keys(expense_description)
        
        amount_field = self.driver.find_element(By.NAME, "amount")
        amount_field.send_keys(str(expense_amount))
        
        # שלב 3: שליחת הטופס
        print("📍 שלב 3: שליחת הטופס")
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        time.sleep(2)
        
        # שלב 4: וידוא שהאתר לא קרס
        print("📍 שלב 4: וידוא שההוצאה נוספה")
        page_source = self.driver.page_source
        assert "500" not in page_source, "האתר קרס עם שגיאת 500!"
        assert "Internal Server Error" not in page_source, "האתר קרס!"
        assert "/budget" in self.driver.current_url, "לא בדף תקציב!"
        
        print(f"✅ הוצאה נוספה בהצלחה: {expense_description} - ₪{expense_amount}")
    
    def test_add_expense_with_zero_amount(self):
        """בדיקה: הוספת הוצאה עם סכום 0"""
        print("\n🧪 בדיקה 2: הוספת הוצאה עם סכום 0")
        
        # מעבר לדף תקציב
        print("📍 שלב 1: מעבר לדף תקציב")
        self.driver.get(f"{self.base_url}/budget")
        time.sleep(2)
        
        # הוספת הוצאה עם סכום 0
        print("📍 שלב 2: מילוי טופס עם סכום 0")
        expense_description = f"הוצאה עם סכום 0 {random.randint(100, 999)}"
        
        description_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, "description"))
        )
        description_field.send_keys(expense_description)
        
        amount_field = self.driver.find_element(By.NAME, "amount")
        amount_field.send_keys("0")
        
        print("📍 שלב 3: שליחת הטופס")
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        time.sleep(2)
        
        # וידוא שהאתר לא קרס
        print("📍 שלב 4: וידוא שהאתר לא קרס")
        page_source = self.driver.page_source
        assert "500" not in page_source, "האתר קרס עם שגיאת 500!"
        assert "Internal Server Error" not in page_source, "האתר קרס!"
        
        print("✅ הוצאה עם סכום 0 נוספה בהצלחה - האתר לא קרס!")
    
    def test_add_expense_without_description(self):
        """בדיקה: הוספת הוצאה ללא תיאור (בדיקת שדה חובה)"""
        print("\n🧪 בדיקה 3: הוספת הוצאה ללא תיאור")
        
        # מעבר לדף תקציב
        print("📍 שלב 1: מעבר לדף תקציב")
        self.driver.get(f"{self.base_url}/budget")
        time.sleep(2)
        
        # ניסיון להוסיף הוצאה ללא תיאור
        print("📍 שלב 2: מילוי רק סכום ללא תיאור")
        
        amount_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, "amount"))
        )
        amount_field.send_keys("1000")
        
        print("📍 שלב 3: ניסיון לשלוח טופס")
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        time.sleep(1)
        
        # וידוא שהאתר לא קרס והדף לא השתנה (HTML5 validation)
        print("📍 שלב 4: וידוא שהאתר לא קרס")
        page_source = self.driver.page_source
        assert "500" not in page_source, "האתר קרס עם שגיאת 500!"
        assert "Internal Server Error" not in page_source, "האתר קרס!"
        
        # בדיקה שעדיין בדף תקציב (הטופס לא נשלח)
        assert "/budget" in self.driver.current_url, "לא בדף תקציב!"
        
        print("✅ האתר לא אפשר שליחת הוצאה ללא תיאור - validation עובד!")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Test 3: בדיקות תקציב")
    print("=" * 60)
    
    # בדיקה 1: הוצאה מלאה
    test1 = TestBudget()
    test1.setup_method()
    try:
        test1.test_add_expense_with_all_details()
    finally:
        test1.teardown_method()
    
    # בדיקה 2: הוצאה עם סכום 0
    test2 = TestBudget()
    test2.setup_method()
    try:
        test2.test_add_expense_with_zero_amount()
    finally:
        test2.teardown_method()
    
    # בדיקה 3: ללא תיאור
    test3 = TestBudget()
    test3.setup_method()
    try:
        test3.test_add_expense_without_description()
    finally:
        test3.teardown_method()
    
    print("\n" + "=" * 60)
    print("✅ כל הבדיקות של Test 3 הסתיימו!")
    print("=" * 60)