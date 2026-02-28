import sqlite3
import os

# Get the absolute path to the directory containing init_db.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'recipes.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Cookbooks Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cookbooks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')
    cursor.execute("INSERT OR IGNORE INTO cookbooks (id, name) VALUES (1, 'Master Cookbook')")

    # Create Categories Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')

    # Create Recipes Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT,
        yield TEXT,
        prep_time TEXT,
        image_path TEXT,
        keywords TEXT DEFAULT '',
        cookbook_id INTEGER REFERENCES cookbooks(id) DEFAULT 1
    )
    ''')

    # Create Recipe Categories Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_categories (
            recipe_id INTEGER,
            category_id INTEGER,
            PRIMARY KEY (recipe_id, category_id),
            FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
        )
    ''')

    
    # Create Ingredients Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER,
        amount TEXT,
        unit TEXT,
        item TEXT,
        FOREIGN KEY(recipe_id) REFERENCES recipes(id)
    )
    ''')
    
    # Create Instructions Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS instructions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER,
        step_number INTEGER,
        text TEXT,
        FOREIGN KEY(recipe_id) REFERENCES recipes(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Database schema initialized successfully using standard sqlite3.")

if __name__ == "__main__":
    init_db()
