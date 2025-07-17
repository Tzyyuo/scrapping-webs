import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

def get_idx_companies():
    try:
        # URL Wikipedia untuk daftar perusahaan Indonesia
        url = "https://id.wikipedia.org/wiki/Daftar_perusahaan_yang_tercatat_di_Bursa_Efek_Indonesia"
        
        # Headers untuk request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Get halaman web
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Cari tabel perusahaan
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        companies = []
        for table in tables:
            rows = table.find_all('tr')[1:]  # Skip header row
            for row in rows:
                try:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 3:  # Pastikan ada minimal 3 kolom (Kode, Nama, Sektor)
                        kode = cols[0].text.strip()
                        nama = cols[1].text.strip()
                        sektor = cols[2].text.strip() if len(cols) > 2 else ''
                        
                        if kode and nama:  # Only add if both code and name are not empty
                            company = {
                                'Kode': kode,
                                'Nama Perusahaan': nama,
                                'Sektor Bisnis': sektor,
                                'Website': '',  # Akan diisi nanti
                                'Social Media': [],  # Akan diisi nanti
                                'Kontak': ''  # Akan diisi nanti
                            }
                            companies.append(company)
                            print(f"Added: {nama} ({kode})")
                            
                except Exception as e:
                    print(f"Error processing row: {str(e)}")
                    continue
        
        # Create DataFrame and save to CSV
        if companies:
            df = pd.DataFrame(companies)
            df.to_csv('daftar_perusahaan_idx.csv', index=False)
            print(f"Successfully saved {len(companies)} companies to daftar_perusahaan_idx.csv")
        else:
            print("No companies found!")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    get_idx_companies() 