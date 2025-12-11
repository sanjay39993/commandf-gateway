# 🧪 Testing All Bonus Features - Complete Guide

## Quick Test Server Check

First, verify your server is running:
```bash
# Terminal check (should see Flask running)
python app.py

# Browser check
http://127.0.0.1:5000
```

**Login with admin API key:**
- Go to login tab
- Paste: `gF6x4lU8W6FErUNBf_GB15HLSg47UcDUGKSMQIs441o`

---

## 1️⃣ REQUIRE_APPROVAL - Test Command Approval Workflow

### What It Does
Commands matching rules with `action: REQUIRE_APPROVAL` don't execute immediately. Instead, they become pending and need admin approval.

### Testing Steps

**Step 1: Create REQUIRE_APPROVAL Rule**
```
Admin Dashboard → Rules tab → Create Rule:
- Pattern: deploy_.*
- Action: REQUIRE_APPROVAL ← Select this
- Approval Threshold: 2
- Description: Deploy commands need 2 admins approval
```

**Step 2: Submit Command That Matches Rule**
```
Member tab → Command input:
- Type: deploy_production
- Click Submit
```

**Expected Result:**
- ❌ Command NOT executed immediately
- ✅ Shows "Pending Approval" status
- ✅ Pending tab shows the command waiting

**Step 3: Approve Command (2 Admins)**
```
Admin Dashboard → Pending Approvals tab:
- See "deploy_production" waiting
- Click "Approve" button (counts your vote)
```

Repeat with 2nd admin account:
```
Create 2nd admin user:
- Admin Dashboard → Users → Create User
- Make it admin role
- Login with its API key
- Go to Pending Approvals
- Approve the same command
```

**Expected Result:**
- ✅ Progress bar shows 2/2 approvals
- ✅ Command auto-executes
- ✅ Status changes to "Executed"

**Code Location to Verify:**
- Lines 631-832 in `app.py` - `submit_command()` endpoint
- Search for: `approval_threshold > 0`

---

## 2️⃣ Rule Conflict Detection - Test Overlapping Patterns

### What It Does
Prevents admins from creating rules with patterns that would conflict (match same commands).

### Testing Steps

**Step 1: Create First Rule**
```
Admin Dashboard → Rules → Create Rule:
- Pattern: restart_.*
- Action: AUTO_ACCEPT
- Description: Auto-accept restart commands
```

**Step 2: Try Creating Conflicting Rule**
```
Admin Dashboard → Rules → Create Rule:
- Pattern: restart_web    ← Overlaps with restart_.*
- Action: REQUIRE_APPROVAL
- Description: This should be blocked!
```

**Expected Result:**
- ❌ Form shows error: "Rule conflicts with existing rule"
- ✅ Rule NOT created

### How It Works
The system tests if the new pattern would match any test commands that the existing pattern matches.

**Code Location:**
- Lines 184-220 in `app.py` - `check_rule_conflict()` function
- Lines 1052-1067 in `app.py` - Conflict detection endpoint

**Verify in Code:**
```bash
Open app.py → Find "check_rule_conflict" → See the test logic
```

---

## 3️⃣ Voting Thresholds - Test Approval Count Requirements

### What It Does
Rules can require different numbers of admin approvals (e.g., "threshold: 2" means 2 admins must approve).

### Testing Steps

**Step 1: Create Rule with Threshold**
```
Admin Dashboard → Rules → Create Rule:
- Pattern: delete_database
- Action: REQUIRE_APPROVAL
- Approval Threshold: 3 ← Needs 3 admins
```

**Step 2: Submit Command**
```
Member tab:
- Type: delete_database
- Submit
```

**Step 3: Check Pending Approvals Display**
```
Admin Dashboard → Pending Approvals:
- Shows: "3 needed for approval"
- Progress bar: 0/3
```

**Step 4: Approvals Progression**
```
Admin 1: Click "Approve" → Shows 1/3
Admin 2: Click "Approve" → Shows 2/3
Admin 3: Click "Approve" → Shows 3/3 → Command executes
```

**Expected Result:**
- ✅ Progress bar updates after each vote
- ✅ Only executes after reaching threshold (3/3)
- ✅ If 2nd admin rejects, command stays pending

