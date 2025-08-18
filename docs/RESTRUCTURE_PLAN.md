# Codebase Restructuring Plan

## Current Issues Identified

### 1. Duplicate Files (Identical copies in root and subdirectories)
- `api_v2_orchestrator.py` (root) = `api/api_v2_orchestrator.py`
- `voiceflow_hybrid_router.py` (root) = `api/voiceflow_hybrid_router.py`
- `api_server.py` (root) ≠ `api/api_server.py` (different files!)
- Multiple config files: `config.py`, `config_light.py`, `core/config.py`, `core/config_light.py`
- Multiple model files: `models.py`, `models_enhanced.py`, `core/models.py`
- Resource data files scattered: root vs `data/` directory

### 2. Unclear Naming
- `api_server_railway.py` - platform-specific, should be clearer
- `config_light.py` - vague name, should indicate purpose
- `search_engine_simple.py` vs `search_engine.py` vs `search_engine_enhanced.py`
- Multiple `main.py` files in different locations

### 3. Poor Organization
- Archive folder contains mixed content (docs, code, guides)
- Test files in both root and `tests/` directory
- Documentation scattered across root and subdirectories
- Deployment configs in root instead of `deployment/`
- JavaScript files mixed with Python in root

## Proposed New Structure

```
act-refugee-support/
│
├── src/                        # All source code
│   ├── api/                    # API layer
│   │   ├── __init__.py
│   │   ├── main_api.py        # Main FastAPI server (was api_server.py)
│   │   ├── orchestrator.py    # API orchestrator (was api_v2_orchestrator.py)
│   │   └── voiceflow_router.py # Voiceflow integration
│   │
│   ├── core/                   # Core business logic
│   │   ├── __init__.py
│   │   ├── config.py          # Main configuration
│   │   ├── models.py          # Data models
│   │   ├── cache.py           # Cache management
│   │   └── errors.py          # Error handling
│   │
│   ├── data/                   # Data and resources
│   │   ├── __init__.py
│   │   ├── resources.py       # Main resource data
│   │   ├── economic.py        # Economic integration resources
│   │   └── critical.py        # Critical gap resources
│   │
│   ├── search/                 # Search functionality
│   │   ├── __init__.py
│   │   ├── engine.py          # Main search engine
│   │   ├── enhanced.py        # Enhanced search features
│   │   └── economic.py        # Economic search specialization
│   │
│   └── database/              # Database operations
│       ├── __init__.py
│       ├── ingestion.py       # Data ingestion
│       ├── pipeline.py        # Data pipeline
│       └── qdrant_setup.py    # Qdrant configuration
│
├── integrations/              # External integrations
│   ├── voiceflow/
│   │   ├── functions.js      # Voiceflow functions
│   │   ├── config.json       # Voiceflow configuration
│   │   └── README.md         # Integration guide
│   └── webhook/
│       └── endpoint.js        # Webhook handler
│
├── deployment/                # Deployment configurations
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   ├── railway/
│   │   └── railway.json
│   └── requirements/
│       ├── base.txt          # Core requirements
│       ├── dev.txt           # Development requirements
│       └── prod.txt          # Production requirements
│
├── tests/                     # All tests
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                      # Documentation
│   ├── API.md
│   ├── SETUP.md
│   ├── DEPLOYMENT.md
│   └── VOICEFLOW.md
│
├── scripts/                   # Utility scripts
│   ├── init_db.py            # Database initialization
│   └── validate_deploy.py    # Deployment validation
│
├── archive/                   # Old/deprecated files (to be deleted after migration)
│
├── .github/                   # GitHub specific
│   └── workflows/
│
├── main.py                    # Application entry point
├── README.md                  # Project documentation
├── .env.example              # Environment variables template
├── .gitignore
├── pyproject.toml            # Python project configuration
└── package.json              # Node.js dependencies

```

## File Renaming Plan

### API Files
- `api_server.py` → `src/api/main_api.py`
- `api_v2_orchestrator.py` → `src/api/orchestrator.py`
- `voiceflow_hybrid_router.py` → `src/api/voiceflow_router.py`
- `api_server_railway.py` → DELETE (platform-specific, keep only one main API)

### Core Files
- `config.py` → `src/core/config.py`
- `config_light.py` → DELETE (merge into main config with flags)
- `models.py` → `src/core/models.py`
- `models_enhanced.py` → Merge into `src/core/models.py`
- `cache_manager.py` → `src/core/cache.py`
- `error_handler.py` → `src/core/errors.py`

### Data Files
- `act_resources_data.py` → `src/data/resources.py`
- `economic_integration_resources.py` → `src/data/economic.py`
- `critical_gap_resources.py` → `src/data/critical.py`

### Search Files
- `search_engine.py` → `src/search/engine.py`
- `search_engine_enhanced.py` → `src/search/enhanced.py`
- `search_engine_simple.py` → DELETE (merge into main engine)
- `search_economic_integration.py` → `src/search/economic.py`
- `search_advanced.py` → DELETE (merge into enhanced)

### Database Files
- `data_ingestion.py` → `src/database/ingestion.py`
- `data_pipeline.py` → `src/database/pipeline.py`
- `setup_qdrant_openai.py` → `src/database/qdrant_setup.py`
- `populate_qdrant_cloud.py` → `scripts/populate_db.py`

### Integration Files
- `voiceflow_functions.js` → `integrations/voiceflow/functions.js`
- `voiceflow-api-connector.js` → `integrations/voiceflow/connector.js`
- `webhook-endpoint.js` → `integrations/webhook/endpoint.js`
- `voiceflow_api_config.json` → `integrations/voiceflow/config.json`

### Test Files
- `test_*.py` in root → Move to `tests/integration/`
- `tests/*.py` → Organize into `tests/unit/` and `tests/integration/`

### Documentation
- All `*.md` files except README.md → Move to `docs/`
- Consolidate duplicate documentation

## Files to Delete

### Definite Deletions
1. All files in `archive/` directory (30+ files)
2. Duplicate files in root that exist in subdirectories
3. `api_server_railway.py` (platform-specific variant)
4. `config_light.py` and `core/config_light.py` (merge into main config)
5. `search_engine_simple.py` (merge functionality)
6. `models_enhanced.py` (merge into main models)
7. Multiple scattered `main.py` files (keep only one)

### Documentation to Consolidate
- Merge all VOICEFLOW_*.md files into one comprehensive guide
- Merge all MIGRATION_*.md files into deployment guide
- Consolidate deployment guides (Railway, Vercel, etc.)

## Migration Steps

1. **Create new directory structure**
2. **Move and rename files according to plan**
3. **Update all imports in Python files**
4. **Update paths in JavaScript files**
5. **Consolidate duplicate code**
6. **Update configuration files**
7. **Test all functionality**
8. **Delete archive and unnecessary files**
9. **Update documentation**

## Benefits

- **Clarity**: Clear, descriptive file names
- **Organization**: Logical grouping by functionality
- **Maintainability**: No duplicate files, clear structure
- **Scalability**: Easy to add new features in appropriate locations
- **Deployment**: Separated deployment configs by platform
- **Testing**: Organized test structure
- **Documentation**: Centralized and organized docs