# ACT Refugee & Migrant Support Vector Database

A comprehensive Qdrant vector database system designed to power AI chatbots supporting migrants and refugees in the Australian Capital Territory (ACT). This system provides intelligent search and retrieval of essential services and resources, with specialized focus on economic integration and addressing skill underutilization.

## Features

- **Comprehensive Resource Coverage**: 50+ essential services covering legal aid, healthcare, housing, education, employment, mental health, and economic integration
- **Economic Integration Focus**: Specialized resources for skill recognition, career pathways, microenterprise support, and professional development
- **Skill Underutilization Solutions**: Targeted support for overseas-qualified professionals to work in their field
- **Intelligent Semantic Search**: Uses OpenAI embeddings for superior context and intent understanding
- **Multi-language Support**: Resources available in multiple languages with interpreter services
- **Urgency-based Prioritization**: Critical services highlighted for emergency situations
- **Category-based Filtering**: Organized into 14 main service categories

## Technical Stack

- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **Vector Database**: Qdrant for semantic search
- **API Framework**: FastAPI with async support
- **Search**: Multiple specialized search engines
- **Integration**: Optimized for Voiceflow chatbots

## Installation

1. Install Qdrant (using Docker):
```bash
docker run -p 6333:6333 qdrant/qdrant
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
```

4. Set required environment variables in `.env`:
```env
# Required
OPENAI_API_KEY=your-openai-api-key-here

# Qdrant Configuration
QDRANT_HOST=localhost  # or your Qdrant Cloud URL
QDRANT_PORT=6333
QDRANT_API_KEY=  # Required for Qdrant Cloud
```

## Usage

### Initialize the Database
```python
python main.py
```

### Run the API Server
```bash
python run_api.py
# API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Integrate with Your Chatbot
```python
from src.core.config import QdrantConfig
from src.search.engine import SearchEngine
from src.core.models import SearchQuery

# Initialize
config = QdrantConfig()
search_engine = SearchEngine(config)

# Search for resources
query = SearchQuery(
    query="I need help finding a job",
    limit=5
)
results = search_engine.search(query)

# Process results
for result in results:
    print(f"{result.resource.name}: {result.resource.contact.phone}")
```

## Resource Categories

### Essential Services
1. **Legal Aid**: Immigration law, visa applications, refugee protection
2. **Healthcare**: Medical services, mental health, trauma support
3. **Housing**: Emergency accommodation, rental assistance, public housing
4. **Education**: English classes, school enrollment, adult education
5. **Emergency Services**: 000, crisis support, domestic violence help
6. **Community Support**: Social groups, volunteer programs, cultural activities
7. **Mental Health**: Counseling, trauma therapy, support groups
8. **Government Programs**: HSP, SETS, settlement services

### Economic Integration & Employment
9. **Skills Recognition**: Overseas qualification assessment, RPL, professional registration
10. **Career Pathways**: Industry-specific programs, professional development, workplace readiness
11. **Microenterprise Support**: Business loans, microfinance, entrepreneurship training
12. **Vocational Training**: Free TAFE courses, apprenticeships, JobTrainer programs
13. **Professional Networking**: Mentoring programs, industry connections, peer networks
14. **Business Development**: NEIS, incubators, social enterprise support

### Specialized Support
15. **Language Learning**: AMEP, workplace English, professional communication
16. **Financial Assistance**: Centrelink, emergency relief, business grants
17. **Children's Services**: Youth programs, after-school activities
18. **Women's Services**: Women's health, female entrepreneur programs
19. **Disability Support**: NDIS, assistive technology

## Key Services Included

### Emergency Contacts
- **Triple Zero (000)**: Police, Fire, Ambulance
- **Domestic Violence Crisis**: (02) 6280 0900
- **Mental Health Crisis**: 1800 648 911

### Major Support Organizations
- **Companion House**: Trauma and torture counseling
- **Legal Aid ACT**: Free migration law assistance
- **MARSS**: Settlement services for new arrivals
- **CIT AMEP**: Free English language programs
- **Centrelink Multicultural Services**: Financial support

### Economic Integration Services
- **VETASSESS**: Professional skills assessment for migrants
- **NEIS Program**: Business startup training and support
- **Many Rivers Microfinance**: Small business loans up to $50,000
- **Professional Pathways Programs**: Industry-specific integration
- **JobTrainer Fund**: Free training in priority sectors
- **Ignite Business Incubator**: Migrant entrepreneur stream

## Search Capabilities

### Query Types Supported
- Natural language queries: "I need help with my visa"
- Multi-intent queries: "housing and English classes"
- Urgency-based: Filter by critical/high/standard priority
- Language-specific: Find services in specific languages
- Category-specific: Search within service categories

### Example Queries
```python
# Emergency help
"urgent medical help doctor emergency"

