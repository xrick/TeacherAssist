import uuid
import asyncio
from typing import Dict, Any
from app.services.ollama_service import OllamaService
from app.services.pexels_service import PexelsService
from app.services.presenton_service import PresentonService

class ContentProcessor:
    def __init__(self):
        self.ollama = OllamaService()
        self.pexels = PexelsService()
        self.presenton = PresentonService()
        self.tasks = {}
        
    async def process_content(
        self,
        content: str,
        template: str,
        task_id: str
    ) -> Dict[str, Any]:
        """Process content and generate presentation"""

        try:
            # Step 1: Prepare content (20%)
            self._update_progress(task_id, 20, "正在準備內容...")
            await asyncio.sleep(0.5)

            # Step 2: Send to Presenton (40%)
            self._update_progress(task_id, 40, "正在發送給簡報生成引擎...")

            # Step 3: Generate presentation using Presenton (60-90%)
            self._update_progress(task_id, 60, "正在生成簡報...")

            # Presenton handles everything: content analysis, layout, images, generation
            presentation_result = await self.presenton.create_presentation(
                content=content,
                template=template,
                n_slides=6  # Generate 6 slides by default
            )

            # Step 4: Finalize (100%)
            self._update_progress(task_id, 100, "簡報生成完成...")

            # Extract presentation data from Presenton response
            # Presenton /generate returns: {presentation_path, edit_page_path, presentation_id}
            presentation_id = presentation_result.get("presentation_id")
            if not presentation_id:
                # Fallback: extract from paths
                pres_path = presentation_result.get("presentation_path", "")
                presentation_id = pres_path.split("/")[-1].replace(".pptx", "") if pres_path else str(uuid.uuid4())

            result = {
                "task_id": task_id,
                "status": "completed",
                "progress": 100,
                "message": "簡報生成完成",
                "current_step": "完成",
                "presentation": {
                    "title": "AI生成簡報",
                    "slides": []  # Presenton handles slides internally
                },
                "presentation_id": presentation_id,
                "download_url": f"/api/download/{presentation_id}/pptx",
                "pdf_url": f"/api/download/{presentation_id}/pdf",
                "presenton_data": presentation_result
            }

            self.tasks[task_id] = result
            return result

        except Exception as e:
            import traceback
            traceback.print_exc()
            error_result = {
                "task_id": task_id,
                "status": "failed",
                "progress": 0,
                "message": f"生成失敗: {str(e)}",
                "current_step": "錯誤"
            }
            self.tasks[task_id] = error_result
            return error_result
    
    async def _enrich_with_images(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Add images to slides"""
        
        for slide in structure.get("slides", []):
            image_query = slide.get("image_query")
            if image_query:
                image_url = await self.pexels.search_image(image_query)
                if image_url:
                    slide["image_url"] = image_url
                    
        return structure
    
    def _update_progress(self, task_id: str, progress: int, message: str):
        """Update task progress"""
        self.tasks[task_id] = {
            "task_id": task_id,
            "status": "processing",
            "progress": progress,
            "message": message,
            "current_step": message
        }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        return self.tasks.get(task_id, {
            "task_id": task_id,
            "status": "not_found",
            "progress": 0,
            "message": "任務不存在",
            "current_step": "未找到"
        })

# Global instance
content_processor = ContentProcessor()