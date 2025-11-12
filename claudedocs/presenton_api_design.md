# Presenton API Complete Reference and TeacherAssist Integration Design

## API Overview

**Base URL**: `https://api.presenton.ai`
**Authentication**: Bearer token via `Authorization: Bearer sk-presenton-xxxxxxxx`

## Complete API Endpoint Catalog

### 1. Presentation Generation

#### 1.1 Generate Presentation (Synchronous)
```
POST /api/v1/ppt/presentation/generate
```

**Request Parameters**:
- **Core Content**:
  - `content` (string, optional): Raw text for presentation generation
  - `slides_markdown` (array, optional): Pre-formatted slide content in markdown
  - `instructions` (string, optional): Custom directions for generation

- **Presentation Settings**:
  - `n_slides` (integer, default: 8): Desired slide count
  - `language` (string, default: English): Output language
  - `theme` (string, optional): edge-yellow, light-rose, mint-blue, professional-blue, professional-dark
  - `template` (string, default: general): general, modern, standard, swift

- **Content Formatting**:
  - `tone` (string, default: default): casual, professional, funny, educational, sales_pitch
  - `verbosity` (string, default: standard): concise, standard, text-heavy
  - `markdown_emphasis` (boolean, default: true): Enable markdown styling
  - `include_title_slide` (boolean, default: true): Add opening slide
  - `include_table_of_contents` (boolean, default: false): Add overview slide

- **Media & Search**:
  - `image_type` (string, default: stock): stock or ai-generated
  - `web_search` (boolean, default: false): Enable online research
  - `files` (array, optional): Uploaded file identifiers

- **Output**:
  - `export_as` (string, default: pptx): pptx or pdf
  - `trigger_webhook` (boolean, default: false): Activate webhook notifications

**Response (200)**:
```json
{
  "presentation_id": "UUID",
  "path": "download_url",
  "edit_path": "editor_url",
  "credits_consumed": number
}
```

**TeacherAssist Current Usage**: ✅ IMPLEMENTED
- Uses: content, n_slides, language, theme, template, export_as
- Location: `backend/app/services/presenton_service.py::create_presentation()`
- Maps to: GenerateRequest model in `backend/app/models.py`

**Enhancement Opportunities**:
- Add tone selection (educational, professional)
- Enable include_table_of_contents option
- Support web_search for enriched content
- Allow verbosity control (concise for quick summaries)

---

#### 1.2 Generate Presentation (Asynchronous)
```
POST /api/v1/ppt/presentation/generate/async
```

**Request**: Same parameters as synchronous endpoint

**Response**: Returns task_id for status polling

**Status Tracking**:
```
GET /api/v1/ppt/presentation/status/{task_id}
```

**TeacherAssist Current Usage**: ❌ NOT USED
- Current implementation uses synchronous generation only
- Could improve UX for large presentations by switching to async

---

### 2. Presentation Retrieval

#### 2.1 Get All User Presentations
```
GET /api/v1/ppt/presentation/all?page=1&page_size=10
```

**Query Parameters**:
- `page` (integer, optional, default: 1): Current page number
- `page_size` (integer, optional, default: 10): Results per page

**Response (200)**:
```json
{
  "total_pages": number,
  "page": number,
  "page_size": number,
  "results": [PresentationObject...]
}
```

**TeacherAssist Current Usage**: ❌ NOT USED
- Could add presentation history/library feature
- Enable users to browse previously generated presentations

---

#### 2.2 Get Presentation and Slides by ID ⭐
```
GET /api/v1/ppt/presentation/{id}
```

**Path Parameter**:
- `id` (UUID string, required): Presentation identifier

**Response (200)** - `PresentationWithSlides` object:
```json
{
  "id": "UUID",
  "user": "string",
  "n_slides": number,
  "language": "string",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "content": "string (optional)",
  "title": "string (optional)",
  "tone": "string (optional)",
  "verbosity": "string (optional)",
  "theme": "string (optional)",
  "slides": [
    {
      "id": "UUID",
      "presentation": "UUID",
      "layout_group": "string",
      "layout": "string",
      "index": number,
      "content": "object",
      "html_content": "string",
      "properties": "object",
      "speaker_note": "string (optional)"
    }
  ]
}
```

