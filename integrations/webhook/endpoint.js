// Webhook Endpoint for Voiceflow Integration
// This can be deployed on platforms like Vercel, Netlify Functions, or AWS Lambda

const VoiceflowServiceConnector = require('./voiceflow-api-connector');

// Initialize the connector
const connector = new VoiceflowServiceConnector({
    voiceflowAPIKey: process.env.VOICEFLOW_API_KEY,
    voiceflowVersionID: process.env.VOICEFLOW_VERSION_ID
});

// Main webhook handler
exports.handler = async (event, context) => {
    // Enable CORS
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
    };

    // Handle preflight requests
    if (event.httpMethod === 'OPTIONS') {
        return {
            statusCode: 200,
            headers,
            body: ''
        };
    }

    try {
        // Parse the request body
        const body = JSON.parse(event.body);
        
        // Extract request type and data
        const { action, data } = body;

        let response;

        switch (action) {
            case 'process_request':
                // Process user request for service matching
                response = await handleServiceRequest(data);
                break;
                
            case 'get_service_details':
                // Get detailed information about a specific service
                response = await getServiceDetails(data.serviceId);
                break;
                
            case 'send_referral':
                // Send referral via SMS or email
                response = await sendReferral(data);
                break;
                
            case 'check_eligibility':
                // Check eligibility for specific services
                response = await checkEligibility(data);
                break;
                
            case 'get_emergency_contacts':
                // Get emergency contact numbers
                response = getEmergencyContacts();
                break;
                
            case 'update_user_context':
                // Update user context information
                response = await updateUserContext(data);
                break;
                
            default:
                response = {
                    success: false,
                    error: 'Unknown action'
                };
        }

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify(response)
        };

    } catch (error) {
        console.error('Webhook error:', error);
        
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({
                success: false,
                error: 'Internal server error',
                message: error.message
            })
        };
    }
};

// Handle service request processing
async function handleServiceRequest(data) {
    try {
        const userRequest = {
            text: data.message || data.query,
            language: data.language || 'English',
            visaType: data.visaType,
            location: data.location || 'Canberra',
            age: data.age,
            gender: data.gender,
            familySize: data.familySize
        };

        const referralPackage = await connector.processUserRequest(userRequest);
        
        // Format response for Voiceflow
        const voiceflowResponse = formatVoiceflowResponse(referralPackage);
        
        return {
            success: true,
            data: voiceflowResponse
        };
    } catch (error) {
        console.error('Service request error:', error);
        return {
            success: false,
            error: 'Failed to process request'
        };
    }
}

// Get detailed information about a specific service
async function getServiceDetails(serviceId) {
    try {
        const services = connector.servicesDatabase.services;
        const service = services.find(s => s.id === serviceId);
        
        if (!service) {
            return {
                success: false,
                error: 'Service not found'
            };
        }

        return {
            success: true,
            data: {
                service: service,
                formatted: formatServiceForDisplay(service)
            }
        };
    } catch (error) {
        console.error('Get service details error:', error);
        return {
            success: false,
            error: 'Failed to get service details'
        };
    }
}

// Send referral via SMS or email
async function sendReferral(data) {
    try {
        const { method, recipient, referralPackage } = data;
        
        let result;
        
        if (method === 'sms') {
            result = await connector.sendSMSReferral(recipient, referralPackage);
        } else if (method === 'email') {
            result = await connector.sendEmailReferral(recipient, referralPackage);
        } else {
            return {
                success: false,
                error: 'Invalid referral method'
            };
        }
        
        return result;
    } catch (error) {
        console.error('Send referral error:', error);
        return {
            success: false,
            error: 'Failed to send referral'
        };
    }
}

// Check eligibility for services
async function checkEligibility(data) {
    try {
        const { visaType, age, requirements } = data;
        const services = connector.servicesDatabase.services;
        
        const eligibleServices = services.filter(service => {
            // Check visa eligibility
            if (service.eligibility?.visa_types) {
                const visaMatch = service.eligibility.visa_types.includes('all visa types') ||
                    service.eligibility.visa_types.some(visa => 
                        visa.toLowerCase().includes(visaType?.toLowerCase() || '')
                    );
                if (!visaMatch) return false;
            }
            
            // Check age eligibility if specified
            if (age && service.eligibility?.age) {
                if (service.eligibility.age !== 'All ages') {
                    // Parse age requirements (simplified logic)
                    // This would need more sophisticated parsing in production
                    if (service.eligibility.age.includes('18') && age < 18) {
                        return false;
                    }
                }
            }
            
            return true;
        });
        
        return {
            success: true,
            data: {
                eligibleCount: eligibleServices.length,
                services: eligibleServices.map(s => ({
                    id: s.id,
                    name: s.name,
                    category: s.category
                }))
            }
        };
    } catch (error) {
        console.error('Check eligibility error:', error);
        return {
            success: false,
            error: 'Failed to check eligibility'
        };
    }
}

// Get emergency contacts
function getEmergencyContacts() {
    return {
        success: true,
        data: connector.servicesDatabase.emergency_services
    };
}

