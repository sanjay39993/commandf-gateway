# Command Gateway - Deployment Guide

## 🚀 Quick Start Deployment

### Prerequisites
- Git account (GitHub, GitLab, etc.)
- Free account on deployment platform
- (Optional) Telegram Bot Token for notifications

---

## 📦 Option 1: Railway.app (⭐ Recommended - Easiest)

### Step 1: Push to GitHub
```bash
# Initialize git repo
git init
git add .
git commit -m "Initial commit"

# Create GitHub repo at https://github.com/new
# Copy the repository URL

git remote add origin https://github.com/YOUR_USERNAME/cunbound.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Railway
1. Go to https://railway.app
2. Click **"New Project"** → **"Deploy from GitHub"**
3. Authorize Railway to access your GitHub
4. Select your `cunbound` repository
5. Railway auto-detects Python and deploys
6. Get your public URL from the **"Deployments"** tab

### Step 3: Configure Environment Variables (Optional)
1. Go to **Settings** → **Variables**
2. Add `TELEGRAM_BOT_TOKEN=your_bot_token` (if using Telegram)
3. Click **"Deploy"** to redeploy with env vars

**Cost:** Completely FREE with generous limits (includes 5GB/month storage)

---

## 📦 Option 2: Heroku (Free Tier Removed, But $5/month is Affordable)

### Step 1: Install Heroku CLI
```bash
# Windows (using chocolatey)
choco install heroku-cli

# Or download from https://devcenter.heroku.com/articles/heroku-cli
```

### Step 2: Deploy
```bash
heroku login
heroku create your-unique-app-name
git push heroku main
```

### Step 3: View Logs
```bash
heroku logs --tail
```

**Cost:** $5-7/month for a dyno

---

## 📦 Option 3: PythonAnywhere (Free Tier Available)

### Step 1: Create Account
1. Go to https://www.pythonanywhere.com
2. Sign up with email

### Step 2: Upload Code
1. **Beginners' bash console** → Upload files
2. Or clone from GitHub:
   ```bash
   git clone https://github.com/YOUR_USERNAME/cunbound.git
   ```

### Step 3: Configure Web App
1. Go to **Web** tab
2. Click **"Add a new web app"**
3. Select **Python 3.9** → **Flask**
4. Edit WSGI configuration:
   ```python
   # Replace with:
   import sys
   sys.path.insert(0, '/home/your_username/cunbound')
   from app import app
   application = app
   ```

### Step 4: Run
1. Upload `requirements.txt`
2. In bash: `pip install -r requirements.txt`
3. Reload web app from **Web** tab

**Cost:** Free with limited features, or $5/month for more

---

## 📦 Option 4: Render.com (Free Tier Available)

### Step 1: Create Account
1. Go to https://render.com
2. Sign up with GitHub

### Step 2: Deploy
1. Click **"New +"** → **"Web Service"**
2. Select your GitHub repository
3. Fill in settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 4 -b 0.0.0.0:\$PORT app:app`
4. Click **"Create Web Service"**
5. Get URL from dashboard

**Cost:** Free tier available (with limitations)

---

## 📦 Option 5: Replit (Easiest for Beginners)

### Step 1: Import Repository
1. Go to https://replit.com
2. Click **"Import"** → Paste GitHub URL
3. Select Python as language

### Step 2: Run
```bash
# In Replit console
pip install -r requirements.txt
python app.py
```

3. Click **"Run"** button
4. Your app gets a public URL

**Cost:** Free (with Replit Hoster for always-on)

---

## 🔐 Environment Variables

### Add to your deployment platform:

```
TELEGRAM_BOT_TOKEN=123456789:ABCDefGhIjKlMnoPqRsTuVwXyZ_1234567890
FLASK_ENV=production
```

### How to Get Telegram Bot Token:
1. Open Telegram app
2. Search for **@BotFather**
3. Send `/newbot`
4. Follow prompts
5. Copy token → Paste in your deployment platform

---

## ✅ Testing Your Deployment

### 1. Access Your App
```
https://your-app-name.railway.app  (or your platform's URL)
```

### 2. Get Admin API Key
Look at deployment logs:
```
Default admin created with API key: gF6x4lU8W6FErUNBf_GB15HLSg47UcDUGKSMQIs441o
```

### 3. Login
1. Paste API key in the login form
2. Click **"Sign In"**

### 4. Test Features
- [ ] Create a user (Admin → Users → Add New User)
- [ ] Create a rule (Admin → Rules → Add New Rule)
- [ ] Submit a command (Dashboard → Enter command)
- [ ] Approve pending commands (Admin → Approvals)

---

## 📊 Verifying Features Are Working

### Create Test Rule with Approval
```
Pattern: test.*
Action: REQUIRE_APPROVAL
Threshold: 2
```

### Submit Test Command
1. Go to **Commands** tab
2. Type: `test hello`
3. Should show **"Pending Approval"**

### Approve as Admin
1. Go to **Approvals** tab
2. See the pending command
3. Click **"Approve"** (need 2 approvals)
4. Command should show as "Approved"

### Re-submit with Token
1. Copy the approval token
2. Submit command again with token
3. Should execute successfully

---

## 🔧 Troubleshooting

### "Module not found" error
```bash
# Make sure all packages are installed
pip install -r requirements.txt
```

### Database locked error
This happens with SQLite in production. For high-traffic apps, use PostgreSQL:
```bash
# Railway/Render: Add PostgreSQL service
# Update requirements.txt: add psycopg2-binary
# Update DATABASE variable
```

### Port issues
```bash
# Railway/Heroku automatically set PORT env variable
# App reads it: port = int(os.environ.get('PORT', 5000))
```

---

## 📈 Scaling Up

### When you need more features:

1. **More Users**: Deploy PostgreSQL instead of SQLite
2. **Real Command Execution**: Replace `[MOCKED]` with actual `subprocess.run()`
3. **More Admins**: Notifications already support multi-admin
4. **Custom Rules**: Add your own regex patterns
5. **Integration**: Add Slack/Discord webhooks

---

## 🎯 Recommended Setup

**For Individuals/Small Teams:**
- **Platform**: Railway.app (Free & Simple)
- **Database**: SQLite (included)
- **Notifications**: Telegram (free)

**For Production:**
- **Platform**: Heroku or Render (PostgreSQL)
- **Database**: PostgreSQL (included)
- **Notifications**: Telegram + Email

---

## 📞 Support

If deployment fails:
1. Check logs on your platform's dashboard
2. Ensure all files are uploaded (check git status)
3. Verify requirements.txt has all packages
4. Make sure Procfile is present
5. Check Python version (3.9+)