**TeacherAssist Current Usage**: 🔨 PARTIALLY IMPLEMENTED
- Presenton service has `get_presentation_status()` method
- ❌ Not exposed via backend API endpoint
- ❌ Not used in frontend for detailed slide preview

**PRIORITY IMPLEMENTATION TARGET**: This endpoint is crucial for implementing the slide details preview feature.

---

#### 2.3 Delete Presentation by ID
```
DELETE /api/v1/ppt/presentation/{id}
```

**TeacherAssist Current Usage**: ❌ NOT USED
- Could add cleanup feature for old presentations

---

### 3. Template Management

#### 3.1 Get All Templates
```
GET /api/v1/ppt/template/all
```

**Response (200)**:
```json
[
  {
    "id": "string",
    "name": "string"
  }
]
```

**TeacherAssist Current Usage**: ❌ NOT USED (Hardcoded)
- Current: Hardcoded template enum in models.py
- Enhancement: Fetch dynamic template list from API
- Benefit: Always show latest available templates

---

#### 3.2 Get Template by ID
```
GET /api/v1/ppt/template/{id}
```

**TeacherAssist Current Usage**: ❌ NOT USED

---

#### 3.3 Get Template Example
```
GET /api/v1/ppt/template/{id}/example
```

**TeacherAssist Current Usage**: ❌ NOT USED
- Could show template previews in UI dropdown

---

### 4. Images

#### 4.1 Get Uploaded Images
```
GET /api/v1/ppt/images/uploaded
```

**TeacherAssist Current Usage**: ❌ NOT USED

---

#### 4.2 Upload Image
```
POST /api/v1/ppt/images/upload
```

**TeacherAssist Current Usage**: ❌ NOT USED
- Current: Uses Pexels API for stock images
- Enhancement: Allow user-uploaded custom images

---

#### 4.3 Delete Uploaded Image by ID
```
DELETE /api/v1/ppt/images/{id}
```

**TeacherAssist Current Usage**: ❌ NOT USED

---

### 5. Files

#### 5.1 Upload Files
```
POST /api/v1/ppt/files/upload
```

**TeacherAssist Current Usage**: ❌ NOT USED
- Enhancement: Allow PDF/DOCX upload as content source
- Benefit: Teachers can convert existing materials

---

### 6. Webhooks

#### 6.1 Subscribe to Webhook
```
POST /api/v1/webhook/subscribe
```

**TeacherAssist Current Usage**: ❌ NOT USED

---

#### 6.2 Unsubscribe to Webhook
```
DELETE /api/v1/webhook/unsubscribe
```

**TeacherAssist Current Usage**: ❌ NOT USED

---

## Current TeacherAssist Integration Map

### Backend Service Layer

**File**: `backend/app/services/presenton_service.py`

```python
class PresentonService:
    async def create_presentation(
        self,
        content: str,
        n_slides: int = 6,
        template_id: Optional[str] = None,
        theme_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Maps to: POST /api/v1/ppt/presentation/generate"""

    async def get_presentation_status(
        self,
        presentation_id: str
    ) -> Dict[str, Any]:
        """Maps to: GET /api/v1/ppt/presentation/{id}"""
        # ⚠️ Exists but not exposed via backend API

    async def download_presentation(
        self,
        presentation_id: str,
        format: str
    ) -> bytes:
        """Downloads from path returned by generate endpoint"""
```

### Backend API Routes

**File**: `backend/app/api/routes.py`

```python
@router.post("/generate")
# Uses: PresentonService.create_presentation()

@router.get("/download/{presentation_id}/{format}")
# Uses: PresentonService.download_presentation()

# ❌ MISSING: GET /presentation/{id} endpoint
# Should expose: PresentonService.get_presentation_status()
```

### Frontend Integration

**File**: `frontend/index.html`

```javascript
class PresentationApp {
    async generatePresentation() {
        // Calls: POST /api/generate
        // Maps to: Presenton /api/v1/ppt/presentation/generate
    }

    // ❌ MISSING: fetchSlideDetails() method
    // Should call: GET /api/presentation/{id}
    // Should use: Cached slide data for preview panel
}
```

---

## Implementation Plan: Slide Details Preview Feature

### Objective
Enable users to click a slide thumbnail and view complete slide data (content, layout, images, speaker notes) in the right preview panel.

### Architecture

