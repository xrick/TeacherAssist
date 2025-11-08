# Web Search Integration Analysis for TeacherAssist PPT Generator

**Date**: 2025-11-09
**Context**: RAG-enhanced presentation generation with real-time web search capabilities
**Current Status**: Web search disabled due to missing search provider configuration

---

## Executive Summary

Web search integration would significantly enhance the PPT generation system by:
- Providing latest, real-time information for presentation content
- Improving factual accuracy with verifiable sources
- Enabling current events and statistics integration
- Supporting research-backed educational content

**Current Challenge**: Presenton's LLM (`gpt-oss:20b` via Ollama) attempts to use search tools but no search provider is configured, causing 500 errors. We disabled search with `ENABLE_WEB_SEARCH=false` as a temporary fix.

---

## Technical Analysis - Available Search Solutions

### Option 1: Tavily Search API ⭐ **RECOMMENDED**

**Overview**: AI-native search API specifically designed for RAG and LLM applications.

**Strengths**:
- ✅ **RAG-Optimized**: Returns clean, structured results perfect for LLM consumption
- ✅ **Pre-Integrated**: Presenton already has native Tavily support built-in
- ✅ **Quality Filtering**: Automatically filters spam, ads, and low-quality content
- ✅ **Fast Setup**: Just add API key - no code changes required
- ✅ **Answer Engine**: Provides direct answers in addition to search results
- ✅ **Source Citations**: Returns URLs for transparency and verification

**Pricing**:
- **Free Tier**: 1,000 searches/month
- **Starter**: $20/month for 10,000 searches
- **Pro**: $100/month for 100,000 searches
- **Cost per search**: $0.002 (after free tier)

**API Features**:
```json
{
  "query": "latest AI developments 2025",
  "search_depth": "basic",  // or "advanced"
  "max_results": 5,
  "include_answer": true,
  "include_domains": ["edu", "gov", "org"],
  "exclude_domains": ["example.com"]
}
```

**Response Format**:
```json
{
  "answer": "Summary answer from sources",
  "results": [
    {
      "title": "Source Title",
      "url": "https://source.com",
      "content": "Relevant excerpt",
      "score": 0.95,
      "published_date": "2025-01-15"
    }
  ]
}
```

**Integration Complexity**: ⭐ Very Easy (1/5)
**Maintenance**: ⭐ Very Low (1/5)
**Quality**: ⭐⭐⭐⭐⭐ Excellent (5/5)

**Best For**:
- Quick setup and immediate results
- Educational content with source citations
- Cost-effective moderate usage (up to 10K searches/month)
- Production-ready RAG applications

---

### Option 2: Brave Search API

**Overview**: Privacy-focused search with independent web index (not reliant on Google/Bing).

**Strengths**:
- ✅ **Privacy-First**: No tracking, no user profiling
- ✅ **Independent Index**: Own web crawler and index
- ✅ **Presenton-Compatible**: Supported by Presenton out of the box
- ✅ **Rich Results**: Web, news, images, videos
- ✅ **Generous Free Tier**: 2,000 queries/month free

**Pricing**:
- **Free Tier**: 2,000 queries/month
- **Data for AI**: $3 per 1,000 queries (after free tier)
- **AI Pro**: $10/month for 10,000 queries ($1 per 1K after)

**API Features**:
```json
{
  "q": "quantum computing advances",
  "count": 10,
  "safesearch": "moderate",
  "freshness": "pd",  // past day
  "result_filter": "web,news",
  "country": "US"
}
```

**Response Format**:
```json
{
  "web": {
    "results": [
      {
        "title": "Page Title",
        "url": "https://example.com",
        "description": "Meta description",
        "age": "2025-01-10T00:00:00"
      }
    ]
  }
}
```

**Integration Complexity**: ⭐⭐ Easy (2/5)
**Maintenance**: ⭐ Very Low (1/5)
**Quality**: ⭐⭐⭐⭐ Very Good (4/5)

**Best For**:
- Privacy-conscious applications
- Higher search volume with budget constraints
- Independent from Google/Microsoft ecosystems
- Multi-modal search (web + news + images)

---

### Option 3: SerpAPI / Google Search

**Overview**: Wrapper API for Google Search providing structured JSON results.

**Strengths**:
- ✅ **Comprehensive Results**: Leverages Google's search quality
- ✅ **Rich Features**: Knowledge graphs, featured snippets, related questions
- ✅ **Multiple Engines**: Google, Bing, Yahoo, DuckDuckGo support
- ✅ **Extensive Parsing**: Structured data extraction

