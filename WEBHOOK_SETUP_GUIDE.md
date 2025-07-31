# 🪝 GitHub Webhook Setup Guide

Your webhook server is running successfully! Here's how to set up GitHub webhooks.

## ✅ Current Status

- **🟢 Webhook Server**: Running on port 3000
- **🔍 Local URL**: http://localhost:3000/webhook
- **💚 Health Check**: http://localhost:3000/health ✅
- **🔒 Generated Secret**: `***REMOVED***`

## 🌍 Getting a Public URL

For GitHub webhooks to work, you need a **publicly accessible URL**. Here are several options:

### Option 1: ngrok (Recommended for Testing) 🚀

```bash
# Sign up at https://ngrok.com (free account)
# Get your auth token from the dashboard
./ngrok authtoken YOUR_AUTH_TOKEN_HERE

# Start the tunnel
./ngrok http 3000
```

This will give you a URL like: `https://abc123.ngrok.io`

### Option 2: Alternative Tunnel Services

```bash
# Localtunnel (no signup required)
npm install -g localtunnel
lt --port 3000

# Serveo (no install required)  
ssh -R 80:localhost:3000 serveo.net
```

### Option 3: Cloud Deployment

Deploy to a cloud service:
- **Heroku**: `git push heroku main`
- **Railway**: Connect your GitHub repo
- **DigitalOcean**: Use App Platform
- **AWS/GCP/Azure**: Deploy to your preferred cloud

### Option 4: Local Network with Public IP

If you have a public IP and can configure port forwarding:
```bash
# Configure your router to forward port 3000 to this machine
# Your public URL would be: http://YOUR_PUBLIC_IP:3000/webhook
```

## 🔧 GitHub Webhook Configuration

Once you have your public URL, set up the webhook in GitHub:

### 📋 Webhook Settings

| Setting | Value |
|---------|-------|
| **Payload URL** | `https://YOUR_PUBLIC_URL/webhook` |
| **Content type** | `application/json` |
| **Secret** | `***REMOVED***` |
| **SSL verification** | ✅ Enable |

### 🎯 Events to Subscribe

Choose the events you want to receive:

**Recommended for Jira Integration:**
- ✅ Issues (opened, closed, edited)
- ✅ Issue comments
- ✅ Pull requests (opened, closed, merged)
- ✅ Pull request reviews
- ✅ Pull request review comments

**All Events (for full integration):**
- ✅ Send me everything

### 📝 Step-by-Step Setup

1. **Go to your GitHub repository**
2. **Click**: Settings → Webhooks → Add webhook
3. **Enter Payload URL**: `https://YOUR_PUBLIC_URL/webhook`
4. **Select Content type**: `application/json`
5. **Enter Secret**: `***REMOVED***`
6. **Select events** (see above)
7. **Click**: "Add webhook"

## 🔄 Update Environment Variables

Add the webhook secret to your environment:

```bash
# Add to your .env file or export
export GITHUB_WEBHOOK_SECRET="***REMOVED***"

# Update your env.example file
echo 'GITHUB_WEBHOOK_SECRET=***REMOVED***' >> env.example
```

## 🧪 Testing Your Webhook

### 1. Test the Server Health
```bash
curl http://localhost:3000/health
# Should return: {"status": "ok", "timestamp": "..."}
```

### 2. Test with ngrok URL
```bash
curl https://YOUR_NGROK_URL/health
# Should return the same response
```

### 3. GitHub Webhook Test
1. Go to GitHub → Settings → Webhooks
2. Click on your webhook
3. Go to "Recent Deliveries"
4. Click "Redeliver" on any delivery
5. Check your server logs for the incoming request

## 📊 Monitoring Webhooks

### View Server Logs
```bash
# Real-time logs
tail -f webhook_server.log

# Recent logs
tail -20 webhook_server.log

# Search for webhook events
grep "webhook" webhook_server.log
```

### Server Management
```bash
# Check status
python server_status.py status

# View logs
python server_status.py logs

# Restart server
python server_status.py restart
```

## 🔍 Troubleshooting

### Webhook Not Receiving Events
1. **Check public URL accessibility**:
   ```bash
   curl https://YOUR_PUBLIC_URL/health
   ```

2. **Verify webhook secret matches**:
   - GitHub webhook secret
   - Your `GITHUB_WEBHOOK_SECRET` environment variable

3. **Check GitHub webhook deliveries**:
   - Go to GitHub → Settings → Webhooks
   - Click on your webhook
   - Check "Recent Deliveries" for errors

### Common Issues

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Check webhook secret matches |
| 404 Not Found | Verify URL ends with `/webhook` |
| Connection refused | Ensure server is running on port 3000 |
| Tunnel expired | Restart ngrok tunnel |

## 🎉 Success Indicators

You'll know it's working when:
- ✅ GitHub webhook shows "✓" with recent deliveries
- ✅ Your server logs show incoming webhook events
- ✅ JIRA issues are created from GitHub events
- ✅ No errors in webhook delivery attempts

## 🔄 Integration Features

Once working, your webhook will:
- 🎯 Create JIRA issues from GitHub PR comments
- 🔍 Search for similar existing issues
- 📋 Link GitHub PRs to JIRA issues
- 🤖 Automate issue creation and updates

---

**🚀 Ready to go! Choose your public URL method and set up the GitHub webhook!**