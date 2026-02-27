import sqlite3
import os
import xml.etree.ElementTree as ET

DB_PATH = '/Users/pcarff/Documents/_RECIPES/MasterCook 15/My Collection/ModernRecipeApp/data/recipes.db'
MX2_PATH = '/Users/pcarff/Documents/_RECIPES/MasterCook 15/My Collection/mz2_work/LCB2_export.mx2'

def create_category_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Creating categories and recipe_categories tables...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_categories (
            recipe_id INTEGER,
            category_id INTEGER,
            PRIMARY KEY (recipe_id, category_id),
            FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

def parse_and_migrate_categories():
    print("Parsing MX2 XML file to extract historical Categories...")
    
    if not os.path.exists(MX2_PATH):
        print(f"Error: Could not find export MX2 at {MX2_PATH}")
        return

    with open(MX2_PATH, 'r', encoding='ISO-8859-1') as f:
        xml_data = f.read()

    xml_data = xml_data.replace('<?xml version="1.0" standalone="yes" encoding="ISO-8859-1"?>', '')
    xml_data = xml_data.replace('<!DOCTYPE mx2 SYSTEM "mx2.dtd">', '')
    xml_data = "<root>" + xml_data.strip() + "</root>"
    
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    recipes_xml = root.findall('.//RcpE')
    print(f"Scanning {len(recipes_xml)} original recipes for categories...")
    
    category_set = set()
    recipe_category_map = {} # Map title -> list of categories

    for recipe in recipes_xml:
        title = recipe.get('name', 'Unknown Recipe').strip()
        cats = recipe.find('CatS')
        if cats is not None:
            tags = [c.text.strip() for c in cats.findall('CatT') if c.text and c.text.strip()]
            if tags:
                recipe_category_map[title] = tags
                for tag in tags:
                    category_set.add(tag)

    print(f"Found {len(category_set)} unique historical categories.")

    # 1. Insert unique categories into 'categories' table
    for cat in category_set:
        cursor.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (cat,))
    conn.commit()
    
    # Pre-fetch category IDs
    cursor.execute('SELECT id, name FROM categories')
    db_categories = {row[1]: row[0] for row in cursor.fetchall()}

    # 2. Link recipes to categories
    # We must match the title in our DB to get the recipe_id
    linked_count = 0
    for title, tags in recipe_category_map.items():
        cursor.execute("SELECT id FROM recipes WHERE title = ?", (title,))
        row = cursor.fetchone()
        if row:
            recipe_id = row[0]
            for tag in tags:
                cat_id = db_categories.get(tag)
                if cat_id:
                    cursor.execute('INSERT OR IGNORE INTO recipe_categories (recipe_id, category_id) VALUES (?, ?)', (recipe_id, cat_id))
                    linked_count += 1

    conn.commit()
    conn.close()
    print(f"Migration complete! Linked {linked_count} category tags to existing recipes in SQLite.")

if __name__ == "__main__":
    create_category_tables()
    parse_and_migrate_categories()
