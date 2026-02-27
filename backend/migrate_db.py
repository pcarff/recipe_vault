import os
import sqlite3
import xml.etree.ElementTree as ET

DB_PATH = '/Users/pcarff/Documents/_RECIPES/MasterCook 15/My Collection/ModernRecipeApp/data/recipes.db'
MX2_PATH = '/Users/pcarff/Documents/_RECIPES/MasterCook 15/My Collection/mz2_work/LCB2_export.mx2'
IMAGES_DIR = '/Users/pcarff/Documents/_RECIPES/MasterCook 15/My Collection/Lauras Cookbook 2 (Images Combined)'

def parse_and_migrate():
    print("Parsing MX2 XML file...")
    
    with open(MX2_PATH, 'r', encoding='ISO-8859-1') as f:
        xml_data = f.read()

    # The MX2 file starts with <?xml ...> and <!DOCTYPE ...>
    # We need to strip these if we are going to wrap it in <root>
    xml_data = xml_data.replace('<?xml version="1.0" standalone="yes" encoding="ISO-8859-1"?>', '')
    xml_data = xml_data.replace('<!DOCTYPE mx2 SYSTEM "mx2.dtd">', '')
    
    # Wrap in root to ensure a single parent node
    xml_data = "<root>" + xml_data.strip() + "</root>"
    
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    recipes = root.findall('.//RcpE')
    print(f"Found {len(recipes)} recipes to migrate.")
    
    images = sorted([img for img in os.listdir(IMAGES_DIR) if img.endswith('.png')])
    img_idx = 0
    migrated_count = 0

    for recipe in recipes:
        # Basic Info
        title = recipe.get('name', 'Unknown Recipe')
        author = recipe.get('author', '')
        
        # In MasterCook MX2, Yield is usually an attribute or a simple node, let's look for both
        yld = ''
        yld_elem = recipe.find('Yield')
        if yld_elem is not None:
            yld = yld_elem.text or ''

        # Map an image sequentially
        image_path = ''
        if img_idx < len(images):
            image_path = images[img_idx]
            img_idx += 1
            
        # Insert Recipe
        cursor.execute(
            'INSERT INTO recipes (title, author, yield, prep_time, image_path) VALUES (?, ?, ?, ?, ?)',
            (title, author, yld, '', image_path)
        )
        recipe_id = cursor.lastrowid
        
        # Insert Ingredients (MX2 uses <IngR name="..." unit="..." qty="...">)
        for ing in recipe.findall('IngR'):
            name = ing.get('name', '')
            unit = ing.get('unit', '')
            qty = ing.get('qty', '')
            
            if name or qty:
                cursor.execute(
                    'INSERT INTO ingredients (recipe_id, amount, unit, item) VALUES (?, ?, ?, ?)',
                    (recipe_id, qty, unit, name)
                )
                
        # Insert Instructions
        dirs = recipe.find('DirS')
        if dirs is not None:
            steps = dirs.findall('DirT')
            for i, step in enumerate(steps):
                text = step.text or step.get('text', '')
                if text:
                    cursor.execute(
                        'INSERT INTO instructions (recipe_id, step_number, text) VALUES (?, ?, ?)',
                        (recipe_id, i+1, text.strip())
                    )
        migrated_count += 1

    conn.commit()
    conn.close()
    print(f"Migration complete! {migrated_count} recipes loaded into SQLite.")

if __name__ == "__main__":
    parse_and_migrate()
