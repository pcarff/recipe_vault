import sqlite3
import os

DB_PATH = '/Users/pcarff/Documents/_RECIPES/MasterCook 15/My Collection/ModernRecipeApp/data/recipes.db'

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Recipes Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT,
        yield TEXT,
        prep_time TEXT,
        image_path TEXT
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
