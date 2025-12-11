from flask import Flask, request, jsonify, render_template
import sqlite3
import re
import secrets
import hashlib
from datetime import datetime, time as dt_time
from functools import wraps
import os
import requests
import pytz
from threading import Thread

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)

DATABASE = 'command_gateway.db'

# Database initialization
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  api_key TEXT UNIQUE NOT NULL,
                  role TEXT NOT NULL CHECK(role IN ('admin', 'member')),
                  tier TEXT DEFAULT 'junior' CHECK(tier IN ('junior', 'mid', 'senior', 'lead')),
                  credits INTEGER DEFAULT 100,
                  email TEXT,
                  telegram_chat_id TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Rules table
    c.execute('''CREATE TABLE IF NOT EXISTS rules
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  pattern TEXT NOT NULL,
                  action TEXT NOT NULL CHECK(action IN ('AUTO_ACCEPT', 'AUTO_REJECT', 'REQUIRE_APPROVAL')),
                  description TEXT,
                  approval_threshold INTEGER DEFAULT 1,
                  time_start TEXT,
                  time_end TEXT,
                  timezone TEXT DEFAULT 'UTC',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  created_by INTEGER,
                  FOREIGN KEY(created_by) REFERENCES users(id))''')
    
    # Commands table
    c.execute('''CREATE TABLE IF NOT EXISTS commands
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  command_text TEXT NOT NULL,
                  status TEXT NOT NULL CHECK(status IN ('pending', 'accepted', 'rejected', 'executed', 'approved')),
                  matched_rule_id INTEGER,
                  credits_deducted INTEGER DEFAULT 0,
                  execution_output TEXT,
                  approval_token TEXT,
                  escalation_at TIMESTAMP,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  executed_at TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id),
                  FOREIGN KEY(matched_rule_id) REFERENCES rules(id))''')
    
    # Approval votes table
    c.execute('''CREATE TABLE IF NOT EXISTS approval_votes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  command_id INTEGER NOT NULL,
                  approver_id INTEGER NOT NULL,
                  vote TEXT NOT NULL CHECK(vote IN ('approve', 'reject')),
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(command_id) REFERENCES commands(id),
                  FOREIGN KEY(approver_id) REFERENCES users(id),
                  UNIQUE(command_id, approver_id))''')
    
    # Audit log table
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  action_type TEXT NOT NULL,
                  details TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

# Database helper functions
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query, params=(), fetch_one=False, fetch_all=False):
    conn = get_db()
    c = conn.cursor()
    c.execute(query, params)
    if fetch_one:
        result = c.fetchone()
    elif fetch_all:
        result = c.fetchall()
    else:
        result = None
    conn.commit()
    conn.close()
    return result

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.json.get('api_key') if request.is_json else None
        
        print(f"DEBUG: Headers: {dict(request.headers)}")
        print(f"DEBUG: API Key from headers: {api_key}")
        print(f"DEBUG: Request is JSON: {request.is_json}")
        
        if not api_key:
            print("DEBUG: No API key found")
            return jsonify({'error': 'API key required'}), 401
        
        user = execute_query(
            'SELECT * FROM users WHERE api_key = ?',
            (api_key,),
            fetch_one=True
        )
        
        print(f"DEBUG: User found: {user is not None}")
        
        if not user:
            return jsonify({'error': 'Invalid API key'}), 401
        
        request.current_user = dict(user)
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    @wraps(f)
    @require_auth
    def decorated_function(*args, **kwargs):
        if request.current_user['role'] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Generate API key
def generate_api_key():
    return secrets.token_urlsafe(32)

