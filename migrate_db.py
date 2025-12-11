import sqlite3

def migrate_database():
    conn = sqlite3.connect('command_gateway.db')
    c = conn.cursor()
    
    # Check if tier column exists
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    
    print(f"Current columns: {columns}")
    
    # Add missing columns if they don't exist
    if 'tier' not in columns:
        print("Adding tier column...")
        c.execute("ALTER TABLE users ADD COLUMN tier TEXT DEFAULT 'junior' CHECK(tier IN ('junior', 'mid', 'senior', 'lead'))")
    
    if 'email' not in columns:
        print("Adding email column...")
        c.execute("ALTER TABLE users ADD COLUMN email TEXT")
    
    if 'telegram_chat_id' not in columns:
        print("Adding telegram_chat_id column...")
        c.execute("ALTER TABLE users ADD COLUMN telegram_chat_id TEXT")
    
    conn.commit()
    
    # Verify the changes
    c.execute("PRAGMA table_info(users)")
    new_columns = c.fetchall()
    print("\nUpdated columns:")
    for col in new_columns:
        print(f"  {col[1]} ({col[2]})")
    
    conn.close()
    print("\nMigration completed!")

if __name__ == "__main__":
    migrate_database()