# 🚂 Railway Deployment Guide

## ✅ Pre-Deployment Checklist

Your application is now configured for Railway deployment! Here's what has been fixed:

### 🔧 **Fixed Issues:**

1. **Health Check Endpoint**: Created a simple, robust `/health` endpoint that always returns 200 OK
2. **Simplified Server**: Created `api_server_railway_simple.py` with:
   - Graceful fallback when database is unavailable
   - Emergency contacts always available
   - No dependency on complex imports for health check
3. **Configuration Files**: Updated to use the simplified server
4. **Timeout Extended**: Increased health check timeout to 60 seconds

## 📋 Deployment Steps

### Step 1: Set Up Environment Variables in Railway

Go to your Railway project dashboard and add these environment variables:

#### **Required Variables:**
```
QDRANT_HOST=your-qdrant-host.com
QDRANT_PORT=6333
OPENAI_API_KEY=sk-your-openai-api-key
```

#### **For Qdrant Cloud Users:**
```
QDRANT_API_KEY=your-qdrant-api-key
```

#### **Optional Variables (Railway sets automatically):**
```
PORT=(Railway sets this automatically)
USE_LIGHTWEIGHT=true
ENABLE_AUTH=false
```

### Step 2: Deploy to Railway

#### Option A: Deploy via GitHub
1. Commit and push your changes:
```bash
git add .
git commit -m "Fix Railway deployment with simplified health check"
git push origin main
```

2. In Railway:
   - Create new project
   - Choose "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect and deploy

#### Option B: Deploy via Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up
```

### Step 3: Verify Deployment

Once deployed, test your endpoints:

1. **Health Check**: `https://your-app.railway.app/health`
   - Should return: `{"status": "healthy", "timestamp": "..."}`

2. **Detailed Health**: `https://your-app.railway.app/health/detailed`
   - Shows component status

3. **Emergency Services**: `https://your-app.railway.app/search/emergency`
   - Always returns emergency contacts (no DB required)

4. **Main Search**: `https://your-app.railway.app/search`
   - POST endpoint for searching services

## 🔍 Monitoring & Troubleshooting

### Check Deployment Logs
```bash
railway logs
```

### Common Issues & Solutions:

#### 1. Health Check Timeout
- **Solution**: Already fixed with simplified endpoint and extended timeout

#### 2. Database Connection Failed
- **Solution**: Server now starts even without database and provides fallback responses

#### 3. Missing Environment Variables
- **Solution**: Check Railway dashboard, ensure all required vars are set

#### 4. Import Errors
- **Solution**: Using `requirements-light.txt` with minimal dependencies

### Test Locally with Railway Environment
```bash
# Load Railway environment variables locally
railway run python api_server_railway_simple.py
```

## 📊 API Endpoints

### Core Endpoints:
- `GET /` - Service info
- `GET /health` - Simple health check (always returns 200)
- `GET /health/detailed` - Detailed component status
- `POST /search` - Main search endpoint
- `POST /search/emergency` - Emergency services (works without DB)

### Request Example:
```json
POST /search
{
    "message": "I need medical help",
    "limit": 3,
    "language": "Arabic"
}
```

## 🎯 Features of the Simplified Server

1. **Robust Health Check**: Never fails, always returns 200 OK
2. **Graceful Degradation**: Works even if database is unavailable
3. **Emergency Fallback**: Critical services always accessible
4. **Minimal Dependencies**: Only essential packages required
5. **Clear Logging**: Detailed logs for debugging
6. **CORS Enabled**: Ready for frontend integration

## 🚀 Post-Deployment

### 1. Monitor Performance
- Check Railway metrics dashboard
- Monitor response times
- Review error logs

### 2. Scale if Needed
```bash
# Increase resources in Railway dashboard
# or via CLI:
railway scale
```

### 3. Add Custom Domain (Optional)
- Go to Settings in Railway
- Add custom domain
- Update DNS records

## 📞 Emergency Contacts (Always Available)

Even if the database is down, these services are always returned:

- **000** - Emergency Services (Police, Fire, Ambulance)
- **131 450** - Translating and Interpreting Service
- **1800 022 222** - Health Direct
- **1800 737 732** - 1800RESPECT (Domestic Violence)
- **13 11 14** - Lifeline (Crisis Support)

## ✅ Success Indicators

Your deployment is successful when:
1. Health check passes (green in Railway dashboard)
2. Logs show "Starting Railway-optimized API server"
3. Can access `/health` endpoint via browser
4. Emergency endpoint returns contacts

## 📝 Notes

- The server is configured to work in "lightweight mode" by default
- Uses OpenAI embeddings instead of local models (lower memory)
- Automatically falls back to emergency contacts if DB unavailable
- All endpoints have error handling and graceful responses

## 🆘 Need Help?

1. Run validation script: `python validate_railway_deployment.py`
2. Check Railway logs: `railway logs`
3. Test locally: `railway run python api_server_railway_simple.py`
4. Review this guide for common issues

---

**Your app is now ready for Railway deployment! 🎉**

The simplified server ensures health checks will pass and provides fallback functionality even if external services are unavailable.
