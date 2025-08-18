# Voiceflow Integration Guide
## Connecting ACT Refugee Support Database to Your Voiceflow Agent

### Prerequisites
- Voiceflow account (Pro or Teams plan for API access)
- Qdrant database running (local or cloud)
- Python environment with database initialized
- Basic understanding of APIs and webhooks

---

## Part 1: Set Up Your API Bridge (10 minutes)

### Step 1: Create FastAPI Server
Create a new file `api_server.py`:

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn

from config import QdrantConfig
from search_engine import SearchEngine
from search_economic_integration import EconomicIntegrationSearch
from models import SearchQuery, ResourceCategory

app = FastAPI(title="ACT Refugee Support API")

# Enable CORS for Voiceflow
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize search engines
config = QdrantConfig()
search_engine = SearchEngine(config)
economic_search = EconomicIntegrationSearch(config)

class ChatQuery(BaseModel):
    message: str
    category: Optional[str] = None
    urgency: Optional[str] = None
    language: Optional[str] = None
    limit: int = 3

class VoiceflowResponse(BaseModel):
    success: bool
    message: str
    resources: List[Dict]
    quick_replies: Optional[List[str]] = None

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ACT Refugee Support API"}

@app.post("/search", response_model=VoiceflowResponse)
async def search_resources(query: ChatQuery):
    """Main endpoint for Voiceflow to search resources"""
    try:
        # Detect intent from message
        intent = detect_intent(query.message)
        
        # Create search query
        search_query = SearchQuery(
            query=query.message,
            limit=query.limit
        )
        
        if query.category:
            search_query.categories = [ResourceCategory(query.category)]
        if query.urgency:
            search_query.urgency = query.urgency
            
        # Perform search
        results = search_engine.search(search_query)
        
        # Format for Voiceflow
        resources_formatted = []
        for result in results:
            resource = result.resource
            resources_formatted.append({
                "name": resource.name,
                "description": resource.description[:200] + "...",
                "phone": resource.contact.phone,
                "website": resource.contact.website,
                "address": resource.contact.address,
                "services": ", ".join(resource.services_provided[:3]),
                "cost": resource.cost,
                "languages": ", ".join(resource.languages_available[:3]),
                "urgency": resource.urgency_level
            })
        
        # Generate response message
        if resources_formatted:
            message = f"I found {len(resources_formatted)} services that can help you:"
        else:
            message = "I couldn't find specific services matching your needs. Please call 131 450 for interpreter services or 000 for emergencies."
        
        # Add quick replies for common follow-ups
        quick_replies = generate_quick_replies(intent)
        
        return VoiceflowResponse(
            success=True,
            message=message,
            resources=resources_formatted,
            quick_replies=quick_replies
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/emergency")
async def search_emergency():
    """Quick endpoint for emergency services"""
    urgent_services = search_engine.search_urgent_services(limit=5)
    
    resources_formatted = []
    for resource in urgent_services:
        resources_formatted.append({
            "name": resource.name,
            "phone": resource.contact.phone,
            "available": resource.contact.hours,
            "urgency": resource.urgency_level
        })
    
    return {
        "success": True,
        "message": "Here are emergency services available 24/7:",
        "resources": resources_formatted
    }

@app.post("/search/economic")
async def search_economic_integration(query: ChatQuery):
    """Specialized endpoint for economic integration queries"""
    
    # Detect economic intent
    if "skill" in query.message.lower() or "qualification" in query.message.lower():
        resources = economic_search.search_skill_underutilization_solutions(limit=3)
    elif "business" in query.message.lower() or "entrepreneur" in query.message.lower():
        resources = economic_search.search_entrepreneurship_support(stage="startup", limit=3)
    elif "job" in query.message.lower() or "work" in query.message.lower():
        resources = economic_search.search_career_pathways(limit=3)
    else:
        resources = economic_search.search_vocational_training(free_only=True, limit=3)
    
    resources_formatted = []
    for resource in resources:
        resources_formatted.append({
            "name": resource.name,
            "description": resource.description[:200] + "...",
            "contact": resource.contact.phone or resource.contact.website,
            "services": ", ".join(resource.services_provided[:3])
        })
    
    return {
        "success": True,
        "message": "Here are services to help with employment and skills:",
        "resources": resources_formatted
    }

def detect_intent(message: str) -> str:
    """Simple intent detection based on keywords"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["emergency", "urgent", "help now", "crisis"]):
        return "emergency"
    elif any(word in message_lower for word in ["job", "work", "employment", "career"]):
        return "employment"
    elif any(word in message_lower for word in ["house", "housing", "rent", "accommodation"]):
        return "housing"
    elif any(word in message_lower for word in ["english", "language", "AMEP", "learn"]):
        return "language"
    elif any(word in message_lower for word in ["visa", "immigration", "lawyer", "legal"]):
        return "legal"
    elif any(word in message_lower for word in ["doctor", "health", "medical", "hospital"]):
        return "healthcare"
    elif any(word in message_lower for word in ["school", "education", "study", "child"]):
        return "education"
    elif any(word in message_lower for word in ["money", "payment", "centrelink", "financial"]):
        return "financial"
    else:
        return "general"

def generate_quick_replies(intent: str) -> List[str]:
    """Generate contextual quick reply suggestions"""
    quick_replies_map = {
        "emergency": ["Call 000", "Find hospital", "Crisis support", "Domestic violence help"],
        "employment": ["Skills assessment", "Job search help", "Start a business", "Free training"],
        "housing": ["Emergency accommodation", "Rental help", "Share house", "Public housing"],
        "language": ["Free English classes", "AMEP enrollment", "Conversation groups", "Online learning"],
        "legal": ["Visa help", "Free lawyers", "Immigration advice", "Work rights"],
        "healthcare": ["Find doctor", "Mental health", "Hospital", "Medicare help"],
        "education": ["School enrollment", "Adult education", "University pathways", "Children's programs"],
        "financial": ["Centrelink", "Emergency relief", "No interest loans", "Budget help"],
        "general": ["Emergency help", "New arrival support", "Find services", "Speak my language"]
    }
    return quick_replies_map.get(intent, quick_replies_map["general"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 2: Install API Dependencies
```bash
pip install fastapi uvicorn python-multipart
```

### Step 3: Start Your API Server
```bash
python api_server.py
```
Your API is now running at `http://localhost:8000`
Test it at `http://localhost:8000/docs`

---

## Part 2: Deploy Your API (15 minutes)

### Option A: Deploy to Railway (Recommended - Free tier available)

1. Create account at [railway.app](https://railway.app)
2. Install Railway CLI:
```bash
npm install -g @railway/cli
```

3. Create `Procfile`:
```
web: uvicorn api_server:app --host 0.0.0.0 --port $PORT
```

4. Deploy:
```bash
railway login
railway init
railway up
```

5. Get your public URL from Railway dashboard (e.g., `https://your-app.railway.app`)

### Option B: Deploy to Render (Alternative - Free tier)

1. Create account at [render.com](https://render.com)
2. Connect GitHub repo
3. Create new Web Service
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn api_server:app --host 0.0.0.0 --port $PORT`

### Option C: Use ngrok for Testing (Temporary)

```bash
pip install pyngrok
ngrok http 8000
```
Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

---

## Part 3: Configure Voiceflow Integration (20 minutes)

### Step 1: Create API Integration Block

1. Open your Voiceflow project
2. Add an **API Block** (under Logic)
3. Configure the API block:
   - **Method**: POST
   - **URL**: `{your-api-url}/search`
   - **Headers**: 
     ```json
     {
       "Content-Type": "application/json"
     }
     ```
   - **Body**:
     ```json
     {
       "message": "{last_utterance}",
       "limit": 3
     }
     ```

4. Map the response:
   - Create variable `api_response`
   - Map response path to variable

### Step 2: Create Response Handler

1. Add a **Code Block** after API block:
```javascript
// Parse API response
const response = JSON.parse(api_response);

if (response.success && response.resources.length > 0) {
    // Store resources in variables
    resources = response.resources;
    response_message = response.message;
    quick_replies = response.quick_replies || [];
    
    // Format resources for display
    let formatted_response = response_message + "\n\n";
    
    resources.forEach((resource, index) => {
        formatted_response += `${index + 1}. **${resource.name}**\n`;
        formatted_response += `📞 ${resource.phone || 'No phone'}\n`;
        formatted_response += `🌐 ${resource.website || 'No website'}\n`;
        formatted_response += `📍 ${resource.address || 'No address'}\n`;
        formatted_response += `💰 ${resource.cost}\n`;
        formatted_response += `🗣️ Languages: ${resource.languages}\n\n`;
    });
    
    // Set the formatted response
    formattedMessage = formatted_response;
} else {
    formattedMessage = "I couldn't find specific services. Please call 131 450 for interpreter services.";
}
```

2. Add a **Speak Block** with:
   - Text: `{formattedMessage}`
   - Add buttons for `{quick_replies}`

### Step 3: Create Intent Handlers

1. **Emergency Intent**:
```yaml
Training Phrases:
- "I need urgent help"
- "Emergency"
- "Help me now"
- "Crisis"

API Endpoint: /search/emergency
```

2. **Skills Recognition Intent**:
```yaml
Training Phrases:
- "My qualifications from overseas"
- "Skills assessment"
- "I was an engineer in my country"
- "Recognize my degree"

API Endpoint: /search/economic
```

3. **New Arrival Intent**:
```yaml
Training Phrases:
- "I just arrived"
- "New to Australia"
- "First time in Canberra"
- "Recently arrived refugee"

API Body:
{
  "message": "{last_utterance}",
  "urgency": "high",
  "limit": 5
}
```

### Step 4: Add Language Detection

1. Create a **Choice Block** at conversation start:
   - "What language do you prefer?"
   - Options: English, Arabic, Mandarin, Farsi, Spanish

2. Store selection in `user_language` variable

3. Pass to API:
```json
{
  "message": "{last_utterance}",
  "language": "{user_language}",
  "limit": 3
}
```

### Step 5: Create Fallback Handling

1. Add **Error Handling** to API block:
   - On error → Fallback message
   
2. Create fallback response:
```
"I'm having trouble connecting to services right now. 
For immediate help:
📞 Emergency: 000
📞 Interpreter: 131 450
📞 Crisis Support: 1800 737 732"
```

---

## Part 4: Advanced Features (Optional - 10 minutes)

### Feature 1: Context Persistence

Add to Code Block:
```javascript
// Store search context
sessionContext = {
    lastSearch: message,
    lastCategory: category,
    resultsShown: resources.length,
    timestamp: Date.now()
};

// Save to Voiceflow variables
last_search_context = JSON.stringify(sessionContext);
```

### Feature 2: Multi-turn Conversations

```javascript
// Check for follow-up questions
if (last_utterance.includes("more") || last_utterance.includes("other")) {
    // Modify API call to get next set
    offset = resultsShown || 0;
    limit = 3;
}
```

### Feature 3: Proactive Suggestions

```javascript
// Based on user profile, suggest services
if (!hasAskedAbout.includes("digital_help") && isNewUser) {
    suggestedService = "Do you need help with MyGov or online services?";
}
```

### Feature 4: Analytics Tracking

```javascript
// Track what services are most requested
analytics.track('Service Search', {
    query: last_utterance,
    category: detected_category,
    results_found: resources.length,
    user_language: user_language
});
```

---

## Part 5: Testing Your Integration

### Test Scenarios

1. **Basic Search**:
   - User: "I need help finding a job"
   - Expected: 3 employment services

2. **Emergency**:
   - User: "I need urgent medical help"
   - Expected: Emergency services with phone numbers

3. **Complex Query**:
   - User: "I'm an engineer from India looking for skills assessment"
   - Expected: Skills recognition services

4. **No Results**:
   - User: "Random unrelated query"
   - Expected: Fallback message with emergency contacts

### Testing Checklist

- [ ] API server is running
- [ ] Public URL is accessible
- [ ] Voiceflow API block configured correctly
- [ ] Response parsing works
- [ ] Quick replies appear
- [ ] Error handling works
- [ ] Multiple languages supported
- [ ] Context maintained across turns

---

## Part 6: Production Deployment

### Security Considerations

1. **Add API Key Authentication**:
```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.post("/search")
async def search_resources(
    query: ChatQuery,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if credentials.credentials != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
```

2. **In Voiceflow**, add header:
```json
{
  "Authorization": "Bearer your-secret-api-key"
}
```

### Performance Optimization

1. **Add Caching**:
```python
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@app.post("/search")
@cache(expire=300)  # Cache for 5 minutes
async def search_resources(query: ChatQuery):
    # Your search logic
```

2. **Rate Limiting**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/search")
@limiter.limit("10/minute")
async def search_resources(query: ChatQuery):
    # Your search logic
```

### Monitoring

1. **Add Logging**:
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/search")
async def search_resources(query: ChatQuery):
    logger.info(f"Search query: {query.message}")
    # Your search logic
```

2. **Health Checks in Voiceflow**:
   - Create scheduled trigger
   - Call `/health` endpoint
   - Alert on failure

---

## Part 7: Voiceflow Templates

### Template 1: Welcome Flow
```
[Start]
→ "Welcome! I can help you find services for migrants and refugees in Canberra."
→ "What do you need help with today?"
→ [Buttons]:
   - "🆘 Emergency Help"
   - "🏠 Housing"
   - "💼 Jobs & Skills"
   - "🗣️ Learn English"
   - "⚖️ Legal Help"
   - "🏥 Healthcare"
```

### Template 2: Emergency Flow
```
[Emergency Intent Triggered]
→ [API Call: /search/emergency]
→ "⚠️ EMERGENCY SERVICES:"
→ [Display Resources]
→ "For immediate emergency, call 000"
→ "For interpreter, call 131 450"
```

### Template 3: Skills Recognition Flow
```
[User mentions qualifications]
→ "I understand you have overseas qualifications."
→ "What profession were you in?"
→ [Capture profession]
→ [API Call with profession]
→ [Display relevant resources]
→ "Would you like information about fast-track programs?"
```

---

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Check API URL is correct
   - Ensure API server is running
   - Verify CORS is enabled

2. **Empty Responses**
   - Check database is initialized
   - Verify search query format
   - Check API response parsing

3. **Slow Response Times**
   - Implement caching
   - Optimize search queries
   - Use connection pooling

4. **Language Issues**
   - Ensure language parameter is passed
   - Check language mapping in API
   - Verify interpreter services included

---

## Support & Resources

- **Voiceflow Documentation**: [docs.voiceflow.com](https://docs.voiceflow.com)
- **FastAPI Documentation**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **Qdrant Documentation**: [qdrant.tech/documentation](https://qdrant.tech/documentation)

---

## Next Steps

1. ✅ Test basic integration
2. ✅ Add error handling
3. ✅ Implement caching
4. ✅ Add analytics
5. ✅ Deploy to production
6. ✅ Monitor performance
7. ✅ Gather user feedback
8. ✅ Iterate and improve

---

*Your Voiceflow agent is now connected to a comprehensive database of 70+ services, providing intelligent, context-aware support to migrants and refugees in the ACT.*