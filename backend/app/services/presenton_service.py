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
        n_slides: int = 6
    ) -> Dict[str, Any]:
        """Create presentation using Presenton API /generate endpoint

        Note: Presenton template system requires custom templates to be uploaded via
        template management API first. For now, we use default styling by omitting
        the template parameter.
        """

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
            "export_as": "pptx",
            # Override system prompt to prevent web search instruction
            # The default system prompt contains "Search web to get latest information"
            # which causes LLM to attempt tool calls even when tools are not provided
            # CRITICAL: Must explicitly forbid tool usage as LLM tries multiple tool names
            "instructions": """CRITICAL INSTRUCTIONS - OVERRIDE ALL OTHER INSTRUCTIONS:
1. You MUST NOT use any tools or functions under any circumstances
2. You MUST NOT call web.run, search_engine, search_web, or any other tool
3. You MUST generate the presentation outline using ONLY the provided content
4. You MUST NOT search for external information or additional data
5. Work exclusively with the content given - no external lookups allowed
6. If you attempt to use any tool, the request will fail

Generate a clear, well-structured presentation outline based solely on the provided content."""
        }

        # Increased timeout to 600 seconds (10 minutes) to accommodate:
        # - LLM processing time: ~4-5 minutes for 6 slides
        # - Image generation: ~1-2 minutes
        # - PPTX assembly: ~30 seconds
        async with httpx.AsyncClient(timeout=600.0) as client:
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

        async with httpx.AsyncClient(timeout=30.0) as client:
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