**Weaknesses**:
- ⚠️ **Custom Integration**: Requires implementing search handler in Presenton
- ⚠️ **Higher Cost**: More expensive than dedicated RAG APIs
- ⚠️ **No Free Tier**: Starts at $50/month

**Pricing**:
- **Starter**: $50/month for 5,000 searches
- **Developer**: $100/month for 10,000 searches
- **Production**: Custom pricing
- **Cost per search**: $0.01 (significantly higher than alternatives)

**API Features**:
```python
params = {
  "q": "AI presentation tools",
  "location": "United States",
  "hl": "en",
  "gl": "us",
  "num": 10,
  "tbm": "nws"  # news search
}
```

**Integration Complexity**: ⭐⭐⭐⭐ Complex (4/5)
**Maintenance**: ⭐⭐⭐ Moderate (3/5)
**Quality**: ⭐⭐⭐⭐⭐ Excellent (5/5)

**Best For**:
- Applications requiring Google-quality results
- Need for knowledge graph data
- Already using SerpAPI for other purposes
- Budget allows premium search costs

---

### Option 4: Self-Hosted Search (Searxng)

**Overview**: Open-source metasearch engine that aggregates results from multiple search engines.

**Strengths**:
- ✅ **Free & Open Source**: No API costs
- ✅ **Privacy-Focused**: No tracking, self-hosted
- ✅ **Aggregated Results**: Combines Google, Bing, DuckDuckGo, etc.
- ✅ **Customizable**: Full control over behavior and filtering
- ✅ **No Rate Limits**: Limited only by your infrastructure

**Weaknesses**:
- ⚠️ **Infrastructure Required**: Need to host and maintain server
- ⚠️ **Complex Setup**: Docker deployment, configuration, monitoring
- ⚠️ **Custom Integration**: Need to implement Presenton search handler
- ⚠️ **Maintenance Overhead**: Updates, security, uptime management
- ⚠️ **Potential Blocking**: Search engines may block automated queries

**Technical Requirements**:
- Docker container deployment
- Reverse proxy with SSL (nginx/Traefik)
- Monitoring and alerting
- Regular updates and security patches

**Integration Complexity**: ⭐⭐⭐⭐⭐ Very Complex (5/5)
**Maintenance**: ⭐⭐⭐⭐⭐ Very High (5/5)
**Quality**: ⭐⭐⭐ Good (3/5)

**Best For**:
- High-volume applications (>100K searches/month)
- Strict privacy requirements
- Already have DevOps infrastructure
- Long-term cost optimization (>$200/month search budget)

**Docker Deployment**:
```yaml
services:
  searxng:
    image: searxng/searxng:latest
    container_name: searxng
    ports:
      - "8080:8080"
    volumes:
      - ./searxng:/etc/searxng
    environment:
      - SEARXNG_BASE_URL=https://search.yourdomain.com
    restart: unless-stopped
```

---

### Option 5: Custom RAG with Vector Database

**Overview**: Build domain-specific knowledge base with vector search and hybrid retrieval.

**Architecture**:
```
User Query → Embedding Model → Vector Search (Chroma/Qdrant)
                              ↓
                    [Local Knowledge Base]
                              ↓
                    LLM Synthesis → Response
```

**Strengths**:
- ✅ **Domain-Specific**: Curated, high-quality content
- ✅ **Offline Capability**: No external API dependencies
- ✅ **Consistent Quality**: Controlled source reliability
- ✅ **Cost-Effective**: No per-query costs after setup
- ✅ **Fast Retrieval**: Optimized for specific use cases
- ✅ **Version Control**: Track knowledge base updates

**Weaknesses**:
- ⚠️ **No Real-Time Data**: Requires manual updates for latest information
- ⚠️ **Initial Setup**: Significant development and data preparation
- ⚠️ **Maintenance**: Regular content updates needed
- ⚠️ **Limited Scope**: Only searches pre-indexed content
- ⚠️ **Hybrid Needed**: Best combined with web search for current events

**Technical Stack**:
- **Vector DB**: Chroma (lightweight) or Qdrant (production-scale)
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` or OpenAI embeddings
- **Storage**: PostgreSQL with pgvector extension
- **Orchestration**: LangChain or LlamaIndex

**Implementation Complexity**: ⭐⭐⭐⭐⭐ Very Complex (5/5)
**Maintenance**: ⭐⭐⭐⭐ High (4/5)
**Quality**: ⭐⭐⭐⭐ Very Good (4/5) for domain-specific content

**Best For**:
- Educational institutions with curated content libraries
- Domain-specific applications (medical, legal, technical)
- Compliance requirements (data residency, audit trails)
- Hybrid approach: local knowledge + web search fallback

**Example Architecture**:
```python
# Vector DB setup
from chromadb import Client
from sentence_transformers import SentenceTransformer

