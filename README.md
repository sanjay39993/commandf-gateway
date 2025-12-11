# Command Gateway

A secure command execution system with rule-based access control, credit management, and comprehensive audit logging. Built for the Unbound Hackathon.

## Features

### Core Functionality
- ✅ **API Key Authentication** - Simple API key-based authentication with role-based access control
- ✅ **User Management** - Admin and member roles with different permissions
- ✅ **Command Credits System** - Track and deduct credits on command execution
- ✅ **Rule-Based Command Control** - Regex pattern matching with AUTO_ACCEPT and AUTO_REJECT actions
- ✅ **Command Execution** - Mocked command execution with transaction support
- ✅ **Audit Trail** - Complete logging of all actions and command executions
- ✅ **Web Interface** - Modern, responsive web UI for both admins and members

### User Roles

**Members can:**
- View their command credits
- Submit commands for execution
- View command status (accepted, rejected, executed)
- View their command history

**Admins can do everything members can, plus:**
- Configure rules (define patterns and their actions)
- Manage users and their credits
- View audit logs
- Create new users with API keys

## Tech Stack

- **Backend:** Flask (Python)
- **Frontend:** HTML, CSS, JavaScript (Vanilla JS)
- **Database:** SQLite3
- **Authentication:** API Key-based

## Setup Instructions

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- (Optional) Telegram Bot Token for notifications (set `TELEGRAM_BOT_TOKEN` environment variable)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd cunbound
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Access the application:**
   - Open your browser and navigate to `http://localhost:5000`
   - The application will automatically create a default admin user on first run
   - **IMPORTANT:** Check the console output for the default admin API key - save it immediately!

## Usage Guide

### Getting Started

1. **First Time Setup:**
   - When you first run the application, a default admin user is created
   - The API key is printed to the console - **save this key!**
   - Use this API key to log in to the web interface

2. **Logging In:**
   - Enter your API key in the login form
   - Click "Login" to access the dashboard

3. **As a Member:**
   - View your credits balance
   - Submit commands in the "Commands" tab
   - View your command history in the "History" tab

4. **As an Admin:**
   - All member features, plus:
   - Manage rules in the "Rules" tab
   - Manage users and credits in the "Users" tab
   - View audit logs in the "Audit Logs" tab

### Default Rules

The system comes pre-configured with these starter rules:

| Pattern | Action | Description |
|---------|--------|-------------|
| `:(){ :|:& };:` | AUTO_REJECT | Fork bomb |
| `rm\s+-rf\s+/` | AUTO_REJECT | Dangerous rm command |
| `mkfs\.` | AUTO_REJECT | Filesystem formatting |
| `git\s+(status|log|diff)` | AUTO_ACCEPT | Safe git commands |
| `^(ls|cat|pwd|echo)` | AUTO_ACCEPT | Safe read commands |

### Creating Rules

1. Navigate to the "Rules" tab (admin only)
2. Click "Add New Rule"
3. Enter a regex pattern (e.g., `^ls|cat`)
4. Select an action (AUTO_ACCEPT or AUTO_REJECT)
5. Optionally add a description
6. Click "Create Rule"

**Note:** Invalid regex patterns will be rejected with an error message.

### Creating Users

1. Navigate to the "Users" tab (admin only)
2. Click "Add New User"
3. Enter username, role, and initial credits
4. Click "Create User"
5. **IMPORTANT:** Save the API key shown - this is the only time it will be displayed!

### Command Execution Flow

1. User submits a command
2. System checks if user has credits > 0
3. Command is matched against rules (first match wins)
4. Based on matched rule action:
   - **AUTO_ACCEPT:** Command is executed, credits deducted, status updated
   - **AUTO_REJECT:** Command is rejected, logged, no credits deducted
5. Result is returned to the user

### Credit System

- Each user starts with 100 credits (configurable)
- Commands cost 1 credit per execution
- Credits are only deducted on successful execution
- Commands are rejected if credits = 0
- Admins can update user credits at any time

## API Documentation

### Authentication

All API requests require an API key in the `X-API-Key` header:

```
X-API-Key: your-api-key-here
```

### Endpoints

#### Health Check
```
GET /api/health
```
Returns system status.

#### Get Current User
```
GET /api/auth/me
```
Returns information about the authenticated user.

#### Create User (Admin Only)
```
POST /api/users
Body: {
  "username": "string",
  "role": "admin" | "member",
  "credits": number
}
```

#### List Users (Admin Only)
```
GET /api/users
```

#### Update User Credits (Admin Only)
```
PUT /api/users/{user_id}/credits
Body: {
  "credits": number
}
```

#### List Rules
```
GET /api/rules
```

