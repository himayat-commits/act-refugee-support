import logging
from config import QdrantConfig, CollectionManager
from data_ingestion import DataIngestion
from search_engine import SearchEngine
from models import SearchQuery, ResourceCategory
from act_resources_data import get_act_refugee_resources
from economic_integration_resources import get_economic_integration_resources
from critical_gap_resources import get_critical_gap_resources

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_database():
    """Initialize the Qdrant database with ACT refugee resources"""
    logger.info("Initializing database...")
    
    config = QdrantConfig()
    ingestion = DataIngestion(config)
    
    resources = get_act_refugee_resources()
    economic_resources = get_economic_integration_resources()
    critical_resources = get_critical_gap_resources()
    all_resources = resources + economic_resources + critical_resources
    logger.info(f"Loading {len(all_resources)} resources into database:")
    logger.info(f"  - {len(resources)} general support services")
    logger.info(f"  - {len(economic_resources)} economic integration services")
    logger.info(f"  - {len(critical_resources)} critical gap services")
    
    success = ingestion.ingest_resources(all_resources)
    
    if success:
        logger.info("Database initialized successfully!")
    else:
        logger.error("Failed to initialize database")
    
    return success

def demo_search_scenarios():
    """Demonstrate various search scenarios for the chatbot"""
    config = QdrantConfig()
    search_engine = SearchEngine(config)
    
    print("\n" + "="*60)
    print("ACT REFUGEE & MIGRANT SUPPORT - SEARCH DEMONSTRATIONS")
    print("="*60)
    
    # Scenario 1: Emergency Help
    print("\n1. EMERGENCY HELP SEARCH")
    print("-" * 40)
    query = SearchQuery(
        query="I need urgent help emergency medical doctor",
        urgency="high",
        limit=5
    )
    results = search_engine.search(query)
    for result in results:
        print(f"• {result.resource.name}")
        print(f"  Phone: {result.resource.contact.phone}")
        print(f"  Category: {result.resource.category.value}")
        print(f"  Score: {result.score:.3f}")
    
    # Scenario 2: New Arrival Needs
    print("\n2. NEW ARRIVAL COMPREHENSIVE SUPPORT")
    print("-" * 40)
    query = SearchQuery(
        query="I just arrived in Australia need help with housing English classes and job",
        limit=8
    )
    results = search_engine.search(query)
    for result in results:
        print(f"• {result.resource.name}")
        print(f"  Services: {', '.join(result.resource.services_provided[:3])}...")
        print(f"  Contact: {result.resource.contact.phone or result.resource.contact.email}")
    
    # Scenario 3: Legal Help
    print("\n3. VISA AND LEGAL ASSISTANCE")
    print("-" * 40)
    query = SearchQuery(
        query="visa application lawyer immigration appeal citizenship",
        categories=[ResourceCategory.LEGAL_AID],
        limit=5
    )
    results = search_engine.search(query)
    for result in results:
        print(f"• {result.resource.name}")
        print(f"  Eligibility: {result.resource.eligibility}")
        print(f"  Cost: {result.resource.cost}")
    
    # Scenario 4: Mental Health Support
    print("\n4. MENTAL HEALTH & TRAUMA SUPPORT")
    print("-" * 40)
    query = SearchQuery(
        query="counseling trauma PTSD depression anxiety mental health",
        categories=[ResourceCategory.MENTAL_HEALTH],
        limit=5
    )
    results = search_engine.search(query)
    for result in results:
        print(f"• {result.resource.name}")
        print(f"  Languages: {', '.join(result.resource.languages_available)}")
        print(f"  Services: {', '.join(result.resource.services_provided[:2])}...")
    
    # Scenario 5: Children's Services
    print("\n5. SERVICES FOR CHILDREN")
    print("-" * 40)
    query = SearchQuery(
        query="school children education homework English support kids",
        limit=6
    )
    results = search_engine.search(query)
    for result in results:
        print(f"• {result.resource.name}")
        print(f"  Category: {result.resource.category.value}")
        print(f"  Description: {result.resource.description[:100]}...")
    
    # Scenario 6: Language-specific search
    print("\n6. ARABIC LANGUAGE SERVICES")
    print("-" * 40)
    results = search_engine.search_by_language("Arabic", limit=5)
    for resource in results:
        print(f"• {resource.name}")
        print(f"  Languages: {', '.join(resource.languages_available)}")
        print(f"  Category: {resource.category.value}")
    
    # Scenario 7: Urgent Services
    print("\n7. CRITICAL & URGENT SERVICES")
    print("-" * 40)
    urgent_services = search_engine.search_urgent_services(limit=5)
    for resource in urgent_services:
        print(f"• {resource.name} [{resource.urgency_level.upper()}]")
        print(f"  Phone: {resource.contact.phone}")
        print(f"  Hours: {resource.contact.hours}")
    
    # Scenario 8: Employment Support
    print("\n8. EMPLOYMENT & JOB SEARCH")
    print("-" * 40)
    query = SearchQuery(
        query="job employment work resume interview career",
        categories=[ResourceCategory.EMPLOYMENT],
        limit=5
    )
    results = search_engine.search(query)
    for result in results:
        print(f"• {result.resource.name}")
        print(f"  Services: {', '.join(result.resource.services_provided[:3])}...")
    
    # Scenario 9: Financial Assistance
    print("\n9. FINANCIAL HELP & EMERGENCY RELIEF")
    print("-" * 40)
    query = SearchQuery(
        query="financial help money Centrelink payment emergency relief food voucher",
        categories=[ResourceCategory.FINANCIAL_ASSISTANCE],
        limit=5
    )
    results = search_engine.search(query)
    for result in results:
        print(f"• {result.resource.name}")
        print(f"  Services: {', '.join(result.resource.services_provided[:2])}...")
        print(f"  Eligibility: {result.resource.eligibility}")
    
    # Scenario 10: Women's Services
    print("\n10. SERVICES FOR WOMEN")
    print("-" * 40)
    query = SearchQuery(
        query="women domestic violence safety health parenting mother",
        limit=5
    )
    results = search_engine.search(query)
    for result in results:
        print(f"• {result.resource.name}")
        print(f"  Category: {result.resource.category.value}")
        print(f"  Contact: {result.resource.contact.phone}")
    
    # Scenario 11: Skills Recognition & Qualifications
    print("\n11. SKILLS RECOGNITION & QUALIFICATION ASSESSMENT")
    print("-" * 40)
    query = SearchQuery(
        query="overseas qualification skills assessment recognition professional degree",
        limit=5
    )
    results = search_engine.search(query)
    for result in results:
        print(f"• {result.resource.name}")
        print(f"  Services: {', '.join(result.resource.services_provided[:2])}...")
        print(f"  Cost: {result.resource.cost}")
    
    # Scenario 12: Business & Entrepreneurship
    print("\n12. BUSINESS STARTUP & ENTREPRENEURSHIP")
    print("-" * 40)
    query = SearchQuery(
        query="start business entrepreneur microfinance loan self-employment",
        limit=5
    )
    results = search_engine.search(query)
    for result in results:
        print(f"• {result.resource.name}")
        print(f"  Services: {', '.join(result.resource.services_provided[:2])}...")
        print(f"  Eligibility: {result.resource.eligibility[:50]}...")
    
    # Scenario 13: Professional Career Development
    print("\n13. PROFESSIONAL CAREER PATHWAYS")
    print("-" * 40)
    query = SearchQuery(
        query="professional career mentoring networking industry placement",
        limit=5
    )
    results = search_engine.search(query)
    for result in results:
        print(f"• {result.resource.name}")
        print(f"  Category: {result.resource.category.value}")
        print(f"  Services: {', '.join(result.resource.services_provided[:2])}...")
    
    # Scenario 14: Vocational Training & Apprenticeships
    print("\n14. VOCATIONAL TRAINING & APPRENTICESHIPS")
    print("-" * 40)
    query = SearchQuery(
        query="apprenticeship trade vocational certificate training TAFE",
        limit=5
    )
    results = search_engine.search(query)
    for result in results:
        print(f"• {result.resource.name}")
        print(f"  Cost: {result.resource.cost}")
        print(f"  Services: {', '.join(result.resource.services_provided[:2])}...")

