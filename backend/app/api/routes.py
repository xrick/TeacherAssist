# backend/app/api/routes.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import FileResponse
from typing import Optional
import uuid
import os
import shutil
from app.models import GenerateRequest, GenerateResponse, ProgressResponse, TranscriptRequest, TranscriptResponse
from app.services.content_processor import content_processor
from app.services.presenton_service import PresentonService
from app.services.zephyr_service import ZephyrService
from app.services.template_manager import TemplateManager
from app.config import get_settings

router = APIRouter()
settings = get_settings()
presenton = PresentonService()
zephyr = ZephyrService()

# Simple in-memory cache for transcripts
transcripts_cache = {}

@router.post("/generate", response_model=GenerateResponse)
async def generate_presentation(
    request: GenerateRequest,
    background_tasks: BackgroundTasks
):
    """Generate presentation from content"""
    
    task_id = str(uuid.uuid4())
    
    # Start processing in background
    background_tasks.add_task(
        content_processor.process_content,
        request.content,
        request.template.value,
        task_id,
        request.n_slides,
        request.theme.value if request.theme else None,
        request.enhance,
        request.enhancement_template,
        request.title
    )
    
    return GenerateResponse(
        task_id=task_id,
        status="processing",
        progress=0,
        message="開始處理內容..."
    )

@router.get("/progress/{task_id}", response_model=ProgressResponse)
async def get_progress(task_id: str):
    """Get generation progress"""
    
    status = content_processor.get_task_status(task_id)
    
    if status.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="任務不存在")
    
    return ProgressResponse(**status)

@router.get("/download/{presentation_id}/{format}")
async def download_presentation(presentation_id: str, format: str):
    """Download generated presentation"""
    
    if format not in ["pptx", "pdf"]:
        raise HTTPException(status_code=400, detail="不支援的格式")
    
    try:
        # Download from Presenton
        content = await presenton.download_presentation(presentation_id, format)
        
        # Save temporarily
        output_dir = settings.output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{presentation_id}.{format}"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(content)
        
        return FileResponse(
            filepath,
            media_type="application/octet-stream",
            filename=f"簡報_{presentation_id}.{format}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下載失敗: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    
    # Check Zephyr model availability
    zephyr_available = await zephyr.check_model_availability()
    
    return {
        "status": "healthy",
        "services": {
            "presenton": "connected",
            "ollama": "connected",
            "pexels": "connected",
            "zephyr": "available" if zephyr_available else "not_installed"
        }
    }

@router.post("/transcript/generate", response_model=TranscriptResponse)
async def generate_transcript(request: TranscriptRequest):
    """Generate presentation transcript using Zephyr 7B"""
    
    # Check if Zephyr model is available
    if not await zephyr.check_model_availability():
        raise HTTPException(
            status_code=503,
            detail="Transcript model not available. Please run: ollama pull phi4-mini-reasoning:3.8b"
        )
    
    # Get presentation data from content processor
    presentation_data = None
    for task_id, task_data in content_processor.tasks.items():
        if task_data.get("presentation_id") == request.presentation_id:
            presentation_data = task_data.get("presentation")
            break
    
    if not presentation_data:
        raise HTTPException(
            status_code=404,
            detail="Presentation not found. Please generate a presentation first."
        )
    
    try:
        # Generate transcript
        slides = presentation_data.get("slides", [])
        transcript_data = await zephyr.generate_transcript(
            slides=slides,
            style=request.style,
            language=request.language
        )
        
        # Cache transcript
        transcripts_cache[request.presentation_id] = transcript_data
        
        return TranscriptResponse(
            presentation_id=request.presentation_id,
            **transcript_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate transcript: {str(e)}"
        )

@router.get("/transcript/{presentation_id}/download")
async def download_transcript(presentation_id: str):
    """Download transcript as text file"""
    
    transcript_data = transcripts_cache.get(presentation_id)
    
    if not transcript_data:
        raise HTTPException(
            status_code=404,
            detail="Transcript not found. Please generate transcript first."
        )
    
    # Create text file
    output_dir = settings.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{presentation_id}_transcript.txt"
    filepath = os.path.join(output_dir, filename)
    
    # Write transcript to file
    full_transcript = transcript_data.get("full_transcript", "")
    
    # Add header
    header = f"""簡報演講稿
{'=' * 50}
投影片數量: {transcript_data.get('total_slides', 0)}
預估演講時間: {transcript_data.get('total_duration_minutes', 0)} 分鐘
{'=' * 50}

"""
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header)
        f.write(full_transcript)
    
    return FileResponse(
        filepath,
        media_type="text/plain; charset=utf-8",
        filename=f"演講稿_{presentation_id}.txt"
    )

@router.get("/transcript/{presentation_id}")
async def get_transcript(presentation_id: str):
    """Get cached transcript data"""

    transcript_data = transcripts_cache.get(presentation_id)

    if not transcript_data:
        raise HTTPException(
            status_code=404,
            detail="Transcript not found"
        )

    return transcript_data

@router.get("/presentation/{presentation_id}")
async def get_presentation_details(presentation_id: str):
    """Get complete presentation data including all slides"""

    try:
        presentation_data = await presenton.get_presentation_status(presentation_id)
        return presentation_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch presentation: {str(e)}"
        )

@router.post("/generate-with-template", response_model=GenerateResponse)
async def generate_presentation_with_template(
    background_tasks: BackgroundTasks,
    template_file: UploadFile = File(...),
    content: str = Form(...),
    title: Optional[str] = Form(None),
    template: str = Form("general"),
    language: str = Form("zh-TW"),
    n_slides: int = Form(6),
    theme: Optional[str] = Form(None),
    enhance: bool = Form(False)
):
    """Generate presentation with custom uploaded template"""

    if not template_file.filename.endswith('.pptx'):
        raise HTTPException(status_code=400, detail="只接受PPTX格式檔案")

    if len(content.strip()) < 20:
        raise HTTPException(status_code=400, detail="內容至少需要20個字元")

    try:
        template_manager = TemplateManager()

        upload_dir = template_manager.templates_dir / "uploaded"
        upload_dir.mkdir(exist_ok=True)

        template_filename = f"uploaded_{uuid.uuid4().hex[:8]}_{template_file.filename}"
        template_path = upload_dir / template_filename

        with open(template_path, "wb") as buffer:
            shutil.copyfileobj(template_file.file, buffer)

        validation_result = template_manager.validate_template(str(template_path))
        if not validation_result.get("valid"):
            os.remove(template_path)
            raise HTTPException(
                status_code=400,
                detail=f"模板驗證失敗: {validation_result.get('error', 'Unknown error')}"
            )

        task_id = str(uuid.uuid4())

        background_tasks.add_task(
            content_processor.process_content,
            content,
            template,
            task_id,
            n_slides,
            theme,
            enhance,
            str(template_path),
            title
        )

        return GenerateResponse(
            task_id=task_id,
            status="processing",
            progress=0,
            message="開始處理內容 (使用自訂模板)..."
        )

    except Exception as e:
        if 'template_path' in locals() and os.path.exists(template_path):
            os.remove(template_path)
        raise HTTPException(status_code=500, detail=f"上傳失敗: {str(e)}")