# Initialize
client = Client()
collection = client.create_collection("education_content")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Index documents
for doc in documents:
    embedding = embedder.encode(doc['content'])
    collection.add(
        documents=[doc['content']],
        metadatas=[doc['metadata']],
        embeddings=[embedding],
        ids=[doc['id']]
    )

# Query
query_embedding = embedder.encode(query)
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5
)
```

---

## Comparison Matrix

| Feature | Tavily | Brave | SerpAPI | Searxng | Custom RAG |
|---------|--------|-------|---------|---------|------------|
| **Setup Time** | 15 min | 30 min | 2 hours | 4 hours | 2 days |
| **Free Tier** | 1K/mo | 2K/mo | None | Unlimited | One-time cost |
| **Cost (10K/mo)** | $20 | $10 | $100 | Hosting | $0 recurring |
| **RAG-Optimized** | Yes | Partial | No | No | Yes |
| **Real-Time Data** | Yes | Yes | Yes | Yes | No |
| **Presenton Ready** | Yes | Yes | No | No | No |
| **Maintenance** | None | None | Low | High | High |
| **Quality** | Excellent | Very Good | Excellent | Good | Very Good |
| **Scalability** | High | High | High | Medium | High |

---

## Cost Analysis (Monthly)

### Scenario 1: Moderate Usage (50 presentations/day, ~100 searches/day)
- **3,000 searches/month**

| Provider | Monthly Cost | Setup Cost | Total Year 1 |
|----------|-------------|------------|--------------|
| Tavily | $20 | $0 | $240 |
| Brave | $0 (free tier) | $0 | $0 |
| SerpAPI | $50 | $0 | $600 |
| Searxng | ~$10 (hosting) | $100 (dev) | $220 |
| Custom RAG | $0 | $2,000 (dev) | $2,000 |

**Winner**: Brave (free tier covers usage)

---

### Scenario 2: High Usage (200 presentations/day, ~500 searches/day)
- **15,000 searches/month**

| Provider | Monthly Cost | Setup Cost | Total Year 1 |
|----------|-------------|------------|--------------|
| Tavily | $30 | $0 | $360 |
| Brave | $15 | $0 | $180 |
| SerpAPI | $150 | $0 | $1,800 |
| Searxng | ~$30 (hosting) | $100 (dev) | $460 |
| Custom RAG | $0 | $2,000 (dev) | $2,000 |

**Winner**: Brave (lowest total cost)

---

### Scenario 3: Enterprise Usage (1,000 presentations/day, ~3,000 searches/day)
- **90,000 searches/month**

| Provider | Monthly Cost | Setup Cost | Total Year 1 |
|----------|-------------|------------|--------------|
| Tavily | $100 | $0 | $1,200 |
| Brave | $90 | $0 | $1,080 |
| SerpAPI | $900 | $0 | $10,800 |
| Searxng | ~$50 (hosting) | $100 (dev) | $700 |
| Custom RAG | $0 | $5,000 (dev) | $5,000 |

**Winner**: Searxng (long-term cost efficiency)

---

## Implementation Recommendations

### Recommended: Tiered Approach

**Phase 1: Quick Win (Week 1)**
- **Provider**: Tavily API
- **Rationale**: Fastest time-to-value, RAG-optimized
- **Setup**: 15 minutes
- **Cost**: Free tier for initial testing

**Phase 2: Production Ready (Month 1)**
- **Provider**: Brave API (primary) + Tavily (fallback)
- **Rationale**: Cost-effective, redundancy
- **Features**:
  - Caching layer for repeated queries
  - Usage monitoring and analytics
  - Per-user search toggle
- **Cost**: ~$10-30/month depending on volume

**Phase 3: Enterprise Scale (Month 3+)**
- **Provider**: Brave + Custom RAG hybrid
- **Rationale**: Balance real-time + domain-specific content
- **Features**:
  - Curated knowledge base for educational content
  - Web search for current events and statistics
  - Advanced result ranking and filtering
  - Source credibility scoring
- **Cost**: ~$50-100/month + one-time dev investment

---

## Risk Assessment

### Tavily
- **Risk**: API dependency, rate limits
- **Mitigation**: Implement caching, fallback provider
- **Severity**: Low

### Brave
- **Risk**: API changes, service availability
- **Mitigation**: Multi-provider strategy
- **Severity**: Low

### SerpAPI
- **Risk**: High cost, Google API changes
- **Mitigation**: Not recommended unless required
- **Severity**: Medium

### Searxng
- **Risk**: Maintenance burden, potential blocking
- **Mitigation**: Monitoring, rotating IPs, rate limiting
- **Severity**: High

### Custom RAG
- **Risk**: Stale data, high development cost
- **Mitigation**: Hybrid approach with web search
- **Severity**: Medium

---

## Next Steps for Implementation

### Step 1: Get Tavily API Key (5 minutes)
1. Visit https://tavily.com
2. Sign up for free account
3. Generate API key from dashboard
4. Note: 1,000 free searches/month

### Step 2: Configure Presenton (5 minutes)
```bash
# Add to .env
TAVILY_API_KEY=tvly-your-api-key-here