```
User clicks slide
    ↓
Frontend: selectSlide(index)
    ↓
Frontend: fetchSlideDetails(presentationId) [with cache]
    ↓
Backend: GET /api/presentation/{id}
    ↓
Presenton: GET /api/v1/ppt/presentation/{id}
    ↓
Response: PresentationWithSlides object
    ↓
Frontend: renderSlidePreview(slideData)
    ↓
Display: title, content, layout, html_content, speaker_note
```

### Implementation Steps

#### STEP 1: Backend API Endpoint

**File**: `backend/app/api/routes.py`

Add new endpoint:
```python
@router.get("/presentation/{presentation_id}")
async def get_presentation_details(presentation_id: str):
    """Get complete presentation data including all slides"""
    try:
        presentation_data = await presenton.get_presentation_status(presentation_id)
        return presentation_data
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Presenton API error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch presentation: {str(e)}"
        )
```

**No changes needed to PresentonService** - `get_presentation_status()` already exists.

---

#### STEP 2: Frontend Slide Details Fetching

**File**: `frontend/index.html` - JavaScript section

Add method to PresentationApp class:

```javascript
async fetchSlideDetails(presentationId) {
    if (this.slideDetailsCache[presentationId]) {
        console.log('Using cached slide details');
        return this.slideDetailsCache[presentationId];
    }

    try {
        const response = await fetch(`${API_BASE_URL}/presentation/${presentationId}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        this.slideDetailsCache[presentationId] = data;
        console.log('Fetched and cached slide details:', data);
        return data;
    } catch (error) {
        console.error('Failed to fetch slide details:', error);
        this.showError('無法獲取投影片詳細資訊');
        return null;
    }
}
```

---

#### STEP 3: Enhanced Slide Selection

**File**: `frontend/index.html` - Modify `selectSlide()` method

```javascript
async selectSlide(index, slide) {
    document.querySelectorAll('.slide-card').forEach(card => {
        card.classList.remove('selected');
    });
    document.querySelector(`.slide-card[data-slide-index="${index}"]`)?.classList.add('selected');

    this.selectedSlideIndex = index;

    // Fetch complete slide details if presentation_id available
    if (this.presentationId) {
        const detailedData = await this.fetchSlideDetails(this.presentationId);
        if (detailedData && detailedData.slides && detailedData.slides[index]) {
            const detailedSlide = detailedData.slides[index];
            this.renderSlidePreview(slide, detailedSlide);
        } else {
            this.renderSlidePreview(slide, null);
        }
    } else {
        this.renderSlidePreview(slide, null);
    }

    // Update transcript if available
    if (this.transcriptData && this.transcriptData.transcripts[index]) {
        const transcript = this.transcriptData.transcripts[index];
        this.slidePreviewTranscript.style.display = 'block';
        this.slideTranscriptText.textContent = transcript.transcript;
    } else {
        this.slidePreviewTranscript.style.display = 'none';
    }
}
```

---

#### STEP 4: Slide Preview Rendering

**File**: `frontend/index.html` - Add new method

```javascript
renderSlidePreview(basicSlide, detailedSlide) {
    let previewHtml = `
        <div style="display: flex; flex-direction: column; gap: 1.5rem; padding: 2rem;">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="font-size: 2rem;">${this.getSlideIcon(basicSlide.type)}</div>
                <div>
                    <div style="font-size: 1.5rem; font-weight: 600;">${basicSlide.title}</div>
                    <div style="font-size: 0.875rem; color: var(--text-secondary); margin-top: 0.25rem;">
                        類型: ${basicSlide.type} | 投影片 ${this.selectedSlideIndex + 1}
                    </div>
                </div>
            </div>
    `;

    // Add detailed content if available
    if (detailedSlide) {
        if (detailedSlide.layout) {
            previewHtml += `
                <div>
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">佈局樣式</div>
                    <div style="padding: 0.75rem; background: var(--bg-secondary); border-radius: 6px; font-size: 0.875rem;">
                        ${detailedSlide.layout_group} / ${detailedSlide.layout}
                    </div>
                </div>
            `;
        }

        if (detailedSlide.content) {
            previewHtml += `
                <div>
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">投影片內容</div>
                    <div style="padding: 1rem; background: var(--bg-secondary); border-radius: 6px; font-size: 0.875rem; white-space: pre-wrap;">
                        ${JSON.stringify(detailedSlide.content, null, 2)}
                    </div>
                </div>
            `;
        }

        if (detailedSlide.speaker_note) {
            previewHtml += `
                <div>
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">演講者備註</div>
                    <div style="padding: 1rem; background: var(--bg-secondary); border-radius: 6px; font-size: 0.875rem;">
                        ${detailedSlide.speaker_note}
                    </div>
                </div>
            `;
        }
    } else {
        // Basic content from generation response
        if (basicSlide.content && basicSlide.content.length > 0) {
            previewHtml += `
                <div>
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">內容要點</div>
                    <ul style="padding-left: 1.5rem; margin: 0;">
                        ${basicSlide.content.map(point => `<li style="margin-bottom: 0.5rem;">${point}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        if (basicSlide.image_url) {
            previewHtml += `
                <div>
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">投影片圖片</div>
                    <img src="${basicSlide.image_url}"
                         alt="Slide image"
                         style="max-width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                </div>
            `;
        }
    }

    previewHtml += `</div>`;
    this.slidePreview.innerHTML = previewHtml;
}
```

---

#### STEP 5: Store Presentation ID

**File**: `frontend/index.html` - Modify `checkProgress()` method

Add after successful completion:
```javascript
async checkProgress(taskId) {
    // ... existing polling logic ...

    if (data.status === 'completed') {
        this.presentationId = data.presentation_id;  // ⭐ Store for later use

        // ... rest of existing code ...
    }
}
```

---

### Testing Checklist

- [ ] Backend endpoint returns complete presentation data
- [ ] Frontend caches presentation details (no redundant API calls)
- [ ] Clicking slide fetches and displays detailed information
- [ ] Preview panel shows layout, content, speaker notes
- [ ] Basic slide data shown when detailed data unavailable
- [ ] Error handling for failed API requests
- [ ] Loading states during fetch operations

---

## Future Enhancement Opportunities

### High Priority
1. **Async Generation Support**: Switch to async endpoint for better UX with large presentations
2. **Template Gallery**: Fetch and display template previews dynamically
3. **Presentation History**: Allow users to browse and reload past presentations

### Medium Priority
4. **Custom Image Upload**: Replace Pexels with user-uploaded images
5. **Tone & Verbosity Controls**: Add UI controls for educational tone and verbosity
6. **Table of Contents**: Enable TOC generation option
7. **File Upload Support**: Allow PDF/DOCX upload as content source

### Low Priority
8. **Web Search Integration**: Enable web search for enriched content
9. **Webhook Notifications**: Notify users when presentations complete
10. **Presentation Deletion**: Add cleanup for old presentations

---

## API Error Handling Standards

All Presenton API endpoints return:
- **200**: Success
- **422**: Validation Error (invalid parameters)
- **401/403**: Authentication/Authorization errors

**TeacherAssist Error Handling Pattern**:
```python
try:
    response = await client.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()
except httpx.HTTPStatusError as e:
    raise HTTPException(
        status_code=e.response.status_code,
        detail=f"Presenton API error: {e.response.text}"
    )
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

---

## Configuration Requirements

**Environment Variables** (`.env`):
```bash
PRESENTON_API_KEY=sk-presenton-xxxxxxxx
PRESENTON_API_URL=http://presenton:8000  # Docker internal
# OR for direct API access:
# PRESENTON_API_URL=https://api.presenton.ai
```

**Current Setup**: TeacherAssist uses self-hosted Presenton container, not cloud API.

---

## Summary

### Currently Used Presenton APIs (2/23)
1. ✅ POST /api/v1/ppt/presentation/generate (Synchronous)
2. 🔨 GET /api/v1/ppt/presentation/{id} (Partially - service layer only)

### Immediate Implementation Target
- Complete integration of GET /api/v1/ppt/presentation/{id}
- Expose via backend API endpoint
- Use in frontend for slide details preview

### Future Integration Candidates
- GET /api/v1/ppt/template/all (Dynamic template list)
- POST /api/v1/ppt/presentation/generate/async (Better UX)
- GET /api/v1/ppt/presentation/all (Presentation history)
- POST /api/v1/ppt/images/upload (Custom images)
- POST /api/v1/ppt/files/upload (Document conversion)