**Code Location:**
- Lines 309-342 in `app.py` - `check_approval_status()` function
- Lines 863-878 in `app.py` - `get_pending_commands()` returns threshold

---

## 4️⃣ User-Tier Rules - Test Role-Based Thresholds

### What It Does
Different user tiers require different approval counts:
- **Junior**: 3 approvals needed
- **Mid**: 2 approvals needed  
- **Senior**: 1 approval needed
- **Lead**: 1 approval needed

### Testing Steps

**Step 1: Create 3 Users with Different Tiers**
```
Admin Dashboard → Users → Create User:
1. username: junior_user,    tier: junior
2. username: mid_user,       tier: mid
3. username: senior_user,    tier: senior
```

**Step 2: Create Tier-Aware Rule**
```
Admin Dashboard → Rules → Create Rule:
- Pattern: config_change
- Action: REQUIRE_APPROVAL
- Description: Uses user tier thresholds
```

**Step 3: Submit from Junior User**
```
Login as junior_user API key
Member tab → Type: config_change → Submit
Admin Dashboard → Pending Approvals
- Shows: "3 needed for approval" ← Because junior
```

**Step 4: Submit from Senior User**
```
Login as senior_user API key
Member tab → Type: config_change → Submit
Admin Dashboard → Pending Approvals
- Shows: "1 needed for approval" ← Because senior
```

**Expected Result:**
- ✅ Junior commands need 3 approvals
- ✅ Mid commands need 2 approvals
- ✅ Senior/Lead commands need 1 approval

**Code Location:**
- Lines 247-254 in `app.py` - `get_user_tier_threshold()` function
- Maps tiers to approval counts

**Verify in Database:**
```sql
-- Check user tiers
SELECT username, tier FROM users;
```

---

## 5️⃣ Escalation - Test Auto-Escalation After Timeout

### What It Does
If a command is pending approval for too long (30 minutes default), it automatically escalates to ALL admins.

### Testing Steps

**Step 1: Create Escalation-Enabled Rule**
```
Admin Dashboard → Rules → Create Rule:
- Pattern: critical_alert
- Action: REQUIRE_APPROVAL
- Approval Threshold: 1
```

**Step 2: Submit Command**
```
Member tab → Type: critical_alert → Submit
```

**Step 3: Check Escalation Logic (without waiting 30 min)**
```
Method A - Read the code:
Open app.py → Lines 353-385 → escalate_command() function
Shows logic: if created_at < now - 30min, notify all admins

Method B - Check database:
Admin Dashboard → Audit Logs
- See "escalation_notified" entries after 30 min window

Method C - Test in code directly:
Terminal:
python -c "
from app import db, escalate_command, get_db
conn = get_db()
# Check pending commands older than 25 minutes for testing
commands = conn.execute('''
  SELECT id, created_at FROM commands 
  WHERE status = \"pending\"
''').fetchall()
for cmd in commands:
    print(f'Command {cmd[0]} created: {cmd[1]}')
"
```

**Expected Result:**
- ✅ Escalation logic runs every 5 minutes (background thread)
- ✅ Commands pending > 30 min get escalated
- ✅ All admins get notified

**Code Location:**
- Lines 353-385 in `app.py` - `escalate_command()` function
- Lines 1070-1091 in `app.py` - `check_escalations()` background task
- Runs in daemon thread (line 1098)

**Verify Background Task Running:**
```bash
Terminal during server startup:
- See log: "Started escalation checker daemon"
- Every 5 min: "Checking for escalations..."
```

---

## 6️⃣ Time-Based Rules - Test Timezone-Aware Time Windows

### What It Does
Rules can have time windows (e.g., auto-accept during business hours 9-5, require approval after hours).

### Testing Steps

**Step 1: Create Time-Based Rule (Business Hours)**
```
Admin Dashboard → Rules → Create Rule:
- Pattern: deploy
- Action: AUTO_ACCEPT
- Enable Time Window: ✓
- Start Time: 09:00
- End Time: 17:00
- Timezone: America/New_York
- Description: Auto-accept deploys during business hours
```

