# backend/app/services/zephyr_service.py
import httpx
import logging
from typing import Dict, Any, List
from app.config import get_settings

logger = logging.getLogger(__name__)

class ZephyrService:
    """Service for generating presentation transcripts using Ollama model"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.ollama_url
        self.model = self.settings.ollama_model#"phi4-mini-reasoning:3.8b"
        logger.info(f"Initialized ZephyrService with model: {self.model}")
    async def generate_transcript(
        self,
        slides: List[Dict[str, Any]],
        style: str = "educational",
        language: str = "zh-TW"
    ) -> Dict[str, Any]:
        """Generate complete transcript for all slides"""
        
        transcripts = []
        total_duration = 0
        
        for idx, slide in enumerate(slides):
            slide_transcript = await self._generate_slide_transcript(
                slide_number=idx + 1,
                slide_data=slide,
                style=style,
                language=language
            )
            
            transcripts.append(slide_transcript)
            total_duration += slide_transcript.get("duration_seconds", 60)
        
        # Generate full transcript text
        full_transcript = self._combine_transcripts(transcripts)
        
        return {
            "total_slides": len(slides),
            "total_duration_minutes": round(total_duration / 60, 1),
            "transcripts": transcripts,
            "full_transcript": full_transcript
        }
    
    async def _generate_slide_transcript(
        self,
        slide_number: int,
        slide_data: Dict[str, Any],
        style: str,
        language: str
    ) -> Dict[str, Any]:
        """Generate transcript for a single slide"""
        
        prompt = self._build_transcript_prompt(slide_data, style, language)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 512
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
        
        transcript_text = result.get("response", "").strip()
        
        # Estimate duration based on word count (average speaking rate: 150 words/minute)
        word_count = len(transcript_text.split())
        duration_seconds = max(30, int((word_count / 150) * 60))
        
        return {
            "slide_number": slide_number,
            "title": slide_data.get("title", f"Slide {slide_number}"),
            "transcript": transcript_text,
            "duration_seconds": duration_seconds
        }
    
    def _build_transcript_prompt(
        self,
        slide_data: Dict[str, Any],
        style: str,
        language: str
    ) -> str:
        """Build prompt for transcript generation"""
        
        title = slide_data.get("title", "")
        content = slide_data.get("content", [])
        slide_type = slide_data.get("type", "content")
        
        style_instructions = {
            "formal": "使用正式、專業的語言風格，適合商業或學術演講",
            "conversational": "使用輕鬆、對話式的語言風格，容易理解",
            "educational": "使用清晰、教學式的語言風格，循序漸進地解釋"
        }
        
        style_desc = style_instructions.get(style, style_instructions["educational"])
        
        content_text = "\n".join([f"- {item}" for item in content]) if content else "無具體內容"
        
        if slide_type == "title":
            prompt = f"""你是一位專業的演講者。請為以下標題投影片撰寫開場白的演講稿。

投影片標題: {title}

要求:
1. 語言: 繁體中文 (台灣)
2. 風格: {style_desc}
3. 長度: 30-60秒的演講內容
4. 包含: 歡迎詞、主題介紹、簡短的吸引力開場
5. 語氣: 熱情、專業、吸引聽眾注意

請直接輸出演講稿，不要有其他說明文字。"""

        elif slide_type == "overview":
            prompt = f"""你是一位專業的演講者。請為以下概述投影片撰寫演講稿。

投影片標題: {title}
投影片內容:
{content_text}

要求:
1. 語言: 繁體中文 (台灣)
2. 風格: {style_desc}
3. 長度: 60-90秒的演講內容
4. 包含: 清楚說明每個重點的概要
5. 結構: 先總結全貌，再逐一簡介各重點

請直接輸出演講稿，不要有其他說明文字。"""

        elif slide_type == "conclusion":
            prompt = f"""你是一位專業的演講者。請為以下結論投影片撰寫演講稿。

投影片標題: {title}
投影片內容:
{content_text}

要求:
1. 語言: 繁體中文 (台灣)
2. 風格: {style_desc}
3. 長度: 40-70秒的演講內容
4. 包含: 總結重點、行動呼籲、感謝詞
5. 結尾: 有力且令人印象深刻

請直接輸出演講稿，不要有其他說明文字。"""

        else:  # content slides
            prompt = f"""你是一位專業的演講者。請為以下內容投影片撰寫演講稿。

投影片標題: {title}
投影片內容:
{content_text}

要求:
1. 語言: 繁體中文 (台灣)
2. 風格: {style_desc}
3. 長度: 60-120秒的演講內容
4. 詳細解釋每個要點，使用例子或比喻幫助理解
5. 保持邏輯連貫，從一個點自然過渡到下一個點
6. 使用「首先」「接著」「此外」「最後」等連接詞

請直接輸出演講稿，不要有其他說明文字。"""
        
        return prompt
    
    def _combine_transcripts(self, transcripts: List[Dict[str, Any]]) -> str:
        """Combine all slide transcripts into full transcript"""
        
        full_text = []
        
        for t in transcripts:
            slide_num = t["slide_number"]
            title = t["title"]
            transcript = t["transcript"]
            duration = t["duration_seconds"]
            
            full_text.append(f"【投影片 {slide_num}: {title}】")
            full_text.append(f"[預估時間: {duration}秒]")
            full_text.append(transcript)
            full_text.append("")  # Empty line between slides
        
        return "\n".join(full_text)
    
    async def check_model_availability(self) -> bool:
        """Check if transcript model is available"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                
                models = data.get("models", [])
                for model in models:
                    name = model.get("name", "").lower()
                    if "phi4-mini-reasoning:3.8b" in name or "phi4-mini" in name:
                        return True
                
                return False
        except Exception as e:
            print(f"Error checking transcript model: {e}")
            return False
    
    async def download_model_if_needed(self) -> bool:
        """Download transcript model if not available"""
        
        if await self.check_model_availability():
            return True
        
        try:
            print("Downloading phi4-mini-reasoning:3.8b model... This may take a few minutes.")
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": "phi4-mini-reasoning:3.8b"}
                )
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Error downloading transcript model: {e}")
            return False