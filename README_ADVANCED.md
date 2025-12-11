# Command Gateway - Advanced Edition

> **Secure Command Execution System with Multi-Admin Approval, Escalation, and Audit Logging**

A production-ready command gateway for controlled, audited command execution. Perfect for DevOps teams, system administrators, and organizations that need fine-grained access control with accountability.

---

## ⭐ Advanced Features

### 1. **Multi-Admin Approval System**
Commands can require multiple admin approvals before execution. Configurable thresholds per rule or per user tier.

```
User submits command → Pending Approval
Admin 1 approves → 1/2 approvals
Admin 2 approves → Threshold met, Ready to Execute
User re-submits → Command executes
```

### 2. **User-Tier Based Approval Levels**
Different users have different approval requirements:
- **Junior**: Requires 3 approvals (high scrutiny)
- **Mid**: Requires 2 approvals (standard)
- **Senior/Lead**: Requires 1 approval (trusted)

### 3. **Automatic Escalation**
Commands waiting for approval auto-escalate to all admins after 1 hour with notifications.

### 4. **Time-Based Rules**
Rules adapt based on time of day:
```
- "Auto-accept deployments 09:00-17:00 (business hours)"
- "Require approval outside business hours"
- "Timezone-aware (supports global teams)"
```

### 5. **Rule Conflict Detection**
System prevents creation of overlapping rules that would cause execution ambiguity.

### 6. **Real-Time Notifications**
- Telegram notifications for approval requests & escalations
- Email notifications for audit trail
- Async (non-blocking)

### 7. **Complete Audit Trail**
Every action logged with timestamp:
- User creation/deletion
- Rule creation/modification
- Command submissions & executions
- Approvals & rejections
- Escalations

### 8. **Credit-Based Rate Limiting**
Users consume credits per command. Admins can allocate credits to users.

---

## 🚀 Deployment (Choose One)

### ⭐ Railway.app (Recommended - Free & Simple)
```bash
# Push to GitHub first
git push origin main

# Then go to https://railway.app → Deploy from GitHub
# Takes 2 minutes, includes free tier
```

### Heroku ($5-7/month)
```bash
heroku create your-app-name
git push heroku main
```

