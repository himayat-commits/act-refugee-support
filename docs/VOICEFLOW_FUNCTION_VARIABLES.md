# Voiceflow Function Variables & Configuration Guide

## searchServices Function - Complete Setup

### 1️⃣ INPUT VARIABLES

When setting up the function step in Voiceflow, configure these input parameters:

| Variable Name | Type | Required | Default Value | Description | Example Mapping |
|--------------|------|----------|---------------|-------------|-----------------|
| `query` | Text | **Yes** | - | User's search query | `{last_utterance}` or `{user_query}` |
| `category` | Text | No | null | Service category filter | `{detected_category}` |
| `urgency` | Text | No | null | Urgency level (critical/high/medium/low) | `{urgency_level}` |
| `language` | Text | No | null | User's preferred language | `{user_language}` |
| `limit` | Number | No | 3 | Maximum results to return | `3` |

#### How to Set Input Variables in Voiceflow:

1. **In Function Step**, click on "Parameters"
2. Add each parameter:
   ```
   query: {last_utterance}
   category: {category_var}
   urgency: {urgency_var}
   language: {user_language}
   limit: 3
   ```

### 2️⃣ OUTPUT VARIABLES

The function returns an object with these properties:

| Output Path | Type | Description | How to Access in Voiceflow |
|------------|------|-------------|---------------------------|
| `success` | Boolean | Whether the search was successful | `{function_result.success}` |
| `message` | Text | Main response message | `{function_result.message}` |
| `services` | Array | Array of service objects | `{function_result.services}` |
| `services[0].name` | Text | First service name | `{function_result.services[0].name}` |
| `services[0].phone` | Text | First service phone | `{function_result.services[0].phone}` |
| `services[0].description` | Text | First service description | `{function_result.services[0].description}` |
| `services[0].location` | Text | First service location | `{function_result.services[0].location}` |
| `suggestions` | Array | Quick reply suggestions | `{function_result.suggestions}` |
| `count` | Number | Number of services found | `{function_result.count}` |
| `error` | Boolean | Whether an error occurred | `{function_result.error}` |

#### How to Store Output in Voiceflow:

1. **In Function Step**, under "Output":
   - Variable name: `function_result` (or any name you prefer)
   - Type: Object

### 3️⃣ COMPLETE VOICEFLOW SETUP

#### Step A: Create Variables First

Go to Variables section and create:

```yaml
Variables to Create:
  # Input Variables
  - user_query: (Text) - Stores user's question
  - detected_category: (Text) - Optional category from intent
  - urgency_level: (Text) - Detected urgency
  - user_language: (Text) - User's language preference
  
  # Output Variables
  - function_result: (Object) - Stores complete function response
  - service_count: (Number) - Number of services found
  - service_list: (Array) - List of services
  - error_occurred: (Boolean) - Error flag
```

#### Step B: Function Step Configuration

In your Function step:

```javascript
// INPUTS Section
{
  "query": "{user_query}",
  "category": "{detected_category}",
  "urgency": "{urgency_level}",
  "language": "{user_language}",
  "limit": 3
}

// OUTPUT Section
Variable: function_result
Type: Object
```

### 4️⃣ PATHS FOR DIFFERENT SCENARIOS

#### Path 1: Success Path ✅
```
Condition: {function_result.success} == true
Actions:
  1. Display {function_result.message}
  2. Loop through {function_result.services}
  3. Show quick replies from {function_result.suggestions}
```

#### Path 2: No Results Path ⚠️
```
Condition: {function_result.success} == false AND {function_result.error} != true
Actions:
  1. Display {function_result.message}
  2. Show fallback options
  3. Offer to search differently
```

#### Path 3: Error Path ❌
```
Condition: {function_result.error} == true
Actions:
  1. Display emergency contacts
  2. Show {function_result.message}
  3. Provide offline help options
```

### 5️⃣ DISPLAY TEMPLATES

#### Template 1: Display All Services
```handlebars
{{function_result.message}}

{{#if function_result.services}}
  {{#each function_result.services}}
    📍 **{{this.name}}**
    📞 Phone: {{this.phone}}
    📝 {{this.description}}
    📍 Location: {{this.location}}
    🔗 Website: {{this.website}}
    ━━━━━━━━━━━━━━━━━━
  {{/each}}
{{else}}
  No services found. Please try different keywords.
{{/if}}
```

#### Template 2: Display as Cards
```javascript
// In a Code step after function
const services = function_result.services || [];

services.forEach(service => {
  addCard({
    title: service.name,
    description: service.description,
    image: "https://example.com/default-service-icon.png",
    buttons: [
      {
        name: "Call " + service.phone,
        type: "call",
        value: service.phone
      },
      {
        name: "Visit Website",
        type: "url",
        value: service.website || "https://www.refugeecouncil.org.au"
      }
    ]
  });
});
```

#### Template 3: Quick Replies
```javascript
// Add quick reply buttons
const suggestions = function_result.suggestions || [
  "Find other services",
  "Emergency contacts",
  "Speak to someone"
];

addQuickReplies(suggestions);
```

