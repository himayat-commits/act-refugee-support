# Voiceflow API Integration Guide

## Quick Start - Connect Your Voiceflow Agent to the Backend API

This guide will help you connect your Voiceflow agent to the ACT Refugee Support backend API in simple steps.

---

## 🚀 Step 1: Deploy the Backend API

### Option A: Local Development (For Testing)

1. **Install Docker** (if not already installed):
   - Download Docker Desktop from https://www.docker.com/products/docker-desktop

2. **Start Qdrant Vector Database**:
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

3. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create Environment File**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add:
   ```
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   QDRANT_API_KEY=optional_for_local
   ENABLE_AUTH=false
   API_KEY=your_secret_key_here
   ```

5. **Initialize the Database**:
   ```bash
   python main.py
   ```

6. **Start the API Server**:
   ```bash
   python api_server.py
   ```
   Your API will be available at: `http://localhost:8000`

### Option B: Production Deployment (Recommended)

#### Deploy to Railway.app (Easiest):

1. **Push code to GitHub**
2. **Go to Railway.app** and sign in
3. **Create New Project** → Deploy from GitHub repo
4. **Add Qdrant Service**:
   - Click "New" → "Database" → Search for "Qdrant"
5. **Set Environment Variables**:
   ```
   QDRANT_HOST=qdrant.railway.internal
   QDRANT_PORT=6333
   ENABLE_AUTH=true
   API_KEY=generate_secure_key_here
   ```
6. **Deploy** - Railway will provide you with a public URL like:
   `https://your-app.railway.app`

---

## 🔌 Step 2: Configure Voiceflow Integration

### In Your Voiceflow Project:

1. **Open your Voiceflow Assistant**
2. **Go to Functions** (in the left sidebar)
3. **Create a New Function** called `searchResources`:

