# Voiceflow Function Setup Guide

## How to Add the searchServices Function to Voiceflow

### Step 1: Open Function Editor
1. Go to your Voiceflow project
2. Click on **Functions** in the left sidebar
3. Click **"+ New Function"**
4. Name it: `searchServices`

### Step 2: Copy the Correct Code

**IMPORTANT**: Do NOT copy the JSON schema format. Copy this exact JavaScript code:

```javascript
export default async function main(args) {
  // Extract parameters from args
  const { query, category, urgency, language, limit = 3 } = args;
  
  // Your Railway API endpoint
  const API_URL = 'https://act-refugee-support-production.up.railway.app/voiceflow';
  
  try {
    // Make API request
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: query || '',
        category: category || null,
        urgency: urgency || null,
        language: language || null,
        limit: limit
      })
    });
    
    // Check if response is ok
    if (!response.ok) {
      throw new Error(`API returned status ${response.status}`);
    }
    
    // Parse response
    const data = await response.json();
    
    // Check if we got successful response
    if (data.success) {
      // Format services for easier display
      const formattedServices = data.resources.map(service => ({
        name: service.name,
        description: service.description,
        phone: service.phone || 'Not available',
        website: service.website || 'Not available',
        location: service.location || service.address || 'Not specified',
        services: service.services || '',
        urgency: service.urgency || 'normal'
      }));
      
      return {
        success: true,
        message: data.message || `I found ${formattedServices.length} services that can help:`,
        services: formattedServices,
        suggestions: data.quick_replies || [],
        count: formattedServices.length
      };
    } else {
      // API returned success: false
      return {
        success: false,
        message: data.message || "I couldn't find services matching your request.",
        services: [],
        suggestions: ["Try different keywords", "Call 131 450 for interpreter", "Call 000 for emergency"]
      };
    }
    
  } catch (error) {
    console.error('Error calling API:', error);
    
    // Return fallback emergency information on error
    return {
      success: false,
      message: "I'm having trouble connecting right now. Here are emergency contacts you can use:",
      services: [
        {
          name: "Emergency Services",
          description: "Police, Fire, Ambulance",
          phone: "000",
          website: "",
          location: "Australia-wide",
          services: "Life-threatening emergencies",
          urgency: "critical"
        },
        {
          name: "Interpreter Service",
          description: "24/7 phone interpretation in your language",
          phone: "131 450",
          website: "www.tisnational.gov.au",
          location: "Australia-wide",
          services: "Translation and interpretation",
          urgency: "high"
        },
        {
          name: "Mental Health Crisis",
          description: "24/7 mental health crisis support",
          phone: "1800 648 911",
          website: "",
          location: "ACT",
          services: "Mental health emergency support",
          urgency: "critical"
        }
      ],
      suggestions: ["Try again", "Emergency contacts", "Get help another way"],
      error: true
    };
  }
}
```

### Step 3: Save and Test

1. Click **"Save"** in the function editor
2. Click **"Test"** to open the test panel
3. Add test parameters:
```json
{
  "query": "I need help finding housing"
}
```
4. Click **"Run Test"**

### Step 4: Use in Your Flow

#### For AI Agent:
1. In your agent's system prompt, mention the function:
```
When users ask for help finding services, use the searchServices function.
```

2. The AI Agent will automatically call it when appropriate.

#### For Step-Based Flow:
1. Add a **Function** step to your canvas
2. Select `searchServices` from the dropdown
3. Map variables:
   - `query` → `{last_utterance}` or a captured variable
   - `category` → (optional) from intent detection
   - `urgency` → (optional) based on keywords
   - `language` → (optional) user preference

4. Save output to a variable:
   - Variable name: `search_result`
   - Type: Object

### Step 5: Display Results

Add a **Text** step after the function:

```
{search_result.message}

{{#if search_result.services}}
  {{#each search_result.services}}
    📍 **{{name}}**
    📞 Phone: {{phone}}
    📝 {{description}}
    📍 Location: {{location}}
    
  {{/each}}
{{/if}}
```

## Common Errors and Solutions

### Error: "Unexpected token ':'"
**Cause**: You copied the JSON schema format instead of JavaScript
**Solution**: Copy the JavaScript function code (with `export default async function`)

### Error: "fetch is not defined"
**Cause**: Older Voiceflow runtime
**Solution**: Use axios instead:
```javascript
const axios = require('axios');
// Replace fetch with axios.post
```

### Error: "Cannot read property 'resources' of undefined"
**Cause**: API response structure different than expected
**Solution**: Add more defensive coding:
```javascript
const formattedServices = (data.resources || []).map(service => ({
  // ... mapping code
}));
```

### Error: "Network request failed"
**Cause**: API is down or URL is wrong
**Solution**: Check if API is running at https://act-refugee-support-production.up.railway.app/health

## Testing Your Function

### Test Cases to Try:

1. **Basic search**:
```json
{
  "query": "I need medical help"
}
```

2. **With category**:
```json
{
  "query": "where can I find a doctor",
  "category": "healthcare"
}
```

3. **Emergency**:
```json
{
  "query": "urgent help needed",
  "urgency": "critical"
}
```

4. **With language**:
```json
{
  "query": "I need help",
  "language": "Arabic"
}
```

## Alternative: Simple Function Version

If you're having issues, try this simplified version:

```javascript
export default async function main(args) {
  const query = args.query || "general help";
  
  try {
    const response = await fetch('https://act-refugee-support-production.up.railway.app/voiceflow', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query, limit: 3 })
    });
    
    const data = await response.json();
    
    if (data.success && data.resources) {
      return {
        success: true,
        message: `Found ${data.resources.length} services`,
        services: data.resources
      };
    }
    
    throw new Error("No services found");
    
  } catch (error) {
    return {
      success: false,
      message: "Please call 000 for emergency or 131 450 for interpreter services",
      services: []
    };
  }
}
```

## Function for Emergency Services

Create another function called `getEmergencyServices`:

```javascript
export default async function main(args) {
  // Always return emergency numbers immediately
  return {
    success: true,
    message: "⚠️ EMERGENCY CONTACTS - Available 24/7:",
    services: [
      {
        name: "Emergency (Police, Fire, Ambulance)",
        phone: "000",
        description: "Life threatening emergencies"
      },
      {
        name: "Interpreter Service",
        phone: "131 450",
        description: "24/7 interpretation"
      },
      {
        name: "Mental Health Crisis",
        phone: "1800 648 911",
        description: "Mental health emergencies"
      }
    ],
    critical: true
  };
}
```

## Next Steps

1. ✅ Function created and tested
2. ✅ Connected to your flow/agent
3. ✅ Test with real queries
4. ✅ Add error handling
5. ✅ Monitor API logs

## Support

- Check if API is running: https://act-refugee-support-production.up.railway.app/health
- View API docs: https://act-refugee-support-production.up.railway.app/docs
- Test function in Voiceflow's test panel before using in flow
