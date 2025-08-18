# Voiceflow AI Agent + Qdrant Database Integration Guide

## Direct Database Connection vs API Gateway Approach

This guide explains how to connect your Qdrant vector database to Voiceflow's AI Agent feature, which provides more sophisticated conversational capabilities than traditional step-based flows.

---

## 🤖 Understanding Voiceflow AI Agents

### What's Different About AI Agents?

Voiceflow's **AI Agent** feature (available in Pro/Teams plans) is fundamentally different from traditional step-based flows:

**Traditional Steps:**
- Linear, predefined paths
- Rule-based responses
- Manual intent mapping
- Limited context awareness

**AI Agents:**
- Dynamic conversation flow
- LLM-powered understanding
- Automatic intent detection
- Full context awareness
- Knowledge base integration
- Function calling capabilities

---

## 🔌 Integration Architecture Options

### Option 1: Direct Database Connection (Not Recommended)

**Why it's challenging:**
- Voiceflow AI Agents cannot directly connect to Qdrant
- No native vector database connectors
- Security concerns with exposing database credentials
- Limited query optimization capabilities

### Option 2: API Gateway with Knowledge Base (Recommended) ✅

**Architecture:**
```
┌────────────────────┐
│  Voiceflow Agent   │
│  - LLM Processing  │
│  - Context Mgmt    │
└──────────┬─────────┘
           │
    [Knowledge Base]
    [Function Calls]
           │
┌──────────▼─────────┐
│   Your Railway     │
│   API Gateway      │
│   (FastAPI)        │
└──────────┬─────────┘
           │
┌──────────▼─────────┐
│   Qdrant Cloud     │
│   Vector Database  │
└────────────────────┘
```

---

## 🚀 Setting Up AI Agent Integration

### Step 1: Configure Your API for AI Agent Compatibility

Your existing Railway API at `https://act-refugee-support-production.up.railway.app` is already compatible! The AI Agent can use it through **Function Calling**.

### Step 2: Create a Voiceflow AI Agent

1. **Open Voiceflow**
2. **Create New Agent** (not a traditional flow)
3. **Go to Agent Settings**
4. **Configure the AI Model:**
   - Model: GPT-4 or GPT-3.5-turbo
   - Temperature: 0.7 (balanced)
   - Max tokens: 500

### Step 3: Add Your Knowledge Base

Voiceflow AI Agents can use two types of knowledge:

#### Option A: Static Knowledge Base (Quick Setup)
1. **Go to Knowledge Base** in Voiceflow
2. **Add Documents** about ACT refugee services
3. **Enable RAG (Retrieval Augmented Generation)**

Example knowledge document:
```markdown
# ACT Refugee Support Services

## Emergency Services
- Emergency: 000 (Police, Fire, Ambulance)
- Mental Health Crisis: 1800 648 911
- Domestic Violence: 1800 RESPECT (1800 737 732)

## Key Support Organizations
- Companion House: Trauma counseling and support
- MARSS: Migrant and Refugee Settlement Services
- Red Cross: Emergency relief and support
```

#### Option B: Dynamic API Integration (Recommended)

### Step 4: Create Custom Functions for Database Access

In your Voiceflow AI Agent, create these functions:

```javascript
// Function: searchServices
{
  "name": "searchServices",
  "description": "Search the ACT refugee services database for relevant support services",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The user's query or need"
      },
      "category": {
        "type": "string",
        "enum": ["housing", "healthcare", "education", "employment", "legal", "emergency", "financial"],
        "description": "Service category if identified"
      },
      "urgency": {
        "type": "string",
        "enum": ["critical", "high", "medium", "low"],
        "description": "Urgency level of the request"
      },
      "language": {
        "type": "string",
        "description": "User's preferred language"
      }
    },
    "required": ["query"]
  },
  "implementation": async (params) => {
    const API_URL = 'https://act-refugee-support-production.up.railway.app/voiceflow';
    
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: params.query,
          category: params.category,
          urgency: params.urgency,
          language: params.language,
          limit: 3
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        return {
          success: true,
          services: data.resources,
          message: data.message,
          suggestions: data.quick_replies
        };
      }
      
      return {
        success: false,
        message: "Unable to find services at this time."
      };
    } catch (error) {
      return {
        success: false,
        message: "Connection error. Please try again."
      };
    }
  }
}
```