# Update docker-compose.yml
environment:
  - TAVILY_API_KEY=${TAVILY_API_KEY}
  - WEB_GROUNDING=true
  - ENABLE_WEB_SEARCH=true  # Change from false
```

### Step 3: Restart Services (5 minutes)
```bash
docker compose down
docker compose up -d
```

### Step 4: Test Search Functionality (5 minutes)
```bash
# Monitor logs
docker compose logs -f presenton

# Generate test presentation with current events topic
# e.g., "Latest developments in quantum computing 2025"
```

### Step 5: Implement Caching (Optional - 1 hour)
```python
# Add Redis caching layer
import redis
import hashlib
import json

cache = redis.Redis(host='localhost', port=6379, decode_responses=True)

def cached_search(query: str, ttl: int = 3600):
    cache_key = f"search:{hashlib.md5(query.encode()).hexdigest()}"

    # Check cache
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)

    # Perform search
    result = tavily_client.search(query)

    # Cache result
    cache.setex(cache_key, ttl, json.dumps(result))

    return result
```

---

## Monitoring and Analytics

### Key Metrics to Track
1. **Search Volume**: Queries per day/month
2. **Cost per Search**: Actual API costs
3. **Cache Hit Rate**: Percentage of cached results
4. **Search Quality**: User satisfaction with results
5. **Source Diversity**: Variety of information sources
6. **Response Time**: Search latency impact on PPT generation

### Recommended Monitoring Setup
```python
# Add to backend/app/services/search_service.py
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SearchMetrics:
    def __init__(self):
        self.queries = []

    def log_search(self, query, provider, cached, cost, latency):
        self.queries.append({
            'timestamp': datetime.now(),
            'query': query,
            'provider': provider,
            'cached': cached,
            'cost': cost,
            'latency_ms': latency
        })

        logger.info(f"Search: {query} | Provider: {provider} | "
                   f"Cached: {cached} | Cost: ${cost} | "
                   f"Latency: {latency}ms")
```

---

## Security Considerations

### API Key Management
- ✅ Store keys in environment variables, never in code
- ✅ Use `.env` file excluded from git (`.gitignore`)
- ✅ Rotate keys quarterly
- ✅ Monitor usage for anomalies

### Query Sanitization
```python
import re

def sanitize_query(query: str) -> str:
    # Remove potential injection attempts
    query = re.sub(r'[^\w\s\-\+\'\"]', '', query)

    # Limit length
    if len(query) > 500:
        query = query[:500]

    return query.strip()
```

### Rate Limiting
```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.post("/api/generate")
@limiter.limit("10/hour")  # 10 presentations per hour per user
async def generate_presentation(request: Request):
    # Implementation
    pass
```

---

## Conclusion

**Recommended Path**: Start with Tavily for immediate results, transition to Brave + caching for production, consider Custom RAG for domain-specific content enhancement.

**Estimated Timeline**:
- Tavily Integration: 1 hour
- Testing & Validation: 2 hours
- Production Deployment: 1 day
- Monitoring Setup: 1 day
- **Total**: 2-3 days to production-ready web search

**Estimated Costs**:
- Development: $0 (using existing Presenton support)
- Month 1: $0 (free tiers)
- Months 2-12: $10-30/month (depending on usage)
- **Year 1 Total**: $120-360

**Expected Benefits**:
- 🎯 More accurate, up-to-date presentations
- 📈 Enhanced educational value with current data
- 🔍 Verifiable sources and citations
- ⚡ Faster content research for users
- 💡 Better factual accuracy and relevance
