# Presentation Transcript Generation Guide 🎤

## Overview

The Teaching PPT Generator now includes **automatic transcript generation** using the **Zephyr 7B** language model. This feature creates professional presentation scripts that speakers can use when delivering their presentations.

## Features

### 🎭 Three Speaking Styles

1. **Educational (教學式)**
   - Clear, step-by-step explanations
   - Suitable for teaching and training
   - Uses simple language with examples
   - Best for: Courses, tutorials, workshops

2. **Formal (正式)**
   - Professional business language
   - Appropriate for official settings
   - Maintains professional tone throughout
   - Best for: Business meetings, conferences, official presentations

3. **Conversational (對話式)**
   - Easy, relatable speaking style
   - Natural flow and rhythm
   - Engaging and approachable
   - Best for: Informal presentations, team meetings, casual talks

### ⏱️ Smart Duration Estimation

- Calculates speaking time based on word count
- Average speaking rate: 150 words per minute
- Individual timing for each slide
- Total presentation duration calculated

### 📊 Slide-by-Slide Scripts

Each slide gets its own custom script:
- **Title Slide**: Opening remarks and introduction
- **Overview Slide**: Summary of main points
- **Content Slides**: Detailed explanations with transitions
- **Conclusion Slide**: Summary and closing remarks

## Installation

### Prerequisites

```bash
# Ensure Ollama is installed
ollama --version

# Download Zephyr 7B model (one-time setup)
ollama pull zephyr:7b

# Verify installation
ollama list | grep zephyr
```

**Note**: The Zephyr 7B model is approximately **4.1 GB**. Download time depends on your internet connection.

## Usage

### Step 1: Generate Presentation

First, create a presentation using the main interface:
1. Enter your content (minimum 50 characters)
2. Select template style
3. Click "生成簡報" (Generate)
4. Wait for presentation generation to complete

### Step 2: Generate Transcript

Once the presentation is ready:
1. Click the **"生成演講稿"** (Generate Transcript) button
2. Select your preferred speaking style from dropdown
3. Wait 30-90 seconds for generation
4. Review the generated transcript

### Step 3: Download Transcript

Click **"下載演講稿"** (Download Transcript) to save as text file.

## Example Output

### Sample Transcript Format

```
簡報演講稿
==================================================
投影片數量: 6
預估演講時間: 8.5 分鐘
==================================================

【投影片 1: 人工智慧在教育中的應用】
[預估時間: 45秒]
各位老師、同學們大家好！今天我非常榮幸能夠與大家分享一個令人興奮的主題 - 人工智慧在教育領域的應用。在接下來的幾分鐘裡，我們將一起探討AI技術如何改變傳統的教學方式，並為教育帶來革命性的變革。

【投影片 2: 學習目標】
[預估時間: 60秒]
在開始之前，讓我們先了解今天的學習目標。首先，我們會探討機器學習的基本概念，包括它的核心原理和運作方式。接著，我們將深入了解AI在個性化學習方面的應用...

【投影片 3: 機器學習基礎】
[預估時間: 90秒]
現在讓我們深入了解機器學習的基礎知識。機器學習是人工智慧的一個重要分支，它使電腦能夠從數據中學習並改進，而無需明確的編程...
```

## API Reference

### Generate Transcript Endpoint

**POST** `/api/transcript/generate`

**Request Body:**
```json
{
  "presentation_id": "uuid-string",
  "language": "zh-TW",
  "style": "educational"
}
```

**Response:**
```json
{
  "presentation_id": "uuid-string",
  "total_slides": 6,
  "total_duration_minutes": 8.5,
  "transcripts": [
    {
      "slide_number": 1,
      "title": "投影片標題",
      "transcript": "演講稿內容...",
      "duration_seconds": 45
    }
  ],
  "full_transcript": "完整演講稿文字..."
}
```

### Download Transcript Endpoint

**GET** `/api/transcript/{presentation_id}/download`

Returns a `.txt` file with the complete transcript.

### Get Cached Transcript

**GET** `/api/transcript/{presentation_id}`

Returns the previously generated transcript data (if available).

## Configuration

### Model Settings

The Zephyr service uses these default parameters:

```python
{
    "model": "zephyr:7b",
    "temperature": 0.7,
    "top_p": 0.9,
    "num_predict": 512
}
```

### Speaking Rate

- **Default**: 150 words per minute
- **Minimum Duration**: 30 seconds per slide
- **Based on**: Average professional speaking speed

## Best Practices

### 1. Content Quality

- **Input**: Provide structured, clear content for better transcripts
- **Length**: 200-1000 characters work best
- **Organization**: Well-organized content produces better scripts

### 2. Style Selection

- **Educational**: Use for training materials and courses
- **Formal**: Use for business and professional settings
- **Conversational**: Use for team meetings and casual presentations

### 3. Post-Processing

- Review generated transcripts before use
- Edit for personal speaking style
- Add pauses and emphasis markers if needed
- Practice delivery with the script

### 4. Integration Tips

- Generate transcript after finalizing slides
- Use transcript for speaker notes
- Share with co-presenters for consistency
- Archive for future reference

## Performance

### Generation Time

| Slides | Estimated Time |
|--------|----------------|
| 4-5    | 30-45 seconds  |
| 6-7    | 45-60 seconds  |
| 8+     | 60-90 seconds  |

### Resource Usage

- **Model Size**: 4.1 GB (Zephyr 7B)
- **RAM**: ~8 GB recommended
- **CPU**: Multi-core processor recommended
- **GPU**: Optional, speeds up generation

## Troubleshooting

### Model Not Available

**Error**: "Zephyr 7B model not available"

**Solution**:
```bash
ollama pull zephyr:7b
ollama list  # Verify installation
```

### Generation Timeout

**Issue**: Transcript generation takes too long

**Solutions**:
- Check Ollama service is running: `ps aux | grep ollama`
- Restart Ollama: `ollama serve`
- Reduce content length
- Try with fewer slides

### Poor Quality Transcripts

**Issue**: Generated scripts are not natural

**Solutions**:
- Improve input content quality
- Try different speaking style
- Provide more structured content
- Add clear section breaks

### Memory Issues

**Issue**: System runs out of memory

**Solutions**:
- Close unnecessary applications
- Increase Docker memory limit
- Use GPU if available
- Generate transcripts one at a time

## Advanced Features

### Custom Prompts

You can modify the transcript generation prompts in:
```
backend/app/services/zephyr_service.py
```

Look for the `_build_transcript_prompt` method to customize:
- Speaking style instructions
- Content structure
- Language tone
- Slide-specific formats

### Integration with External Tools

Export transcripts to:
- Teleprompter software
- Video editing tools (captions)
- Translation services
- Text-to-speech engines

## Limitations

1. **Language**: Currently optimized for Traditional Chinese (zh-TW)
2. **Model Dependency**: Requires Zephyr 7B model
3. **Internet**: Ollama must be running locally
4. **Storage**: Transcripts stored in memory (consider Redis for production)
5. **Concurrency**: Process one transcript at a time

## Future Enhancements

Planned features:
- [ ] Multiple language support (English, Japanese, etc.)
- [ ] Custom speaking rate adjustment
- [ ] Voice preview (text-to-speech)
- [ ] Export to SRT/VTT for videos
- [ ] Speaker notes integration