### Render, PythonAnywhere, Replit
See [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step instructions.

---

## 🎯 Quick Start (Local)

```bash
# Install dependencies
pip install -r requirements.txt

# Run
python app.py

# Open browser
http://localhost:5000
```

Login with auto-generated admin API key (check console output)

---

## 📋 Test the Features

### ✅ Test REQUIRE_APPROVAL Workflow
1. **Create Rule**: 
   - Pattern: `test.*`
   - Action: REQUIRE_APPROVAL
   - Threshold: 2

2. **Submit Command**: Type `test hello`
   - Status: "Pending Approval"

3. **Approve**:
   - Login as Admin 1 → Approve
   - Login as Admin 2 → Approve
   - Status: "Approved"

4. **Execute**:
   - Submit command with approval token
   - Status: "Executed"

### ✅ Test User-Tier Rules
1. Create user "junior_dev" with tier "junior"
2. Create user "senior_dev" with tier "senior"
3. Create rule requiring approval
4. Submit same command as both users
5. Junior user needs 3 approvals, senior needs 1

### ✅ Test Time-Based Rules
1. Create rule: Pattern=`deploy.*`, Time=09:00-17:00
2. Submit during business hours → Auto-accepts
3. Submit outside hours → Requires approval

### ✅ Test Escalation
1. Submit command requiring approval
2. Don't approve anything
3. Wait 1 hour (check logs)
4. All admins notified via Telegram/Email

---

## 🔑 Getting Telegram Notifications

1. **Create Bot**:
   - Open Telegram
   - Search @BotFather
   - Send `/newbot`
   - Follow prompts
   - Copy token

2. **Deploy with Token**:
   - Railway/Heroku/etc: Add env var `TELEGRAM_BOT_TOKEN=your_token`
   - Redeploy

3. **Add Bot to Chat**:
   - Search for your bot in Telegram
   - Send any message
   - Get chat ID from logs

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [FEATURES.md](FEATURES.md) | Detailed feature documentation & API examples |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Step-by-step deployment for all platforms |
| This README | Quick start & overview |

---

## 🏗️ Architecture

```
Frontend (HTML/CSS/JS)
        ↓
REST API (Flask)
        ↓
SQLite Database
        ↓
Background Tasks (Escalation, Notifications)
```

### Key Files
- `app.py` - Flask backend (900+ lines, well-organized)
- `static/js/app.js` - Frontend logic
- `templates/index.html` - UI
- `static/css/style.css` - Styling

---

## 🔐 Security Features

| Feature | Implementation |
|---------|-----------------|
| **Authentication** | API key (unique per user) |
| **Authorization** | Role-based (admin/member) |
| **Injection Protection** | Parameterized SQL queries |
| **Input Validation** | Regex validation, request sanitization |
| **Audit Logging** | Complete action history |
| **Token Management** | Secure approval tokens |

---

## 💡 Real-World Use Cases

### DevOps Team
- Gate production deployments with multi-admin approval
- Auto-accept dev/staging, require approval for prod
- Audit trail for compliance

### SRE Team
- Critical operations (kill process, restart service) require approvals
- Escalate if on-call engineer doesn't approve within 1 hour
- Track all operational changes

### Security Team
- High-risk commands require multiple approvals
- Different thresholds for different user levels
- Real-time notifications for all approvals

### Compliance
- HIPAA/SOC2 audit trail
- Who did what and when
- Automatic escalation tracking

---

## 📊 Database Schema

```sql
-- Users with roles and tiers
CREATE TABLE users (
  id, username, api_key, role, tier, credits, 
  email, telegram_chat_id, created_at
)

-- Rules with approval thresholds
CREATE TABLE rules (
  id, pattern, action, description, approval_threshold,
  time_start, time_end, timezone, created_at, created_by
)

-- Command execution history
CREATE TABLE commands (
  id, user_id, command_text, status, matched_rule_id,
  credits_deducted, approval_token, escalation_at, created_at
)

-- Multi-admin voting
CREATE TABLE approval_votes (
  id, command_id, approver_id, vote, created_at
)

-- Complete audit trail
CREATE TABLE audit_logs (
  id, user_id, action_type, details, created_at
)
```

---

## 🎮 Web UI Features

### Admin Dashboard
- **Users**: Create, update credits, delete users
- **Rules**: Create with conflict detection, time-based rules
- **Approvals**: Approve/reject pending commands with voting
- **Audit Logs**: View all system actions with timestamps
- **Commands**: View all user commands and their status

### Member Dashboard
- **Submit Commands**: Type and execute commands
- **History**: View command execution history
- **Credits**: See remaining credits

---

## 🔧 Configuration

### Environment Variables

```bash
# Telegram bot (optional)
TELEGRAM_BOT_TOKEN=123456789:ABCDefGhI...

# Deployment
FLASK_ENV=production

# Database (auto-created)
DATABASE=command_gateway.db

# Port (auto-detected)
PORT=5000
```

### Rule Examples

**Auto-Accept Safe Operations:**
```
Pattern: ^(ls|cat|pwd|echo|git status)
Action: AUTO_ACCEPT
```

**Require Approval for Risky Operations:**
```
Pattern: ^(rm|mkfs|fdisk|kill -9)
Action: REQUIRE_APPROVAL
Threshold: 2
```

**Business Hours Auto-Approve:**
```
Pattern: ^deploy
Time Start: 09:00
Time End: 17:00
Timezone: America/New_York
Action: AUTO_ACCEPT
```

---

## 📈 Performance & Scaling

| Metric | Value |
|--------|-------|
| **Concurrent Users** | 10+ (SQLite) |
| **Command/Second** | 100+ (depends on rule matching) |
| **Database** | SQLite (dev), PostgreSQL (prod) |
| **Deployment** | Single container, 512MB RAM |

### Scaling to Production
- Upgrade to PostgreSQL (from SQLite)
- Add Redis for caching
- Use proper WSGI server (gunicorn - already included)
- Add load balancer for multiple instances

---

## ✅ Monitoring & Debugging

### View Logs
```bash
# Railway
railway logs

# Heroku
heroku logs --tail

# Local
python app.py  # Logs in console
```

### Check Status
```bash
curl https://your-app.railway.app/api/health
# Response: {"status": "ok"}
```

### Debug Commands
```python
# In app.py, see DEBUG: lines
# Example: "DEBUG: User found: True"
```

---

## 🤝 Contributing

Want to add features? The codebase is clean and modular:

1. **Add API endpoint** → `app.py`
2. **Add UI element** → `templates/index.html` + `static/js/app.js`
3. **Add styling** → `static/css/style.css`
4. **Test locally** → `python app.py`
5. **Deploy** → `git push origin main` (Railway auto-deploys)

---

## 📞 Support & Troubleshooting

### "Module not found"
```bash
pip install -r requirements.txt
```

### "Database locked"
SQLite limitation. Upgrade to PostgreSQL for production.

### "Port already in use"
```bash
# Use different port
PORT=5001 python app.py
```

### Telegram notifications not working
- Check `TELEGRAM_BOT_TOKEN` is set
- Verify bot is in your chat
- Check deployment logs

---

## 🎓 Learning Resources

Built with standard Python/Flask tech:
- Flask docs: https://flask.palletsprojects.com
- SQLite docs: https://sqlite.org
- REST API concepts: https://restfulapi.net
- Regex patterns: https://regex101.com

---

## 📄 License

Built for Unbound Hackathon. Free to use, modify, and deploy.

---

## 🚀 Next Steps

1. **Read** [DEPLOYMENT.md](DEPLOYMENT.md) to deploy
2. **Test** all features with examples above  
3. **Configure** rules for your use case
4. **Invite** team members with API keys
5. **Monitor** audit logs for compliance

**Questions?** Check the code - it's well-commented and organized!

