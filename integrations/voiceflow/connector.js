// Voiceflow API Connector for ACT Refugee & Migrant Support Assistant
// This module handles service referrals and API integrations

const axios = require('axios');

class VoiceflowServiceConnector {
    constructor(config) {
        this.voiceflowAPIKey = config.voiceflowAPIKey;
        this.voiceflowVersionID = config.voiceflowVersionID;
        this.servicesDatabase = require('./services-database.json');
        this.userSession = {};
    }

    // Main function to process user needs and match with services
    async processUserRequest(userRequest) {
        const analysis = this.analyzeUserNeeds(userRequest);
        const matchedServices = this.matchServices(analysis);
        const referralPackage = this.createReferralPackage(matchedServices, analysis);
        
        return referralPackage;
    }

    // Analyze user needs based on their request
    analyzeUserNeeds(userRequest) {
        const analysis = {
            urgencyLevel: this.determineUrgency(userRequest),
            categories: this.extractCategories(userRequest),
            language: userRequest.language || 'English',
            location: userRequest.location || 'Canberra',
            visaType: userRequest.visaType || 'unknown',
            specificNeeds: this.extractSpecificNeeds(userRequest),
            demographics: {
                age: userRequest.age,
                gender: userRequest.gender,
                familySize: userRequest.familySize
            }
        };
        
        return analysis;
    }

    // Determine urgency level based on keywords and context
    determineUrgency(userRequest) {
        const text = userRequest.text?.toLowerCase() || '';
        const urgencyKeywords = {
            crisis: ['emergency', 'urgent', 'crisis', 'immediate', 'help now', 'danger', 'homeless', 'no food', 'violence'],
            priority: ['soon', 'quickly', 'priority', 'worried', 'concerned', 'struggling'],
            standard: ['information', 'planning', 'future', 'general', 'wondering']
        };

        if (urgencyKeywords.crisis.some(keyword => text.includes(keyword))) {
            return 'crisis';
        } else if (urgencyKeywords.priority.some(keyword => text.includes(keyword))) {
            return 'priority';
        }
        return 'standard';
    }

    // Extract service categories from user request
    extractCategories(userRequest) {
        const text = userRequest.text?.toLowerCase() || '';
        const categories = [];
        
        const categoryKeywords = {
            'healthcare': ['health', 'doctor', 'medical', 'hospital', 'sick', 'medicine', 'nurse'],
            'mental-health': ['mental', 'counselling', 'therapy', 'trauma', 'stress', 'anxiety', 'depression'],
            'housing': ['housing', 'accommodation', 'homeless', 'shelter', 'rent', 'house', 'apartment'],
            'employment': ['job', 'work', 'employment', 'career', 'resume', 'interview'],
            'education': ['school', 'education', 'study', 'english', 'training', 'course', 'learn'],
            'legal': ['visa', 'legal', 'immigration', 'lawyer', 'citizenship', 'documents'],
            'financial-assistance': ['money', 'financial', 'payment', 'benefit', 'centrelink', 'support payment'],
            'emergency-relief': ['emergency', 'food', 'crisis', 'urgent help', 'relief'],
            'community-support': ['community', 'social', 'friends', 'lonely', 'connect', 'group']
        };

        for (const [category, keywords] of Object.entries(categoryKeywords)) {
            if (keywords.some(keyword => text.includes(keyword))) {
                categories.push(category);
            }
        }

        return categories.length > 0 ? categories : ['general-support'];
    }

    // Extract specific needs from the request
    extractSpecificNeeds(userRequest) {
        const text = userRequest.text?.toLowerCase() || '';
        const needs = [];

        const needsMapping = {
            'interpreter': ['interpreter', 'translation', 'language help', "don't speak english"],
            'childcare': ['childcare', 'children', 'kids', 'baby'],
            'transportation': ['transport', 'bus', 'travel', 'get there'],
            'documentation': ['documents', 'paperwork', 'forms', 'application'],
            'culturalSupport': ['cultural', 'religious', 'halal', 'mosque', 'church', 'temple']
        };

        for (const [need, keywords] of Object.entries(needsMapping)) {
            if (keywords.some(keyword => text.includes(keyword))) {
                needs.push(need);
            }
        }

        return needs;
    }