# Seed data
def seed_data():
    conn = get_db()
    c = conn.cursor()
    
    # Check if admin exists
    admin = c.execute('SELECT * FROM users WHERE role = ?', ('admin',)).fetchone()
    if not admin:
        api_key = generate_api_key()
        c.execute('INSERT INTO users (username, api_key, role, credits) VALUES (?, ?, ?, ?)',
                  ('admin', api_key, 'admin', 1000))
        print(f"Default admin created with API key: {api_key}")
        print("SAVE THIS API KEY - you'll need it to access the admin panel!")
    
    # Check if rules exist
    rule_count = c.execute('SELECT COUNT(*) FROM rules').fetchone()[0]
    if rule_count == 0:
        starter_rules = [
            (':\\(\\)\\{ :\\|:& \\};:', 'AUTO_REJECT', 'Fork bomb'),
            ('rm\\s+-rf\\s+/', 'AUTO_REJECT', 'Dangerous rm command'),
            ('mkfs\\.', 'AUTO_REJECT', 'Filesystem formatting'),
            ('git\\s+(status|log|diff)', 'AUTO_ACCEPT', 'Safe git commands'),
            ('^(ls|cat|pwd|echo)', 'AUTO_ACCEPT', 'Safe read commands'),
        ]
        admin_id = c.execute('SELECT id FROM users WHERE role = ?', ('admin',)).fetchone()[0]
        for pattern, action, desc in starter_rules:
            c.execute('INSERT INTO rules (pattern, action, description, created_by) VALUES (?, ?, ?, ?)',
                      (pattern, action, desc, admin_id))
    
    conn.commit()
    conn.close()

# Helper Functions for Bonus Features

def check_rule_conflict(new_pattern, exclude_id=None):
    """Check if a new rule pattern conflicts with existing rules"""
    rules = execute_query('SELECT id, pattern FROM rules', fetch_all=True)
    conflicts = []
    
    for rule in rules:
        if exclude_id and rule['id'] == exclude_id:
            continue
        
        try:
            # Try to match patterns against each other
            pattern1 = re.compile(new_pattern)
            pattern2 = re.compile(rule['pattern'])
            
            # Check if patterns overlap by testing common command patterns
            test_commands = [
                'ls -la',
                'rm -rf /',
                'git status',
                'cat file.txt',
                'echo hello',
                'mkfs.ext4 /dev/sda',
                ':(){ :|:& };:'
            ]
            
            for cmd in test_commands:
                match1 = bool(pattern1.search(cmd))
                match2 = bool(pattern2.search(cmd))
                if match1 and match2:
                    conflicts.append({
                        'rule_id': rule['id'],
                        'pattern': rule['pattern'],
                        'conflict_command': cmd
                    })
                    break
        except re.error:
            continue
    
    return conflicts

def evaluate_time_based_rule(rule):
    """Evaluate if a time-based rule should apply based on current time"""
    # Convert sqlite3.Row to dict if needed
    rule_dict = dict(rule) if hasattr(rule, 'keys') else rule
    
    if not rule_dict.get('time_start') or not rule_dict.get('time_end'):
        return True  # No time restriction, always applies
    
    try:
        tz = pytz.timezone(rule_dict.get('timezone', 'UTC'))
        now = datetime.now(tz)
        current_time = now.time()
        
        time_start = datetime.strptime(rule_dict['time_start'], '%H:%M').time()
        time_end = datetime.strptime(rule_dict['time_end'], '%H:%M').time()
        
        if time_start <= time_end:
            # Same day window
            return time_start <= current_time <= time_end
        else:
            # Overnight window
            return current_time >= time_start or current_time <= time_end
    except:
        return True  # Default to applying if time parsing fails

def get_user_tier_threshold(user_tier):
    """Get approval threshold based on user tier"""
    thresholds = {
        'junior': 3,
        'mid': 2,
        'senior': 1,
        'lead': 1
    }
    return thresholds.get(user_tier, 2)

def send_telegram_notification(chat_id, message, bot_token=None):
    """Send Telegram notification"""
    if not bot_token or not chat_id:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=data, timeout=5)
        return response.status_code == 200
    except:
        return False

