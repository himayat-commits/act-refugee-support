# 🚀 Qdrant Cloud Setup Guide

## Step 1: Create Your Qdrant Cloud Account

### 1.1 Sign Up
1. Go to **[https://cloud.qdrant.io](https://cloud.qdrant.io)**
2. Click **"Get Started"** or **"Sign Up"**
3. Sign up using:
   - GitHub (recommended for developers)
   - Google
   - Or email/password

### 1.2 Verify Your Email
- Check your email for verification link
- Click to verify your account

---

## Step 2: Create Your First Cluster

### 2.1 Create Free Cluster
1. Once logged in, click **"Create Cluster"** or **"+ New Cluster"**
2. Choose the **Free Tier** (1GB RAM, 0.5 vCPU)
   - Perfect for your refugee support project
   - No credit card required
3. Select options:
   - **Cluster Name**: `act-refugee-support` (or your preference)
   - **Region**: Choose closest to your users (e.g., `us-east-1` or `ap-southeast-2` for Australia)
   - **Version**: Use latest (default)

### 2.2 Wait for Provisioning
- Takes about 30-60 seconds
- You'll see a progress indicator
- Status will change from "Creating" to "Running"

---

## Step 3: Get Your Connection Details

### 3.1 Access Cluster Dashboard
1. Click on your cluster name once it's running
2. You'll see the cluster details page

### 3.2 Copy Your Credentials
Look for these important details:

**Cluster URL:**
```
https://YOUR-CLUSTER-ID.us-east-1-0.aws.cloud.qdrant.io
```
(This is your QDRANT_HOST - copy the full URL)

**Port:**
```
6333
```
(Usually 6333 for HTTPS connections)

### 3.3 Generate API Key
1. In cluster dashboard, click **"API Keys"** tab
2. Click **"Create API Key"**
3. Give it a name: `railway-api-key`
4. **IMPORTANT**: Copy the API key immediately (shown only once!)
5. Save it somewhere secure

Your credentials will look like:
```
QDRANT_HOST=abc123xyz.us-east-1-0.aws.cloud.qdrant.io
QDRANT_PORT=6333
QDRANT_API_KEY=YOUR_LONG_API_KEY_HERE
```

---

## Step 4: Add Credentials to Railway

### 4.1 Open Railway Dashboard
1. Go to your Railway project
2. Click on your deployed service
3. Go to **"Variables"** tab

### 4.2 Add Environment Variables
Add these three variables:

```bash
QDRANT_HOST=YOUR-CLUSTER-ID.us-east-1-0.aws.cloud.qdrant.io
QDRANT_PORT=6333
QDRANT_API_KEY=YOUR_API_KEY_HERE
```

**⚠️ IMPORTANT**: 
- Do NOT include `https://` in QDRANT_HOST
- Just use the domain: `xxx.us-east-1-0.aws.cloud.qdrant.io`

### 4.3 Deploy Changes
- Railway will automatically redeploy when you add variables
- Wait for the deployment to complete (green checkmark)

---

## Step 5: Update Local .env File

Create/update your local `.env` file for testing:

```env
# Qdrant Cloud Configuration
QDRANT_HOST=YOUR-CLUSTER-ID.us-east-1-0.aws.cloud.qdrant.io
QDRANT_PORT=6333
QDRANT_API_KEY=YOUR_API_KEY_HERE

# OpenAI Configuration (if not already set)
OPENAI_API_KEY=your-openai-key

# Other settings
USE_LIGHTWEIGHT=true
```

---

## Step 6: Test Connection

Run this test script to verify connection:

```python
python test_qdrant_connection.py
```

You should see:
```
✅ Connected to Qdrant Cloud successfully!
✅ Cluster is healthy
Collections: []  # Empty initially
```

---

## Step 7: Populate Your Database

Now populate with refugee service data:

```bash
python populate_qdrant_cloud.py
```

This will:
1. Create the collection
2. Generate embeddings for all services
3. Upload to Qdrant Cloud
4. Verify the data

Expected output:
```
Creating collection: act_refugee_resources
Loading data from CSV...
Generating embeddings...
Uploading to Qdrant Cloud...
✅ Successfully uploaded 300+ services
```

---

## Step 8: Verify Everything Works

### 8.1 Test Your Live API
```bash
python test_live_api.py
```

Now search should return real results!

### 8.2 Check Qdrant Dashboard
1. In Qdrant Cloud dashboard, click your cluster
2. Go to **"Collections"** tab
3. You should see `act_refugee_resources` with point count

### 8.3 Test a Real Search
```powershell
$body = @{
    message = "medical services in Canberra"
    limit = 3
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://YOUR-APP.railway.app/search" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"
```

---

## 🎯 Quick Checklist

- [ ] Created Qdrant Cloud account
- [ ] Created free cluster
- [ ] Copied cluster URL
- [ ] Generated API key
- [ ] Added credentials to Railway
- [ ] Updated local .env file
- [ ] Tested connection
- [ ] Populated database
- [ ] Verified search works

---

## 🆘 Troubleshooting

### "Connection Refused" Error
- Check QDRANT_HOST doesn't include `https://`
- Verify API key is correct
- Ensure cluster is in "Running" state

### "Authentication Failed"
- API key might be incorrect
- Try generating a new API key
- Make sure no extra spaces in the key

### "Collection Not Found"
- Run `populate_qdrant_cloud.py` to create and populate
- Check collection name matches: `act_refugee_resources`

### Railway Not Connecting
- Verify all three env variables are set in Railway
- Check Railway logs: `railway logs`
- Ensure cluster allows connections from any IP

---

## 📊 Qdrant Cloud Features

Your free cluster includes:
- **1GB RAM** - Enough for ~50,000 vectors
- **0.5 vCPU** - Good for moderate traffic
- **Persistent Storage** - Data saved automatically
- **Automatic Backups** - Daily snapshots
- **HTTPS/TLS** - Secure connections
- **99.9% Uptime SLA** - Reliable service

---

## 🚀 Next Steps

Once connected and populated:

1. **Monitor Usage**
   - Check Qdrant dashboard for metrics
   - View search performance

2. **Optimize Searches**
   - Add filters for better results
   - Implement caching for common queries

3. **Scale if Needed**
   - Upgrade to paid tier for more resources
   - Add more collections for different data types

---

## 📝 Important Links

- **Qdrant Cloud Dashboard**: [cloud.qdrant.io](https://cloud.qdrant.io)
- **Qdrant Documentation**: [qdrant.tech/documentation](https://qdrant.tech/documentation)
- **API Reference**: [api.qdrant.tech](https://api.qdrant.tech)
- **Status Page**: [status.qdrant.io](https://status.qdrant.io)

---

**Need help?** The Qdrant Cloud free tier is perfect for your refugee support project and can handle thousands of searches per day!
