let apiKey = localStorage.getItem('apiKey') || '';
let currentUser = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    if (apiKey) {
        login();
    }
});

// API helper function
async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': apiKey
        }
    };
    
    if (body) {
        options.body = JSON.stringify(body);
    }
    
    const response = await fetch(`/api${endpoint}`, options);
    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(data.error || 'Request failed');
    }
    
    return data;
}

// Login
async function login() {
    const input = document.getElementById('api-key-input');
    apiKey = input.value.trim();
    
    if (!apiKey) {
        alert('Please enter an API key');
        return;
    }
    
    try {
        currentUser = await apiCall('/auth/me');
        localStorage.setItem('apiKey', apiKey);
        
        document.getElementById('login-section').style.display = 'none';
        document.getElementById('app-section').style.display = 'block';
        
        updateUserInfo();
        loadHistory();
        
        // Hide all admin-only elements first
        document.querySelectorAll('.admin-only').forEach(el => {
            el.style.display = 'none';
        });
        
        // Only show admin features if user is admin
        if (currentUser.role === 'admin') {
            document.querySelectorAll('.admin-only').forEach(el => {
                el.style.display = 'block';
            });
            loadRules();
            loadUsers();
            loadAuditLogs();
            loadPendingApprovals();
        } else {
            // Ensure members can't access admin tabs even if they try
            document.querySelectorAll('.admin-only').forEach(el => {
                el.style.display = 'none';
            });
        }
    } catch (error) {
        alert('Invalid API key: ' + error.message);
    }
}

// Logout
function logout() {
    apiKey = '';
    localStorage.removeItem('apiKey');
    currentUser = null;
    document.getElementById('login-section').style.display = 'block';
    document.getElementById('app-section').style.display = 'none';
    document.getElementById('api-key-input').value = '';
}

// Update user info display
function updateUserInfo() {
    if (!currentUser) return;
    
    document.getElementById('username').textContent = currentUser.username;
    document.getElementById('credits-value').textContent = currentUser.credits;
    
    const roleBadge = document.getElementById('role-badge');
    roleBadge.textContent = currentUser.role.toUpperCase();
    roleBadge.className = `role-badge ${currentUser.role}`;
}

// Tab switching
function showTab(tabName) {
    // Prevent members from accessing admin tabs
    const adminTabs = ['rules', 'users', 'audit'];
    if (adminTabs.includes(tabName) && (!currentUser || currentUser.role !== 'admin')) {
        console.warn('Access denied: Admin only feature');
        return;
    }
    
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const tabElement = document.getElementById(`${tabName}-tab`);
    if (!tabElement) {
        console.error(`Tab ${tabName} not found`);
        return;
    }
    
    tabElement.classList.add('active');
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    // Load data when switching to admin tabs
    if (currentUser && currentUser.role === 'admin') {
        if (tabName === 'rules') {
            loadRules();
        } else if (tabName === 'users') {
            loadUsers();
        } else if (tabName === 'audit') {
            loadAuditLogs();
        }
    }
}

// Submit command
async function submitCommand() {
    const input = document.getElementById('command-input');
    const commandText = input.value.trim();
    const resultBox = document.getElementById('command-result');
    
    if (!commandText) {
        alert('Please enter a command');
        return;
    }
    
    try {
        const result = await apiCall('/commands', 'POST', {
            command_text: commandText
        });
        
        input.value = '';
        
        if (result.status === 'executed') {
            resultBox.className = 'result-box success';
            resultBox.innerHTML = `
                <strong>✓ Command Executed</strong><br>
                Output: ${result.output}<br>
                Credits deducted: ${result.credits_deducted}<br>
                New balance: ${result.new_balance}
            `;
            currentUser.credits = result.new_balance;
            updateUserInfo();
        } else if (result.status === 'rejected') {
            resultBox.className = 'result-box error';
            resultBox.innerHTML = `
                <strong>✗ Command Rejected</strong><br>
                Reason: ${result.reason}
            `;
        } else if (result.status === 'pending') {
            resultBox.className = 'result-box info';
            resultBox.innerHTML = `
                <strong>⏳ Command Pending Approval</strong><br>
                ${result.reason || 'Your command is waiting for approval.'}<br>
                ${result.approval_token ? `Approval Token: <code>${result.approval_token}</code><br>` : ''}
                ${result.approval_token ? '<small>Save this token. You can resubmit the command with this token once approved.</small>' : ''}
            `;
            // Store approval token
            if (result.approval_token) {
                localStorage.setItem(`approval_token_${result.command_id}`, result.approval_token);
            }
        }
        
        setTimeout(() => {
            loadHistory();
        }, 500);
    } catch (error) {
        resultBox.className = 'result-box error';
        resultBox.innerHTML = `<strong>Error:</strong> ${error.message}`;
    }
}

