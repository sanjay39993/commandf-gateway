import sqlite3

conn = sqlite3.connect('command_gateway.db')
c = conn.cursor()

# Get table schema
c.execute("PRAGMA table_info(users)")
columns = c.fetchall()
print("Users table columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()