import os
import requests

class ImageFinder:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.cse_id = os.getenv("GOOGLE_CSE_ID")

    def find_image_url(self, query):
        """
        Finds an image URL for the given query (product name).
        """
        print(f"[*] Searching for image for: {query}")
        
        if not self.api_key or "SIMULATED" in self.api_key:
            print("   [!] Simulator Mode: returning placeholder image.")
            # Return a reliable placeholder image
            return "https://placehold.co/600x400?text=" + requests.utils.quote(query)

        # Real Implementation (Google Custom Search API)
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'q': query,
            'cx': self.cse_id,
            'key': self.api_key,
            'searchType': 'image',
            'num': 1,
            'imgSize': 'large'
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()
            if 'items' in data and len(data['items']) > 0:
                link = data['items'][0]['link']
                print(f"   [+] Found: {link}")
                return link
        except Exception as e:
            print(f"   [!] Error searching Google: {e}")
        
        return None
