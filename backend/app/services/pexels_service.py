import httpx
from typing import Optional
from app.config import get_settings

class PexelsService:
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.pexels_api_key
        self.base_url = "https://api.pexels.com/v1"
        
    async def search_image(self, query: str) -> Optional[str]:
        """Search for image URL from Pexels"""
        
        if not self.api_key or self.api_key == "your_pexels_api_key_here":
            return None
            
        headers = {
            "Authorization": self.api_key
        }
        
        params = {
            "query": query,
            "per_page": 1,
            "orientation": "landscape"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    headers=headers,
                    params=params,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("photos") and len(data["photos"]) > 0:
                    return data["photos"][0]["src"]["large"]
                    
        except Exception as e:
            print(f"Pexels API error: {e}")
            
        return None