```javascript
// Voiceflow Function: searchResources
export default async function main(args) {
  const { query, category, urgency, language, limit = 3 } = args;
  
  // Your API endpoint (change this to your deployed URL)
  const API_URL = 'https://your-app.railway.app/search';
  const API_KEY = 'your_api_key_here'; // Store in Voiceflow variables
  
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`
      },
      body: JSON.stringify({
        message: query,
        category: category,
        urgency: urgency,
        language: language,
        limit: limit
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Store resources in Voiceflow variables
      return {
        success: true,
        message: data.message,
        resources: data.resources,
        quickReplies: data.quick_replies
      };
    }
    
    return {
      success: false,
      message: "I couldn't find any resources. Please try different keywords."
    };
    
  } catch (error) {
    console.error('API Error:', error);
    return {
      success: false,
      message: "I'm having trouble connecting to the database. Please try again."
    };
  }
}
```

4. **Create Variables** in Voiceflow:
   - `user_query` (text) - Stores user's message
   - `search_results` (object) - Stores API response
   - `api_key` (text) - Your API key (set as environment variable)

---

## 📝 Step 3: Create Conversation Flow

### Basic Flow Setup:

1. **Start Block** → Connect to:

2. **Capture Block** (User Input):
   - Prompt: "How can I help you today?"
   - Save response to: `{user_query}`

3. **Function Block**:
   - Select function: `searchResources`
   - Parameters:
     - query: `{user_query}`
     - limit: `3`
   - Save result to: `{search_results}`

4. **Condition Block**:
   - If `{search_results.success}` is `true` → Go to Success Response
   - Else → Go to Error Response

5. **Success Response Block** (Text):
   ```
   {search_results.message}

   {{#each search_results.resources}}
   📍 **{{name}}**
   📞 {{phone}}
   🕐 {{available}}
   📝 {{description}}
   
   {{/each}}
   ```

6. **Choice Block** (Quick Replies):
   - Add buttons from `{search_results.quickReplies}`

### Advanced Intent Detection:

Create specific intents in Voiceflow for common queries:

- **Emergency Intent**: "emergency", "urgent", "help now", "crisis"
  → Trigger: Call `/search/emergency` endpoint

- **Housing Intent**: "accommodation", "housing", "shelter", "homeless"
  → Set category: "housing" before calling API

- **Job Intent**: "job", "work", "employment", "career"
  → Call `/search/economic` endpoint

- **Medical Intent**: "doctor", "medical", "health", "hospital"
  → Set category: "healthcare" and urgency: "high"

---

## 🔑 Step 4: API Endpoints Reference

### Main Endpoints:

1. **General Search**
   ```
   POST /search
   Body: {
     "message": "user query",
     "category": "optional",
     "urgency": "optional",
     "language": "optional",
     "limit": 3
   }
   ```

2. **Emergency Services**
   ```
   POST /search/emergency
   No body required - returns critical services
   ```

3. **Economic Integration**
   ```
   POST /search/economic
   Body: {
     "message": "job/skill/business query",
     "limit": 3
   }
   ```

4. **Health Check**
   ```
   GET /health
   Returns API status
   ```

---

## 🧪 Step 5: Test Your Integration

### In Voiceflow Test Console:

Test these queries:
1. "I need emergency medical help"
2. "Where can I find English classes?"
3. "I need help with my visa"
4. "I want to start a business"
5. "I need housing assistance"

### Expected Responses:
- Each query should return 1-3 relevant resources
- Emergency queries should prioritize 24/7 services
- Resources should include contact details and descriptions

---

## 🔒 Step 6: Security Setup

### For Production:

1. **Enable Authentication** in `.env`:
   ```
   ENABLE_AUTH=true
   API_KEY=generate_32_char_random_string
   ```

2. **Store API Key Securely** in Voiceflow:
   - Go to Settings → Environment Variables
   - Add `API_KEY` as a secret variable

3. **Use HTTPS Only**:
   - Ensure your deployed API uses HTTPS
   - Railway/Render provide this automatically

---

## 📊 Step 7: Monitor & Maintain

### Logging:
- API logs all queries for monitoring
- Check logs in your deployment platform

### Update Resources:
```bash
# To add/update resources:
1. Edit act_resources_data.py
2. Run: python main.py
3. Restart API server
```

### Rate Limiting (Optional):
Add to `api_server.py` if needed:
```python
from slowapi import Limiter
limiter = Limiter(key_func=lambda: request.client.host)
app.state.limiter = limiter

@app.post("/search")
@limiter.limit("30/minute")
async def search_resources(...):
```

---

## 🎯 Example Voiceflow Responses

### For Emergency:
```
User: "I need urgent help"
Bot: "⚠️ EMERGENCY SERVICES - Available 24/7:
🚨 Triple Zero (000)
📞 000
🕐 24/7 Emergency
📝 Police, Fire, Ambulance - Life threatening emergencies

🚨 Mental Health Crisis Team
📞 1800 648 911
🕐 24/7 Crisis Support
📝 Immediate mental health crisis intervention"
```

### For General Query:
```
User: "I need help finding work"
Bot: "I found 3 services that can help you:

📍 JobActive Canberra
📞 02 6247 7755
🕐 Mon-Fri 9am-5pm
📝 Free employment services, job matching, resume help

📍 MARSS Employment Support
📞 02 6248 8577
🕐 Mon-Fri 9am-4pm
📝 Specialized migrant employment programs"
```

---

## 🆘 Troubleshooting

### Common Issues:

1. **"Cannot connect to database"**
   - Check Qdrant is running: `docker ps`
   - Verify QDRANT_HOST in .env

2. **"401 Unauthorized"**
   - Check API_KEY matches in both .env and Voiceflow
   - Ensure Authorization header is sent

3. **"No resources found"**
   - Run `python main.py` to populate database
   - Check search query spelling

4. **Slow responses**
   - Ensure adequate server resources
   - Consider caching frequent queries

---

## 📚 Additional Resources

- **API Documentation**: http://your-api-url/docs
- **Voiceflow Docs**: https://docs.voiceflow.com
- **Support**: Create an issue in the GitHub repository

---

## ✅ Checklist

Before going live:
- [ ] Database populated with resources
- [ ] API deployed and accessible
- [ ] Authentication enabled
- [ ] Voiceflow function created
- [ ] Variables configured
- [ ] Flow tested with sample queries
- [ ] Error handling implemented
- [ ] Quick replies configured
- [ ] Production API key secured

---

**Need help?** The API includes Swagger documentation at `/docs` endpoint for interactive testing.