```javascript
// Function: getEmergencyServices
{
  "name": "getEmergencyServices",
  "description": "Immediately retrieve emergency and crisis services",
  "parameters": {
    "type": "object",
    "properties": {
      "type": {
        "type": "string",
        "enum": ["medical", "mental_health", "domestic_violence", "general"],
        "description": "Type of emergency"
      }
    }
  },
  "implementation": async (params) => {
    const API_URL = 'https://act-refugee-support-production.up.railway.app/search/emergency';
    
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        type: params.type || 'general'
      })
    });
    
    const data = await response.json();
    
    return {
      emergency_services: data.resources,
      immediate_action: "Call 000 for life-threatening emergencies",
      message: data.message
    };
  }
}
```

### Step 5: Configure AI Agent System Prompt

Set up your AI Agent's personality and behavior:

```markdown
You are the ACT Refugee & Migrant Support Assistant, providing culturally sensitive, 
practical support to migrants and refugees in the Australian Capital Territory.

## Your Core Responsibilities:
1. Provide accurate information about available services
2. Detect urgency and respond appropriately
3. Be culturally sensitive and empathetic
4. Offer services in multiple languages when possible
5. Never make assumptions about legal status

## When to Use Functions:
- Use `searchServices` when users ask about any support services
- Use `getEmergencyServices` immediately for crisis situations
- Always provide phone numbers and practical next steps

## Communication Style:
- Clear and simple English
- Avoid jargon and complex terms
- Be warm but professional
- Always offer interpreter services (131 450) if language is a barrier

## Important Guidelines:
- For emergencies, ALWAYS provide 000 first
- Include 131 450 (interpreter service) when language might be an issue
- Be sensitive to trauma and vulnerability
- Provide step-by-step guidance when needed
```

### Step 6: Enable Conversation Memory

In AI Agent settings, enable:
- **Conversation Memory**: Remember context within session
- **User Attributes**: Store language preference, location
- **Context Window**: Set to maximum (typically 4000 tokens)

---

## 🔧 Advanced Integration Features

### 1. Semantic Search with Vector Embeddings

Your Qdrant database already stores vector embeddings. The AI Agent can leverage this through your API:

```python
# In your api_v2_orchestrator.py
@app.post("/ai-agent/semantic-search")
async def semantic_search_for_agent(request: AgentSearchRequest):
    """
    Optimized endpoint for AI Agent semantic queries
    """
    # Convert query to embedding
    query_embedding = await get_embedding(request.query)
    
    # Search Qdrant with semantic similarity
    results = qdrant_client.search(
        collection_name="act_refugee_resources",
        query_vector=query_embedding,
        limit=5,
        score_threshold=0.7  # Relevance threshold
    )
    
    # Format for AI Agent consumption
    return {
        "results": format_for_agent(results),
        "confidence": calculate_confidence(results),
        "related_topics": extract_related_topics(results)
    }
```

### 2. Context-Aware Responses

The AI Agent can maintain context across the conversation:

```javascript
// In Voiceflow AI Agent
{
  "name": "updateUserContext",
  "description": "Update user context based on conversation",
  "parameters": {
    "type": "object",
    "properties": {
      "identified_needs": {
        "type": "array",
        "items": {"type": "string"}
      },
      "urgency_level": {"type": "string"},
      "language_preference": {"type": "string"},
      "previous_services": {"type": "array"}
    }
  }
}
```

### 3. Proactive Service Suggestions

Based on patterns in your Qdrant data:

```python
# Pattern detection for hidden needs
def detect_hidden_needs(query_history, services_accessed):
    """
    Analyze user interactions to suggest additional services
    """
    patterns = {
        "housing_to_employment": ["housing", "employment"],
        "visa_to_legal": ["visa", "legal", "migration"],
        "health_to_mental": ["doctor", "mental health", "counseling"]
    }
    
    suggestions = []
    for pattern_name, keywords in patterns.items():
        if any(kw in query_history for kw in keywords):
            suggestions.extend(get_related_services(pattern_name))
    
    return suggestions
```

---

## 🎯 Optimal Configuration for Your Use Case

Given your ACT Refugee Support Assistant requirements, here's the optimal setup:

### 1. Hybrid Approach: Knowledge Base + API

**Static Knowledge Base** for:
- Emergency contacts (000, 131 450)
- Basic service information
- Common procedures
- Rights and entitlements

**Dynamic API Calls** for:
- Specific service searches
- Real-time availability
- Personalized recommendations
- Complex queries requiring vector search