#### Create Rule (Admin Only)
```
POST /api/rules
Body: {
  "pattern": "regex pattern",
  "action": "AUTO_ACCEPT" | "AUTO_REJECT",
  "description": "string (optional)"
}
```

#### Delete Rule (Admin Only)
```
DELETE /api/rules/{rule_id}
```

#### Submit Command
```
POST /api/commands
Body: {
  "command_text": "string"
}
```

#### List Commands
```
GET /api/commands
```

#### Get Audit Logs (Admin Only)
```
GET /api/audit-logs
```

## Database Schema

### Users Table
- `id` - Primary key
- `username` - Unique username
- `api_key` - Unique API key for authentication
- `role` - 'admin' or 'member'
- `credits` - Current credit balance
- `created_at` - Timestamp

### Rules Table
- `id` - Primary key
- `pattern` - Regex pattern
- `action` - AUTO_ACCEPT, AUTO_REJECT, or REQUIRE_APPROVAL
- `description` - Optional description
- `created_by` - User ID who created the rule
- `created_at` - Timestamp

### Commands Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `command_text` - The command that was submitted
- `status` - pending, accepted, rejected, or executed
- `matched_rule_id` - Foreign key to rules
- `credits_deducted` - Credits deducted (if executed)
- `execution_output` - Mocked execution output
- `created_at` - Timestamp
- `executed_at` - Timestamp (if executed)

### Audit Logs Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `action_type` - Type of action (command_executed, command_rejected, rule_created, etc.)
- `details` - Additional details
- `created_at` - Timestamp

## Transaction Safety

All command execution operations are wrapped in database transactions to ensure atomicity:
- Credit deduction
- Command record creation
- Audit log entry

If any step fails, the entire transaction is rolled back, preventing inconsistent state.

## Security Features

- API key authentication
- Role-based access control
- Input validation (regex pattern validation)
- SQL injection protection (parameterized queries)
- XSS protection (HTML escaping in frontend)

## Testing

### Test Scenarios

1. **Member submits safe command:**
   - Submit `ls -la`
   - Should execute successfully
   - Credits should decrease by 1

2. **Member submits dangerous command:**
   - Submit `rm -rf /`
   - Should be rejected
   - Credits should remain unchanged

3. **Member with zero credits:**
   - Set credits to 0
   - Submit any command
   - Should be rejected immediately

4. **Admin creates rule:**
   - Create a new rule with pattern `^test`
   - Submit command `test123`
   - Should match and apply rule action

5. **Admin manages users:**
   - Create new user
   - Update user credits
   - Verify changes in audit logs

## Project Structure

```
cunbound/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .gitignore            # Git ignore file
├── templates/
│   └── index.html        # Main HTML template
└── static/
    ├── css/
    │   └── style.css     # Stylesheet
    └── js/
        └── app.js        # Frontend JavaScript
```

## Demo Video

[Link to demo video - to be added]

## Bonus Features Implemented ✅

All bonus features have been implemented:

### ✅ REQUIRE_APPROVAL
- Commands requiring approval create approval requests
- Admins receive notifications via Telegram/Email (if configured)
- Voting system tracks approvals/rejections
- Commands can be resubmitted with approval token once approved

### ✅ Rule Conflict Detection
- System detects overlapping regex patterns
- Warns admins when creating conflicting rules
- API endpoint: `POST /api/rules/check-conflict`

### ✅ Voting Thresholds
- Rules can specify approval thresholds (1-10 approvers)
- Different thresholds per rule
- Progress tracking shows approval status

### ✅ User-Tier Rules
- Users have tiers: junior, mid, senior, lead
- Different approval thresholds based on tier:
  - Junior: 3 approvals
  - Mid: 2 approvals
  - Senior/Lead: 1 approval
- Admins can update user tiers

### ✅ Escalation System
- Commands auto-escalate after 1 hour if not approved
- All admins notified on escalation
- Escalation time tracked in database

### ✅ Time-Based Rules
- Rules can have time windows (e.g., 09:00-17:00)
- Rules only apply during specified hours
- Supports timezone configuration
- Useful for business hours restrictions

### ✅ Notification System
- Telegram notifications (set `TELEGRAM_BOT_TOKEN` environment variable)
- Email notifications (placeholder - configure SMTP)
- Real-time approval requests

### Deployment Ready
- `Procfile` for Heroku/Railway deployment
- `runtime.txt` for Python version
- Environment variable support (`PORT`, `TELEGRAM_BOT_TOKEN`)

## License

This project was created for the Unbound Hackathon.

## Author

Built for Unbound Hackathon - December 2024

---

**Note:** This is a demonstration project. In production, consider additional security measures such as:
- Rate limiting
- API key rotation
- Encrypted API keys
- More robust error handling
- Production-grade database (PostgreSQL, MySQL)
- HTTPS enforcement