// Update user context
async function updateUserContext(data) {
    try {
        // Store user context for session continuity
        // This would typically update a database or session store
        const updatedContext = {
            userId: data.userId,
            timestamp: new Date().toISOString(),
            context: {
                language: data.language,
                visaType: data.visaType,
                location: data.location,
                previousServices: data.previousServices || [],
                preferences: data.preferences || {}
            }
        };
        
        // In production, save to database
        // await saveUserContext(updatedContext);
        
        return {
            success: true,
            data: {
                message: 'Context updated successfully',
                context: updatedContext
            }
        };
    } catch (error) {
        console.error('Update context error:', error);
        return {
            success: false,
            error: 'Failed to update context'
        };
    }
}

// Format response for Voiceflow
function formatVoiceflowResponse(referralPackage) {
    const response = {
        message: generateMessage(referralPackage),
        cards: [],
        buttons: [],
        variables: {}
    };
    
    // Create cards for top 3 services
    const topServices = referralPackage.recommendations.slice(0, 3);
    
    for (const service of topServices) {
        // Create service card
        response.cards.push({
            title: service.serviceName,
            description: service.description,
            image: null, // Could add service logos here
            buttons: [
                {
                    type: 'call',
                    label: 'Call Now',
                    value: service.contact.primary.value
                },
                {
                    type: 'link',
                    label: 'Website',
                    value: service.contact.website
                }
            ]
        });
        
        // Add quick action buttons
        response.buttons.push({
            label: `Call ${service.serviceName}`,
            value: `call_service_${service.serviceId}`
        });
    }
    
    // Set variables for Voiceflow to use
    response.variables = {
        urgency: referralPackage.urgencyLevel,
        serviceCount: referralPackage.recommendations.length,
        topServiceName: topServices[0]?.serviceName || 'No service found',
        topServicePhone: topServices[0]?.contact.primary.value || '',
        needsInterpreter: referralPackage.userNeeds.language !== 'English'
    };
    
    return response;
}

// Generate conversational message
function generateMessage(referralPackage) {
    const { urgencyLevel, recommendations } = referralPackage;
    
    if (recommendations.length === 0) {
        return "I couldn't find specific services matching your needs, but please call 131 450 for interpreter services and they can help connect you with appropriate support.";
    }
    
    let message = '';
    
    // Urgency-based opening
    if (urgencyLevel === 'crisis') {
        message = "This seems urgent. I've found immediate help for you:\n\n";
    } else if (urgencyLevel === 'priority') {
        message = "I understand this is important. Here are services that can help you soon:\n\n";
    } else {
        message = "I've found these services that can help you:\n\n";
    }
    
    // Add top service details
    const topService = recommendations[0];
    message += `**${topService.serviceName}**\n`;
    message += `📞 ${topService.contact.primary.value}\n`;
    
    if (topService.waitTime) {
        message += `⏱️ Wait time: ${topService.waitTime}\n`;
    }
    
    if (topService.cost) {
        message += `💰 Cost: ${topService.cost}\n`;
    }
    
    // Add interpreter reminder if needed
    if (referralPackage.userNeeds.language !== 'English') {
        message += `\n🌐 Remember: Call 131 450 for free interpreter service when contacting any service.`;
    }
    
    // Add emergency reminder for crisis
    if (urgencyLevel === 'crisis') {
        message += `\n\n🚨 For immediate emergency, call 000`;
    }
    
    return message;
}

// Format service for display
function formatServiceForDisplay(service) {
    return {
        name: service.name,
        description: service.description,
        contact: {
            phone: service.contact.phone,
            email: service.contact.email,
            website: service.contact.website,
            address: service.contact.address
        },
        hours: formatHours(service.hours),
        services: service.services_provided,
        eligibility: formatEligibility(service.eligibility),
        languages: service.languages,
        cost: service.cost,
        waitTime: service.wait_time
    };
}

// Format operating hours
function formatHours(hours) {
    if (!hours) return 'Contact for hours';
    
    const formatted = [];
    for (const [day, time] of Object.entries(hours)) {
        formatted.push(`${day}: ${time}`);
    }
    return formatted.join('\n');
}

// Format eligibility criteria
function formatEligibility(eligibility) {
    if (!eligibility) return 'Contact for eligibility';
    
    const criteria = [];
    
    if (eligibility.visa_types) {
        criteria.push(`Visa: ${eligibility.visa_types.join(', ')}`);
    }
    
    if (eligibility.age) {
        criteria.push(`Age: ${eligibility.age}`);
    }
    
    if (eligibility.requirements) {
        criteria.push(`Requirements: ${eligibility.requirements}`);
    }
    
    return criteria.join('\n');
}

// For local testing
if (require.main === module) {
    // Test the webhook locally
    const testEvent = {
        httpMethod: 'POST',
        body: JSON.stringify({
            action: 'process_request',
            data: {
                message: "I need help with housing, I'm a refugee",
                language: 'Arabic',
                visaType: 'humanitarian',
                location: 'Canberra'
            }
        })
    };
    
    exports.handler(testEvent, {}).then(response => {
        console.log('Test response:', JSON.stringify(JSON.parse(response.body), null, 2));
    });
}
