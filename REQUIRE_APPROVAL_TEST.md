# REQUIRE_APPROVAL - Complete Testing Guide

## How It Works

When a command matches a **REQUIRE_APPROVAL** rule:
1. Command is NOT executed immediately
2. Command enters "pending" state
3. Admins are notified (Telegram/Email)
4. Admins vote to approve/reject
5. When threshold is reached, command is marked "approved"
6. User must resubmit with approval token to execute it

---

## Current REQUIRE_APPROVAL Rules

```
Rule 8: Pattern: sudo\s+
        Description: Sudo commands require admin approval
        Threshold: 2 approvals needed

Rule 9: Pattern: (dd|fdisk|parted)\s+
        Description: Dangerous disk operations require approval
        Threshold: 2 approvals needed
```

---

## Step-by-Step Testing

### Prerequisites
- At least 2 admin users (or more members with admin role)
- Server running at http://127.0.0.1:5000

### Step 1: Verify Your Users
```bash
Admin Dashboard → Users Tab
You should see:
  - admin (admin role)
  - sanjay (member)
  - kavin (member)
```

### Step 2: Log In as a Member
1. Click "Logout" (or new tab)
2. Click "Login"
3. Enter sanjay's API key: `RF-5MmKG_xp9kOQbyiOqiprE-9-tbM88G1J035-4xio`
4. Switch to "Member" tab

### Step 3: Submit a Command Matching REQUIRE_APPROVAL Rule
```
Command Input: sudo apt update
Click: Submit
```

**Expected Result:**
- Status: "Pending Approval"
- Message: "Requires 2 approval(s)"
- Command ID: (shown)
- Approval Token: (shown - copy this!)

### Step 4: Check Pending Approvals (As Admin)
1. Logout or open new tab
2. Login with admin API key: `gF6x4lU8W6FErUNBf_GB15HLSg47UcDUGKSMQIs441o`
3. Switch to "Admin" tab
4. Click "Pending Approvals"

**Expected Result:**
- See your "sudo apt update" command
- Progress bar showing: 0/2 (0 approvals, 2 needed)
- Two buttons: "Approve" and "Reject"

### Step 5: First Admin Approves
1. Click "Approve" button
2. Progress updates to: 1/2

**Expected Result:**
- Vote recorded
- Status still "pending" (need 1 more)
- Message: "Vote recorded"

### Step 6: Second Admin Approves
1. Create another admin user:
   - Admin Dashboard → Users → Create User
   - Username: `approver2`
   - Role: `admin`
   - Copy the API key
2. Login as approver2
3. Go to Pending Approvals
4. Click "Approve" on the same command

**Expected Result:**
- Progress updates to: 2/2
- Command status changes to "approved"
- Message: "Command approved. Threshold met. User can now execute."
- Approval token displayed

### Step 7: User Resubmits with Approval Token
1. Go back to member user (sanjay)
2. Switch to "Member" tab
3. Paste the approval token in the "Approval Token" field
4. Type the command again: `sudo apt update`
5. Click "Submit"

**Expected Result:**
- Status: "Executed"
- Output: "[MOCKED] Executed: sudo apt update"
- Command ID: (same as original)
- Credits deducted: 1
- New balance: (updated)

---

## Testing Rejection

### Test Rejecting a Command

**Step 1: Submit another REQUIRE_APPROVAL command**
```
Command: sudo reboot
```

**Step 2: Admin rejects it**
1. Go to Pending Approvals
2. Click "Reject"

**Expected Result:**
- Status changes to "rejected"
- Command cannot be executed
- User sees rejection in command history

---

## Testing Notifications (Optional)

### Enable Telegram Notifications

