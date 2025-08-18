# Migration Guide - ACT Refugee Support Codebase

## Current Status

The codebase has been reorganized for better maintainability while preserving backward compatibility.

### What's Been Done

1. **Archived unused files** to `archive/` folder
2. **Created organized structure** with files COPIED (not moved) to new locations
3. **Original files remain in root** to maintain compatibility with deployment

## New Directory Structure

```
act-refugee-support/
├── api/                    # API endpoints and routing
│   ├── api_server.py
│   ├── api_v2_orchestrator.py
│   └── voiceflow_hybrid_router.py
├── search/                 # Search engines
│   ├── search_engine.py
│   ├── search_engine_simple.py
│   └── search_economic_integration.py
├── data/                   # Resource databases
│   ├── act_resources_data.py
│   ├── critical_gap_resources.py
│   └── economic_integration_resources.py
├── core/                   # Core utilities
│   ├── config.py
│   ├── config_light.py
│   ├── models.py
│   ├── error_handler.py
│   ├── cache_manager.py
│   └── data_ingestion.py
├── voiceflow/             # Voiceflow configuration
│   ├── voiceflow_api_config.json
│   └── voiceflow_functions.js
├── scripts/               # Utility scripts
│   └── main.py
├── tests/                 # All test files
│   └── test_*.py
├── deployment/            # Deployment configs
│   ├── Dockerfile
│   ├── Procfile
│   ├── railway.json
│   └── docker-compose.yml
├── docs/                  # Documentation
│   ├── README.md
│   └── VOICEFLOW_INTEGRATION_GUIDE.md
└── archive/               # Unused/old files
```

## Current Deployment Status

**IMPORTANT**: The deployment still uses files from the ROOT directory:
- `Procfile` points to `api_server.py` in root
- `Dockerfile` copies all files from root
- `railway.json` expects files in root

## Migration Options

### Option 1: Keep Dual Structure (CURRENT - SAFE)
- Files exist in both root (for deployment) and organized folders (for development)
- No import changes needed
- Can gradually migrate

### Option 2: Full Migration (FUTURE)
When ready to fully migrate:

1. **Update deployment configs**:
   - Modify `Procfile`: `web: python api/api_server.py`
   - Update `Dockerfile` to use new paths
   - Adjust `railway.json` accordingly

2. **Update imports in files**:
   ```python
   # Old imports (current)
   from config_light import QdrantConfig
   from search_engine_simple import SimpleSearchEngine
   
   # New imports (after migration)
   from core.config_light import QdrantConfig
   from search.search_engine_simple import SimpleSearchEngine
   ```

3. **Test thoroughly** before removing root files

## Files Safe to Delete from Root (after testing)

Once you confirm the organized structure works:
```
# These are now duplicated in organized folders
- api_server.py
- api_v2_orchestrator.py
- voiceflow_hybrid_router.py
- search_engine.py
- search_engine_simple.py
- search_economic_integration.py
- act_resources_data.py
- critical_gap_resources.py
- economic_integration_resources.py
- config.py
- config_light.py
- models.py
- error_handler.py
- cache_manager.py
- data_ingestion.py
- main.py
- voiceflow_api_config.json
- voiceflow_functions.js
- README.md
- VOICEFLOW_INTEGRATION_GUIDE.md
```

## Testing the New Structure

1. **Test imports**:
   ```bash
   python -c "from api.api_server import app; print('API import works')"
   python -c "from search.search_engine_simple import SimpleSearchEngine; print('Search import works')"
   ```

2. **Test database initialization**:
   ```bash
   python scripts/main.py
   ```

3. **Test API locally**:
   ```bash
   python api/api_server.py
   ```

## Rollback Plan

If issues arise:
1. All original files remain in root (unchanged)
2. Backup created at: `../act-refugee-support-backup-[timestamp]`
3. Can restore from archive: `move archive/* .`

## Next Steps

1. ✅ Archive unused files
2. ✅ Create organized structure
3. ✅ Copy files to new locations
4. 🔄 Test new structure locally
5. 🔄 Update deployment configs (when ready)
6. 🔄 Remove duplicates from root (after successful deployment)

## Notes

- **Current deployment continues to work** from root files
- **No immediate changes required** to deployment
- Can migrate gradually at your own pace
- All tests moved to `tests/` folder for cleaner root