// Load command history
async function loadHistory() {
    try {
        const commands = await apiCall('/commands');
        const historyList = document.getElementById('history-list');
        
        if (commands.length === 0) {
            historyList.innerHTML = '<div class="empty-state">No commands yet</div>';
            return;
        }
        
        historyList.innerHTML = commands.map(cmd => {
            const date = new Date(cmd.created_at).toLocaleString();
            const statusClass = cmd.status.toLowerCase();
            
            return `
                <div class="history-item ${statusClass}">
                    <div class="item-header">
                        <div class="item-title">${escapeHtml(cmd.command_text)}</div>
                        <span class="status-badge ${statusClass}">${cmd.status}</span>
                    </div>
                    <div class="item-meta">
                        ${cmd.execution_output ? `Output: ${escapeHtml(cmd.execution_output)}<br>` : ''}
                        ${cmd.credits_deducted > 0 ? `Credits: -${cmd.credits_deducted}<br>` : ''}
                        ${currentUser.role === 'admin' ? `User: ${cmd.username || 'N/A'}<br>` : ''}
                        Time: ${date}
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        document.getElementById('history-list').innerHTML = 
            `<div class="result-box error">Error loading history: ${error.message}</div>`;
    }
}

// Load rules (Admin only)
async function loadRules() {
    // Security check: Only admins can load rules
    if (!currentUser || currentUser.role !== 'admin') {
        console.warn('Access denied: Only admins can view rules');
        return;
    }
    
    try {
        console.log('Loading rules...');
        const rules = await apiCall('/rules');
        console.log('Rules loaded:', rules);
        console.log('Rules count:', rules ? rules.length : 0);
        const rulesList = document.getElementById('rules-list');
        
        if (!rulesList) {
            console.error('rules-list element not found!');
            return;
        }
        
        if (!rules || rules.length === 0) {
            console.log('No rules found, showing empty state');
            rulesList.innerHTML = '<div class="empty-state">No rules configured</div>';
            return;
        }
        
        console.log('Rendering', rules.length, 'rules');
        const html = rules.map(rule => {
            return `
                <div class="rule-item">
                    <div class="item-header">
                        <div class="item-title">${escapeHtml(rule.pattern)}</div>
                        <span class="status-badge ${rule.action === 'AUTO_ACCEPT' ? 'executed' : rule.action === 'AUTO_REJECT' ? 'rejected' : 'pending'}">${rule.action}</span>
                    </div>
                    <div class="item-meta">
                        ${rule.description ? `Description: ${escapeHtml(rule.description)}<br>` : ''}
                        ${rule.action === 'REQUIRE_APPROVAL' && rule.approval_threshold ? `Approval Threshold: ${rule.approval_threshold}<br>` : ''}
                        ${rule.time_start && rule.time_end ? `Time Window: ${rule.time_start} - ${rule.time_end} (${rule.timezone || 'UTC'})<br>` : ''}
                        Created: ${new Date(rule.created_at).toLocaleString()}
                    </div>
                    <button onclick="deleteRule(${rule.id})" class="btn btn-danger" style="margin-top: 10px; padding: 6px 12px; font-size: 0.8rem;">Delete</button>
                </div>
            `;
        }).join('');
        console.log('Setting innerHTML for rules-list');
        rulesList.innerHTML = html;
        console.log('Rules rendered successfully');
    } catch (error) {
        console.error('Error loading rules:', error);
        const rulesList = document.getElementById('rules-list');
        if (rulesList) {
            rulesList.innerHTML = 
                `<div class="result-box error">Error loading rules: ${error.message}</div>`;
        }
    }
}

// Add rule (Admin only)
function showAddRuleModal() {
    // Security check: Only admins can add rules
    if (!currentUser || currentUser.role !== 'admin') {
        alert('Access denied: Only admins can create rules');
        return;
    }
    
    document.getElementById('add-rule-modal').style.display = 'block';
    document.getElementById('rule-pattern').value = '';
    document.getElementById('rule-description').value = '';
    document.getElementById('rule-action').value = 'AUTO_ACCEPT';
    document.getElementById('rule-approval-threshold').value = '1';
    document.getElementById('rule-time-based').checked = false;
    document.getElementById('rule-time-start').value = '';
    document.getElementById('rule-time-end').value = '';
    document.getElementById('rule-timezone').value = 'UTC';
    document.getElementById('rule-conflict-warning').style.display = 'none';
    toggleApprovalFields();
    toggleTimeFields();
}

async function checkRuleConflict() {
    const pattern = document.getElementById('rule-pattern').value.trim();
    const warningDiv = document.getElementById('rule-conflict-warning');
    
    if (!pattern) {
        warningDiv.style.display = 'none';
        return;
    }
    
    try {
        const result = await apiCall('/rules/check-conflict', 'POST', { pattern });
        if (result.has_conflicts) {
            warningDiv.style.display = 'block';
            warningDiv.textContent = `⚠️ Conflicts with ${result.conflicts.length} existing rule(s)`;
        } else {
            warningDiv.style.display = 'none';
        }
    } catch (error) {
        // Ignore errors for conflict checking
    }
}

function toggleApprovalFields() {
    const action = document.getElementById('rule-action').value;
    const thresholdGroup = document.getElementById('approval-threshold-group');
    thresholdGroup.style.display = action === 'REQUIRE_APPROVAL' ? 'block' : 'none';
}

function toggleTimeFields() {
    const checked = document.getElementById('rule-time-based').checked;
    document.getElementById('time-fields').style.display = checked ? 'block' : 'none';
}

async function addRule() {
    // Security check: Only admins can add rules
    if (!currentUser || currentUser.role !== 'admin') {
        alert('Access denied: Only admins can create rules');
        return;
    }
    
    const pattern = document.getElementById('rule-pattern').value.trim();
    const action = document.getElementById('rule-action').value;
    const description = document.getElementById('rule-description').value.trim();
    const approval_threshold = parseInt(document.getElementById('rule-approval-threshold').value) || 1;
    const timeBased = document.getElementById('rule-time-based').checked;
    const time_start = timeBased ? document.getElementById('rule-time-start').value : '';
    const time_end = timeBased ? document.getElementById('rule-time-end').value : '';
    const timezone = timeBased ? (document.getElementById('rule-timezone').value || 'UTC') : 'UTC';
    
    if (!pattern) {
        alert('Please enter a pattern');
        return;
    }
    
    try {
        await apiCall('/rules', 'POST', {
            pattern,
            action,
            description,
            approval_threshold: action === 'REQUIRE_APPROVAL' ? approval_threshold : undefined,
            time_start,
            time_end,
            timezone
        });
        
        closeModal('add-rule-modal');
        loadRules();
        alert('Rule created successfully!');
    } catch (error) {
        alert('Error creating rule: ' + error.message);
    }
}

// Delete rule (Admin only)
async function deleteRule(ruleId) {
    // Security check: Only admins can delete rules
    if (!currentUser || currentUser.role !== 'admin') {
        alert('Access denied: Only admins can delete rules');
        return;
    }
    
    if (!confirm('Are you sure you want to delete this rule?')) {
        return;
    }
    
    try {
        await apiCall(`/rules/${ruleId}`, 'DELETE');
        loadRules();
        alert('Rule deleted successfully!');
    } catch (error) {
        alert('Error deleting rule: ' + error.message);
    }
}

// Load users (Admin only)
async function loadUsers() {
    // Security check: Only admins can load users
    if (!currentUser || currentUser.role !== 'admin') {
        console.warn('Access denied: Only admins can view users');
        return;
    }
    
    try {
        console.log('Loading users...');
        const users = await apiCall('/users');
        console.log('Users loaded:', users);
        console.log('Users count:', users ? users.length : 0);
        const usersList = document.getElementById('users-list');
        
        if (!usersList) {
            console.error('users-list element not found!');
            return;
        }
        
        if (!users || users.length === 0) {
            console.log('No users found, showing empty state');
            usersList.innerHTML = '<div class="empty-state">No users found</div>';
            return;
        }
        
        console.log('Rendering', users.length, 'users');
        const html = users.map(user => {
            return `
                <div class="user-item">
                    <div class="item-header">
                        <div class="item-title">${escapeHtml(user.username)}</div>
                        <div style="display: flex; gap: 8px; align-items: center;">
                            <span class="status-badge ${user.role === 'admin' ? 'executed' : 'accepted'}">${user.role}</span>
                            <span class="status-badge" style="background: #dbeafe; color: #1e40af;">${user.tier || 'junior'}</span>
                        </div>
                    </div>
                    <div class="item-meta">
                        Credits: ${user.credits}<br>
                        Tier: ${user.tier || 'junior'} (Threshold: ${user.tier === 'junior' ? 3 : user.tier === 'mid' ? 2 : 1})<br>
                        ${user.email ? `Email: ${escapeHtml(user.email)}<br>` : ''}
                        ${user.telegram_chat_id ? `Telegram: ${escapeHtml(user.telegram_chat_id)}<br>` : ''}
                        Created: ${new Date(user.created_at).toLocaleString()}
                    </div>
                    <div style="margin-top: 12px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                        <input type="number" id="credits-${user.id}" value="${user.credits}" min="0" style="width: 120px; padding: 6px;">
                        <button onclick="updateUserCredits(${user.id})" class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.8rem;">Update Credits</button>
                        <select id="tier-${user.id}" style="padding: 6px; font-size: 0.8rem;">
                            <option value="junior" ${(user.tier || 'junior') === 'junior' ? 'selected' : ''}>Junior</option>
                            <option value="mid" ${user.tier === 'mid' ? 'selected' : ''}>Mid</option>
                            <option value="senior" ${user.tier === 'senior' ? 'selected' : ''}>Senior</option>
                            <option value="lead" ${user.tier === 'lead' ? 'selected' : ''}>Lead</option>
                        </select>
                        <button onclick="updateUserTier(${user.id})" class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.8rem;">Update Tier</button>
                        ${user.role === 'member' ? `<button onclick="deleteUser(${user.id}, '${escapeHtml(user.username)}')" class="btn btn-danger" style="padding: 6px 12px; font-size: 0.8rem;">Delete</button>` : ''}
                    </div>
                </div>
            `;
        }).join('');
        console.log('Setting innerHTML for users-list');
        usersList.innerHTML = html;
        console.log('Users rendered successfully');
    } catch (error) {
        console.error('Error loading users:', error);
        const usersList = document.getElementById('users-list');
        if (usersList) {
            usersList.innerHTML = 
                `<div class="result-box error">Error loading users: ${error.message}</div>`;
        }
    }
}

// Add user (Admin only)
function showAddUserModal() {
    // Security check: Only admins can add users
    if (!currentUser || currentUser.role !== 'admin') {
        alert('Access denied: Only admins can create users');
        return;
    }
    
    document.getElementById('add-user-modal').style.display = 'block';
    document.getElementById('user-username').value = '';
    document.getElementById('user-role').value = 'member';
    document.getElementById('user-tier').value = 'junior';
    document.getElementById('user-credits').value = '100';
    document.getElementById('user-email').value = '';
    document.getElementById('user-telegram').value = '';
    document.getElementById('new-user-api-key').style.display = 'none';
}

async function addUser() {
    // Security check: Only admins can add users
    if (!currentUser || currentUser.role !== 'admin') {
        alert('Access denied: Only admins can create users');
        return;
    }
    
    const username = document.getElementById('user-username').value.trim();
    const role = document.getElementById('user-role').value;
    const tier = document.getElementById('user-tier').value;
    const credits = parseInt(document.getElementById('user-credits').value);
    const email = document.getElementById('user-email').value.trim();
    const telegram_chat_id = document.getElementById('user-telegram').value.trim();
    
    if (!username) {
        alert('Please enter a username');
        return;
    }
    
    try {
        const result = await apiCall('/users', 'POST', {
            username,
            role,
            tier,
            credits,
            email: email || undefined,
            telegram_chat_id: telegram_chat_id || undefined
        });
        
        const apiKeyDisplay = document.getElementById('new-user-api-key');
        apiKeyDisplay.innerHTML = `
            <strong>⚠️ IMPORTANT: Save this API key now!</strong>
            <code>${result.api_key}</code>
            <p style="margin-top: 10px; color: #856404;">This is the only time you'll see this key.</p>
            <button onclick="copyToClipboard('${result.api_key}')" class="btn btn-secondary" style="margin-top: 8px; width: 100%;">📋 Copy API Key</button>
        `;
        apiKeyDisplay.style.display = 'block';
        
        alert(`User created successfully!\n\nUsername: ${result.username}\nAPI Key: ${result.api_key}\n\nMake sure to save the API key now - you won't see it again!`);
    } catch (error) {
        alert('Error creating user: ' + error.message);
    }
}

// Update user credits (Admin only)
async function updateUserCredits(userId) {
    // Security check: Only admins can update user credits
    if (!currentUser || currentUser.role !== 'admin') {
        alert('Access denied: Only admins can update user credits');
        return;
    }
    
    const creditsInput = document.getElementById(`credits-${userId}`);
    const credits = parseInt(creditsInput.value);
    
    if (isNaN(credits) || credits < 0) {
        alert('Please enter a valid credits amount');
        return;
    }
    
    try {
        // Disable the button during update
        const updateBtn = creditsInput.nextElementSibling;
        if (updateBtn) {
            updateBtn.disabled = true;
            updateBtn.textContent = 'Updating...';
        }
        
        await apiCall(`/users/${userId}/credits`, 'PUT', {
            credits
        });
        
        // Refresh the users list to show updated credits
        await loadUsers();
        
        // If the updated user is the current user, refresh their info too
        if (currentUser && currentUser.id === userId) {
            try {
                currentUser = await apiCall('/auth/me');
                updateUserInfo();
            } catch (error) {
                console.error('Error refreshing current user info:', error);
            }
        }
        
        alert('Credits updated successfully!');
    } catch (error) {
        alert('Error updating credits: ' + error.message);
        // Re-enable button on error
        const updateBtn = creditsInput.nextElementSibling;
        if (updateBtn) {
            updateBtn.disabled = false;
            updateBtn.textContent = 'Update Credits';
        }
    }
}

// Update user tier
async function updateUserTier(userId) {
    if (!currentUser || currentUser.role !== 'admin') {
        alert('Access denied: Only admins can update user tiers');
        return;
    }
    
    const tierSelect = document.getElementById(`tier-${userId}`);
    const tier = tierSelect.value;
    
    try {
        await apiCall(`/users/${userId}`, 'PUT', { tier });
        await loadUsers();
        alert('User tier updated successfully!');
    } catch (error) {
        alert('Error updating tier: ' + error.message);
    }
}

// Delete user (Admin only)
async function deleteUser(userId, username) {
    // Security check: Only admins can delete users
    if (!currentUser || currentUser.role !== 'admin') {
        alert('Access denied: Only admins can delete users');
        return;
    }
    
    // Prevent deleting yourself
    if (currentUser.id === userId) {
        alert('You cannot delete your own account');
        return;
    }
    
    if (!confirm(`Are you sure you want to delete user "${username}"?\n\nThis action cannot be undone.`)) {
        return;
    }
    
    try {
        await apiCall(`/users/${userId}`, 'DELETE');
        await loadUsers();
        alert('User deleted successfully!');
    } catch (error) {
        alert('Error deleting user: ' + error.message);
    }
}

// Load audit logs (Admin only)
async function loadAuditLogs() {
    // Security check: Only admins can load audit logs
    if (!currentUser || currentUser.role !== 'admin') {
        console.warn('Access denied: Only admins can view audit logs');
        return;
    }
    
    try {
        console.log('Loading audit logs...');
        const logs = await apiCall('/audit-logs');
        console.log('Audit logs loaded:', logs);
        console.log('Logs count:', logs ? logs.length : 0);
        const auditList = document.getElementById('audit-logs-list');
        
        if (!auditList) {
            console.error('audit-logs-list element not found!');
            return;
        }
        
        if (!logs || logs.length === 0) {
            console.log('No audit logs found, showing empty state');
            auditList.innerHTML = '<div class="empty-state">No audit logs</div>';
            return;
        }
        
        console.log('Rendering', logs.length, 'audit logs');
        const html = logs.map(log => {
            return `
                <div class="audit-item">
                    <div class="item-header">
                        <div class="item-title">${escapeHtml(log.action_type)}</div>
                        <span class="item-meta">${new Date(log.created_at).toLocaleString()}</span>
                    </div>
                    <div class="item-meta">
                        User: ${log.username || 'System'}<br>
                        Details: ${escapeHtml(log.details || 'N/A')}
                    </div>
                </div>
            `;
        }).join('');
        console.log('Setting innerHTML for audit-logs-list');
        auditList.innerHTML = html;
        console.log('Audit logs rendered successfully');
    } catch (error) {
        console.error('Error loading audit logs:', error);
        const auditList = document.getElementById('audit-logs-list');
        if (auditList) {
            auditList.innerHTML = 
                `<div class="result-box error">Error loading audit logs: ${error.message}</div>`;
        }
    }
}

// Modal functions
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

// Toggle API key visibility
function toggleApiKeyVisibility() {
    const input = document.getElementById('api-key-input');
    if (input.type === 'password') {
        input.type = 'text';
    } else {
        input.type = 'password';
    }
}

// Load pending approvals (Admin only)
async function loadPendingApprovals() {
    if (!currentUser || currentUser.role !== 'admin') {
        return;
    }
    
    try {
        const commands = await apiCall('/commands/pending');
        const approvalsList = document.getElementById('approvals-list');
        
        if (!approvalsList) return;
        
        if (!commands || commands.length === 0) {
            approvalsList.innerHTML = '<div class="empty-state">No pending approvals</div>';
            return;
        }
        
        approvalsList.innerHTML = commands.map(cmd => {
            const threshold = cmd.approval_threshold || 1;
            const approvalCount = cmd.approval_count || 0;
            const rejectionCount = cmd.rejection_count || 0;
            const progress = Math.min((approvalCount / threshold) * 100, 100);
            
            return `
                <div class="history-item pending">
                    <div class="item-header">
                        <div class="item-title">${escapeHtml(cmd.command_text)}</div>
                        <span class="status-badge pending">Pending</span>
                    </div>
                    <div class="item-meta">
                        User: ${escapeHtml(cmd.username)} (${cmd.tier || 'junior'})<br>
                        Approvals: ${approvalCount}/${threshold} | Rejections: ${rejectionCount}<br>
                        <div style="background: #e5e7eb; border-radius: 4px; height: 8px; margin: 8px 0;">
                            <div style="background: #3b82f6; height: 100%; width: ${progress}%; border-radius: 4px; transition: width 0.3s;"></div>
                        </div>
                        Created: ${new Date(cmd.created_at).toLocaleString()}<br>
                        ${cmd.escalation_at ? `Escalation: ${new Date(cmd.escalation_at).toLocaleString()}<br>` : ''}
                    </div>
                    <div style="margin-top: 12px; display: flex; gap: 8px;">
                        <button onclick="approveCommand(${cmd.id})" class="btn btn-primary">Approve</button>
                        <button onclick="rejectCommand(${cmd.id})" class="btn btn-danger">Reject</button>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading pending approvals:', error);
        const approvalsList = document.getElementById('approvals-list');
        if (approvalsList) {
            approvalsList.innerHTML = `<div class="result-box error">Error: ${error.message}</div>`;
        }
    }
}

// Approve command
async function approveCommand(commandId) {
    try {
        const result = await apiCall(`/commands/${commandId}/approve`, 'POST');
        alert(result.message || 'Command approved');
        loadPendingApprovals();
        loadHistory();
    } catch (error) {
        alert('Error approving command: ' + error.message);
    }
}

// Reject command
async function rejectCommand(commandId) {
    if (!confirm('Are you sure you want to reject this command?')) {
        return;
    }
    
    try {
        const result = await apiCall(`/commands/${commandId}/reject`, 'POST');
        alert(result.message || 'Command rejected');
        loadPendingApprovals();
        loadHistory();
    } catch (error) {
        alert('Error rejecting command: ' + error.message);
    }
}

// Utility function
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Copy to clipboard function
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('API key copied to clipboard!');
    }).catch(err => {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        alert('API key copied to clipboard!');
    });
}