### 6️⃣ CONDITIONAL BRANCHING

#### Set up IF conditions after function:

```yaml
IF Block Configuration:
  
  Condition 1: Emergency Detected
    If: {function_result.services[0].urgency} == "critical"
    Then: Go to Emergency Flow
  
  Condition 2: Multiple Services Found
    If: {function_result.count} > 1
    Then: Go to Service Selection Flow
  
  Condition 3: No Services Found
    If: {function_result.count} == 0
    Then: Go to Fallback Flow
  
  Else: Display Single Service
```

### 7️⃣ EXAMPLE FLOWS

#### Flow 1: Basic Search
```
1. Capture Step
   - Prompt: "What kind of help do you need?"
   - Save to: {user_query}

2. Function Step
   - Function: searchServices
   - Input: query = {user_query}
   - Output: {function_result}

3. Text Step
   - Display: {function_result.message}

4. Loop Step
   - Through: {function_result.services}
   - Display each service
```

#### Flow 2: Category-Based Search
```
1. Choice Step
   - Options: Housing, Healthcare, Employment, Education
   - Save to: {detected_category}

2. Capture Step
   - Prompt: "Tell me more about what you need"
   - Save to: {user_query}

3. Function Step
   - Function: searchServices
   - Inputs:
     - query = {user_query}
     - category = {detected_category}
   - Output: {function_result}

4. Conditional Display
   - Based on {function_result.success}
```

#### Flow 3: Emergency Detection
```
1. Capture Step
   - Save to: {user_query}

2. Code Step (Detect Emergency)
   - Check for emergency keywords
   - Set {urgency_level} = "critical" if found

3. Function Step
   - Function: searchServices
   - Inputs:
     - query = {user_query}
     - urgency = {urgency_level}
   - Output: {function_result}

4. IF Step
   - If {urgency_level} == "critical"
   - Then: Immediate emergency display
   - Else: Normal display
```

### 8️⃣ ACCESSING NESTED DATA

#### To access specific service details:

```javascript
// First service name
{function_result.services[0].name}

// Second service phone
{function_result.services[1].phone}

// Last service (using code step)
const services = function_result.services;
const lastService = services[services.length - 1];
```

#### Loop through all services:

```handlebars
{{#each function_result.services}}
  Service {{@index}}: {{this.name}}
  Contact: {{this.phone}}
{{/each}}
```

### 9️⃣ ERROR HANDLING

#### Always include error handling:

```javascript
// In an IF step after function
Condition: {function_result.error} == true

Then Path:
  Text: "I'm having connection issues. Here are emergency contacts:"
  Text: "🚨 Emergency: 000"
  Text: "🗣️ Interpreter: 131 450"
  Text: "🧠 Mental Health Crisis: 1800 648 911"
```

### 🔟 TESTING VALUES

#### Test your function with these inputs:

```javascript
// Test 1: Basic Search
{
  "query": "I need help finding housing"
}

// Test 2: With Category
{
  "query": "medical assistance",
  "category": "healthcare"
}

// Test 3: Emergency
{
  "query": "urgent help needed",
  "urgency": "critical"
}

// Test 4: With Language
{
  "query": "help with visa",
  "language": "Arabic",
  "category": "legal"
}

// Test 5: Limited Results
{
  "query": "employment services",
  "limit": 1
}
```

### 📋 COMPLETE VARIABLE REFERENCE

```yaml
# Create these variables in Voiceflow

Input Variables:
  user_query: Text
  detected_category: Text (optional)
  urgency_level: Text (optional)
  user_language: Text (optional)
  search_limit: Number (default: 3)

Output Variables:
  function_result: Object (main output)
  
Derived Variables (set using Set steps):
  has_results: Boolean = {function_result.success}
  service_count: Number = {function_result.count}
  first_service_name: Text = {function_result.services[0].name}
  first_service_phone: Text = {function_result.services[0].phone}
  error_message: Text = {function_result.message}
  suggestions_list: Array = {function_result.suggestions}
```

### 🎯 QUICK SETUP CHECKLIST

- [ ] Create all input variables in Voiceflow
- [ ] Create function_result output variable (Object type)
- [ ] Add Function step to canvas
- [ ] Configure input parameters
- [ ] Set output to function_result
- [ ] Add Text step to display {function_result.message}
- [ ] Add Loop or Cards to show services
- [ ] Add IF conditions for error handling
- [ ] Test with sample queries
- [ ] Add quick replies from suggestions

### 💡 PRO TIPS

1. **Always check success first**: Use IF condition to check `{function_result.success}`
2. **Handle empty arrays**: Check if `{function_result.count} > 0` before looping
3. **Provide fallbacks**: Always have emergency contacts available
4. **Use cards for services**: Better UX than plain text
5. **Save important values**: Store phone numbers in variables for quick access
6. **Test edge cases**: Empty results, network errors, malformed queries

---

## Need Help?

- Test your API: https://act-refugee-support-production.up.railway.app/health
- View API docs: https://act-refugee-support-production.up.railway.app/docs
- Function returns undefined? Check variable names and paths
- Services not displaying? Check the loop configuration