    // Match user needs with available services
    matchServices(analysis) {
        const { urgencyLevel, categories, visaType, language, specificNeeds } = analysis;
        let matchedServices = [];

        // Filter services based on criteria
        for (const service of this.servicesDatabase.services) {
            let matchScore = 0;
            
            // Check urgency level compatibility
            if (service.urgency_levels.includes(urgencyLevel)) {
                matchScore += 3;
            }
            
            // Check category match
            const categoryMatch = service.category.some(cat => categories.includes(cat));
            if (categoryMatch) {
                matchScore += 5;
            }
            
            // Check visa eligibility
            if (this.checkVisaEligibility(service, visaType)) {
                matchScore += 2;
            }
            
            // Check language support
            if (this.checkLanguageSupport(service, language)) {
                matchScore += 1;
            }
            
            // Add service with match score
            if (matchScore > 0) {
                matchedServices.push({
                    ...service,
                    matchScore,
                    relevance: this.calculateRelevance(matchScore)
                });
            }
        }

        // Sort by match score and return top matches
        matchedServices.sort((a, b) => b.matchScore - a.matchScore);
        
        // Return top 3-5 most relevant services
        return matchedServices.slice(0, 5);
    }

    // Check if user's visa type is eligible for the service
    checkVisaEligibility(service, userVisaType) {
        if (!service.eligibility?.visa_types) return true;
        
        const eligibleVisas = service.eligibility.visa_types;
        if (eligibleVisas.includes('all visa types')) return true;
        if (userVisaType === 'unknown') return true;
        
        return eligibleVisas.some(visa => 
            visa.toLowerCase().includes(userVisaType.toLowerCase())
        );
    }

    // Check if service supports user's language
    checkLanguageSupport(service, userLanguage) {
        if (!service.languages) return true;
        
        return service.languages.some(lang => 
            lang.toLowerCase().includes(userLanguage.toLowerCase()) ||
            lang.toLowerCase().includes('interpreter')
        );
    }

    // Calculate relevance score
    calculateRelevance(matchScore) {
        if (matchScore >= 8) return 'highly-relevant';
        if (matchScore >= 5) return 'relevant';
        if (matchScore >= 3) return 'potentially-relevant';
        return 'low-relevance';
    }

    // Create comprehensive referral package
    createReferralPackage(matchedServices, analysis) {
        const referralPackage = {
            timestamp: new Date().toISOString(),
            urgencyLevel: analysis.urgencyLevel,
            userNeeds: analysis,
            recommendations: [],
            emergencyContacts: null,
            followUpActions: []
        };

        // Add emergency contacts if crisis
        if (analysis.urgencyLevel === 'crisis') {
            referralPackage.emergencyContacts = this.servicesDatabase.emergency_services;
        }

        // Format service recommendations
        for (const service of matchedServices) {
            const recommendation = {
                serviceId: service.id,
                serviceName: service.name,
                description: service.description,
                relevance: service.relevance,
                contact: this.formatContactInfo(service.contact, analysis.urgencyLevel),
                quickActions: this.generateQuickActions(service, analysis),
                waitTime: service.wait_time,
                cost: service.cost,
                languages: service.languages,
                nextSteps: this.generateNextSteps(service, analysis)
            };
            
            referralPackage.recommendations.push(recommendation);
        }

        // Add follow-up actions
        referralPackage.followUpActions = this.generateFollowUpActions(matchedServices, analysis);

        return referralPackage;
    }

    // Format contact information based on urgency
    formatContactInfo(contact, urgencyLevel) {
        const formatted = {
            primary: null,
            secondary: null,
            address: contact.address,
            website: contact.website
        };

        if (urgencyLevel === 'crisis') {
            formatted.primary = {
                type: 'phone',
                value: contact.phone,
                action: 'call-immediately'
            };
        } else {
            formatted.primary = {
                type: 'phone',
                value: contact.phone,
                action: 'call-during-hours'
            };
            formatted.secondary = {
                type: 'email',
                value: contact.email,
                action: 'email-for-info'
            };
        }

        return formatted;
    }

