import sqlite3

DB_PATH = '/Users/pcarff/Documents/_RECIPES/MasterCook 15/My Collection/ModernRecipeApp/data/recipes.db'

def upgrade_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if keywords column exists
    cursor.execute("PRAGMA table_info(recipes)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'keywords' not in columns:
        print("Adding 'keywords' column to recipes table...")
        cursor.execute("ALTER TABLE recipes ADD COLUMN keywords TEXT DEFAULT ''")
        conn.commit()
    else:
        print("'keywords' column already exists.")
        
    conn.close()
    print("Database upgrade complete.")

if __name__ == '__main__':
    upgrade_schema()
