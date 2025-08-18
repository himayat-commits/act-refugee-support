// Voiceflow Function Code for ACT Refugee Support Bot
// Copy these functions into your Voiceflow Function blocks

// Function 1: Process API Response
// Use this after your API call to format the response
async function processAPIResponse() {
  // Get the API response
  const response = api_response;
  
  if (!response || !response.success) {
    // Handle error
    message = "I'm having trouble finding services right now. For immediate help, call 000 for emergencies or 131 450 for translation services.";
    return;
  }
  
  // Format the main message
  message = response.message || "Here are the services I found:";
  
  // Store resources for display
  resources = response.resources || [];
  quick_replies = response.quick_replies || [];
  
  // Create formatted text for each resource
  let formattedResources = [];
  
  for (let i = 0; i < resources.length; i++) {
    const resource = resources[i];
    let formatted = `📍 **${resource.name}**\n`;
    
    if (resource.description) {
      formatted += `${resource.description}\n\n`;
    }
    
    if (resource.phone) {
      formatted += `📞 Phone: ${resource.phone}\n`;
    }
    
    if (resource.website) {
      formatted += `🌐 Website: ${resource.website}\n`;
    }
    
    if (resource.location) {
      formatted += `📍 Location: ${resource.location}\n`;
    }
    
    if (resource.hours) {
      formatted += `🕐 Hours: ${resource.hours}\n`;
    }
    
    if (resource.languages) {
      formatted += `🗣️ Languages: ${resource.languages}\n`;
    }
    
    formattedResources.push(formatted);
  }
  
  // Store formatted resources
  formatted_resources = formattedResources;
  
  // Store metadata
  intent = response.metadata?.intent || "general";
  results_count = response.metadata?.results_count || 0;
}

// Function 2: Detect Intent
// Use this to detect the user's intent from their message
function detectIntent() {
  const userInput = user_input.toLowerCase();
  
  // Emergency detection
  const emergencyKeywords = ["emergency", "urgent", "help now", "crisis", "danger", "police", "ambulance", "000"];
  if (emergencyKeywords.some(keyword => userInput.includes(keyword))) {
    detected_intent = "emergency";
    should_use_emergency_api = true;
    return;
  }
  
  // Housing detection
  const housingKeywords = ["accommodation", "housing", "shelter", "homeless", "rent", "share house", "place to live", "temporary housing"];
  if (housingKeywords.some(keyword => userInput.includes(keyword))) {
    detected_intent = "housing";
    category = "housing";
    return;
  }
  
  // Healthcare detection
  const healthKeywords = ["doctor", "medical", "health", "hospital", "clinic", "mental health", "counseling", "therapy", "sick", "unwell"];
  if (healthKeywords.some(keyword => userInput.includes(keyword))) {
    detected_intent = "healthcare";
    category = "healthcare";
    return;
  }
  
  // Education detection
  const educationKeywords = ["school", "education", "training", "english class", "study", "university", "tafe", "course", "learn"];
  if (educationKeywords.some(keyword => userInput.includes(keyword))) {
    detected_intent = "education";
    category = "education";
    return;
  }
  
  // Employment detection
  const employmentKeywords = ["job", "work", "employment", "career", "skills", "qualification", "resume", "interview", "hire"];
  if (employmentKeywords.some(keyword => userInput.includes(keyword))) {
    detected_intent = "employment";
    category = "employment";
    return;
  }
  
  // Legal detection
  const legalKeywords = ["visa", "legal", "lawyer", "immigration", "rights", "protection", "citizenship", "passport"];
  if (legalKeywords.some(keyword => userInput.includes(keyword))) {
    detected_intent = "legal";
    category = "legal";
    return;
  }
  
  // Financial detection
  const financialKeywords = ["money", "financial", "centrelink", "payment", "support payment", "benefit", "allowance"];
  if (financialKeywords.some(keyword => userInput.includes(keyword))) {
    detected_intent = "financial";
    category = "financial";
    return;
  }
  
  // Default
  detected_intent = "general";
  category = "general";
}

