import sqlite3

DB_PATH = '/Users/pcarff/Documents/_RECIPES/MasterCook 15/My Collection/ModernRecipeApp/data/recipes.db'

def clear_all_images():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE recipes SET image_path = ''")
    conn.commit()
    print(f"Removed image associations from {cursor.rowcount} recipes.")
    conn.close()

if __name__ == "__main__":
    clear_all_images()