### 2. Multi-Modal Responses

Configure your AI Agent to provide:
- **Text responses** with service information
- **Cards** with contact details
- **Quick replies** for common follow-ups
- **Buttons** for immediate actions (call, website)

### 3. Fallback Handling

```javascript
// Fallback function when API is unavailable
{
  "name": "getOfflineEmergencyInfo",
  "description": "Provide emergency information when API is offline",
  "implementation": () => {
    return {
      emergency: {
        police_fire_ambulance: "000",
        interpreter_service: "131 450",
        mental_health_crisis: "1800 648 911",
        domestic_violence: "1800 737 732"
      },
      message: "Key emergency services are always available 24/7"
    };
  }
}
```

---

## 📊 Performance Optimization

### 1. Caching Strategy

Implement caching at the API level:

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def cached_vector_search(query_hash: str):
    """Cache frequent queries for 1 hour"""
    return perform_vector_search(query_hash)

def get_cached_results(query: str):
    query_hash = hashlib.md5(query.encode()).hexdigest()
    return cached_vector_search(query_hash)
```

### 2. Response Time Optimization

- **Pre-compute** common query embeddings
- **Index** frequently accessed services
- **Batch** multiple service lookups
- **Compress** response payloads

---

## 🔒 Security Considerations

### 1. API Authentication

Even though Voiceflow AI Agents handle authentication internally, secure your API:

```python
# In your Railway API
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.post("/ai-agent/search")
async def secure_search(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    if not verify_token(credentials.credentials):
        raise HTTPException(status_code=401)
    # Process request
```

### 2. Rate Limiting

Protect your Qdrant database:

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/ai-agent/search")
@limiter.limit("100/minute")
async def rate_limited_search():
    # Process request
```

---

## 🧪 Testing Your AI Agent Integration

### Test Scenarios

1. **Emergency Detection:**
   - "I need urgent medical help"
   - Expected: Immediate emergency services + 000

2. **Context Retention:**
   - "I need housing"
   - "Also looking for work"
   - Expected: Both housing and employment services

3. **Language Support:**
   - "I don't speak English well"
   - Expected: Interpreter services + simplified language

4. **Complex Queries:**
   - "My visa is expiring and I lost my job"
   - Expected: Legal aid + employment services + visa help

---

## 📈 Monitoring and Analytics

Track your AI Agent performance:

```python
# In your API
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Log to your analytics service
    log_analytics({
        "endpoint": request.url.path,
        "duration": duration,
        "status": response.status_code,
        "user_agent": "voiceflow-ai-agent"
    })
    
    return response
```

---

## 🎓 Best Practices

1. **Keep functions focused**: One function = one purpose
2. **Handle errors gracefully**: Always provide fallback information
3. **Optimize for speed**: Users need quick responses in crisis
4. **Test edge cases**: Multilingual queries, typos, unclear requests
5. **Monitor usage**: Track which services are most requested
6. **Update regularly**: Keep service information current

---

## 🚦 Quick Start Checklist

- [x] Railway API deployed and working
- [x] Qdrant database populated with services
- [ ] Voiceflow AI Agent created
- [ ] System prompt configured
- [ ] Functions created and tested
- [ ] Knowledge base populated (optional)
- [ ] Emergency fallbacks configured
- [ ] Testing completed
- [ ] Analytics enabled

---

## 💡 Summary

While Voiceflow AI Agents cannot directly connect to Qdrant, your current architecture with the Railway API gateway is actually the **optimal solution**. It provides:

1. **Security**: Database credentials stay private
2. **Flexibility**: Process and format data before sending to agent
3. **Reliability**: API can handle errors and provide fallbacks
4. **Scalability**: Can cache frequent queries
5. **Enhancement**: Add business logic and validation

Your deployed API at `https://act-refugee-support-production.up.railway.app` is perfectly suited to work with Voiceflow's AI Agent through function calling, providing intelligent, context-aware support to refugees and migrants in the ACT.

---

## 🆘 Need Help?

- **Voiceflow AI Agent Docs**: https://docs.voiceflow.com/ai-agents
- **Your API Docs**: https://act-refugee-support-production.up.railway.app/docs
- **Qdrant Docs**: https://qdrant.tech/documentation

The combination of Voiceflow's AI Agent with your Qdrant-powered API creates a powerful, compassionate support system for those who need it most.
