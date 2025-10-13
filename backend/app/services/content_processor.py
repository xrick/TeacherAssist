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
            # Step 1: Analyze content (20%)
            self._update_progress(task_id, 20, "正在分析內容結構...")
            structure = await self.ollama.analyze_content(content, template)
            
            # Step 2: Identify key topics (40%)
            self._update_progress(task_id, 40, "正在識別關鍵主題...")
            await asyncio.sleep(0.5)
            
            # Step 3: Fetch images (60%)
            self._update_progress(task_id, 60, "正在建立投影片佈局...")
            structure = await self._enrich_with_images(structure)
            
            # Step 4: Generate presentation (80%)
            self._update_progress(task_id, 80, "正在生成內容...")
            presentation = await self.presenton.create_presentation(structure, template)
            
            # Step 5: Finalize (100%)
            self._update_progress(task_id, 100, "正在完成簡報...")
            
            presentation_id = presentation.get("id", str(uuid.uuid4()))
            
            result = {
                "task_id": task_id,
                "status": "completed",
                "progress": 100,
                "message": "簡報生成完成",
                "current_step": "完成",
                "presentation": structure,
                "presentation_id": presentation_id,
                "download_url": f"/api/download/{presentation_id}/pptx",
                "pdf_url": f"/api/download/{presentation_id}/pdf"
            }
            
            self.tasks[task_id] = result
            return result
            
        except Exception as e:
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