**Step 2: Test During Business Hours (9 AM - 5 PM)**
```
Member tab → Type: deploy → Submit
- Expected: ✅ Executes immediately (AUTO_ACCEPT during business hours)
- Shows: "Executed"
```

**Step 3: Test Outside Business Hours (After 5 PM)**
```
System Time: 6:00 PM New York time
Member tab → Type: deploy → Submit
- Expected: ❌ Not auto-accepted
- Shows: "Pending Approval" (requires manual approval)
```

### Test Without Changing System Time

**Check Rule Evaluation Logic:**
```
Open app.py → Lines 224-245 → evaluate_time_based_rule()
Shows: 
- Converts current time to rule's timezone
- Checks if current_time is between time_start and time_end
- Returns True if within window
```

**Create Test Rule for Current Time:**
```
If current time is 3:30 PM:
- Create rule with Start: 15:00 (3 PM), End: 16:00 (4 PM)
- Test should auto-accept
```

**Expected Result:**
- ✅ Commands during time window use action (AUTO_ACCEPT)
- ✅ Commands outside window require approval
- ✅ Timezone conversion works correctly

**Code Location:**
- Lines 224-245 in `app.py` - `evaluate_time_based_rule()` function
- Uses `pytz` library for timezone support

**Verify Timezone Support:**
```bash
Terminal:
python -c "
import pytz
tz = pytz.timezone('America/New_York')
from datetime import datetime
now = datetime.now(tz)
print(f'Current time in NY: {now}')
"
```

---

## 7️⃣ Notifications - Test Telegram/Email Alerts

### What It Does
Admins receive real-time notifications when:
- Approval requests created
- Command escalated
- Commands approved/rejected

### Testing Steps

**Step 1: Check Email Function (Code Review)**
```
Open app.py → Lines 256-272
- send_email_notification() function exists
- Ready for SMTP configuration
- Currently supports basic SMTP
```

**Step 2: Set Up Telegram Notifications (Optional)**
```
Terminal:
1. Get TELEGRAM_BOT_TOKEN from @BotFather on Telegram
2. Get your chat ID
3. Set environment variable:
   $env:TELEGRAM_BOT_TOKEN = "your_token_here"
4. Restart server: python app.py
```

**Step 3: Create REQUIRE_APPROVAL Command**
```
Member tab → Submit command matching REQUIRE_APPROVAL rule
- Expected: Telegram message to all admins
- Shows: "New approval request: [command]"
```

**Step 4: Verify Notification Calls**
```
Open app.py → Line 796
- See: notify_approvers(command_id) called
- Goes to background thread
- Calls send_telegram_notification() for each admin

Check server logs during command submission:
- See: "Sending notification to admin..."
```

**Expected Result:**
- ✅ Telegram notifications sent (if token configured)
- ✅ Email functions available (awaiting SMTP config)
- ✅ Notifications include command details

**Code Location:**
- Lines 256-272 in `app.py` - `send_telegram_notification()` and `send_email_notification()`
- Lines 274-307 in `app.py` - `notify_approvers()` background task
- Line 796 in `app.py` - Notification triggered on REQUIRE_APPROVAL

**Enable Email Notifications:**
```python
# In app.py around line 265, configure SMTP:
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "your_email@gmail.com"
SMTP_PASSWORD = "your_app_password"
```

---

## 🎯 Complete Test Checklist

Use this checklist to verify all 7 features:

### Feature Verification Checklist

- [ ] **REQUIRE_APPROVAL**
  - [ ] Rule created with REQUIRE_APPROVAL action
  - [ ] Command matching rule shows "Pending"
  - [ ] First admin approval shows progress 1/X
  - [ ] Reaching threshold executes command
  - [ ] Rejecting blocks execution

- [ ] **Rule Conflict Detection**
  - [ ] Create rule with pattern `test_.*`
  - [ ] Try creating `test_sub` (should be blocked)
  - [ ] Error message shows conflict detected
  - [ ] First rule still exists

- [ ] **Voting Thresholds**
  - [ ] Rule with threshold 2 shows "2 needed"
  - [ ] Progress bar at 0/2 initially
  - [ ] After 1 vote: shows 1/2
  - [ ] After 2 votes: auto-executes