**Step 1: Get Telegram Bot Token**
1. Open Telegram
2. Search for `@BotFather`
3. Send: `/newbot`
4. Follow prompts to create a bot
5. Copy the token (format: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

**Step 2: Get Your Chat ID**
1. Search for `@userinfobot` or use `https://api.telegram.org/bot<TOKEN>/getMe`
2. Send: `/start`
3. Get your numeric chat ID

**Step 3: Update User with Chat ID**
```bash
Admin Dashboard → Users → Admin User
Add Telegram Chat ID: <your_chat_id>
```

**Step 4: Set Environment Variable**
```bash
# On Windows (PowerShell):
$env:TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# Then restart server:
python app.py
```

**Step 5: Submit Command and Wait for Telegram Notification**
- You should receive a Telegram message when approval is needed

---

## Audit Log Verification

1. Admin Dashboard → Audit Logs
2. Look for these actions:
   - `command_pending_approval` - When command submitted
   - `command_approved` - When threshold reached
   - `command_executed` - When resubmitted with token
   - `command_rejected` - When rejected

---

## Testing Different Thresholds

### Create Custom REQUIRE_APPROVAL Rules

**Rule with Threshold 1 (Only 1 approval needed):**
```
Pattern: deploy_
Action: REQUIRE_APPROVAL
Threshold: 1
```

**Rule with Threshold 3 (3 approvals needed):**
```
Pattern: critical_
Action: REQUIRE_APPROVAL
Threshold: 3
```

**Testing:**
1. Submit `deploy_production`
   - Only needs 1 approval
   - First admin approve = immediately approved
   
2. Submit `critical_system_change`
   - Needs 3 approvals
   - First admin approve = still pending
   - Second admin approve = still pending
   - Third admin approve = approved and ready

---

## Testing User-Tier Based Thresholds

When no rule threshold is set, approval requirement is based on user tier:

| Tier | Approvals Needed |
|------|------------------|
| junior | 3 |
| mid | 2 |
| senior | 1 |
| lead | 1 |

**Create a rule without approval_threshold:**
```
Pattern: deploy_
Action: REQUIRE_APPROVAL
Approval Threshold: (leave empty or use default)
```

**Test:**
1. Submit command as junior user → needs 3 approvals
2. Submit command as senior user → needs 1 approval

---

## Complete Flow Summary

```
Member submits "sudo apt update"
         ↓
Server matches Rule 8 (REQUIRE_APPROVAL, threshold: 2)
         ↓
Command status = "pending"
User gets: command_id, approval_token
         ↓
Admins notified (Telegram/Email)
         ↓
Admin 1 votes APPROVE (1/2 votes)
Command still PENDING
         ↓
Admin 2 votes APPROVE (2/2 votes)
Command status = "approved"
Admins notified of approval
         ↓
User resubmits with approval_token
Command status = "executed"
Credits deducted
User gets execution output
         ↓
Audit log updated
```

---

## Troubleshooting

**Q: Command not going pending?**
- Check the pattern matches your command
- Test regex on https://regex101.com

**Q: Pending command not showing in Pending Approvals?**
- Make sure you're logged in as admin
- Refresh the page

**Q: Command executed without approval?**
- Check if rule is AUTO_ACCEPT instead of REQUIRE_APPROVAL
- Verify pattern matches the command

**Q: Approval token not working?**
- Make sure you're copying the correct token from response
- Token must be from an "approved" command (2/2 votes met)
- Resubmit within the time window (30 minutes)

---

## Code Locations

Key functions for REQUIRE_APPROVAL:

- **Command submission logic**: `app.py` lines 713-833
- **Approval checking**: `app.py` lines 364-407
- **Threshold calculation**: `app.py` lines 247-254
- **Notification system**: `app.py` lines 271-307
- **Escalation**: `app.py` lines 408-465
- **Pending commands endpoint**: `app.py` lines 908-926
- **Approval/Rejection endpoints**: `app.py` lines 928-1058

---

## Full Feature Checklist

- [x] Commands marked "pending" when matching REQUIRE_APPROVAL rule
- [x] Approval threshold per rule (2 in our rules)
- [x] User-tier based thresholds (junior=3, mid=2, senior=1, lead=1)
- [x] Multi-admin voting system
- [x] Approval status tracking (1/2, 2/2, etc)
- [x] Token-based re-execution
- [x] Audit logging of all actions
- [x] Telegram notifications (ready, needs config)
- [x] Email notifications (ready, needs SMTP config)
- [x] Escalation after 30 minutes (auto-notifies all admins)
- [x] Rejection with majority vote

✅ **REQUIRE_APPROVAL is fully implemented and ready to test!**