    // Generate quick action buttons/links
    generateQuickActions(service, analysis) {
        const actions = [];

        // Phone call action
        if (service.contact.phone) {
            actions.push({
                type: 'call',
                label: `Call ${service.name}`,
                value: service.contact.phone,
                priority: analysis.urgencyLevel === 'crisis' ? 'high' : 'medium'
            });
        }

        // Website action
        if (service.contact.website) {
            actions.push({
                type: 'website',
                label: 'Visit Website',
                value: service.contact.website,
                priority: 'low'
            });
        }

        // Map directions action
        if (service.contact.address) {
            actions.push({
                type: 'directions',
                label: 'Get Directions',
                value: `https://maps.google.com/?q=${encodeURIComponent(service.contact.address)}`,
                priority: 'medium'
            });
        }

        // Email action
        if (service.contact.email && analysis.urgencyLevel !== 'crisis') {
            actions.push({
                type: 'email',
                label: 'Send Email',
                value: service.contact.email,
                priority: 'low'
            });
        }

        return actions;
    }

    // Generate specific next steps for user
    generateNextSteps(service, analysis) {
        const steps = [];

        // Immediate action for crisis
        if (analysis.urgencyLevel === 'crisis') {
            steps.push({
                order: 1,
                action: `Call ${service.name} immediately at ${service.contact.phone}`,
                timeframe: 'now'
            });
            
            if (service.contact.address) {
                steps.push({
                    order: 2,
                    action: `If needed, go directly to ${service.contact.address}`,
                    timeframe: 'today'
                });
            }
        } else {
            // Standard referral process
            steps.push({
                order: 1,
                action: `Contact ${service.name} during business hours`,
                timeframe: 'within 2-3 days'
            });

            // Documentation preparation
            if (analysis.categories.includes('legal') || analysis.categories.includes('government-services')) {
                steps.push({
                    order: 2,
                    action: 'Prepare your documents: passport, visa, proof of address',
                    timeframe: 'before appointment'
                });
            }

            // Language support
            if (analysis.language !== 'English') {
                steps.push({
                    order: 3,
                    action: 'Request an interpreter when booking appointment',
                    timeframe: 'when calling'
                });
            }
        }

        return steps;
    }

    // Generate follow-up actions for the system
    generateFollowUpActions(services, analysis) {
        const actions = [];

        // Schedule follow-up based on urgency
        const followUpTiming = {
            'crisis': '24 hours',
            'priority': '3 days',
            'standard': '1 week'
        };

        actions.push({
            type: 'follow-up',
            timing: followUpTiming[analysis.urgencyLevel],
            message: 'Check if user accessed recommended services'
        });

        // Additional support for specific needs
        if (analysis.specificNeeds.includes('interpreter')) {
            actions.push({
                type: 'resource',
                action: 'Send TIS (131 450) information',
                timing: 'immediate'
            });
        }

        if (analysis.specificNeeds.includes('documentation')) {
            actions.push({
                type: 'resource',
                action: 'Send document checklist',
                timing: 'immediate'
            });
        }

        return actions;
    }

    // Send referral via SMS (integration with SMS gateway)
    async sendSMSReferral(phoneNumber, referralPackage) {
        // Format SMS message with key information
        const message = this.formatSMSMessage(referralPackage);
        
        // This would integrate with an SMS API like Twilio
        try {
            // const response = await twilioClient.messages.create({
            //     body: message,
            //     from: process.env.TWILIO_PHONE,
            //     to: phoneNumber
            // });
            
            return {
                success: true,
                message: 'SMS referral sent successfully'
            };
        } catch (error) {
            console.error('SMS sending error:', error);
            return {
                success: false,
                error: 'Failed to send SMS'
            };
        }
    }

    // Format referral for SMS
    formatSMSMessage(referralPackage) {
        const topService = referralPackage.recommendations[0];
        let message = `ACT Refugee Support Referral:\n\n`;
        
        if (referralPackage.urgencyLevel === 'crisis') {
            message += `URGENT: `;
        }
        
        message += `${topService.serviceName}\n`;
        message += `Ph: ${topService.contact.primary.value}\n`;
        
        if (topService.contact.address) {
            message += `Addr: ${topService.contact.address}\n`;
        }
        
        message += `\nFor translator call 131 450`;
        
        return message;
    }

    // Send referral via Email
    async sendEmailReferral(email, referralPackage) {
        // Format email with detailed information
        const emailContent = this.formatEmailContent(referralPackage);
        
        // This would integrate with an email service
        try {
            // const response = await emailService.send({
            //     to: email,
            //     subject: 'Your ACT Support Service Referrals',
            //     html: emailContent
            // });
            
            return {
                success: true,
                message: 'Email referral sent successfully'
            };
        } catch (error) {
            console.error('Email sending error:', error);
            return {
                success: false,
                error: 'Failed to send email'
            };
        }
    }

