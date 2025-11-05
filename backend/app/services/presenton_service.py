import httpx
import asyncio
from typing import Dict, Any, Optional
from app.config import get_settings

class PresentonService:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.presenton_api_url
        self.api_key = self.settings.presenton_api_key
        self._template_cache = {}
        
    async def get_template_info(self, template_id: Optional[str] = None) -> Dict[str, Any]:
        """Query template management API to get template constraints

        Returns template metadata including available slide layouts
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/ppt/template-management/summary",
                    headers=headers
                )
                response.raise_for_status()
                template_data = response.json()

                # Extract max slides from template metadata
                # Fallback to 5 if structure is unexpected
                if isinstance(template_data, dict):
                    # Try to find max_slides or count of layouts
                    return {
                        "max_slides": template_data.get("max_slides", 5),
                        "available_layouts": len(template_data.get("layouts", [])) or 5
                    }
                return {"max_slides": 5, "available_layouts": 5}
        except Exception as e:
            # Fallback to safe defaults if template API fails
            print(f"Warning: Template API query failed: {e}. Using safe defaults.")
            return {"max_slides": 5, "available_layouts": 5}

    async def create_presentation(
        self,
        content: str,
        n_slides: int = 6,
        template_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create presentation using Presenton API /generate endpoint

        Args:
            content: Presentation content text
            n_slides: Number of slides to generate (default: 6, user-configurable)
            template_id: Optional template ID (not yet implemented in Presenton)

        Note: Presenton template system requires custom templates to be uploaded via
        template management API first. For now, we use default styling by omitting
        the template parameter.

        This method validates n_slides against template constraints and auto-adjusts
        if the requested count exceeds template capabilities.
        """

        # Query template constraints to validate n_slides
        template_info = await self.get_template_info(template_id)
        max_slides = template_info.get("max_slides", 5)  # Template default: 5 layouts

        # Enforce template constraints
        if n_slides > max_slides:
            print(f"Warning: Requested {n_slides} slides exceeds template max ({max_slides}). Adjusting to {max_slides}.")
            n_slides = max_slides

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Build Presenton /generate API payload
        # Note: template field is removed - Presenton requires custom templates to be uploaded first
        # The API works without template field and uses default styling
        payload = {
            "content": content,
            "n_slides": n_slides,
            "language": "zh-TW",
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
        """Download presentation file

        Presenton export API returns file path, not file content.
        We need to:
        1. Call export API to get file path
        2. Read file from shared volume mount
        """

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Step 1: Call export API to get file path
        payload = {
            "id": presentation_id,
            "export_as": format.lower()
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/ppt/presentation/export",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

        # Step 2: Read file from shared volume
        # result["path"] is like "/app_data/exports/filename.pptx"
        file_path = result.get("path")
        if not file_path:
            raise ValueError(f"Export API did not return file path: {result}")

        # Read file from shared volume mount (both containers mount ./app_data/exports)
        try:
            with open(file_path, "rb") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Exported file not found at {file_path}. "
                "Ensure volume mount ./app_data/exports is configured for both presenton and backend containers."
            )