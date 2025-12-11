# Email Notification Setup

The approval request notifications can be sent via email. Here's how to configure it:

## For Gmail Users (Recommended)

### Step 1: Create Gmail App Password
1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/app-passwords)
2. Select "Mail" and "Windows Computer"
3. Generate a new app-specific password (16 characters)
4. Copy the password

### Step 2: Set Environment Variables (Windows PowerShell)

```powershell
$env:SMTP_SERVER = "smtp.gmail.com"
$env:SMTP_PORT = "587"
$env:SMTP_EMAIL = "your-email@gmail.com"
$env:SMTP_PASSWORD = "your-app-password"
```

**Example:**
```powershell
$env:SMTP_SERVER = "smtp.gmail.com"
$env:SMTP_PORT = "587"
$env:SMTP_EMAIL = "my.command.gateway@gmail.com"
$env:SMTP_PASSWORD = "abcd efgh ijkl mnop"
```

### Step 3: Restart Server
```powershell
python app.py
```

### Step 4: Test Email Notifications
1. Login as admin
2. Create a REQUIRE_APPROVAL rule
3. Submit a command matching the rule
4. Check your email for the approval notification

---

## For Other Email Providers

### Outlook/Microsoft 365
```powershell
$env:SMTP_SERVER = "smtp.office365.com"
$env:SMTP_PORT = "587"
$env:SMTP_EMAIL = "your-email@outlook.com"
$env:SMTP_PASSWORD = "your-password"
```

### Yahoo Mail
```powershell
$env:SMTP_SERVER = "smtp.mail.yahoo.com"
$env:SMTP_PORT = "587"
$env:SMTP_EMAIL = "your-email@yahoo.com"
$env:SMTP_PASSWORD = "your-app-password"
```

### SendGrid (if using SendGrid API)
```powershell
$env:SMTP_SERVER = "smtp.sendgrid.net"
$env:SMTP_PORT = "587"
$env:SMTP_EMAIL = "apikey"
$env:SMTP_PASSWORD = "SG.your-sendgrid-api-key"
```

---

## Updating User Email Address

To receive approval notifications, users must have an email address set:

### Via Admin Panel
1. Login as admin
2. Go to "Users" tab
3. Edit user and add their email address
4. Save

### Via API
```bash
curl -X PUT http://127.0.0.1:5000/api/users/{user_id} \
  -H "X-API-Key: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

---

## Troubleshooting

### "SMTP not configured" message
- Check that all 4 environment variables are set correctly
- Verify no typos in SMTP server name
- For Gmail, ensure you're using an App Password, not your Google account password

### "Login failed" error
- Verify your SMTP_EMAIL and SMTP_PASSWORD are correct
- For Gmail, enable "Less secure app access" OR use App Passwords (recommended)
- For Office 365, ensure 2FA is enabled and you're using App Password

### "Connection timeout"
- Check your firewall settings
- Verify SMTP port (usually 587 for TLS or 465 for SSL)
- Try a different SMTP server

### Emails not being received
- Check spam/junk folder
- Verify the email address in user profile is correct
- Check server logs for error messages

---

## Permanent Setup (Optional)

To make environment variables persistent on Windows:

### Method 1: System Environment Variables
1. Right-click "This PC" → Properties
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Click "New" under System variables
5. Add:
   - Variable name: `SMTP_SERVER`
   - Variable value: `smtp.gmail.com`
6. Repeat for SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD
7. Restart computer for changes to take effect

### Method 2: .env File
1. Create a file named `.env` in the project directory
2. Add:
   ```
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_EMAIL=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```

---

## Testing Email Configuration

Run this Python script to test:

```python
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

smtp_server = os.environ.get('SMTP_SERVER')
smtp_port = int(os.environ.get('SMTP_PORT', 587))
sender_email = os.environ.get('SMTP_EMAIL')
sender_password = os.environ.get('SMTP_PASSWORD')

print(f"Testing SMTP Configuration:")
print(f"  Server: {smtp_server}")
print(f"  Port: {smtp_port}")
print(f"  Email: {sender_email}")

try:
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
    print("✅ SMTP connection successful!")
except Exception as e:
    print(f"❌ SMTP connection failed: {e}")
```

---

## Full REQUIRE_APPROVAL + Email Workflow

1. **Admin creates a rule:**
   - Pattern: `sudo\s+`
   - Action: REQUIRE_APPROVAL
   - Threshold: 2

2. **User submits a command:**
   - Command: `sudo apt update`
   - System checks rule → matches REQUIRE_APPROVAL
   - Command status set to "pending"
   - Approval token generated

3. **Admins notified:**
   - Telegram message sent (if TELEGRAM_BOT_TOKEN set)
   - Email sent to admin's email address

4. **Admins review in web UI:**
   - Admin logs in
   - Goes to "Pending Approvals" tab
   - Sees: "sudo apt update" (requires 2 approvals)

5. **Admins vote:**
   - Admin 1 clicks "Approve" → 1/2 votes
   - Admin 2 clicks "Approve" → 2/2 votes (APPROVED!)

6. **User executes:**
   - User resubmits with approval token
   - System finds token is valid
   - Command executes immediately

---

## FAQ

**Q: Can I use both Telegram and Email?**
A: Yes! Set both TELEGRAM_BOT_TOKEN and SMTP variables. Admins with telegram_chat_id and/or email will be notified.

**Q: What if an admin doesn't have an email?**
A: They won't receive email notifications but will still see pending commands in the web UI.

**Q: How long are email credentials stored?**
A: Only in memory during server runtime. They're not saved to database.

**Q: Is it secure to set passwords in environment variables?**
A: In development it's fine. For production, use Docker secrets or Kubernetes secrets.

**Q: Can I customize the email template?**
A: Yes! Edit the `notify_approvers()` function in app.py to customize the message format.