def chatbot_integration_example():
    """Example of how to integrate with a chatbot"""
    config = QdrantConfig()
    search_engine = SearchEngine(config)
    
    print("\n" + "="*60)
    print("CHATBOT INTEGRATION EXAMPLE")
    print("="*60)
    
    user_queries = [
        "I just arrived from Afghanistan and need help",
        "My child needs to go to school but doesn't speak English",
        "I'm feeling very depressed and need someone to talk to",
        "How do I apply for Centrelink payments?",
        "I need a lawyer for my visa application",
        "I'm an engineer from overseas, how can I work in my profession here?",
        "I want to start my own business but need a small loan",
        "I have IT qualifications from my country, are they recognized here?"
    ]
    
    for user_input in user_queries:
        print(f"\n🤖 User: {user_input}")
        print("💬 Chatbot Response:")
        
        query = SearchQuery(query=user_input, limit=3)
        results = search_engine.search(query)
        
        if results:
            print("I found these services that can help you:\n")
            for i, result in enumerate(results, 1):
                resource = result.resource
                print(f"{i}. **{resource.name}**")
                print(f"   📞 Phone: {resource.contact.phone}")
                print(f"   🌐 Website: {resource.contact.website}")
                print(f"   📍 Address: {resource.contact.address}")
                print(f"   ⏰ Hours: {resource.contact.hours}")
                print(f"   ℹ️ {resource.description}")
                print()
        else:
            print("I couldn't find specific services for your query. Please call 131 450 for interpreter services or 000 for emergencies.")

if __name__ == "__main__":
    print("ACT Refugee Support Vector Database System")
    print("-" * 40)
    
    # Initialize the database
    if initialize_database():
        # Run demonstrations
        demo_search_scenarios()
        chatbot_integration_example()
    else:
        print("Failed to initialize database. Please check your Qdrant connection.")