import pandas as pd
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import chromedriver_autoinstaller

def setup_driver():
    """Setup Chrome driver with options"""
    chromedriver_autoinstaller.install()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)

def get_company_info(company_code, driver):
    """Get company information from IDX website"""
    info = {
        'Kode': company_code,
        'Nama Perusahaan': '',
        'Sektor': '',
        'Website': '',
        'Email': '',
        'Telepon': '',
        'Alamat': ''
    }
    
    try:
        # New IDX URL format
        idx_url = f"https://www.idx.co.id/id/perusahaan-tercatat/profil-perusahaan/{company_code}/"
        
        # Add random delay between requests
        time.sleep(random.uniform(1, 3))
        
        driver.get(idx_url)
        
        # Wait for the content to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "container")))
        
        # Get the page source after JavaScript renders
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find the company details table
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    label = cols[0].text.strip().lower()
                    value = cols[2].text.strip()
                    
                    if 'nama' in label:
                        info['Nama Perusahaan'] = value
                    elif 'sektor' in label:
                        info['Sektor'] = value
                    elif 'situs' in label:
                        info['Website'] = value
                    elif 'email' in label:
                        info['Email'] = value
                    elif 'telepon' in label:
                        info['Telepon'] = value
                    elif 'alamat' in label:
                        info['Alamat'] = value

        # Get social media links if available
        social_links = []
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if any(platform in href for platform in ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com']):
                social_links.append(href)
        
        if social_links:
            info['Social Media'] = social_links

    except TimeoutException:
        print(f"Timeout waiting for {company_code} page to load")
    except Exception as e:
        print(f"Error processing {company_code}: {str(e)}")
    
    return info

def scrape_companies(start=0, limit=10):
    """Scrape company information from IDX website"""
    # Read the CSV file
    df = pd.read_csv('daftar_perusahaan_idx.csv')
    
    # Get company codes
    data = df.iloc[start:start+limit]
    companies = []
    
    for _, row in data.iterrows():
        name = row['Nama Perusahaan']
        if isinstance(name, str) and 'BEI:' in name:
            code = name.split('BEI:')[1].strip()
            companies.append(code)
    
    print(f"\nScraping data for {len(companies)} companies starting from index {start}...")
    companies_data = []
    
    # Initialize the driver
    driver = setup_driver()
    
    try:
        for company_code in tqdm(companies, desc="Processing companies"):
            info = get_company_info(company_code, driver)
            companies_data.append(info)
    finally:
        driver.quit()
    
    return companies_data

def save_to_excel(data, filename='company_data.xlsx'):
    """Save data to Excel file"""
    if not data:
        print("No data to save")
        return
        
    df = pd.DataFrame(data)
    
    # Convert social media list to string if exists
    if 'Social Media' in df.columns:
        df['Social Media'] = df['Social Media'].apply(lambda x: '\n'.join(x) if isinstance(x, list) else '')
    
    try:
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"\nData saved to {filename}")
    except Exception as e:
        print(f"Error saving to Excel: {str(e)}")
        # Save to backup file
        backup_file = f'company_data_backup_{int(time.time())}.xlsx'
        try:
            df.to_excel(backup_file, index=False, engine='openpyxl')
            print(f"Data saved to backup file: {backup_file}")
        except Exception as e:
            print(f"Error saving to backup file: {str(e)}")
            # Save as CSV as last resort
            csv_file = f'company_data_backup_{int(time.time())}.csv'
            df.to_csv(csv_file, index=False)
            print(f"Data saved to CSV file: {csv_file}")

def main():
    start_index = 0  # Start from the first company
    batch_size = 10  # Process 10 companies at a time
    
    print("Starting company data scraping...")
    companies_data = scrape_companies(start=start_index, limit=batch_size)
    
    if companies_data:
        # Print summary
        print("\nData collected:")
        print(f"Total companies processed: {len(companies_data)}")
        
        # Count companies with each type of data
        with_name = sum(1 for c in companies_data if c['Nama Perusahaan'])
        with_sector = sum(1 for c in companies_data if c['Sektor'])
        with_website = sum(1 for c in companies_data if c['Website'])
        with_contact = sum(1 for c in companies_data if c['Telepon'] or c['Email'])
        
        print(f"Companies with name: {with_name}")
        print(f"Companies with sector info: {with_sector}")
        print(f"Companies with website: {with_website}")
        print(f"Companies with contact info: {with_contact}")
        
        save_to_excel(companies_data)
    else:
        print("\nNo data was collected")
    
    print("\nScraping completed!")

if __name__ == "__main__":
    main()
