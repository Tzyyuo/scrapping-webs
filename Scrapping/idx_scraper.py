from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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

def get_company_info(driver, company_code):
    """Get company information from IDX website"""
    info = {
        'Kode': company_code,
        'Nama Perusahaan': '',
        'Sektor Bisnis': '',
        'Website': '',
        'Social Media': [],
        'Kontak': ''
    }
    
    try:
        # Open company profile page
        url = f"https://www.idx.co.id/id/perusahaan-tercatat/profil-perusahaan-tercatat/{company_code}/"
        driver.get(url)
        
        # Wait for content to load
        wait = WebDriverWait(driver, 10)
        content = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'company-profile')))
        
        # Get company name
        try:
            name_elem = driver.find_element(By.CLASS_NAME, 'company-name')
            info['Nama Perusahaan'] = name_elem.text.strip()
        except NoSuchElementException:
            print(f"Could not find company name for {company_code}")
        
        # Get company details
        try:
            details = driver.find_elements(By.CLASS_NAME, 'company-detail')
            for detail in details:
                label = detail.find_element(By.CLASS_NAME, 'label').text.strip().lower()
                value = detail.find_element(By.CLASS_NAME, 'value').text.strip()
                
                if 'sektor' in label:
                    info['Sektor Bisnis'] = value
                elif 'website' in label:
                    info['Website'] = value if value != '-' else ''
                elif 'telepon' in label or 'phone' in label:
                    info['Kontak'] = value if value != '-' else ''
        except NoSuchElementException:
            print(f"Could not find company details for {company_code}")
        
        # If website found, try to get social media
        if info['Website'] and info['Website'] != '-':
            try:
                driver.get(info['Website'])
                time.sleep(2)  # Wait for page to load
                
                social_patterns = {
                    'facebook': ['facebook.com', 'fb.com'],
                    'twitter': ['twitter.com', 'x.com'],
                    'linkedin': ['linkedin.com'],
                    'instagram': ['instagram.com'],
                    'youtube': ['youtube.com']
                }
                
                links = driver.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    href = link.get_attribute('href')
                    if href:
                        href = href.lower()
                        for platform, patterns in social_patterns.items():
                            if any(pattern in href for pattern in patterns):
                                info['Social Media'].append(href)
                                break
                
                info['Social Media'] = list(set(info['Social Media']))
            except Exception as e:
                print(f"Error getting social media for {company_code}: {str(e)}")
    
    except Exception as e:
        print(f"Error getting info for {company_code}: {str(e)}")
    
    return info

def scrape_companies(start=0, limit=10):
    """Scrape company information from IDX website"""
    # Read the CSV file
    df = pd.read_csv('daftar_perusahaan_idx.csv')
    
    # Get company codes and names
    data = df.iloc[start:start+limit]
    companies = []
    
    for _, row in data.iterrows():
        name = row['Nama Perusahaan']
        if isinstance(name, str) and 'BEI:' in name:
            # Extract code from name column
            code = name.split('BEI:')[1].strip()
            companies.append(code)
        else:
            print(f"Skipping invalid entry: {name}")
    
    print(f"\nScraping data for {len(companies)} companies starting from index {start}...")
    
    # Setup browser
    driver = setup_driver()
    companies_data = []
    
    try:
        for company_code in companies:
            print(f"\nProcessing {company_code}...")
            info = get_company_info(driver, company_code)
            companies_data.append(info)
            time.sleep(2)  # Delay between requests
    finally:
        driver.quit()
    
    return companies_data

def save_to_excel(data, filename=None):
    """Save data to Excel file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"idx_company_data_{timestamp}.xlsx"
    
    if not data:
        print("No data to save")
        return
    
    df = pd.DataFrame(data)
    
    # Convert social media list to string
    if 'Social Media' in df.columns:
        df['Social Media'] = df['Social Media'].apply(lambda x: '\n'.join(x) if x else '')
    
    try:
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"\nData saved to {filename}")
    except Exception as e:
        print(f"Error saving to Excel: {str(e)}")
        # Save to CSV as backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = f"idx_company_data_{timestamp}.csv"
        df.to_csv(csv_file, index=False)
        print(f"Data saved to CSV file: {csv_file}")

def main():
    start_index = 0  # Start from the first company
    batch_size = 10  # Process 10 companies at a time
    
    print("Starting IDX company data scraping...")
    companies_data = scrape_companies(start=start_index, limit=batch_size)
    
    if companies_data:
        # Print summary
        print("\nData collected:")
        print(f"Total companies processed: {len(companies_data)}")
        
        # Count companies with each type of data
        with_sector = sum(1 for c in companies_data if c['Sektor Bisnis'])
        with_website = sum(1 for c in companies_data if c['Website'])
        with_social = sum(1 for c in companies_data if c['Social Media'])
        with_contact = sum(1 for c in companies_data if c['Kontak'])
        
        print(f"Companies with sector info: {with_sector}")
        print(f"Companies with website: {with_website}")
        print(f"Companies with social media: {with_social}")
        print(f"Companies with contact info: {with_contact}")
        
        save_to_excel(companies_data)
    else:
        print("\nNo data was collected")
    
    print("\nScraping completed!")

if __name__ == "__main__":
    main() 