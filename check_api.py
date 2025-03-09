import requests
import json

def check_api():
    """Make a request to the Flask API and check what libraries it returns"""
    try:
        # Get libraries from API
        print("=== REQUESTING LIBRARIES FROM API ===")
        response = requests.get('http://localhost:5000/api/libraries')
        
        if response.status_code == 200:
            libraries = response.json()
            print(f"Found {len(libraries)} libraries:")
            for lib_id, lib_data in libraries.items():
                print(f"  Library ID: {lib_id}, Name: {lib_data['name']}, Editable: {lib_data['editable']}")
            
            # Check if there's a patchwork library
            patchwork_libs = [lib for lib_id, lib in libraries.items() 
                             if 'patchwork' in lib_id.lower() or 'patchwork' in lib['name'].lower()]
            
            if patchwork_libs:
                print("\nFound patchwork libraries:")
                for lib in patchwork_libs:
                    print(f"  {lib}")
            else:
                print("\nNo patchwork libraries found in API response.")
                
        else:
            print(f"Error: API returned status code {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"Error checking API: {str(e)}")

if __name__ == "__main__":
    check_api() 