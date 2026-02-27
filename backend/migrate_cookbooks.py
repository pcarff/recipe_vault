import sqlite3
import os

DB_PATH = '/Users/pcarff/Documents/_RECIPES/MasterCook 15/My Collection/ModernRecipeApp/data/recipes.db'

def run_migration():
    if not os.path.exists(DB_PATH):
        print("Database not found. Nothing to migrate.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if cookbook_id exists in recipes table
        cursor.execute("PRAGMA table_info(recipes)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'cookbook_id' in columns:
            print("Migration already applied. cookbook_id exists.")
            return

        print("Creating cookbooks table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cookbooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')

        print("Adding default cookbook...")
        cursor.execute("INSERT OR IGNORE INTO cookbooks (id, name) VALUES (1, 'Master Cookbook')")

        print("Adding cookbook_id column to recipes...")
        cursor.execute("ALTER TABLE recipes ADD COLUMN cookbook_id INTEGER REFERENCES cookbooks(id)")

        print("Assigning all existing recipes to 'Master Cookbook'...")
        cursor.execute("UPDATE recipes SET cookbook_id = 1 WHERE cookbook_id IS NULL")

        conn.commit()
        print("Migration successful!")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
