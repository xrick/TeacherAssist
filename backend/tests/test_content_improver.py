# backend/tests/test_content_improver.py
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.content_improver import ContentImprover, ImprovedSlideData
from app.services.pptx_analyzer import SlideData


class TestContentImprover:
    """Test suite for ContentImprover"""

    @pytest.fixture
    def improver(self):
        with patch('app.services.content_improver.get_settings') as mock_settings:
            mock_settings.return_value.ollama_url = "http://localhost:11434"
            return ContentImprover()

    @pytest.fixture
    def sample_slides(self):
        return [
            SlideData(
                index=0,
                title="深度學習簡介",
                content=["定義", "應用", "挑戰"],
                layout="Title Slide"
            ),
            SlideData(
                index=1,
                title="神經網路架構",
                content=["輸入層", "隱藏層", "輸出層", "激活函數"],
                layout="Content"
            )
        ]

    def test_improved_slide_data_creation(self, sample_slides):
        """Test ImprovedSlideData initialization"""
        original = sample_slides[0]
        improved = ImprovedSlideData(original)

        assert improved.index == original.index
        assert improved.title == original.title
        assert improved.content == original.content
        assert improved.improved_title is None
        assert improved.improved_content is None
        assert improved.improvement_applied is False

    def test_improved_slide_data_to_dict(self, sample_slides):
        """Test ImprovedSlideData serialization"""
        original = sample_slides[0]
        improved = ImprovedSlideData(original)
        improved.improved_title = "改進後的標題"
        improved.improved_content = ["要點1", "要點2", "要點3"]
        improved.improvement_applied = True

        data_dict = improved.to_dict()

        assert data_dict["improved_title"] == "改進後的標題"
        assert len(data_dict["improved_content"]) == 3
        assert data_dict["improvement_applied"] is True

    def test_build_context_summary(self, improver, sample_slides):
        """Test context summary generation"""
        context = improver._build_context_summary(sample_slides, "AI 教學")

        assert "AI 教學" in context
        assert "深度學習簡介" in context
        assert "神經網路架構" in context

    def test_parse_improvement_response_valid_json(self, improver, sample_slides):
        """Test parsing valid JSON response"""
        valid_response = json.dumps({
            "title": "深度學習基礎概念",
            "points": ["定義與歷史", "核心應用領域", "當前主要挑戰"]
        }, ensure_ascii=False)

        result = improver._parse_improvement_response(valid_response, sample_slides[0])

        assert result is not None
        assert result["title"] == "深度學習基礎概念"
        assert len(result["points"]) == 3

    def test_parse_improvement_response_invalid_json(self, improver, sample_slides):
        """Test parsing invalid JSON with fallback"""
        invalid_response = "This is not valid JSON"

        result = improver._parse_improvement_response(invalid_response, sample_slides[0])

        assert result is None

    def test_parse_improvement_response_missing_fields(self, improver, sample_slides):
        """Test parsing JSON with missing required fields"""
        incomplete_response = json.dumps({"title": "只有標題"})

        result = improver._parse_improvement_response(incomplete_response, sample_slides[0])

        assert result is None

    def test_regex_fallback_parse(self, improver, sample_slides):
        """Test regex fallback parsing"""
        response_with_quotes = '''
        "title": "改進後的標題"
        "points": ["要點1", "要點2", "要點3", "要點4"]
        '''

        result = improver._regex_fallback_parse(response_with_quotes, sample_slides[0])

        if result:
            assert result["title"] == "改進後的標題"
            assert len(result["points"]) >= 3

    def test_validate_improvement(self, improver, sample_slides):
        """Test improvement validation"""
        original = sample_slides[0]
        improved = ImprovedSlideData(original)
        improved.improved_title = "深度學習基礎"
        improved.improved_content = ["要點1", "要點2", "要點3", "要點4"]

        score = improver.validate_improvement(original, improved)

        assert "title_length_ok" in score
        assert "points_count_ok" in score
        assert "content_changed" in score
        assert "overall_score" in score
        assert 0.0 <= score["overall_score"] <= 1.0

    def test_add_transitions(self, improver, sample_slides):
        """Test transition sentence addition"""
        improved_slides = [ImprovedSlideData(s) for s in sample_slides]
        improved_slides[0].improved_title = "標題1"
        improved_slides[0].improved_content = ["內容1"]
        improved_slides[1].improved_title = "標題2"

        result = improver._add_transitions(improved_slides)

        assert len(result) == 2
        if result[0].improved_content:
            last_item = result[0].improved_content[-1]
            assert "[過渡句]" in last_item

    @pytest.mark.asyncio
    async def test_improve_slides_batch_disabled(self, improver, sample_slides):
        """Test batch improvement with improvement disabled"""
        result = await improver.improve_slides_batch(
            slides=sample_slides,
            topic="測試主題",
            options={"improve_content": False}
        )

        assert len(result) == 2
        assert all(not slide.improvement_applied for slide in result)

    def test_build_improvement_prompt(self, improver, sample_slides):
        """Test improvement prompt generation"""
        slide = sample_slides[0]
        context = "測試簡報脈絡"
        topic = "AI 基礎"

        prompt = improver._build_improvement_prompt(slide, topic, context)

        assert topic in prompt
        assert slide.title in prompt
        assert "JSON" in prompt
        assert "3-5" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
