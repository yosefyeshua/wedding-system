from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
import time
import random

class TestSuppliers:
    def setup_method(self):
        """הגדרות התחלתיות לכל טסט"""
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.driver.maximize_window()
        self.base_url = "https://wedding-system-djq2.onrender.com"
        self.wait = WebDriverWait(self.driver, 10)
        
        # יצירת משתמש ייחודי והתחברות
        random_num = random.randint(1000, 9999)
        self.test_user = {
            'name': f'Supplier Tester {random_num}',
            'email': f'suppliertester{random_num}@example.com',
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
    
    def test_add_supplier_with_all_details(self):
        """בדיקה: הוספת ספק עם כל הפרטים"""
        print("\n🧪 בדיקה 1: הוספת ספק עם כל הפרטים")
        
        # שלב 1: מעבר לדף ספקים
        print("📍 שלב 1: מעבר לדף ספקים")
        suppliers_link = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/suppliers']"))
        )
        suppliers_link.click()
        time.sleep(2)
        
        # שלב 2: הוספת ספק
        print("📍 שלב 2: מילוי טופס ספק")
        supplier_name = f"ספק בדיקה {random.randint(100, 999)}"
        supplier_phone = f"050-{random.randint(1000000, 9999999)}"
        supplier_price = random.randint(5000, 15000)
        
        name_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, "name"))
        )
        name_field.send_keys(supplier_name)
        
        phone_field = self.driver.find_element(By.NAME, "phone")
        phone_field.send_keys(supplier_phone)
        
        # בחירת קטגוריה
        category_select = Select(self.driver.find_element(By.NAME, "category"))
        category_select.select_by_value("אולם")
        
        price_field = self.driver.find_element(By.NAME, "price")
        price_field.send_keys(str(supplier_price))
        
        # שלב 3: שליחת הטופס
        print("📍 שלב 3: שליחת הטופס")
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        time.sleep(2)
        
        # שלב 4: וידוא שהאתר לא קרס
        print("📍 שלב 4: וידוא שהספק נוסף")
        page_source = self.driver.page_source
        assert "500" not in page_source, "האתר קרס עם שגיאת 500!"
        assert "Internal Server Error" not in page_source, "האתר קרס!"
        assert "/suppliers" in self.driver.current_url, "לא בדף ספקים!"
        
        print(f"✅ ספק נוסף בהצלחה: {supplier_name} - ₪{supplier_price}")
    
    def test_add_supplier_without_price(self):
        """בדיקה: הוספת ספק ללא מחיר"""
        print("\n🧪 בדיקה 2: הוספת ספק ללא מחיר")
        
        # מעבר לדף ספקים
        print("📍 שלב 1: מעבר לדף ספקים")
        self.driver.get(f"{self.base_url}/suppliers")
        time.sleep(2)
        
        # הוספת ספק ללא מחיר
        print("📍 שלב 2: מילוי טופס ללא מחיר")
        supplier_name = f"ספק ללא מחיר {random.randint(100, 999)}"
        supplier_phone = f"052-{random.randint(1000000, 9999999)}"
        
        name_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, "name"))
        )
        name_field.send_keys(supplier_name)
        
        phone_field = self.driver.find_element(By.NAME, "phone")
        phone_field.send_keys(supplier_phone)
        
        # בחירת קטגוריה
        category_select = Select(self.driver.find_element(By.NAME, "category"))
        category_select.select_by_value("צלם")
        
        # לא ממלאים מחיר!
        
        print("📍 שלב 3: שליחת הטופס")
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        time.sleep(2)
        
        # וידוא שהאתר לא קרס
        print("📍 שלב 4: וידוא שהאתר לא קרס")
        page_source = self.driver.page_source
        assert "500" not in page_source, "האתר קרס עם שגיאת 500!"
        assert "Internal Server Error" not in page_source, "האתר קרס!"
        
        print("✅ ספק ללא מחיר נוסף בהצלחה - האתר לא קרס!")
    
    def test_add_supplier_without_phone(self):
        """בדיקה: הוספת ספק ללא טלפון"""
        print("\n🧪 בדיקה 3: הוספת ספק ללא טלפון")
        
        # מעבר לדף ספקים
        print("📍 שלב 1: מעבר לדף ספקים")
        self.driver.get(f"{self.base_url}/suppliers")
        time.sleep(2)
        
        # הוספת ספק ללא טלפון
        print("📍 שלב 2: מילוי טופס ללא טלפון")
        supplier_name = f"ספק ללא טלפון {random.randint(100, 999)}"
        supplier_price = random.randint(3000, 8000)
        
        name_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, "name"))
        )
        name_field.send_keys(supplier_name)
        
        # לא ממלאים טלפון!
        
        # בחירת קטגוריה
        category_select = Select(self.driver.find_element(By.NAME, "category"))
        category_select.select_by_value("DJ")
        
        price_field = self.driver.find_element(By.NAME, "price")
        price_field.send_keys(str(supplier_price))
        
        print("📍 שלב 3: שליחת הטופס")
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        time.sleep(2)
        
        # וידוא שהאתר לא קרס
        print("📍 שלב 4: וידוא שהאתר לא קרס")
        page_source = self.driver.page_source
        assert "500" not in page_source, "האתר קרס עם שגיאת 500!"
        assert "Internal Server Error" not in page_source, "האתר קרס!"
        
        print("✅ ספק ללא טלפון נוסף בהצלחה - האתר לא קרס!")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Test 4: בדיקות ספקים")
    print("=" * 60)
    
    # בדיקה 1: ספק מלא
    test1 = TestSuppliers()
    test1.setup_method()
    try:
        test1.test_add_supplier_with_all_details()
    finally:
        test1.teardown_method()
    
    # בדיקה 2: ללא מחיר
    test2 = TestSuppliers()
    test2.setup_method()
    try:
        test2.test_add_supplier_without_price()
    finally:
        test2.teardown_method()
    
    # בדיקה 3: ללא טלפון
    test3 = TestSuppliers()
    test3.setup_method()
    try:
        test3.test_add_supplier_without_phone()
    finally:
        test3.teardown_method()
    
    print("\n" + "=" * 60)
    print("✅ כל הבדיקות של Test 4 הסתיימו!")
    print("=" * 60)