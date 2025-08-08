# Voiceflow Integration Guide for ACT Refugee Support API

## API Endpoint Information
- **Base URL**: `https://act-refugee-support-production.up.railway.app`
- **Main Endpoint**: `/voiceflow` (POST)
- **Health Check**: `/health` (GET)

## Step 1: Set up API Integration in Voiceflow

### 1.1 Add API Step in Your Flow
1. Open your Voiceflow project
2. Add an **API Step** block to your canvas
3. Configure the following settings:

**Request Type**: `POST`
**URL**: `https://act-refugee-support-production.up.railway.app/voiceflow`

### 1.2 Configure Headers
Add the following header:
```
Content-Type: application/json
```

### 1.3 Configure Request Body
Set the body type to `JSON` and use this template:
```json
{
  "query": "{user_input}",
  "user_id": "{user_id}",
  "language": "{language}",
  "category": "{category}"
}
```

## Step 2: Capture User Input

### 2.1 Add a Capture Step
Before the API call, add a **Capture** step to get the user's query:
- Variable name: `user_input`
- Type: Text
- Prompt: "How can I help you today? You can ask about housing, healthcare, education, employment, or any other support services."

### 2.2 Optional: Capture Language Preference
Add another Capture step for language:
- Variable name: `language`
- Type: Choice
- Options: English, Arabic, Farsi, Mandarin, Spanish

## Step 3: Handle API Response

### 3.1 Parse the Response
The API returns a JSON response with this structure:
```json
{
  "success": true,
  "message": "I found 3 services that can help you:",
  "resources": [
    {
      "name": "Service Name",
      "description": "Service description",
      "phone": "Contact number",
      "website": "URL",
      "location": "Address",
      "hours": "Operating hours",
      "services": "Available services",
      "languages": "Supported languages",
      "eligibility": "Who can access"
    }
  ],
  "quick_replies": ["Option 1", "Option 2", "Option 3"],
  "metadata": {
    "intent": "detected_intent",
    "results_count": 3
  }
}
```

### 3.2 Store Response Variables
In the API step, map the response to variables:
- `api_response` → Full response
- `api_message` → `response.message`
- `api_resources` → `response.resources`
- `api_quick_replies` → `response.quick_replies`

## Step 4: Display Results to User

### 4.1 Add a Speak/Text Step
Display the main message:
```
{api_message}
```

### 4.2 Display Resources (Loop)
Use a **Loop** step to iterate through resources:
1. Set loop variable: `current_resource`
2. Loop through: `{api_resources}`
3. Inside the loop, add a **Card** or **Text** step:

```
📍 {current_resource.name}
📝 {current_resource.description}
📞 {current_resource.phone}
🌐 {current_resource.website}
📍 {current_resource.location}
🕐 {current_resource.hours}
```

### 4.3 Add Quick Replies
After the loop, add a **Choice** step with quick replies:
- Use the `{api_quick_replies}` array for options

## Step 5: Handle Special Intents

### 5.1 Emergency Services
Create a separate flow for emergencies:
1. Add intent detection for keywords: "emergency", "urgent", "help now", "crisis"
2. Call the emergency endpoint directly:
   - URL: `https://act-refugee-support-production.up.railway.app/search/emergency`
   - Method: `POST`

### 5.2 Category-Specific Searches
Create buttons or choices for specific categories:
- Housing & Accommodation
- Healthcare & Medical
- Education & Training
- Employment & Jobs
- Legal Services
- Emergency Support

## Step 6: Error Handling

### 6.1 Add Error Path
In the API step, configure the error handling:
1. Create an error path from the API block
2. Add a fallback message:
```
I'm having trouble finding services right now. Please try:
- Calling 131 450 for translation services
- Visiting https://www.refugeecouncil.org.au
- Calling 000 for emergencies
```

### 6.2 No Results Handling
Check if `api_resources` is empty:
```javascript
if (!api_resources || api_resources.length === 0) {
  // Show alternative message
  "I couldn't find specific services matching your request, but here are some general resources that might help..."
}
```

## Step 7: Advanced Features

### 7.1 Multi-language Support
Create language-specific flows:
1. Detect user language at the start
2. Store in a variable: `user_language`
3. Pass to API in requests
4. Use conditional blocks to show responses in preferred language

### 7.2 Context Retention
Store conversation context:
- Previous queries
- User preferences
- Selected services
Pass context in API calls:
```json
{
  "query": "{user_input}",
  "context": {
    "previous_intent": "{last_intent}",
    "selected_category": "{category}"
  }
}
```

### 7.3 Follow-up Actions
After showing results, offer follow-ups:
- "Would you like more information about any of these services?"
- "Do you need help with anything else?"
- "Would you like me to translate this information?"

## Step 8: Testing Your Integration

### 8.1 Test API Connection
1. Use Voiceflow's test console
2. Try these test queries:
   - "I need help finding accommodation"
   - "Where can I get medical help?"
   - "Emergency services"
   - "I need a job"

### 8.2 Monitor Responses
Check that you receive:
- Relevant services
- Correct contact information
- Appropriate quick replies

## Sample Voiceflow Flow Structure

```
[Start]
    ↓
[Welcome Message]
    ↓
[Language Selection] (Optional)
    ↓
[Capture User Query]
    ↓
[API Call to /voiceflow]
    ↓
[Check Success]
    ├─ Success → [Display Message]
    │              ↓
    │          [Loop Through Resources]
    │              ↓
    │          [Show Quick Replies]
    │              ↓
    │          [Ask for More Help]
    │
    └─ Error → [Show Fallback Message]
                 ↓
             [Provide Emergency Contacts]
```

## Troubleshooting

### Common Issues and Solutions

1. **API Not Responding**
   - Check the API health: https://act-refugee-support-production.up.railway.app/health
   - Verify the URL is correct
   - Check Railway deployment status

2. **Empty Results**
   - Ensure query is being passed correctly
   - Check variable mapping in API step
   - Verify the request body format

3. **Authentication Errors**
   - If authentication is enabled, add API key to headers:
     ```
     Authorization: Bearer YOUR_API_KEY
     ```

4. **Parsing Errors**
   - Ensure response mapping uses correct JSON paths
   - Use dot notation for nested properties

## Support and Updates

- **API Documentation**: Check `/docs` endpoint (if FastAPI docs enabled)
- **Railway Dashboard**: Monitor at https://railway.app
- **Test Endpoint**: Use `/health` to verify API status

## Example Conversation Flow

**User**: "I need help finding a place to live"

**Bot**: "I found 3 services that can help you:

📍 Capital Region Community Services
- Housing support and homelessness services
- Phone: (02) 6126 9000
- Hours: Mon-Fri 9am-5pm

📍 Canberra Refugee Support
- Practical support for refugees
- Email: info@canberrarefugeesupport.org.au

📍 YWCA Canberra - Multicultural Hub
- Support for migrant and refugee families
- Phone: (02) 6185 2000

Would you like to know more about:
- Emergency shelter
- Rental help
- Share house options
- Bond assistance"

**User**: "Emergency shelter"

**Bot**: [Continues with emergency housing information...]
