import uuid
import asyncio
import io
from typing import Dict, Any, Optional
from app.services.ollama_service import OllamaService
from app.services.pexels_service import PexelsService
from app.services.presenton_service import PresentonService
from app.services.pptx_analyzer import PythonPptxAnalyzer
from app.services.content_improver import ContentImprover
from app.services.presentation_rebuilder import PresentationRebuilder
from app.services.template_manager import TemplateManager

class ContentProcessor:
    def __init__(self):
        self.ollama = OllamaService()
        self.pexels = PexelsService()
        self.presenton = PresentonService()
        self.tasks = {}

        self.analyzer = PythonPptxAnalyzer()
        self.improver = ContentImprover()
        self.rebuilder = PresentationRebuilder()
        self.template_manager = TemplateManager()
        
    async def process_content(
        self,
        content: str,
        template: str,
        task_id: str,
        n_slides: int = 6,
        theme: str = None,
        enhance: bool = False,
        enhancement_template: Optional[str] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process content and generate presentation

        Args:
            content: Input text content
            template: Template style (general, modern, standard, swift)
            task_id: Unique task identifier
            n_slides: Number of slides to generate (user-specified, default 6)
            theme: Theme style (edge-yellow, mint-blue, light-rose, professional-blue, professional-dark)
            enhance: Enable quality enhancement pipeline (default: False)
            enhancement_template: PPTX template for enhancement (default: auto-select from template_manager)
            title: Presentation title (optional, max 50 chars)
        """

        try:
            # Step 1: Prepare content (20%)
            self._update_progress(task_id, 20, "正在準備內容...")
            await asyncio.sleep(0.5)

            # Step 2: Send to Presenton (40%)
            self._update_progress(task_id, 40, "正在發送給簡報生成引擎...")

            # Step 3: Generate presentation using Presenton (60-90%)
            self._update_progress(task_id, 60, "正在生成簡報...")

            # Presenton handles everything: content analysis, layout, images, generation
            # Note: n_slides is user-specified, validated against template constraints in presenton_service
            presentation_result = await self.presenton.create_presentation(
                content=content,
                n_slides=n_slides,  # User-specified slide count (validated against template)
                template_id=template,  # Template style (general, modern, standard, swift)
                theme_id=theme,  # Theme style (edge-yellow, mint-blue, etc.)
                title=title  # User-provided title (optional)
            )

            # Step 4: Enhancement Pipeline (Optional, 90-100%)
            if enhance:
                await self._apply_enhancement_pipeline(
                    task_id=task_id,
                    presentation_id=presentation_id,
                    presentation_result=presentation_result,
                    enhancement_template=enhancement_template
                )

            # Step 5: Finalize (100%)
            self._update_progress(task_id, 100, "簡報生成完成...")

            # Extract presentation data from Presenton response
            # Presenton /generate returns: {presentation_path, edit_page_path, presentation_id}
            presentation_id = presentation_result.get("presentation_id")
            if not presentation_id:
                # Fallback: extract from paths
                pres_path = presentation_result.get("presentation_path", "")
                presentation_id = pres_path.split("/")[-1].replace(".pptx", "") if pres_path else str(uuid.uuid4())

            # Fetch full presentation details including slides
            presentation_details = await self.presenton.get_presentation_status(presentation_id)

            # Extract slides from Presenton response and convert to our format
            presenton_slides = presentation_details.get("slides", [])
            slides = []
            for slide in presenton_slides:
                slide_content = slide.get("content", {})
                slides.append({
                    "title": slide_content.get("title", ""),
                    "type": "content",  # Presenton doesn't specify type, default to content
                    "content": self._extract_slide_content(slide_content),
                    "image_query": slide_content.get("image", {}).get("__image_prompt__", ""),
                    "image_url": slide_content.get("image", {}).get("__image_url__", "")
                })

            result = {
                "task_id": task_id,
                "status": "completed",
                "progress": 100,
                "message": "簡報生成完成",
                "current_step": "完成",
                "presentation": {
                    "title": presentation_details.get("title", "AI生成簡報"),
                    "slides": slides,
                    "template": template  # Add template field for Pydantic validation
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
    
    async def _apply_enhancement_pipeline(
        self,
        task_id: str,
        presentation_id: str,
        presentation_result: Dict[str, Any],
        enhancement_template: Optional[str] = None
    ):
        """Apply 3-stage enhancement pipeline to improve PPTX quality

        Stages:
        1. Parse (90%): Extract slide data from Presenton PPTX
        2. Improve (93%): Enhance content with LLM
        3. Rebuild (96%): Generate new PPTX with template and improvements
        """
        try:
            # Stage 1: Parse Presenton PPTX (90%)
            self._update_progress(task_id, 90, "正在解析簡報結構...")

            pptx_bytes = await self.presenton.download_presentation(presentation_id, "pptx")
            slides_data = self.analyzer.parse_presentation(pptx_bytes)

            # Stage 2: Improve content with LLM (93%)
            self._update_progress(task_id, 93, "正在優化內容品質...")

            presentation_details = await self.presenton.get_presentation_status(presentation_id)
            topic = presentation_details.get("title", "簡報")
            improved_slides = await self.improver.improve_slides_batch(slides_data, topic)

            # Stage 3: Rebuild with template (96%)
            self._update_progress(task_id, 96, "正在重建簡報...")

            if not enhancement_template:
                enhancement_template = self.template_manager.get_recommended_template("educational")

            if enhancement_template:
                from pathlib import Path
                template_path = self.template_manager.templates_dir / enhancement_template
                enhanced_pptx_bytes = self.rebuilder.rebuild_presentation(
                    improved_slides,
                    template_path=str(template_path)
                )
            else:
                enhanced_pptx_bytes = self.rebuilder.rebuild_presentation(
                    improved_slides,
                    template_path=None
                )

            # Replace original PPTX in output directory
            import os
            from app.config import get_settings
            settings = get_settings()
            output_dir = settings.output_dir
            os.makedirs(output_dir, exist_ok=True)

            enhanced_filepath = os.path.join(output_dir, f"{presentation_id}_enhanced.pptx")
            with open(enhanced_filepath, "wb") as f:
                f.write(enhanced_pptx_bytes)

            self._update_progress(task_id, 99, "品質增強完成...")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self._update_progress(task_id, 90, f"品質增強失敗: {str(e)}")

    def _extract_slide_content(self, slide_content: Dict[str, Any]) -> list:
        """Extract bullet points or content from Presenton slide"""
        content = []

        # Extract from bulletPoints if available
        bullet_points = slide_content.get("bulletPoints", [])
        for bullet in bullet_points:
            if isinstance(bullet, dict):
                title = bullet.get("title", "")
                description = bullet.get("description", "")
                # Combine title and description if both exist
                if title and description:
                    content.append(f"{title}: {description}")
                elif title:
                    content.append(title)
                elif description:
                    content.append(description)
            elif isinstance(bullet, str):
                content.append(bullet)

        # If no bullet points, try to get description
        if not content:
            description = slide_content.get("description", "")
            if description:
                content.append(description)

        return content

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