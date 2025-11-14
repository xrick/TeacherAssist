# backend/app/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

class TemplateType(str, Enum):
    GENERAL = "general"
    MODERN = "modern"
    STANDARD = "standard"
    SWIFT = "swift"

class ThemeType(str, Enum):
    EDGE_YELLOW = "edge-yellow"
    MINT_BLUE = "mint-blue"
    LIGHT_ROSE = "light-rose"
    PROFESSIONAL_BLUE = "professional-blue"
    PROFESSIONAL_DARK = "professional-dark"

class GenerateRequest(BaseModel):
    content: str = Field(..., min_length=20, description="Input content for presentation (minimum 20 characters)")
    title: Optional[str] = Field(default=None, max_length=50, description="Presentation title (optional, max 50 chars)")
    template: TemplateType = Field(default=TemplateType.GENERAL, description="Presentation template style")
    theme: Optional[ThemeType] = Field(default=None, description="Presentation theme (optional)")
    language: str = Field(default="zh-TW", description="Content language")
    n_slides: int = Field(default=6, ge=3, le=12, description="Number of slides to generate (3-12)")
    enhance: bool = Field(default=False, description="Enable quality enhancement pipeline (3-stage: parse + improve + rebuild)")
    enhancement_template: Optional[str] = Field(default=None, description="PPTX template filename for enhancement (auto-select if not provided)")

class SlideContent(BaseModel):
    title: str
    type: Literal["title", "overview", "content", "conclusion"]
    content: Optional[List[str]] = []
    image_query: Optional[str] = None
    image_url: Optional[str] = None

class PresentationStructure(BaseModel):
    title: str
    slides: List[SlideContent]
    template: TemplateType

class GenerateResponse(BaseModel):
    task_id: str
    status: Literal["processing", "completed", "failed"]
    progress: int = Field(ge=0, le=100)
    message: str
    presentation: Optional[PresentationStructure] = None
    presentation_id: Optional[str] = None
    download_url: Optional[str] = None
    pdf_url: Optional[str] = None

class ProgressResponse(BaseModel):
    task_id: str
    status: Literal["processing", "completed", "failed"]
    progress: int
    message: str
    current_step: str
    presentation: Optional[PresentationStructure] = None
    presentation_id: Optional[str] = None

class TranscriptRequest(BaseModel):
    presentation_id: str
    language: str = Field(default="zh-TW", description="Transcript language")
    style: Literal["formal", "conversational", "educational"] = Field(
        default="educational",
        description="Transcript speaking style"
    )

class SlideTranscript(BaseModel):
    slide_number: int
    title: str
    transcript: str
    duration_seconds: int

class TranscriptResponse(BaseModel):
    presentation_id: str
    total_slides: int
    total_duration_minutes: float  # Changed from int to float to support fractional minutes (e.g., 2.5 mins)
    transcripts: List[SlideTranscript]
    full_transcript: str