    // Format detailed email content
    formatEmailContent(referralPackage) {
        let html = `
        <h2>ACT Refugee & Migrant Support Services - Your Referrals</h2>
        <p>Based on your needs, we recommend the following services:</p>
        `;
        
        for (const service of referralPackage.recommendations) {
            html += `
            <div style="border: 1px solid #ccc; padding: 10px; margin: 10px 0;">
                <h3>${service.serviceName}</h3>
                <p>${service.description}</p>
                <p><strong>Contact:</strong> ${service.contact.primary.value}</p>
                ${service.contact.address ? `<p><strong>Address:</strong> ${service.contact.address}</p>` : ''}
                ${service.contact.website ? `<p><strong>Website:</strong> <a href="${service.contact.website}">${service.contact.website}</a></p>` : ''}
                <p><strong>Wait Time:</strong> ${service.waitTime}</p>
                <p><strong>Cost:</strong> ${service.cost}</p>
                
                <h4>Next Steps:</h4>
                <ol>
                ${service.nextSteps.map(step => `<li>${step.action} (${step.timeframe})</li>`).join('')}
                </ol>
            </div>
            `;
        }
        
        if (referralPackage.emergencyContacts) {
            html += `
            <div style="background: #f44336; color: white; padding: 10px; margin: 10px 0;">
                <h3>Emergency Contacts</h3>
                <p>Police/Fire/Ambulance: 000</p>
                <p>Crisis Support: 13 11 14</p>
                <p>Translation Service: 131 450</p>
            </div>
            `;
        }
        
        return html;
    }

    // Integration with Voiceflow webhook
    async handleVoiceflowWebhook(request) {
        const { userId, message, context } = request;
        
        // Process user request
        const userRequest = {
            text: message,
            language: context.language || 'English',
            visaType: context.visaType,
            location: context.location,
            age: context.age,
            gender: context.gender,
            familySize: context.familySize
        };
        
        const referralPackage = await this.processUserRequest(userRequest);
        
        // Format response for Voiceflow
        const voiceflowResponse = {
            success: true,
            data: {
                referrals: referralPackage.recommendations,
                urgency: referralPackage.urgencyLevel,
                quickActions: this.formatVoiceflowActions(referralPackage),
                message: this.generateVoiceflowMessage(referralPackage)
            }
        };
        
        return voiceflowResponse;
    }

    // Format actions for Voiceflow buttons/cards
    formatVoiceflowActions(referralPackage) {
        const actions = [];
        
        for (const service of referralPackage.recommendations.slice(0, 3)) {
            actions.push({
                type: 'button',
                label: `Call ${service.serviceName}`,
                action: {
                    type: 'link',
                    value: `tel:${service.contact.primary.value}`
                }
            });
        }
        
        return actions;
    }

    // Generate conversational message for Voiceflow
    generateVoiceflowMessage(referralPackage) {
        const urgencyMessages = {
            'crisis': "I understand this is urgent. Here's immediate help available:",
            'priority': "I can see this is important. Here are services that can help soon:",
            'standard': "I've found some services that can assist you:"
        };
        
        let message = urgencyMessages[referralPackage.urgencyLevel] + '\n\n';
        
        const topService = referralPackage.recommendations[0];
        message += `${topService.serviceName} can help with your needs. `;
        message += `You can call them at ${topService.contact.primary.value}. `;
        
        if (topService.waitTime) {
            message += `Typical wait time is ${topService.waitTime}. `;
        }
        
        if (referralPackage.urgencyLevel === 'crisis') {
            message += '\n\nIf you need immediate emergency help, please call 000.';
        }
        
        return message;
    }
}

// Export for use in Voiceflow or other integrations
module.exports = VoiceflowServiceConnector;

// Example usage
const exampleUsage = async () => {
    const connector = new VoiceflowServiceConnector({
        voiceflowAPIKey: 'YOUR_VOICEFLOW_API_KEY',
        voiceflowVersionID: 'YOUR_VERSION_ID'
    });
    
    // Example user request
    const userRequest = {
        text: "I need help finding a doctor, I don't speak English well",
        language: 'Arabic',
        visaType: 'humanitarian',
        location: 'Canberra'
    };
    
    const referral = await connector.processUserRequest(userRequest);
    console.log(JSON.stringify(referral, null, 2));
};

// Uncomment to run example
// exampleUsage();