# New arrival needs
"just arrived need housing English job"

# Mental health support
"counseling depression anxiety trauma PTSD"

# Children's services
"school enrollment children education homework"

# Skills recognition
"overseas qualification engineer assessment recognition"

# Business startup
"start business loan microfinance entrepreneur NEIS"

# Career transition
"professional mentoring IT career pathway placement"

# Free training
"free vocational training certificate apprenticeship"
```

## API Reference

### SearchEngine Methods

- `search(query: SearchQuery)`: Main semantic search
- `search_by_category(category: ResourceCategory)`: Category filtering
- `search_urgent_services()`: Get critical/high priority services
- `search_by_language(language: str)`: Find language-specific services
- `get_resource_by_id(resource_id: str)`: Retrieve specific resource

### EconomicIntegrationSearch Methods

- `search_skill_underutilization_solutions(profession: str)`: Find qualification recognition pathways
- `search_entrepreneurship_support(stage: str)`: Business support by stage (idea/startup/growth)
- `search_career_pathways(industry: str, experience_level: str)`: Industry-specific career paths
- `search_vocational_training(free_only: bool, sector: str)`: Training opportunities
- `search_mentoring_programs(profession: str)`: Professional mentoring matches
- `search_financial_support_for_business(amount_needed: str)`: Business funding options
- `get_economic_integration_pathway(user_profile: Dict)`: Personalized integration plan

## Data Structure

Each resource contains:
- Basic info (name, description, category)
- Contact details (phone, email, website, address, hours)
- Service details (services provided, eligibility, cost)
- Language support
- Urgency level
- Keywords for improved search

## Project Structure

```
act-refugee-support/
├── src/                  # Source code
│   ├── api/             # FastAPI endpoints
│   ├── core/            # Configuration and models
│   ├── search/          # Search engines
│   ├── data/            # Resource data
│   └── database/        # Qdrant operations
├── deployment/          # Deployment configs
├── docs/                # Documentation
├── tests/               # Test suites
└── run_api.py          # Main entry point
```

## Requirements

- Python 3.8+
- OpenAI API key (required for embeddings)
- Qdrant (local or cloud)
- 8GB RAM recommended

## Contributing

To add new resources:
1. Edit `src/data/resources.py`
2. Follow the Resource model structure
3. Include accurate contact information
4. Specify appropriate urgency levels
5. Add relevant keywords

## Deployment Options

### Railway (Recommended)
```bash
# Deploy with one click using railway.json
# Set OPENAI_API_KEY in Railway dashboard
```

### Docker
```bash
docker build -f deployment/docker/Dockerfile -t refugee-api .
docker run -p 8000:8000 --env-file .env refugee-api
```

### Production Considerations
1. **Required**: Set OPENAI_API_KEY environment variable
2. Use managed Qdrant Cloud for reliability
3. Enable API authentication (ENABLE_AUTH=true)
4. Implement caching for frequent queries
5. Regular updates of contact information

## Privacy & Security

- No personal user data stored
- Only public service information included
- Suitable for public-facing chatbots
- Regular updates recommended for accuracy

## Support

For issues or questions about the ACT refugee support services database, please refer to the official service providers listed in the resources.