// Function 3: Generate Follow-up Questions
// Use this to create contextual follow-up questions
function generateFollowUpQuestions() {
  const intent = detected_intent || "general";
  
  let followUps = [];
  
  switch(intent) {
    case "housing":
      followUps = [
        "Do you need emergency accommodation?",
        "Are you looking for long-term housing?",
        "Do you need help with rental applications?",
        "Would you like bond assistance information?"
      ];
      break;
      
    case "healthcare":
      followUps = [
        "Do you need to find a GP?",
        "Are you looking for mental health support?",
        "Do you need hospital information?",
        "Would you like interpreter services?"
      ];
      break;
      
    case "education":
      followUps = [
        "Are you looking for English classes?",
        "Do you need school enrollment help?",
        "Are you interested in vocational training?",
        "Do you need qualification recognition?"
      ];
      break;
      
    case "employment":
      followUps = [
        "Do you need help finding job opportunities?",
        "Would you like resume assistance?",
        "Do you need skills recognition?",
        "Are you looking for career counseling?"
      ];
      break;
      
    case "emergency":
      followUps = [
        "Do you need immediate medical help?",
        "Are you in a dangerous situation?",
        "Do you need crisis accommodation?",
        "Would you like to speak to a counselor?"
      ];
      break;
      
    default:
      followUps = [
        "Would you like help with housing?",
        "Do you need healthcare services?",
        "Are you looking for education options?",
        "Can I help you find employment services?"
      ];
  }
  
  follow_up_questions = followUps;
}

// Function 4: Format Card Display
// Use this to format a single resource as a card
function formatResourceCard() {
  const resource = current_resource;
  
  if (!resource) {
    card_title = "Service Information";
    card_text = "No information available";
    return;
  }
  
  // Set card title
  card_title = resource.name || "Service";
  
  // Build card text
  let text = "";
  
  if (resource.description) {
    text += resource.description + "\n\n";
  }
  
  if (resource.phone) {
    text += "📞 " + resource.phone + "\n";
  }
  
  if (resource.website) {
    text += "🌐 " + resource.website + "\n";
  }
  
  if (resource.location) {
    text += "📍 " + resource.location + "\n";
  }
  
  if (resource.hours) {
    text += "🕐 " + resource.hours + "\n";
  }
  
  card_text = text;
  
  // Set card buttons if applicable
  card_buttons = [];
  
  if (resource.phone) {
    card_buttons.push({
      name: "Call",
      value: resource.phone
    });
  }
  
  if (resource.website) {
    card_buttons.push({
      name: "Visit Website",
      value: resource.website
    });
  }
}

// Function 5: Check for No Results
// Use this to handle cases where no resources were found
function checkNoResults() {
  const resources = api_resources || [];
  
  if (resources.length === 0) {
    has_results = false;
    
    // Provide alternative message based on intent
    const intent = detected_intent || "general";
    
    switch(intent) {
      case "housing":
        no_results_message = "I couldn't find specific housing services, but try:\n• Calling ACT Housing on 133 427\n• Visiting OneLink at 1/6 Gritten St, Weston\n• Calling 000 if you need emergency shelter tonight";
        break;
        
      case "healthcare":
        no_results_message = "I couldn't find specific health services, but try:\n• Calling HealthDirect on 1800 022 222\n• Visiting your nearest hospital emergency department\n• Calling 000 for medical emergencies";
        break;
        
      case "education":
        no_results_message = "I couldn't find specific education services, but try:\n• Calling the Education Directorate on (02) 6207 5111\n• Visiting CIT for adult education options\n• Contacting your local school directly";
        break;
        
      default:
        no_results_message = "I couldn't find specific services matching your request. Try:\n• Calling 131 450 for translation help\n• Visiting a Centrelink office\n• Calling 000 for emergencies";
    }
  } else {
    has_results = true;
    no_results_message = "";
  }
}

// Function 6: Language Detection
// Use this to detect if the user needs language support
function detectLanguageNeeds() {
  const userInput = user_input.toLowerCase();
  
  // Arabic indicators
  if (userInput.includes("عربي") || userInput.includes("arabic")) {
    preferred_language = "Arabic";
    needs_interpreter = true;
    return;
  }
  
  // Farsi/Persian indicators
  if (userInput.includes("فارسی") || userInput.includes("farsi") || userInput.includes("persian")) {
    preferred_language = "Farsi";
    needs_interpreter = true;
    return;
  }
  
  // Chinese indicators
  if (userInput.includes("中文") || userInput.includes("chinese") || userInput.includes("mandarin")) {
    preferred_language = "Mandarin";
    needs_interpreter = true;
    return;
  }
  
  // Spanish indicators
  if (userInput.includes("español") || userInput.includes("spanish")) {
    preferred_language = "Spanish";
    needs_interpreter = true;
    return;
  }
  
  // Check for interpreter request
  if (userInput.includes("interpreter") || userInput.includes("translator") || userInput.includes("language help")) {
    needs_interpreter = true;
    interpreter_message = "For interpreter services, call 131 450 (available 24/7)";
    return;
  }
  
  preferred_language = "English";
  needs_interpreter = false;
}
