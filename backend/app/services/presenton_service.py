import httpx
import asyncio
from typing import Dict, Any, Optional
from app.config import get_settings

class PresentonService:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.presenton_api_url
        self.api_key = self.settings.presenton_api_key
        
    async def create_presentation(
        self,
        content: str,
        template: str,
        n_slides: int = 6
    ) -> Dict[str, Any]:
        """Create presentation using Presenton API /generate endpoint"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Build Presenton /generate API payload
        payload = {
            "content": content,
            "n_slides": n_slides,
            "language": "zh-TW",
            "template": template,
            "tone": "default",
            "verbosity": "standard",
            "web_search": False,
            "include_table_of_contents": False,
            "include_title_slide": True,
            "export_as": "pptx"
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/ppt/presentation/generate",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    
    async def get_presentation_status(self, presentation_id: str) -> Dict[str, Any]:
        """Check presentation generation status"""

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/ppt/presentation/{presentation_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    
    async def download_presentation(self, presentation_id: str, format: str = "pptx") -> bytes:
        """Download presentation file"""

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/ppt/presentation/export/{format.lower()}",
                headers=headers,
                params={"id": presentation_id}
            )
            response.raise_for_status()
            return response.content