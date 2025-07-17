import requests
import pandas as pd
from datetime import datetime
import time

def get_places(api_key, query, location="-6.9990899,107.6311617", radius=5000):
    """
    Fetch places data using Google Places API
    
    Parameters:
    - api_key: Your Google Places API key
    - query: Search query (e.g., "restaurant", "cafe", etc.)
    - location: Latitude,Longitude string
    - radius: Search radius in meters
    """
    
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    places_data = []
    
    params = {
        "query": query,
        "location": location,
        "radius": radius,
        "key": api_key
    }
    
    while True:
        try:
            response = requests.get(base_url, params=params)
            result = response.json()
            
            if response.status_code != 200:
                print("Error:", result.get("error_message", "Unknown error"))
                break
                
            for place in result.get("results", []):
                # Get basic place information
                place_data = {
                    "nama": place.get("name", ""),
                    "alamat": place.get("formatted_address", ""),
                    "kategori": ", ".join(place.get("types", [])),
                    "rating": place.get("rating", ""),
                    "total_review": place.get("user_ratings_total", ""),
                }
                
                # Get additional details
                if place.get("place_id"):
                    details = get_place_details(api_key, place["place_id"])
                    place_data.update(details)
                
                places_data.append(place_data)
                time.sleep(0.2)  # Delay to respect API limits
            
            # Check if there are more results
            if "next_page_token" not in result:
                break
                
            # Wait before requesting next page (required by API)
            params["pagetoken"] = result["next_page_token"]
            time.sleep(2)
            
        except Exception as e:
            print(f"Error fetching data: {str(e)}")
            break
    
    return places_data

def get_place_details(api_key, place_id):
    """Get additional place details like website, phone, etc."""
    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
    
    params = {
        "place_id": place_id,
        "fields": "website,formatted_phone_number,url",
        "key": api_key
    }
    
    try:
        response = requests.get(details_url, params=params)
        result = response.json()
        
        if response.status_code == 200 and "result" in result:
            details = result["result"]
            return {
                "website": details.get("website", ""),
                "telepon": details.get("formatted_phone_number", ""),
                "maps_url": details.get("url", "")
            }
    except Exception as e:
        print(f"Error getting details for {place_id}: {str(e)}")
    
    return {
        "website": "",
        "telepon": "",
        "maps_url": ""
    }

def save_to_excel(data, filename=None):
    """Save data to Excel file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_tempat_{timestamp}.xlsx"
    
    df = pd.DataFrame(data)
    
    # Reorder columns
    columns = [
        "nama",
        "kategori",
        "alamat",
        "website",
        "telepon",
        "maps_url",
        "rating",
        "total_review"
    ]
    
    df = df.reindex(columns=columns)
    
    # Save to Excel
    df.to_excel(filename, index=False, engine='openpyxl')
    print(f"Data saved to {filename}")
    return filename

def main():
    # Replace with your API key
    API_KEY = "YOUR_GOOGLE_PLACES_API_KEY"
    
    # Search parameters
    SEARCH_QUERY = input("Masukkan kata kunci pencarian (contoh: restoran bandung): ")
    
    print("\nMengambil data dari Google Maps...")
    places = get_places(API_KEY, SEARCH_QUERY)
    
    if places:
        print(f"\nBerhasil mengumpulkan data {len(places)} tempat")
        filename = save_to_excel(places)
        print(f"\nData telah disimpan ke file {filename}")
    else:
        print("Tidak ada data yang ditemukan atau terjadi error")

if __name__ == "__main__":
    main() 