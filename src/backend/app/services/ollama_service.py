import httpx
from typing import List, Dict, Any
from app.config import get_settings

class OllamaService:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.ollama_url
        self.model = self.settings.ollama_model
        
    async def analyze_content(self, content: str, template: str) -> Dict[str, Any]:
        """Analyze content and generate presentation structure"""
        
        prompt = self._build_prompt(content, template)
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            
        return self._parse_response(result.get("response", ""))
    
    def _build_prompt(self, content: str, template: str) -> str:
        """Build prompt for LLM"""
        
        template_instructions = {
            "administrative": "專業、正式、結構化的行政簡報風格",
            "educational": "清晰、教學導向、易於理解的教學簡報風格",
            "general": "靈活、通用、視覺化的一般簡報風格"
        }
        
        style = template_instructions.get(template, template_instructions["general"])
        
        return f"""你是一個專業的簡報內容分析師。請分析以下內容並生成簡報結構。

內容:
{content}

簡報風格: {style}

請按照以下JSON格式輸出簡報結構:
{{
    "title": "簡報主標題",
    "slides": [
        {{
            "title": "投影片標題",
            "type": "title|overview|content|conclusion",
            "content": ["重點1", "重點2", "重點3"],
            "image_query": "相關圖片搜尋關鍵字(英文)"
        }}
    ]
}}

要求:
1. 生成4-8張投影片
2. 第一張必須是標題頁 (type: "title")
3. 第二張必須是概述 (type: "overview")
4. 最後一張必須是結論 (type: "conclusion")
5. 中間是內容頁 (type: "content")
6. 每張投影片的content包含2-4個重點
7. 為每張投影片提供合適的英文圖片搜尋關鍵字

只返回JSON,不要有其他文字。"""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response"""
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback: generate basic structure
        return {
            "title": "教學簡報",
            "slides": [
                {"title": "標題頁", "type": "title", "content": [], "image_query": "education presentation"},
                {"title": "概述", "type": "overview", "content": ["主題介紹", "學習目標"], "image_query": "overview learning"},
                {"title": "重點內容", "type": "content", "content": ["重點一", "重點二", "重點三"], "image_query": "teaching classroom"},
                {"title": "結論", "type": "conclusion", "content": ["總結", "下一步"], "image_query": "conclusion success"}
            ]
        }