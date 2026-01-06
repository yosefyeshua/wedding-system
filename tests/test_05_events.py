from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import random

class TestEvents:
    def setup_method(self):
        """הגדרות התחלתיות לכל טסט"""
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.driver.maximize_window()
        self.base_url = "https://wedding-system-djq2.onrender.com"
        self.wait = WebDriverWait(self.driver, 10)
        
        # יצירת משתמש ייחודי והתחברות
        random_num = random.randint(1000, 9999)
        self.test_user = {
            'name': f'Event Tester {random_num}',
            'email': f'eventtester{random_num}@example.com',
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
    
    def test_navigate_to_events_page(self):
        """בדיקה 1: ניווט לדף אירועים"""
        print("\n🧪 בדיקה 1: ניווט לדף אירועים")
        
        # שלב 1: מעבר לדף אירועים
        print("📍 שלב 1: לחיצה על קישור אירועים")
        events_link = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/events']"))
        )
        events_link.click()
        time.sleep(2)
        
        # שלב 2: וידוא שהדף נטען
        print("📍 שלב 2: וידוא שדף האירועים נטען")
        assert "/events" in self.driver.current_url, "לא בדף אירועים!"
        
        # שלב 3: וידוא שיש כותרת
        page_source = self.driver.page_source
        assert "לוח שנה ואירועים" in page_source or "אירועים" in page_source, "אין כותרת בדף!"
        
        # שלב 4: וידוא שהטופס קיים
        print("📍 שלב 3: וידוא שטופס הוספת אירוע קיים")
        title_field = self.driver.find_element(By.NAME, "title")
        assert title_field is not None, "שדה כותרת לא נמצא!"
        
        date_field = self.driver.find_element(By.NAME, "event_date")
        assert date_field is not None, "שדה תאריך לא נמצא!"
        
        print("✅ דף אירועים נטען בהצלחה עם כל השדות!")
    
    def test_events_page_has_calendar(self):
        """בדיקה 2: וידוא שיש לוח שנה בדף"""
        print("\n🧪 בדיקה 2: וידוא שיש לוח שנה")
        
        # מעבר לדף אירועים
        print("📍 שלב 1: מעבר לדף אירועים")
        self.driver.get(f"{self.base_url}/events")
        time.sleep(2)
        
        # וידוא שיש אלמנטים של לוח שנה
        print("📍 שלב 2: חיפוש אלמנטים של לוח שנה")
        page_source = self.driver.page_source
        
        # בדיקה שיש כפתורי ניווט
        assert "קודם" in page_source or "הבא" in page_source, "אין כפתורי ניווט בלוח שנה!"
        
        # בדיקה שיש תצוגת חודש או שבוע
        assert "תצוגת חודש" in page_source or "תצוגת שבוע" in page_source, "אין אפשרויות תצוגה!"
        
        print("✅ לוח שנה קיים עם כל האלמנטים!")
    
    def test_events_page_displays_empty_state(self):
        """בדיקה 3: וידוא הצגת מצב ריק"""
        print("\n🧪 בדיקה 3: וידוא הצגת מצב ריק (משתמש חדש)")
        
        # מעבר לדף אירועים
        print("📍 שלב 1: מעבר לדף אירועים")
        self.driver.get(f"{self.base_url}/events")
        time.sleep(2)
        
        # וידוא שיש הודעה למשתמש חדש
        print("📍 שלב 2: בדיקת הודעת מצב ריק")
        page_source = self.driver.page_source
        
        # משתמש חדש לא אמור להיות לו אירועים
        # אז צריך להיות משהו שמראה שאין אירועים
        assert "אין אירועים" in page_source or "הוסף את האירוע הראשון" in page_source or "📭" in page_source, "אין הודעת מצב ריק!"
        
        print("✅ הודעת מצב ריק מוצגת למשתמש חדש!")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Test 5: בדיקות דף אירועים")
    print("=" * 60)
    
    # בדיקה 1: ניווט לדף
    test1 = TestEvents()
    test1.setup_method()
    try:
        test1.test_navigate_to_events_page()
    finally:
        test1.teardown_method()
    
    # בדיקה 2: לוח שנה קיים
    test2 = TestEvents()
    test2.setup_method()
    try:
        test2.test_events_page_has_calendar()
    finally:
        test2.teardown_method()
    
    # בדיקה 3: מצב ריק
    test3 = TestEvents()
    test3.setup_method()
    try:
        test3.test_events_page_displays_empty_state()
    finally:
        test3.teardown_method()
    
    print("\n" + "=" * 60)
    print("✅ כל הבדיקות של Test 5 הסתיימו!")
    print("=" * 60)