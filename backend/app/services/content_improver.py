# backend/app/services/content_improver.py
import httpx
import json
import logging
from typing import List, Dict, Any, Optional
from app.config import get_settings
from app.services.pptx_analyzer import SlideData

logger = logging.getLogger(__name__)


class ImprovedSlideData(SlideData):
    """Extended SlideData with improved content"""
    def __init__(self, original_slide: SlideData):
        super().__init__(
            index=original_slide.index,
            title=original_slide.title,
            content=original_slide.content,
            layout=original_slide.layout,
            has_image=original_slide.has_image,
            images=original_slide.images,
            speaker_notes=original_slide.speaker_notes
        )
        self.improved_title: Optional[str] = None
        self.improved_content: Optional[List[str]] = None
        self.improvement_applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "improved_title": self.improved_title,
            "improved_content": self.improved_content,
            "improvement_applied": self.improvement_applied
        })
        return base_dict


class ContentImprover:
    """LLM-based content improvement service using Ollama phi4-mini-reasoning"""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.ollama_url
        self.model = "phi4-mini-reasoning:3.8b"
        self.logger = logger

    async def improve_slides_batch(
        self,
        slides: List[SlideData],
        topic: str,
        options: Optional[Dict[str, bool]] = None
    ) -> List[ImprovedSlideData]:
        """
        Improve all slides in batch for better context coherence

        Args:
            slides: List of parsed slide data
            topic: Presentation topic for context
            options: Improvement options (improve_content, add_transitions)

        Returns:
            List of ImprovedSlideData with enhanced content
        """
        options = options or {"improve_content": True, "add_transitions": False}

        improved_slides = []
        for slide in slides:
            improved_slide = ImprovedSlideData(slide)
            improved_slides.append(improved_slide)

        if not options.get("improve_content", True):
            self.logger.info("Content improvement disabled, returning original slides")
            return improved_slides

        try:
            context_summary = self._build_context_summary(slides, topic)

            for i, slide in enumerate(slides):
                self.logger.info(f"Improving slide {i+1}/{len(slides)}: {slide.title}")

                improved_data = await self._improve_single_slide(
                    slide=slide,
                    topic=topic,
                    context=context_summary
                )

                if improved_data:
                    improved_slides[i].improved_title = improved_data.get("title", slide.title)
                    improved_slides[i].improved_content = improved_data.get("points", slide.content)
                    improved_slides[i].improvement_applied = True
                else:
                    self.logger.warning(f"Failed to improve slide {i}, using original content")
                    improved_slides[i].improved_title = slide.title
                    improved_slides[i].improved_content = slide.content
                    improved_slides[i].improvement_applied = False

            if options.get("add_transitions", False):
                improved_slides = self._add_transitions(improved_slides)

            self.logger.info(f"Successfully improved {sum(s.improvement_applied for s in improved_slides)}/{len(slides)} slides")
            return improved_slides

        except Exception as e:
            self.logger.error(f"Batch improvement failed: {e}, returning original content")
            return improved_slides

    async def _improve_single_slide(
        self,
        slide: SlideData,
        topic: str,
        context: str
    ) -> Optional[Dict[str, Any]]:
        """
        Improve single slide content using LLM

        Args:
            slide: Slide to improve
            topic: Presentation topic
            context: Overall presentation context

        Returns:
            Improved slide data dict or None on failure
        """
        prompt = self._build_improvement_prompt(slide, topic, context)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9
                        },
                        "format": "json"
                    }
                )
                response.raise_for_status()
                result = response.json()

            llm_response = result.get("response", "")
            return self._parse_improvement_response(llm_response, slide)

        except httpx.HTTPStatusError as e:
            self.logger.error(f"Ollama API error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to improve slide: {e}")
            return None

    def _build_improvement_prompt(self, slide: SlideData, topic: str, context: str) -> str:
        """Build prompt for content improvement"""
        content_text = "\n".join(slide.content) if slide.content else "（無內容）"

        return f"""你是專業的簡報內容優化專家。請改進以下投影片內容。

主題：{topic}

簡報整體結構：
{context}

當前投影片 #{slide.index + 1}:
標題：{slide.title}
內容：
{content_text}

要求：
1. 標題簡潔有力（8-15字）
2. 內容改寫為 3-5 個要點
3. 每個要點 1-2 句話，清晰易懂
4. 確保內容切題、準確、專業
5. 使用繁體中文
6. 保持與整體簡報的邏輯連貫性

請以 JSON 格式回覆：
{{
  "title": "改進後的標題",
  "points": [
    "要點 1",
    "要點 2",
    "要點 3"
  ]
}}

只返回 JSON，不要其他文字。"""

    def _build_context_summary(self, slides: List[SlideData], topic: str) -> str:
        """Build overall presentation context summary"""
        context_lines = [f"主題：{topic}", ""]

        for i, slide in enumerate(slides):
            context_lines.append(f"投影片 {i+1}: {slide.title}")
            if slide.content:
                for content in slide.content[:2]:
                    context_lines.append(f"  - {content[:50]}...")

        return "\n".join(context_lines)

    def _parse_improvement_response(
        self,
        llm_response: str,
        original_slide: SlideData
    ) -> Optional[Dict[str, Any]]:
        """
        Parse LLM improvement response with fallback strategies

        Args:
            llm_response: Raw LLM response
            original_slide: Original slide for fallback

        Returns:
            Parsed improvement data or None
        """
        try:
            data = json.loads(llm_response)

            if not isinstance(data, dict) or "title" not in data or "points" not in data:
                raise ValueError("Invalid JSON structure")

            title = data["title"].strip()
            points = data["points"]

            if not isinstance(points, list) or len(points) == 0:
                raise ValueError("Points must be non-empty list")

            title_length = len(title)
            if title_length < 3 or title_length > 30:
                self.logger.warning(f"Title length {title_length} out of recommended range (8-15)")

            points_count = len(points)
            if points_count < 3 or points_count > 5:
                self.logger.warning(f"Points count {points_count} out of recommended range (3-5)")

            return {
                "title": title,
                "points": [p.strip() for p in points]
            }

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing failed: {e}")
            return self._regex_fallback_parse(llm_response, original_slide)
        except Exception as e:
            self.logger.error(f"Response validation failed: {e}")
            return None

    def _regex_fallback_parse(
        self,
        response: str,
        original_slide: SlideData
    ) -> Optional[Dict[str, Any]]:
        """Fallback: extract title and points using regex"""
        import re

        try:
            title_match = re.search(r'"title"\s*:\s*"([^"]+)"', response)
            points_match = re.findall(r'"([^"]+)"', response)

            if title_match and len(points_match) > 1:
                title = title_match.group(1)
                points = [p for p in points_match if p != title][:5]

                if len(points) >= 3:
                    self.logger.info("Successfully parsed using regex fallback")
                    return {"title": title, "points": points}

        except Exception as e:
            self.logger.error(f"Regex fallback failed: {e}")

        return None

    def _add_transitions(self, slides: List[ImprovedSlideData]) -> List[ImprovedSlideData]:
        """
        Add transition sentences between slides (optional feature)

        Args:
            slides: List of improved slides

        Returns:
            Slides with transition notes added
        """
        for i in range(len(slides) - 1):
            current = slides[i]
            next_slide = slides[i + 1]

            current_title = current.improved_title or current.title
            next_title = next_slide.improved_title or next_slide.title

            transition = f"接下來，我們將探討「{next_title}」的相關內容。"

            if current.improved_content:
                current.improved_content.append(f"\n[過渡句] {transition}")
            elif current.content:
                current.improved_content = current.content + [f"\n[過渡句] {transition}"]

        return slides

    def validate_improvement(
        self,
        original: SlideData,
        improved: ImprovedSlideData
    ) -> Dict[str, Any]:
        """
        Validate improvement quality

        Args:
            original: Original slide
            improved: Improved slide

        Returns:
            Quality score and metrics
        """
        score = {
            "title_length_ok": False,
            "points_count_ok": False,
            "content_changed": False,
            "overall_score": 0.0
        }

        if improved.improved_title:
            title_len = len(improved.improved_title)
            score["title_length_ok"] = 8 <= title_len <= 15

        if improved.improved_content:
            points_count = len(improved.improved_content)
            score["points_count_ok"] = 3 <= points_count <= 5
            score["content_changed"] = improved.improved_content != original.content

        passed_checks = sum([
            score["title_length_ok"],
            score["points_count_ok"],
            score["content_changed"]
        ])
        score["overall_score"] = passed_checks / 3.0

        return score
