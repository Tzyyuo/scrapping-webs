from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time
from datetime import datetime

def setup_driver():
    """Setup Chrome driver with necessary options"""
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    # Uncomment baris di bawah jika ingin browser berjalan di background
    # options.add_argument('--headless')
    return webdriver.Chrome(options=options)

def scrape_place_info(element):
    """Extract information from a place element"""
    info = {
        'nama': '',
        'alamat': '',
        'rating': '',
        'total_review': '',
        'kategori': '',
        'website': '',
        'telepon': ''
    }
    
    try:
        # Get name
        name_elem = element.find_element(By.CSS_SELECTOR, '[class*="fontHeadlineSmall"]')
        info['nama'] = name_elem.text if name_elem else ''
        
        # Get other details that are immediately available
        details = element.find_elements(By.CSS_SELECTOR, '[class*="fontBodyMedium"]')
        for detail in details:
            text = detail.text
            if text:
                # Rating and reviews are usually in the format "4.5 (1,234)"
                if '(' in text and ')' in text and any(c.isdigit() for c in text):
                    parts = text.split('(')
                    info['rating'] = parts[0].strip()
                    info['total_review'] = parts[1].replace(')', '').strip()
                # Address usually doesn't contain special characters
                elif len(text) > 10 and '·' not in text and '(' not in text:
                    info['alamat'] = text
                # Category is usually shorter and might contain "·"
                elif len(text) < 50:
                    info['kategori'] = text
        
        # Click to open place details
        name_elem.click()
        time.sleep(2)
        
        # Wait for details panel to load
        wait = WebDriverWait(driver, 10)
        details_panel = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="section-layout-root"]')))
        
        # Get website and phone
        buttons = details_panel.find_elements(By.CSS_SELECTOR, 'button[class*="CsEnBe"]')
        for button in buttons:
            aria_label = button.get_attribute('aria-label')
            if aria_label:
                if 'situs web' in aria_label.lower():
                    info['website'] = button.text
                elif 'telepon' in aria_label.lower():
                    info['telepon'] = button.text
        
        # Close details panel
        close_button = driver.find_element(By.CSS_SELECTOR, 'button[class*="VfPpkd-icon-button"]')
        close_button.click()
        time.sleep(1)
        
    except Exception as e:
        print(f"Error extracting info: {str(e)}")
    
    return info

def scroll_results(driver, num_scrolls=3):
    """Scroll through results panel to load more places"""
    results_panel = driver.find_element(By.CSS_SELECTOR, '[role="feed"]')
    for _ in range(num_scrolls):
        driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', results_panel)
        time.sleep(2)

def save_to_excel(data, filename=None):
    """Save scraped data to Excel file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_maps_{timestamp}.xlsx"
    
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"\nData telah disimpan ke file: {filename}")

def main():
    global driver
    search_query = input("Masukkan kata kunci pencarian (contoh: restoran bandung): ")
    
    try:
        print("\nMemulai browser...")
        driver = setup_driver()
        
        # Open Google Maps
        print("Membuka Google Maps...")
        driver.get("https://www.google.com/maps")
        time.sleep(2)
        
        # Input search query
        search_box = driver.find_element(By.ID, "searchboxinput")
        search_box.clear()
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)
        
        # Wait for results to load
        print("\nMencari lokasi...")
        time.sleep(5)
        
        # Scroll to load more results
        print("Mengumpulkan data...")
        scroll_results(driver)
        
        # Get all place elements
        places = driver.find_elements(By.CSS_SELECTOR, '[class*="hfpxzc"]')
        print(f"\nDitemukan {len(places)} tempat")
        
        # Extract information from each place
        all_places_info = []
        for i, place in enumerate(places, 1):
            print(f"Mengambil data tempat {i}/{len(places)}...")
            info = scrape_place_info(place)
            all_places_info.append(info)
        
        # Save data
        save_to_excel(all_places_info)
        
    except Exception as e:
        print(f"Terjadi error: {str(e)}")
    
    finally:
        print("\nMenutup browser...")
        driver.quit()

if __name__ == "__main__":
    main() 