- [ ] **User-Tier Rules**
  - [ ] Create junior, mid, senior users
  - [ ] Junior command needs 3 approvals
  - [ ] Senior command needs 1 approval
  - [ ] Thresholds vary by user tier

- [ ] **Escalation**
  - [ ] Command pending > 30 minutes
  - [ ] Check audit logs for escalation
  - [ ] All admins notified
  - [ ] Background task running (see logs)

- [ ] **Time-Based Rules**
  - [ ] Create rule with time window
  - [ ] During window: auto-accepts
  - [ ] Outside window: requires approval
  - [ ] Timezone conversion works

- [ ] **Notifications**
  - [ ] Telegram notifications sent (if configured)
  - [ ] Email function exists and ready
  - [ ] Logs show notification calls
  - [ ] Each approval notifies admins

---

## 🔍 Debugging Tips

### Check Server Logs
```bash
# Terminal where server is running
# Look for:
# - "Starting escalation checker" ✅
# - "Processing command" (with command details)
# - Errors in red if something fails
```

### Check Database State
```bash
# Verify data directly
python -c "
from app import get_db
conn = get_db()

# Check rules
rules = conn.execute('SELECT id, pattern, action FROM rules').fetchall()
print('Rules:', rules)

# Check pending commands
pending = conn.execute('SELECT id, status FROM commands WHERE status = \"pending\"').fetchall()
print('Pending commands:', pending)

# Check votes
votes = conn.execute('SELECT command_id, COUNT(*) as votes FROM approval_votes GROUP BY command_id').fetchall()
print('Approval votes:', votes)
"
```

### Check Audit Logs
```
Admin Dashboard → Audit Logs tab
- See all actions with timestamps
- Look for: command_submitted, command_approved, escalation_notified
```

### Test API Directly
```bash
# Get pending commands with approval info
curl -X GET http://127.0.0.1:5000/api/commands/pending \
  -H "X-API-Key: gF6x4lU8W6FErUNBf_GB15HLSg47UcDUGKSMQIs441o"

# Result shows approval_threshold and approval_count for each
```

---

## 📊 Expected Outputs

### When Testing REQUIRE_APPROVAL
```
API Response:
{
  "status": "pending",
  "message": "Command submitted for approval",
  "approval_token": "abc123...",
  "approval_threshold": 2,
  "approval_count": 0
}
```

### When Checking Pending Commands
```
API Response:
[
  {
    "id": 1,
    "command_text": "deploy_prod",
    "status": "pending",
    "approval_threshold": 2,
    "approval_count": 1,
    "created_by": "user123"
  }
]
```

### In Audit Logs
```
"command_submitted" - Command entered system
"command_approved" - Admin voted approve
"command_rejected" - Admin voted reject
"escalation_notified" - Escalation triggered
"command_executed" - Final execution
```

---

## 🚀 Advanced Testing (For Developers)

### Run Unit Tests
```bash
python -m pytest test_api.py -v
python -m pytest test_health.py -v
```

### Check Code Coverage
```bash
# See which functions are tested
python -m pytest --cov=app test_api.py
```

### Load Test (Simulate Multiple Commands)
```bash
# Test with 10 concurrent commands
for i in {1..10}; do
  curl -X POST http://127.0.0.1:5000/api/commands \
    -H "X-API-Key: API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"command": "deploy_test_'$i'"}'
done
```

### Monitor Performance
```bash
# Watch database size
python -c "
import os
db_size = os.path.getsize('command_gateway.db') / 1024 / 1024
print(f'Database size: {db_size:.2f} MB')
"

# Count records
python -c "
from app import get_db
conn = get_db()
commands = conn.execute('SELECT COUNT(*) FROM commands').fetchone()[0]
print(f'Total commands: {commands}')
"
```

---

## ✅ All Tests Passing?

If all checks pass:
- ✅ All 7 bonus features working
- ✅ Ready for production deployment
- ✅ Can deploy using [DEPLOYMENT.md](DEPLOYMENT.md)

**Next Step:** See [DEPLOYMENT.md](DEPLOYMENT.md) to deploy to Railway.app (2 minutes)