def send_email_notification(email, subject, message, smtp_config=None):
    """Send email notification using SMTP"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Get SMTP configuration from environment variables
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        sender_email = os.environ.get('SMTP_EMAIL')
        sender_password = os.environ.get('SMTP_PASSWORD')
        
        if not sender_email or not sender_password:
            print(f"[EMAIL] SMTP not configured. Message for {email}: {subject}")
            print(f"[EMAIL] To enable email, set SMTP_SERVER, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD environment variables")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = email
        
        # Convert HTML message to plain text and HTML parts
        html_message = message.replace('\n', '<br>')
        text_part = MIMEText(message, 'plain')
        html_part = MIMEText(html_message, 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print(f"[EMAIL] Successfully sent to {email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send to {email}: {str(e)}")
        return False

def notify_approvers(command_id, command_text, user_name, approvers_needed):
    """Notify approvers about a pending command"""
    admins = execute_query(
        'SELECT id, username, email, telegram_chat_id FROM users WHERE role = ?',
        ('admin',),
        fetch_all=True
    )
    
    message = f"🔔 <b>Approval Required</b>\n\n"
    message += f"User: {user_name}\n"
    message += f"Command: <code>{command_text}</code>\n"
    message += f"Approvals needed: {approvers_needed}\n"
    message += f"Command ID: {command_id}"
    
    # Get Telegram bot token from environment (optional)
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    for admin in admins[:approvers_needed]:  # Only notify required number
        if admin.get('telegram_chat_id') and bot_token:
            send_telegram_notification(admin['telegram_chat_id'], message, bot_token)
        if admin.get('email'):
            send_email_notification(
                admin['email'],
                f"Command Approval Required: {command_text[:50]}",
                message
            )

def check_approval_status(command_id):
    """Check if command has enough approvals"""
    command = execute_query(
        'SELECT * FROM commands WHERE id = ?',
        (command_id,),
        fetch_one=True
    )
    
    if not command:
        return False
    
    command = dict(command)
    rule = None
    if command['matched_rule_id']:
        rule = execute_query(
            'SELECT * FROM rules WHERE id = ?',
            (command['matched_rule_id'],),
            fetch_one=True
        )
        rule = dict(rule) if rule else None
    
    # Get threshold
    user = execute_query(
        'SELECT tier FROM users WHERE id = ?',
        (command['user_id'],),
        fetch_one=True
    )
    
    if rule and rule.get('approval_threshold'):
        threshold = rule['approval_threshold']
    elif user:
        threshold = get_user_tier_threshold(user['tier'])
    else:
        threshold = 1
    
    # Count approvals
    approvals = execute_query(
        'SELECT COUNT(*) FROM approval_votes WHERE command_id = ? AND vote = ?',
        (command_id, 'approve'),
        fetch_one=True
    )
    
    return approvals[0] >= threshold if approvals else False

def escalate_command(command_id):
    """Escalate command to all admins"""
    command = execute_query(
        'SELECT c.*, u.username FROM commands c JOIN users u ON c.user_id = u.id WHERE c.id = ?',
        (command_id,),
        fetch_one=True
    )
    
    if not command:
        return
    
    command = dict(command)
    
    # Update escalation time
    execute_query(
        'UPDATE commands SET escalation_at = ? WHERE id = ?',
        (datetime.now(), command_id)
    )
    
    # Notify all admins
    admins = execute_query(
        'SELECT email, telegram_chat_id FROM users WHERE role = ?',
        ('admin',),
        fetch_all=True
    )
    
    message = f"🚨 <b>ESCALATION: Command Pending Approval</b>\n\n"
    message += f"User: {command['username']}\n"
    message += f"Command: <code>{command['command_text']}</code>\n"
    message += f"Command ID: {command_id}\n"
    message += f"Pending since: {command['created_at']}"
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    for admin in admins:
        if admin.get('telegram_chat_id') and bot_token:
            send_telegram_notification(admin['telegram_chat_id'], message, bot_token)
        if admin.get('email'):
            send_email_notification(
                admin['email'],
                f"ESCALATION: Command Approval Required",
                message
            )

# API Routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    user = request.current_user
    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'role': user['role'],
        'credits': user['credits']
    })

@app.route('/api/users', methods=['POST'])
@require_admin
def create_user():
    data = request.json
    username = data.get('username')
    role = data.get('role', 'member')
    initial_credits = data.get('credits', 100)
    tier = data.get('tier', 'junior')
    email = data.get('email', '')
    telegram_chat_id = data.get('telegram_chat_id', '')
    
    if not username:
        return jsonify({'error': 'Username required'}), 400
    
    if role not in ['admin', 'member']:
        return jsonify({'error': 'Invalid role'}), 400
    
    if tier not in ['junior', 'mid', 'senior', 'lead']:
        return jsonify({'error': 'Invalid tier'}), 400
    
    api_key = generate_api_key()
    
    try:
        execute_query(
            'INSERT INTO users (username, api_key, role, credits, tier, email, telegram_chat_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (username, api_key, role, initial_credits, tier, email, telegram_chat_id)
        )
        
        # Log action
        user_id = request.current_user['id']
        execute_query(
            'INSERT INTO audit_logs (user_id, action_type, details) VALUES (?, ?, ?)',
            (user_id, 'user_created', f'Created user: {username} with role: {role}')
        )
        
        return jsonify({
            'message': 'User created successfully',
            'username': username,
            'api_key': api_key,
            'role': role,
            'credits': initial_credits
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 400

@app.route('/api/users', methods=['GET'])
@require_admin
def list_users():
    print("DEBUG: list_users route called")
    users = execute_query('SELECT id, username, role, credits, tier, email, telegram_chat_id, created_at FROM users', fetch_all=True)
    print(f"DEBUG: Found {len(users) if users else 0} users")
    return jsonify([dict(u) for u in users])

@app.route('/api/users/<int:user_id>/credits', methods=['PUT'])
@require_admin
def update_user_credits(user_id):
    data = request.json
    credits = data.get('credits')
    
    if credits is None or credits < 0:
        return jsonify({'error': 'Valid credits amount required'}), 400
    
    execute_query(
        'UPDATE users SET credits = ? WHERE id = ?',
        (credits, user_id)
    )
    
    # Log action
    admin_id = request.current_user['id']
    execute_query(
        'INSERT INTO audit_logs (user_id, action_type, details) VALUES (?, ?, ?)',
        (admin_id, 'credits_updated', f'Updated credits for user {user_id} to {credits}')
    )
    
    return jsonify({'message': 'Credits updated successfully'})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    current_admin = request.current_user
    
    # Get user to delete
    user = execute_query(
        'SELECT * FROM users WHERE id = ?',
        (user_id,),
        fetch_one=True
    )
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user = dict(user)
    
    # Prevent deleting yourself
    if user_id == current_admin['id']:
        return jsonify({'error': 'You cannot delete your own account'}), 400
    
    # Prevent deleting the last admin
    if user['role'] == 'admin':
        admin_count = execute_query(
            'SELECT COUNT(*) FROM users WHERE role = ?',
            ('admin',),
            fetch_one=True
        )[0]
        if admin_count <= 1:
            return jsonify({'error': 'Cannot delete the last admin'}), 400
    
    # Delete related records first (for data integrity)
    # Delete commands by this user
    execute_query(
        'DELETE FROM commands WHERE user_id = ?',
        (user_id,)
    )
    
    # Set audit log user_id to NULL for this user's actions (keep audit trail)
    execute_query(
        'UPDATE audit_logs SET user_id = NULL WHERE user_id = ?',
        (user_id,)
    )
    
    # Delete user
    execute_query(
        'DELETE FROM users WHERE id = ?',
        (user_id,)
    )
    
    # Log action
    execute_query(
        'INSERT INTO audit_logs (user_id, action_type, details) VALUES (?, ?, ?)',
        (current_admin['id'], 'user_deleted', f'Deleted user: {user["username"]} (ID: {user_id})')
    )
    
    return jsonify({'message': 'User deleted successfully'})

@app.route('/api/rules', methods=['GET'])
@require_admin
def list_rules():
    rules = execute_query('SELECT * FROM rules ORDER BY id', fetch_all=True)
    return jsonify([dict(r) for r in rules])

@app.route('/api/rules', methods=['POST'])
@require_admin
def create_rule():
    data = request.json
    pattern = data.get('pattern')
    action = data.get('action')
    description = data.get('description', '')
    approval_threshold = data.get('approval_threshold', 1)
    time_start = data.get('time_start', '')
    time_end = data.get('time_end', '')
    timezone = data.get('timezone', 'UTC')
    
    if not pattern or not action:
        return jsonify({'error': 'Pattern and action required'}), 400
    
    if action not in ['AUTO_ACCEPT', 'AUTO_REJECT', 'REQUIRE_APPROVAL']:
        return jsonify({'error': 'Invalid action'}), 400
    
    # Validate regex pattern
    try:
        re.compile(pattern)
    except re.error as e:
        return jsonify({'error': f'Invalid regex pattern: {str(e)}'}), 400
    
    # Check for rule conflicts
    conflicts = check_rule_conflict(pattern)
    if conflicts:
        return jsonify({
            'error': 'Rule conflicts with existing rules',
            'conflicts': conflicts
        }), 400
    
    # Validate time format if provided
    if time_start or time_end:
        try:
            if time_start:
                datetime.strptime(time_start, '%H:%M')
            if time_end:
                datetime.strptime(time_end, '%H:%M')
        except ValueError:
            return jsonify({'error': 'Invalid time format. Use HH:MM'}), 400
    
    user_id = request.current_user['id']
    
    try:
        execute_query(
            'INSERT INTO rules (pattern, action, description, approval_threshold, time_start, time_end, timezone, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (pattern, action, description, approval_threshold, time_start, time_end, timezone, user_id)
        )
        
        # Log action
        execute_query(
            'INSERT INTO audit_logs (user_id, action_type, details) VALUES (?, ?, ?)',
            (user_id, 'rule_created', f'Created rule: {pattern} -> {action}')
        )
        
        return jsonify({'message': 'Rule created successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/rules/<int:rule_id>', methods=['DELETE'])
@require_admin
def delete_rule(rule_id):
    execute_query('DELETE FROM rules WHERE id = ?', (rule_id,))
    
    # Log action
    user_id = request.current_user['id']
    execute_query(
        'INSERT INTO audit_logs (user_id, action_type, details) VALUES (?, ?, ?)',
        (user_id, 'rule_deleted', f'Deleted rule {rule_id}')
    )
    
    return jsonify({'message': 'Rule deleted successfully'})

@app.route('/api/commands', methods=['POST'])
@require_auth
def submit_command():
    data = request.json
    command_text = data.get('command_text', '').strip()
    
    if not command_text:
        return jsonify({'error': 'Command text required'}), 400
    
    user = request.current_user
    
    # Refresh user credits from database to ensure latest balance
    user_db = execute_query(
        'SELECT * FROM users WHERE id = ?',
        (user['id'],),
        fetch_one=True
    )
    if not user_db:
        return jsonify({'error': 'User not found'}), 404
    user = dict(user_db)
    
    # Check credits
    if user['credits'] <= 0:
        execute_query(
            'INSERT INTO commands (user_id, command_text, status) VALUES (?, ?, ?)',
            (user['id'], command_text, 'rejected')
        )
        execute_query(
            'INSERT INTO audit_logs (user_id, action_type, details) VALUES (?, ?, ?)',
            (user['id'], 'command_rejected', f'Command rejected: insufficient credits - {command_text}')
        )
        return jsonify({
            'status': 'rejected',
            'reason': 'Insufficient credits',
            'credits': user['credits']
        }), 200
    
    # Check if this is a resubmission with approval token
    approval_token = data.get('approval_token')
    if approval_token:
        pending_command = execute_query(
            'SELECT * FROM commands WHERE approval_token = ? AND status = ?',
            (approval_token, 'approved'),
            fetch_one=True
        )
        if pending_command:
            pending_command = dict(pending_command)
            # Execute the approved command
            credits_cost = 1
            new_balance = user['credits'] - credits_cost
            
            conn = get_db()
            c = conn.cursor()
            c.execute('UPDATE users SET credits = ? WHERE id = ?', (new_balance, user['id']))
            c.execute(
                'UPDATE commands SET status = ?, credits_deducted = ?, execution_output = ?, executed_at = ? WHERE id = ?',
                ('executed', credits_cost, f'[MOCKED] Executed: {command_text}', datetime.now(), pending_command['id'])
            )
            c.execute(
                'INSERT INTO audit_logs (user_id, action_type, details) VALUES (?, ?, ?)',
                (user['id'], 'command_executed', f'Command executed after approval: {command_text}')
            )
            conn.commit()
            conn.close()
            
            return jsonify({
                'status': 'executed',
                'command_id': pending_command['id'],
                'credits_deducted': credits_cost,
                'new_balance': new_balance,
                'output': f'[MOCKED] Executed: {command_text}'
            }), 200
    
    # Match against rules (first match wins, considering time-based rules)
    rules = execute_query(
        'SELECT * FROM rules ORDER BY id',
        fetch_all=True
    )
    
    matched_rule = None
    for rule in rules:
        try:
            if re.search(rule['pattern'], command_text):
                # Check if time-based rule applies
                if evaluate_time_based_rule(rule):
                    matched_rule = dict(rule)
                    break
        except re.error:
            continue
    
    # Determine action
    if matched_rule:
        action = matched_rule['action']
        rule_id = matched_rule['id']
    else:
        # Default: reject if no rule matches
        action = 'AUTO_REJECT'
        rule_id = None
    
    # Execute transaction
    conn = get_db()
    c = conn.cursor()
    
    try:
        if action == 'AUTO_ACCEPT':
            # Deduct credits (1 credit per command)
            credits_cost = 1
            new_balance = user['credits'] - credits_cost
            
            # Update user credits
            c.execute('UPDATE users SET credits = ? WHERE id = ?', (new_balance, user['id']))
            
            # Create command record
            c.execute(
                'INSERT INTO commands (user_id, command_text, status, matched_rule_id, credits_deducted, execution_output, executed_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (user['id'], command_text, 'executed', rule_id, credits_cost, f'[MOCKED] Executed: {command_text}', datetime.now())
            )
            command_id = c.lastrowid
            
            # Log to audit
            c.execute(
                'INSERT INTO audit_logs (user_id, action_type, details) VALUES (?, ?, ?)',
                (user['id'], 'command_executed', f'Command executed: {command_text}')
            )
            
            conn.commit()
            
            return jsonify({
                'status': 'executed',
                'command_id': command_id,
                'credits_deducted': credits_cost,
                'new_balance': new_balance,
                'output': f'[MOCKED] Executed: {command_text}'
            }), 200
        
        elif action == 'AUTO_REJECT':
            # Create command record
            c.execute(
                'INSERT INTO commands (user_id, command_text, status, matched_rule_id) VALUES (?, ?, ?, ?)',
                (user['id'], command_text, 'rejected', rule_id)
            )
            
            # Log to audit
            c.execute(
                'INSERT INTO audit_logs (user_id, action_type, details) VALUES (?, ?, ?)',
                (user['id'], 'command_rejected', f'Command rejected by rule: {command_text}')
            )
            
            conn.commit()
            
            return jsonify({
                'status': 'rejected',
                'reason': f'Blocked by rule: {matched_rule["description"] if matched_rule else "No matching rule"}',
                'credits': user['credits']
            }), 200
        
        else:
            # REQUIRE_APPROVAL with voting thresholds
            # Calculate required approvals
            if matched_rule and matched_rule.get('approval_threshold'):
                threshold = matched_rule['approval_threshold']
            else:
                threshold = get_user_tier_threshold(user.get('tier', 'junior'))
            
            # Generate approval token
            approval_token = secrets.token_urlsafe(32)
            
            # Create command record
            escalation_time = datetime.now()
            # Add 1 hour for escalation
            from datetime import timedelta
            escalation_time = escalation_time + timedelta(hours=1)
            
            c.execute(
                'INSERT INTO commands (user_id, command_text, status, matched_rule_id, approval_token, escalation_at) VALUES (?, ?, ?, ?, ?, ?)',
                (user['id'], command_text, 'pending', rule_id, approval_token, escalation_time)
            )
            command_id = c.lastrowid
            
            c.execute(
                'INSERT INTO audit_logs (user_id, action_type, details) VALUES (?, ?, ?)',
                (user['id'], 'command_pending_approval', f'Command pending approval: {command_text} (threshold: {threshold})')
            )
            
            conn.commit()
            
            # Notify approvers in background
            Thread(target=notify_approvers, args=(command_id, command_text, user['username'], threshold)).start()
            
            return jsonify({
                'status': 'pending',
                'reason': f'Requires {threshold} approval(s)',
                'command_id': command_id,
                'approval_token': approval_token,
                'threshold': threshold
            }), 202
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'Transaction failed: {str(e)}'}), 500
    finally:
        conn.close()

@app.route('/api/commands', methods=['GET'])
@require_auth
def list_commands():
    user = request.current_user
    
    if user['role'] == 'admin':
        commands = execute_query(
            'SELECT c.*, u.username FROM commands c JOIN users u ON c.user_id = u.id ORDER BY c.created_at DESC LIMIT 100',
            fetch_all=True
        )
    else:
        commands = execute_query(
            'SELECT * FROM commands WHERE user_id = ? ORDER BY created_at DESC LIMIT 100',
            (user['id'],),
            fetch_all=True
        )
    
    return jsonify([dict(c) for c in commands])

@app.route('/api/audit-logs', methods=['GET'])
@require_admin
def get_audit_logs():
    logs = execute_query(
        'SELECT a.*, u.username FROM audit_logs a LEFT JOIN users u ON a.user_id = u.id ORDER BY a.created_at DESC LIMIT 200',
        fetch_all=True
    )
    return jsonify([dict(l) for l in logs])

@app.route('/api/commands/pending', methods=['GET'])
@require_admin
def get_pending_commands():
    """Get all pending commands requiring approval"""
    commands = execute_query(
        '''SELECT c.*, u.username, u.tier, 
           (SELECT COUNT(*) FROM approval_votes WHERE command_id = c.id AND vote = 'approve') as approval_count,
           (SELECT COUNT(*) FROM approval_votes WHERE command_id = c.id AND vote = 'reject') as rejection_count,
           COALESCE(r.approval_threshold, ?) as approval_threshold
           FROM commands c 
           JOIN users u ON c.user_id = u.id 
           LEFT JOIN rules r ON c.matched_rule_id = r.id
           WHERE c.status = 'pending' 
           ORDER BY c.created_at DESC''',
        (get_user_tier_threshold('junior'),),
        fetch_all=True
    )
    return jsonify([dict(c) for c in commands])

@app.route('/api/commands/<int:command_id>/approve', methods=['POST'])
@require_admin
def approve_command(command_id):
    """Approve a pending command"""
    approver_id = request.current_user['id']
    
    # Check if command exists and is pending
    command = execute_query(
        'SELECT * FROM commands WHERE id = ?',
        (command_id,),
        fetch_one=True
    )
    
    if not command:
        return jsonify({'error': 'Command not found'}), 404
    
    command = dict(command)
    
    if command['status'] != 'pending':
        return jsonify({'error': 'Command is not pending approval'}), 400
    
    # Check if already voted
    existing_vote = execute_query(
        'SELECT * FROM approval_votes WHERE command_id = ? AND approver_id = ?',
        (command_id, approver_id),
        fetch_one=True
    )
    
    if existing_vote:
        # Update vote
        execute_query(
            'UPDATE approval_votes SET vote = ?, created_at = ? WHERE command_id = ? AND approver_id = ?',
            ('approve', datetime.now(), command_id, approver_id)
        )
    else:
        # Create vote
        execute_query(
            'INSERT INTO approval_votes (command_id, approver_id, vote) VALUES (?, ?, ?)',
            (command_id, approver_id, 'approve')
        )
    
    # Check if threshold met
    if check_approval_status(command_id):
        # Mark as approved
        execute_query(
            'UPDATE commands SET status = ? WHERE id = ?',
            ('approved', command_id)
        )
        execute_query(
            'INSERT INTO audit_logs (user_id, action_type, details) VALUES (?, ?, ?)',
            (approver_id, 'command_approved', f'Command {command_id} approved and ready for execution')
        )
        
        return jsonify({
            'message': 'Command approved. Threshold met. User can now execute.',
            'status': 'approved',
            'approval_token': command['approval_token']
        })
    else:
        # Get current counts
        approvals = execute_query(
            'SELECT COUNT(*) FROM approval_votes WHERE command_id = ? AND vote = ?',
            (command_id, 'approve'),
            fetch_one=True
        )[0]
        
        return jsonify({
            'message': 'Vote recorded',
            'approvals': approvals,
            'status': 'pending'
        })

@app.route('/api/commands/<int:command_id>/reject', methods=['POST'])
@require_admin
def reject_command(command_id):
    """Reject a pending command"""
    approver_id = request.current_user['id']
    
    command = execute_query(
        'SELECT * FROM commands WHERE id = ?',
        (command_id,),
        fetch_one=True
    )
    
    if not command:
        return jsonify({'error': 'Command not found'}), 404
    
    command = dict(command)
    
    if command['status'] != 'pending':
        return jsonify({'error': 'Command is not pending approval'}), 400
    
    # Record rejection vote
    existing_vote = execute_query(
        'SELECT * FROM approval_votes WHERE command_id = ? AND approver_id = ?',
        (command_id, approver_id),
        fetch_one=True
    )
    
    if existing_vote:
        execute_query(
            'UPDATE approval_votes SET vote = ? WHERE command_id = ? AND approver_id = ?',
            ('reject', command_id, approver_id)
        )
    else:
        execute_query(
            'INSERT INTO approval_votes (command_id, approver_id, vote) VALUES (?, ?, ?)',
            (command_id, approver_id, 'reject')
        )
    
    # If majority reject, reject the command
    rejections = execute_query(
        'SELECT COUNT(*) FROM approval_votes WHERE command_id = ? AND vote = ?',
        (command_id, 'reject'),
        fetch_one=True
    )[0]
    
    approvals = execute_query(
        'SELECT COUNT(*) FROM approval_votes WHERE command_id = ? AND vote = ?',
        (command_id, 'approve'),
        fetch_one=True
    )[0]
    
    if rejections > approvals:
        execute_query(
            'UPDATE commands SET status = ? WHERE id = ?',
            ('rejected', command_id)
        )
        execute_query(
            'INSERT INTO audit_logs (user_id, action_type, details) VALUES (?, ?, ?)',
            (approver_id, 'command_rejected', f'Command {command_id} rejected by approver')
        )
        return jsonify({'message': 'Command rejected', 'status': 'rejected'})
    
    return jsonify({'message': 'Rejection vote recorded', 'status': 'pending'})

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@require_admin
def update_user(user_id):
    """Update user details including tier, email, telegram"""
    data = request.json
    tier = data.get('tier')
    email = data.get('email')
    telegram_chat_id = data.get('telegram_chat_id')
    
    updates = []
    params = []
    
    if tier:
        if tier not in ['junior', 'mid', 'senior', 'lead']:
            return jsonify({'error': 'Invalid tier'}), 400
        updates.append('tier = ?')
        params.append(tier)
    
    if email is not None:
        updates.append('email = ?')
        params.append(email)
    
    if telegram_chat_id is not None:
        updates.append('telegram_chat_id = ?')
        params.append(telegram_chat_id)
    
    if not updates:
        return jsonify({'error': 'No fields to update'}), 400
    
    params.append(user_id)
    query = f'UPDATE users SET {", ".join(updates)} WHERE id = ?'
    execute_query(query, tuple(params))
    
    return jsonify({'message': 'User updated successfully'})

@app.route('/api/rules/check-conflict', methods=['POST'])
@require_admin
def check_rule_conflict_endpoint():
    """Check if a rule pattern conflicts with existing rules"""
    data = request.json
    pattern = data.get('pattern')
    exclude_id = data.get('exclude_id')
    
    if not pattern:
        return jsonify({'error': 'Pattern required'}), 400
    
    try:
        re.compile(pattern)
    except re.error as e:
        return jsonify({'error': f'Invalid regex: {str(e)}'}), 400
    
    conflicts = check_rule_conflict(pattern, exclude_id)
    return jsonify({'conflicts': conflicts, 'has_conflicts': len(conflicts) > 0})

def check_escalations():
    """Background task to check for commands that need escalation"""
    import time
    while True:
        try:
            time.sleep(300)  # Check every 5 minutes
            
            pending_commands = execute_query(
                'SELECT * FROM commands WHERE status = ? AND escalation_at IS NOT NULL AND escalation_at <= ?',
                ('pending', datetime.now()),
                fetch_all=True
            )
            
            for cmd in pending_commands:
                cmd = dict(cmd)
                # Check if already escalated (simple check to avoid duplicate escalations)
                if cmd.get('escalation_at'):
                    escalate_command(cmd['id'])
        except Exception as e:
            print(f"Error in escalation check: {e}")

if __name__ == '__main__':
    init_db()
    seed_data()
    
    # Start escalation checker in background
    escalation_thread = Thread(target=check_escalations, daemon=True)
    escalation_thread.start()
    
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False)

