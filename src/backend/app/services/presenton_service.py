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
        structure: Dict[str, Any],
        template: str
    ) -> Dict[str, Any]:
        """Create presentation using Presenton API"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Build Presenton API payload
        payload = self._build_payload(structure, template)
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/presentations",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    def _build_payload(self, structure: Dict[str, Any], template: str) -> Dict[str, Any]:
        """Build Presenton API payload"""
        
        slides = []
        for slide_data in structure.get("slides", []):
            slide = {
                "type": slide_data.get("type", "content"),
                "title": slide_data.get("title", ""),
                "content": slide_data.get("content", []),
            }
            
            # Add image if available
            if slide_data.get("image_url"):
                slide["image"] = {
                    "url": slide_data["image_url"],
                    "position": "center"
                }
                
            slides.append(slide)
        
        return {
            "title": structure.get("title", "教學簡報"),
            "template": template,
            "slides": slides,
            "language": "zh-TW"
        }
    
    async def get_presentation_status(self, presentation_id: str) -> Dict[str, Any]:
        """Check presentation generation status"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/presentations/{presentation_id}",
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
                f"{self.base_url}/api/v1/presentations/{presentation_id}/download",
                headers=headers,
                params={"format": format}
            )
            response.raise_for_status()
            return response.content