import sqlite3

conn = sqlite3.connect('command_gateway.db')
c = conn.cursor()

# Check if admin exists
result = c.execute('SELECT username, api_key, role FROM users WHERE role = ?', ('admin',)).fetchall()
print("Admin users:", result)

# Check all users
all_users = c.execute('SELECT username, api_key, role FROM users').fetchall()
print("All users:", all_users)

conn.close()