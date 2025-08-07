from models import Resource, ResourceCategory, ContactInfo
from datetime import datetime

def get_act_refugee_resources():
    resources = [
        # LEGAL AID RESOURCES
        Resource(
            id="legal_001",
            name="Legal Aid ACT - Migration Law Service",
            description="Free legal advice and assistance for migration and refugee matters, including visa applications, appeals, and citizenship issues",
            category=ResourceCategory.LEGAL_AID,
            subcategory="Migration Law",
            contact=ContactInfo(
                phone="1300 654 314",
                email="legalaid@legalaidact.org.au",
                website="https://www.legalaidact.org.au",
                address="2 Allsop Street, Canberra ACT 2601",
                hours="Mon-Fri 9am-4pm"
            ),
            eligibility="Refugees, asylum seekers, and migrants with limited financial means",
            services_provided=[
                "Visa application assistance",
                "Immigration appeals",
                "Citizenship applications",
                "Family reunion cases",
                "Protection visa support"
            ],
            languages_available=["English", "Interpreter services available"],
            cost="Free for eligible clients",
            urgency_level="high",
            keywords=["visa", "immigration", "lawyer", "legal help", "citizenship", "refugee status"]
        ),
        
        Resource(
            id="legal_002",
            name="Refugee Advice and Casework Service (RACS)",
            description="Specialist legal service for refugees and people seeking asylum, providing free legal assistance",
            category=ResourceCategory.LEGAL_AID,
            subcategory="Refugee Law",
            contact=ContactInfo(
                phone="(02) 8355 7227",
                website="https://www.racs.org.au",
                email="admin@racs.org.au",
                hours="Mon-Fri 9am-5pm"
            ),
            eligibility="Asylum seekers and refugees",
            services_provided=[
                "Protection visa applications",
                "Appeals and reviews",
                "Detention support",
                "Temporary protection visa assistance",
                "Safe haven enterprise visa support"
            ],
            languages_available=["English", "Arabic", "Farsi", "Tamil"],
            cost="Free",
            urgency_level="high",
            keywords=["asylum", "protection", "refugee lawyer", "detention", "tribunal"]
        ),
        
        # HEALTHCARE RESOURCES
        Resource(
            id="health_001",
            name="Companion House - Medical Services",
            description="Specialized healthcare services for refugees and asylum seekers who have experienced torture and trauma",
            category=ResourceCategory.HEALTHCARE,
            subcategory="Refugee Health",
            contact=ContactInfo(
                phone="(02) 6251 4550",
                email="info@companionhouse.org.au",
                website="https://www.companionhouse.org.au",
                address="41 Templeton Street, Cook ACT 2614",
                hours="Mon-Fri 9am-5pm"
            ),
            eligibility="Refugees, asylum seekers, and survivors of torture and trauma",
            services_provided=[
                "General medical care",
                "Mental health counseling",
                "Trauma counseling",
                "Psychiatric services",
                "Health assessments",
                "Referrals to specialists"
            ],
            languages_available=["English", "Arabic", "Farsi", "Dari", "Tamil", "Mandarin"],
            cost="Bulk billed for Medicare card holders, free for asylum seekers",
            urgency_level="high",
            keywords=["doctor", "medical", "health", "trauma", "counseling", "mental health"]
        ),
        
        Resource(
            id="health_002",
            name="Canberra Hospital - Refugee Health Nurse Program",
            description="Dedicated nursing program providing health assessments and care coordination for newly arrived refugees",
            category=ResourceCategory.HEALTHCARE,
            subcategory="Hospital Services",
            contact=ContactInfo(
                phone="(02) 5124 0000",
                website="https://www.health.act.gov.au",
                address="Yamba Drive, Garran ACT 2605",
                hours="24/7 Emergency, Clinic hours Mon-Fri 8:30am-5pm"
            ),
            eligibility="Newly arrived refugees and humanitarian entrants",
            services_provided=[
                "Initial health assessments",
                "Immunization catch-up",
                "Health screening",
                "Care coordination",
                "Referrals to specialists",
                "Health education"
            ],
            languages_available=["English", "Interpreter services available"],
            cost="Free with Medicare, emergency care available regardless of status",
            urgency_level="high",
            keywords=["hospital", "emergency", "nurse", "health check", "vaccination"]
        ),
        
        # HOUSING RESOURCES
        Resource(
            id="housing_001",
            name="ACT Housing - Migrant and Refugee Housing Support",
            description="Government housing assistance program for eligible migrants and refugees",
            category=ResourceCategory.HOUSING,
            subcategory="Public Housing",
            contact=ContactInfo(
                phone="133 427",
                website="https://www.communityservices.act.gov.au/housing",
                email="housing@act.gov.au",
                address="Nature Conservation House, 153 Faulding Street, Phillip ACT",
                hours="Mon-Fri 8:30am-5pm"
            ),
            eligibility="Permanent residents and certain visa holders with housing need",
            services_provided=[
                "Public housing applications",
                "Priority housing assessment",
                "Rental assistance",
                "Emergency accommodation referrals",
                "Housing advice"
            ],
            languages_available=["English", "Translator services available"],
            cost="Subsidized based on income",
            urgency_level="high",
            keywords=["accommodation", "rental", "home", "shelter", "public housing"]
        ),
        
        Resource(
            id="housing_002",
            name="Migrant and Refugee Settlement Services (MARSS)",
            description="Settlement support including housing assistance for newly arrived migrants and refugees",
            category=ResourceCategory.HOUSING,
            subcategory="Settlement Services",
            contact=ContactInfo(
                phone="(02) 6248 8577",
                email="admin@marss.org.au",
                website="https://www.marss.org.au",
                address="1/13 Napier Close, Deakin ACT 2600",
                hours="Mon-Fri 9am-5pm"
            ),
            eligibility="Newly arrived refugees and eligible migrants (within 5 years of arrival)",
            services_provided=[
                "Initial accommodation support",
                "Rental property search assistance",
                "Tenancy education",
                "Bond loan assistance",
                "Furniture and household goods support",
                "Utility connection help"
            ],
            languages_available=["English", "Arabic", "Farsi", "Mandarin", "Spanish"],
            cost="Free",
            urgency_level="high",
            keywords=["settlement", "new arrival", "rental help", "bond", "furniture"]
        ),
        
        # EDUCATION RESOURCES
        Resource(
            id="education_001",
            name="CIT - Adult Migrant English Program (AMEP)",
            description="Free English language classes for eligible migrants and refugees",
            category=ResourceCategory.EDUCATION,
            subcategory="Language Education",
            contact=ContactInfo(
                phone="(02) 6207 3188",
                email="amep@cit.edu.au",
                website="https://cit.edu.au/amep",
                address="37 Constitution Avenue, Reid ACT 2612",
                hours="Mon-Fri 8:30am-5pm"
            ),
            eligibility="Permanent residents and eligible visa holders with limited English",
            services_provided=[
                "English language classes",
                "Settlement language pathways",
                "Vocational English",
                "Digital literacy training",
                "Childcare during classes",
                "Flexible learning options"
            ],
            languages_available=["English", "Multiple language support"],
            cost="Free for eligible participants",
            urgency_level="standard",
            keywords=["English", "AMEP", "language class", "ESL", "study"]
        ),
        
        Resource(
            id="education_002",
            name="ACT Education Directorate - New Arrivals Program",
            description="Intensive English support for refugee and migrant children in ACT public schools",
            category=ResourceCategory.EDUCATION,
            subcategory="School Support",
            contact=ContactInfo(
                phone="(02) 6205 5429",
                website="https://www.education.act.gov.au",
                email="EDUEnglishasanAddLanguageorDialect@act.gov.au",
                hours="Mon-Fri 8:30am-5pm"
            ),
            eligibility="School-aged children who are new arrivals with limited English",
            services_provided=[
                "Intensive English centres",
                "ESL support in schools",
                "Bilingual support officers",
                "Parent engagement programs",
                "Transition support",
                "Cultural orientation"
            ],
            languages_available=["English", "Various community languages"],
            cost="Free in public schools",
            urgency_level="standard",
            keywords=["school", "children", "ESL", "education", "student"]
        ),
        
        # EMPLOYMENT RESOURCES
        Resource(
            id="employment_001",
            name="Multicultural Employment Service (MES)",
            description="Specialized employment support for migrants and refugees in the ACT",
            category=ResourceCategory.EMPLOYMENT,
            subcategory="Job Services",
            contact=ContactInfo(
                phone="(02) 6229 2966",
                email="info@mes.org.au",
                website="https://www.mes.org.au",
                address="Level 2, 113 London Circuit, Canberra ACT 2601",
                hours="Mon-Fri 9am-5pm"
            ),
            eligibility="Migrants and refugees seeking employment",
            services_provided=[
                "Job search assistance",
                "Resume writing support",
                "Interview preparation",
                "Skills assessment",
                "Work experience programs",
                "Employer connections",
                "Career counseling"
            ],
            languages_available=["English", "Arabic", "Mandarin", "Cantonese", "Vietnamese"],
            cost="Free",
            urgency_level="standard",
            keywords=["job", "work", "employment", "career", "resume", "interview"]
        ),
        
        Resource(
            id="employment_002",
            name="ThincLab Business Development Program",
            description="Entrepreneurship support program for migrants and refugees wanting to start businesses",
            category=ResourceCategory.EMPLOYMENT,
            subcategory="Business Support",
            contact=ContactInfo(
                phone="(02) 6173 6780",
                email="info@thinclab.org.au",
                website="https://www.thinclab.org.au",
                address="Gordon ACT",
                hours="Mon-Fri 9am-5pm"
            ),
            eligibility="Migrants and refugees interested in starting a business",
            services_provided=[
                "Business planning",
                "Mentoring",
                "Networking opportunities",
                "Access to funding information",
                "Business skills training",
                "Market research support"
            ],
            languages_available=["English"],
            cost="Free for eligible participants",
            urgency_level="standard",
            keywords=["business", "entrepreneur", "startup", "self-employment"]
        ),
        
        # MENTAL HEALTH RESOURCES
        Resource(
            id="mental_001",
            name="Companion House - Counseling Services",
            description="Specialized trauma and torture counseling for refugees and asylum seekers",
            category=ResourceCategory.MENTAL_HEALTH,
            subcategory="Trauma Counseling",
            contact=ContactInfo(
                phone="(02) 6251 4550",
                email="info@companionhouse.org.au",
                website="https://www.companionhouse.org.au",
                address="41 Templeton Street, Cook ACT 2614",
                hours="Mon-Fri 9am-5pm"
            ),
            eligibility="Refugees and asylum seekers who have experienced torture or trauma",
            services_provided=[
                "Individual counseling",
                "Group therapy",
                "Family counseling",
                "Art therapy",
                "Youth programs",
                "Community support groups"
            ],
            languages_available=["English", "Arabic", "Farsi", "Tamil", "Interpreter services"],
            cost="Free",
            urgency_level="high",
            keywords=["counseling", "trauma", "therapy", "mental health", "PTSD", "support"]
        ),
        
        Resource(
            id="mental_002",
            name="Transcultural Mental Health - ACT Services",
            description="Culturally appropriate mental health services for people from diverse backgrounds",
            category=ResourceCategory.MENTAL_HEALTH,
            subcategory="Multicultural Mental Health",
            contact=ContactInfo(
                phone="1800 648 911",
                website="https://www.dhi.health.nsw.gov.au/transcultural-mental-health",
                hours="24/7 helpline"
            ),
            eligibility="People from culturally and linguistically diverse backgrounds",
            services_provided=[
                "Mental health assessments",
                "Crisis support",
                "Referrals to appropriate services",
                "Cultural consultation",
                "Mental health education",
                "Interpreter services"
            ],
            languages_available=["Multiple languages through interpreter service"],
            cost="Free",
            urgency_level="high",
            keywords=["mental health", "crisis", "depression", "anxiety", "helpline"]
        ),
        
        # EMERGENCY SERVICES
        Resource(
            id="emergency_001",
            name="Emergency Services - Triple Zero (000)",
            description="24/7 emergency response for police, fire, and ambulance services",
            category=ResourceCategory.EMERGENCY_SERVICES,
            subcategory="Emergency Response",
            contact=ContactInfo(
                phone="000",
                website="https://www.triplezero.gov.au",
                hours="24/7"
            ),
            eligibility="Anyone in an emergency situation",
            services_provided=[
                "Police emergency response",
                "Fire emergency response",
                "Ambulance services",
                "Interpreter services available"
            ],
            languages_available=["English", "Interpreter services available - say 'police', 'fire', or 'ambulance' first"],
            cost="Free",
            urgency_level="critical",
            keywords=["emergency", "police", "fire", "ambulance", "danger", "urgent"]
        ),
        
        Resource(
            id="emergency_002",
            name="Domestic Violence Crisis Service (DVCS)",
            description="24/7 crisis intervention for people experiencing domestic and family violence",
            category=ResourceCategory.EMERGENCY_SERVICES,
            subcategory="Crisis Support",
            contact=ContactInfo(
                phone="(02) 6280 0900",
                website="https://dvcs.org.au",
                hours="24/7"
            ),
            eligibility="Anyone experiencing domestic or family violence",
            services_provided=[
                "Crisis intervention",
                "Safety planning",
                "Emergency accommodation",
                "Legal support referrals",
                "Counseling",
                "Court support"
            ],
            languages_available=["English", "Interpreter services available"],
            cost="Free",
            urgency_level="critical",
            keywords=["domestic violence", "family violence", "crisis", "safety", "abuse"]
        ),
        
        # COMMUNITY SUPPORT
        Resource(
            id="community_001",
            name="Canberra Refugee Support",
            description="Community organization providing practical support and advocacy for refugees",
            category=ResourceCategory.COMMUNITY_SUPPORT,
            subcategory="Refugee Support",
            contact=ContactInfo(
                phone="0485 945 441",
                email="info@actrefugee.org.au",
                website="https://actrefugee.org.au",
                hours="Volunteer-run, contact for availability"
            ),
            eligibility="Refugees and asylum seekers",
            services_provided=[
                "Donation coordination",
                "Social activities",
                "Advocacy",
                "Volunteer support",
                "Community connections",
                "Practical assistance"
            ],
            languages_available=["English"],
            cost="Free",
            urgency_level="standard",
            keywords=["community", "volunteer", "donation", "social", "support"]
        ),
        
        Resource(
            id="community_002",
            name="Migrant and Refugee Settlement Services - Community Programs",
            description="Community integration programs and social support for migrants and refugees",
            category=ResourceCategory.COMMUNITY_SUPPORT,
            subcategory="Settlement Support",
            contact=ContactInfo(
                phone="(02) 6248 8577",
                email="admin@marss.org.au",
                website="https://www.marss.org.au",
                address="1/13 Napier Close, Deakin ACT 2600",
                hours="Mon-Fri 9am-5pm"
            ),
            eligibility="Migrants and refugees",
            services_provided=[
                "Youth programs",
                "Women's groups",
                "Men's support groups",
                "Parenting programs",
                "Cultural activities",
                "Sports programs",
                "Community gardens"
            ],
            languages_available=["English", "Arabic", "Farsi", "Spanish"],
            cost="Free",
            urgency_level="standard",
            keywords=["community", "social", "group", "activities", "culture"]
        ),
        
        # FINANCIAL ASSISTANCE
        Resource(
            id="financial_001",
            name="Services Australia - Centrelink Multicultural Services",
            description="Government financial assistance and support payments for eligible residents",
            category=ResourceCategory.FINANCIAL_ASSISTANCE,
            subcategory="Government Benefits",
            contact=ContactInfo(
                phone="131 202",
                website="https://www.servicesaustralia.gov.au",
                address="2-6 Bowes Street, Phillip ACT 2606",
                hours="Mon-Fri 8:30am-4:30pm"
            ),
            eligibility="Varies by payment type and visa status",
            services_provided=[
                "Income support payments",
                "Family payments",
                "Healthcare cards",
                "Crisis payments",
                "Rent assistance",
                "Multicultural service officers"
            ],
            languages_available=["English", "Interpreter services available - 131 202"],
            cost="Free service",
            urgency_level="high",
            keywords=["Centrelink", "payment", "financial", "welfare", "benefits"]
        ),
        
        Resource(
            id="financial_002",
            name="Red Cross Emergency Relief",
            description="Emergency financial assistance and material aid for people in crisis",
            category=ResourceCategory.FINANCIAL_ASSISTANCE,
            subcategory="Emergency Aid",
            contact=ContactInfo(
                phone="(02) 6234 7600",
                website="https://www.redcross.org.au",
                address="3 Dann Close, Garran ACT 2605",
                hours="Mon-Fri 9am-5pm"
            ),
            eligibility="People experiencing financial hardship",
            services_provided=[
                "Food vouchers",
                "Emergency accommodation assistance",
                "Clothing and household items",
                "Pharmacy vouchers",
                "Transport assistance",
                "Referrals to other services"
            ],
            languages_available=["English", "Interpreter services available"],
            cost="Free",
            urgency_level="high",
            keywords=["emergency", "food", "voucher", "crisis", "relief"]
        ),
        
        # GOVERNMENT PROGRAMS
        Resource(
            id="gov_001",
            name="Humanitarian Settlement Program (HSP)",
            description="Australian Government program providing intensive support to newly arrived humanitarian entrants",
            category=ResourceCategory.GOVERNMENT_PROGRAMS,
            subcategory="Settlement Program",
            contact=ContactInfo(
                phone="(02) 6248 8577",
                website="https://immi.homeaffairs.gov.au/settling-in-australia/humanitarian-settlement-program",
                hours="Mon-Fri 9am-5pm"
            ),
            eligibility="Humanitarian visa holders in first 6-12 months",
            services_provided=[
                "Airport reception",
                "Initial accommodation",
                "Property orientation",
                "Registration with services",
                "Initial health assessment",
                "School enrollment support"
            ],
            languages_available=["Multiple languages"],
            cost="Free",
            urgency_level="high",
            keywords=["HSP", "humanitarian", "settlement", "new arrival", "government"]
        ),
        
        Resource(
            id="gov_002",
            name="Settlement Engagement and Transition Support (SETS)",
            description="Free settlement support services for eligible migrants in their first 5 years",
            category=ResourceCategory.GOVERNMENT_PROGRAMS,
            subcategory="Integration Support",
            contact=ContactInfo(
                phone="(02) 6248 8577",
                website="https://immi.homeaffairs.gov.au/settling-in-australia/sets-program",
                hours="Mon-Fri 9am-5pm"
            ),
            eligibility="Eligible permanent migrants and humanitarian entrants (first 5 years)",
            services_provided=[
                "Casework and coordination",
                "Information sessions",
                "Community capacity building",
                "Youth settlement services",
                "Education and training pathways",
                "Employment support"
            ],
            languages_available=["Multiple languages"],
            cost="Free",
            urgency_level="standard",
            keywords=["SETS", "settlement", "integration", "support", "government"]
        ),
        
        # LANGUAGE LEARNING
        Resource(
            id="language_001",
            name="ACT Libraries - English Conversation Groups",
            description="Free English conversation practice groups at various library branches",
            category=ResourceCategory.LANGUAGE_LEARNING,
            subcategory="Conversation Practice",
            contact=ContactInfo(
                phone="(02) 6205 9000",
                website="https://www.library.act.gov.au",
                hours="Varies by branch"
            ),
            eligibility="Anyone wanting to practice English",
            services_provided=[
                "Conversation practice groups",
                "Beginner and intermediate levels",
                "Social interaction",
                "Cultural exchange",
                "Free library membership",
                "Access to learning resources"
            ],
            languages_available=["English"],
            cost="Free",
            urgency_level="standard",
            keywords=["English", "conversation", "practice", "library", "free"]
        ),
        
        Resource(
            id="language_002",
            name="AMEP Extend - Additional English Tuition",
            description="Additional free English tuition for AMEP graduates needing more support",
            category=ResourceCategory.LANGUAGE_LEARNING,
            subcategory="Advanced English",
            contact=ContactInfo(
                phone="(02) 6207 3188",
                website="https://immi.homeaffairs.gov.au/settling-in-australia/amep/about-the-program/amep-extend",
                hours="Mon-Fri 8:30am-5pm"
            ),
            eligibility="AMEP graduates who need additional English support",
            services_provided=[
                "Additional 490 hours of tuition",
                "Vocational English",
                "Workplace English",
                "Academic English",
                "Pronunciation classes",
                "Writing skills"
            ],
            languages_available=["English"],
            cost="Free for eligible participants",
            urgency_level="standard",
            keywords=["AMEP Extend", "English", "advanced", "vocational", "workplace"]
        ),
        
        # CHILDREN'S SERVICES
        Resource(
            id="children_001",
            name="Multicultural Hub Canberra - Children's Programs",
            description="Programs and activities specifically designed for migrant and refugee children",
            category=ResourceCategory.CHILDREN_SERVICES,
            subcategory="Youth Programs",
            contact=ContactInfo(
                phone="(02) 6160 5665",
                email="info@mhub.org.au",
                website="https://www.mhub.org.au",
                address="North Building, 180 London Circuit, Canberra",
                hours="Mon-Fri 9am-5pm"
            ),
            eligibility="Migrant and refugee children and youth",
            services_provided=[
                "After school programs",
                "Holiday activities",
                "Homework support",
                "Sports programs",
                "Cultural activities",
                "Leadership development"
            ],
            languages_available=["English", "Various community languages"],
            cost="Free or low cost",
            urgency_level="standard",
            keywords=["children", "youth", "activities", "homework", "after school"]
        ),
        
        # WOMEN'S SERVICES
        Resource(
            id="women_001",
            name="Women's Centre for Health Matters - Multicultural Women's Programs",
            description="Health and wellbeing programs specifically for women from diverse backgrounds",
            category=ResourceCategory.WOMEN_SERVICES,
            subcategory="Women's Health",
            contact=ContactInfo(
                phone="(02) 6290 2166",
                email="admin@wchm.org.au",
                website="https://www.wchm.org.au",
                address="Pearce Community Centre, Collett Place, Pearce",
                hours="Mon-Fri 9am-5pm"
            ),
            eligibility="Women from migrant and refugee backgrounds",
            services_provided=[
                "Health education",
                "Women's health groups",
                "Parenting support",
                "Social connection groups",
                "Information sessions",
                "Referrals to services"
            ],
            languages_available=["English", "Interpreter services available"],
            cost="Free",
            urgency_level="standard",
            keywords=["women", "health", "parenting", "social", "support group"]
        ),
        
        # DISABILITY SUPPORT
        Resource(
            id="disability_001",
            name="National Disability Insurance Scheme (NDIS) - Multicultural Support",
            description="Disability support services with specialized help for people from diverse backgrounds",
            category=ResourceCategory.DISABILITY_SUPPORT,
            subcategory="NDIS",
            contact=ContactInfo(
                phone="1800 800 110",
                website="https://www.ndis.gov.au",
                hours="Mon-Fri 8am-8pm"
            ),
            eligibility="People with permanent disability who meet NDIS criteria",
            services_provided=[
                "Disability assessments",
                "Support planning",
                "Funding for services",
                "Assistive technology",
                "Therapy services",
                "Cultural liaison officers"
            ],
            languages_available=["English", "Interpreter services available"],
            cost="Free assessment, funded supports",
            urgency_level="standard",
            keywords=["disability", "NDIS", "support", "assessment", "funding"]
        )
    ]
    
    return resources