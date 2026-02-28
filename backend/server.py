import sqlite3
import json
import os
import base64
import uuid
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import zipfile
import io
import xml.etree.ElementTree as ET

# Get the absolute path to the directory containing server.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'recipes.db')
UPLOADS_DIR = os.path.join(PROJECT_ROOT, 'data', 'images')

os.makedirs(UPLOADS_DIR, exist_ok=True)

IMAGE_DIRS = [
    # Legacy hardcoded paths fallback for graceful degradation
    '/Users/pcarff/Documents/_RECIPES/MasterCook 15/My Collection/Lauras Cookbook 1 (Family Favorites)',
    '/Users/pcarff/Documents/_RECIPES/MasterCook 15/My Collection/Lauras Cookbook 2 (Images Combined)',
    UPLOADS_DIR
]

class RecipeHandler(SimpleHTTPRequestHandler):
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def get_categories(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY name ASC")
        categories = [dict(row) for row in cursor.fetchall()]
        conn.close()
        self.send_json(categories)

    def get_cookbooks(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM cookbooks ORDER BY name ASC")
            cookbooks = [dict(row) for row in cursor.fetchall()]
        except Exception:
            cookbooks = []
        finally:
            conn.close()
        self.send_json(cookbooks)

    def get_unassigned_images(self):
        all_images = []
        for img_dir in IMAGE_DIRS:
            if os.path.exists(img_dir):
                for f in os.listdir(img_dir):
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        all_images.append(f)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT image_path FROM recipes WHERE image_path IS NOT NULL AND image_path != ''")
            assigned_images = set(row[0] for row in cursor.fetchall())
            unassigned = [img for img in all_images if img not in assigned_images]
        except Exception:
            unassigned = all_images
        finally:
            conn.close()
        
        self.send_json(unassigned)

    def get_missing_image_recipe(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            exclude_str = params.get('exclude', [''])[0]
            
            query = "SELECT id, title, keywords FROM recipes WHERE (image_path IS NULL OR image_path = '')"
            query_params = []
            
            if exclude_str:
                exclude_ids = [int(x) for x in exclude_str.split(',') if x.strip().isdigit()]
                if exclude_ids:
                    placeholders = ','.join(['?' for _ in exclude_ids])
                    query += f" AND id NOT IN ({placeholders})"
                    query_params.extend(exclude_ids)
            
            query += " LIMIT 1"
            cursor.execute(query, query_params)
            row = cursor.fetchone()
            recipe = dict(row) if row else None
        except Exception:
            recipe = None
        finally:
            conn.close()
        self.send_json({"recipe": recipe})

    def get_recipes(self):
        query = parse_qs(urlparse(self.path).query)
        search = query.get('q', [''])[0].strip()
        sort_by = query.get('sort', ['recent'])[0]
        cat_id = query.get('category', [''])[0]
        cookbook_id = query.get('cookbook', [''])[0]
        
        offset = 0
        if 'offset' in query:
            try:
                offset = int(query['offset'][0])
            except ValueError:
                pass

        order_clause = "ORDER BY id DESC" # recent
        if sort_by == "oldest":
            order_clause = "ORDER BY id ASC"
        elif sort_by == "title_asc":
            order_clause = "ORDER BY title ASC"
        elif sort_by == "title_desc":
            order_clause = "ORDER BY title DESC"

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        base_query = """
            SELECT DISTINCT r.id, r.title, r.yield, r.prep_time, r.image_path 
            FROM recipes r
            LEFT JOIN recipe_categories rc ON r.id = rc.recipe_id
        """
        
        where_clauses = []
        params = []
        
        if search:
            if search.startswith('"') and search.endswith('"') and len(search) > 2:
                exact_term = search[1:-1]
                where_clauses.append("(r.title LIKE ? OR r.title LIKE ? || ' %' OR r.title LIKE '% ' || ? || ' %' OR r.title LIKE '% ' || ? OR r.keywords LIKE ? OR r.keywords LIKE ? || ',%' OR r.keywords LIKE '%, ' || ? || ',%' OR r.keywords LIKE '%, ' || ?)")
                params.extend([exact_term] * 8)
            else:
                where_clauses.append("(r.title LIKE ? OR r.keywords LIKE ?)")
                params.extend([f'%{search}%', f'%{search}%'])
                
        if cat_id:
            where_clauses.append("rc.category_id = ?")
            params.append(int(cat_id))

        if cookbook_id:
            where_clauses.append("r.cookbook_id = ?")
            params.append(int(cookbook_id))

        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)
            
        base_query += f" {order_clause} LIMIT 60 OFFSET ?"
        params.append(offset)

        cursor.execute(base_query, params)
        recipes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        self.send_json(recipes)
        
    def get_recipe(self, recipe_id):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(recipes)")
        has_keywords = any(row[1] == 'keywords' for row in cursor.fetchall())
        
        cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
        row = cursor.fetchone()
        if not row:
            self.send_response(404)
            self.end_headers()
            return
            
        recipe = dict(row)
        if not has_keywords:
            recipe['keywords'] = ''
        
        cursor.execute("SELECT amount, unit, item FROM ingredients WHERE recipe_id = ?", (recipe_id,))
        recipe['ingredients'] = [dict(r) for r in cursor.fetchall()]
        
        cursor.execute("SELECT step_number, text FROM instructions WHERE recipe_id = ? ORDER BY step_number", (recipe_id,))
        recipe['instructions'] = [dict(r) for r in cursor.fetchall()]
        
        # Get attached categories
        cursor.execute("""
            SELECT c.id, c.name FROM categories c
            JOIN recipe_categories rc ON c.id = rc.category_id
            WHERE rc.recipe_id = ?
        """, (recipe_id,))
        recipe['categories'] = [dict(r) for r in cursor.fetchall()]
        
        conn.close()
        self.send_json(recipe)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/categories':
            self.get_categories()
        elif parsed.path == '/api/cookbooks':
            self.get_cookbooks()
        elif parsed.path == '/api/images/unassigned':
            self.get_unassigned_images()
        elif parsed.path == '/api/recipes/missing_image':
            self.get_missing_image_recipe()
        elif parsed.path == '/api/recipes':
            self.get_recipes()
        elif parsed.path == '/api/backup':
            self.send_response(200)
            self.send_header('Content-type', 'application/zip')
            self.send_header('Content-Disposition', 'attachment; filename="RecipeVault_Backup.zip"')
            self.end_headers()
            
            # Create an in-memory ZIP file
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add database
                if os.path.exists(DB_PATH):
                    zipf.write(DB_PATH, arcname='data/recipes.db')
                    
                # Add images
                if os.path.exists(UPLOADS_DIR):
                    for root, _, files in os.walk(UPLOADS_DIR):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # calculate relative path within UPLOADS_DIR
                            rel_path = os.path.relpath(file_path, UPLOADS_DIR)
                            zipf.write(file_path, arcname=f'data/images/{rel_path}')
                            
            self.wfile.write(zip_buffer.getvalue())
        elif parsed.path.startswith('/api/recipes/'):
            recipe_id = int(parsed.path.split('/')[-1])
            self.get_recipe(recipe_id)
        elif parsed.path.startswith('/images/'):
            filename = parsed.path.split('/')[-1]
            filepath = None
            for d in IMAGE_DIRS:
                test_path = os.path.join(d, filename)
                if os.path.exists(test_path):
                    filepath = test_path
                    break
            
            if filepath:
                self.send_response(200)
                if filename.endswith('.png'):
                    self.send_header('Content-Type', 'image/png')
                else:
                    self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(filepath, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            super().do_GET()

    def process_image_upload(self, data):
        if data.get('image_base64'):
            try:
                header, encoded = data['image_base64'].split(',', 1)
                file_ext = data.get('image_filename', 'image.jpg').split('.')[-1]
                new_filename = f"{uuid.uuid4().hex}.{file_ext}"
                filepath = os.path.join(UPLOADS_DIR, new_filename)
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(encoded))
                data['image_path'] = new_filename
            except Exception as e:
                print("Error decoding image:", e)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/restore':
            content_length = int(self.headers['Content-Length'])
            zip_data = self.rfile.read(content_length)
            try:
                with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zipf:
                    for info in zipf.infolist():
                        if info.filename == 'data/recipes.db':
                            with open(DB_PATH, 'wb') as f:
                                f.write(zipf.read(info.filename))
                        elif info.filename.startswith('data/images/'):
                            rel_path = info.filename.replace('data/images/', '')
                            if rel_path:
                                out_path = os.path.join(UPLOADS_DIR, rel_path)
                                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                                with open(out_path, 'wb') as f:
                                    f.write(zipf.read(info.filename))
                self.send_json({'status': 'success'})
            except Exception as e:
                print(e)
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
            return

        elif parsed.path == '/api/import_mz2':
            content_length = int(self.headers['Content-Length'])
            max_bytes = 200 * 1024 * 1024 # 200MB limit for MZ2 zips
            if content_length > max_bytes:
                self.send_response(413) # Payload Too Large
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': 'File exceeds 200MB limit'}).encode('utf-8'))
                return
                
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                filename = data.get('filename', 'Imported Cookbook')
                cookbook_name = filename.replace('.mz2', '').replace('.mx2', '').strip()
                
                # Decode and extract ZIP if it's an .mz2
                file_content_bytes = base64.b64decode(data['content'])
                try:
                    with zipfile.ZipFile(io.BytesIO(file_content_bytes), 'r') as zipf:
                        xml_filename = None
                        for info in zipf.infolist():
                            if info.filename.lower().endswith(('.mx2', '.mz2', '.xml')):
                                xml_filename = info.filename
                            elif info.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                                out_path = os.path.join(UPLOADS_DIR, info.filename)
                                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                                with open(out_path, 'wb') as f:
                                    f.write(zipf.read(info.filename))
                        if xml_filename:
                            file_content = zipf.read(xml_filename).decode('ISO-8859-1', errors='ignore')
                        else:
                            raise Exception("No XML or MX2 file found inside MZ2 package")
                except zipfile.BadZipFile:
                    # Fallback for plain XML text
                    file_content = file_content_bytes.decode('ISO-8859-1', errors='ignore')
                
                # Cleanup and parse
                file_content = file_content.replace('<?xml version="1.0" standalone="yes" encoding="ISO-8859-1"?>', '')
                file_content = file_content.replace('<!DOCTYPE mx2 SYSTEM "mx2.dtd">', '')
                if not file_content.strip().startswith('<root>'):
                    file_content = "<root>" + file_content.strip() + "</root>"
                
                root = ET.fromstring(file_content)
                recipes = root.findall('.//RcpE')
                
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                cursor.execute('INSERT OR IGNORE INTO cookbooks (name) VALUES (?)', (cookbook_name,))
                cursor.execute('SELECT id FROM cookbooks WHERE name = ?', (cookbook_name,))
                cookbook_id = cursor.fetchone()[0]
                
                migrated = 0
                for recipe in recipes:
                    title = recipe.get('name', 'Unknown Recipe')
                    author = recipe.get('author', '')
                    img_filename = recipe.get('img', '')
                    
                    yld = ''
                    yld_elem = recipe.find('Yield')
                    if yld_elem is not None:
                        yld = yld_elem.text or ''
                    
                    rcp_categories = set()
                    cat_divs = recipe.findall('.//CatS/CatT')
                    for cat in cat_divs:
                        c_name = cat.get('name', '').strip()
                        if c_name:
                            cursor.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (c_name,))
                            cursor.execute('SELECT id FROM categories WHERE name = ?', (c_name,))
                            cat_row = cursor.fetchone()
                            if cat_row:
                                rcp_categories.add(cat_row[0])

                    cursor.execute(
                        'INSERT INTO recipes (title, author, yield, prep_time, image_path, cookbook_id) VALUES (?, ?, ?, ?, ?, ?)',
                        (title, author, yld, '', img_filename, cookbook_id)
                    )
                    recipe_id = cursor.lastrowid
                    
                    for cat_id in rcp_categories:
                        cursor.execute('INSERT INTO recipe_categories (recipe_id, category_id) VALUES (?, ?)', (recipe_id, cat_id))
                    
                    for ing in recipe.findall('.//IngR'):
                        name = ing.get('name', '')
                        unit = ing.get('unit', '')
                        qty = ing.get('qty', '')
                        if name or qty:
                            cursor.execute(
                                'INSERT INTO ingredients (recipe_id, amount, unit, item) VALUES (?, ?, ?, ?)',
                                (recipe_id, qty, unit, name)
                            )
                            
                    dirs = recipe.find('.//DirS')
                    if dirs is not None:
                        steps = dirs.findall('DirT')
                        for i, step in enumerate(steps):
                            text = step.text or step.get('text', '')
                            if text:
                                cursor.execute(
                                    'INSERT INTO instructions (recipe_id, step_number, text) VALUES (?, ?, ?)',
                                    (recipe_id, i+1, text.strip())
                                )
                    migrated += 1
                
                conn.commit()
                self.send_json({"status": "success", "imported": migrated, "cookbook": cookbook_name})
            except Exception as e:
                print(e)
                if 'conn' in locals():
                    conn.rollback()
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
            finally:
                if 'conn' in locals():
                    conn.close()

        elif parsed.path == '/api/categories':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO categories (name) VALUES (?)', (data.get('name', 'New Category'),))
                conn.commit()
                self.send_json({"id": cursor.lastrowid, "status": "success"})
            except sqlite3.IntegrityError:
                self.send_response(400) # Duplicate name
                self.end_headers()
            except Exception as e:
                print(e)
                self.send_response(500)
                self.end_headers()
            finally:
                conn.close()

        elif parsed.path == '/api/cookbooks':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO cookbooks (name) VALUES (?)', (data.get('name', 'New Cookbook'),))
                conn.commit()
                self.send_json({"id": cursor.lastrowid, "status": "success"})
            except sqlite3.IntegrityError:
                self.send_response(400) # Duplicate name
                self.end_headers()
            except Exception as e:
                print(e)
                self.send_response(500)
                self.end_headers()
            finally:
                conn.close()

        elif parsed.path == '/api/recipes':
            content_length = int(self.headers['Content-Length'])
            max_bytes = 50 * 1024 * 1024 # 50MB limit
            if content_length > max_bytes:
                 self.send_response(413) # Payload too large
                 self.send_header('Content-Type', 'application/json')
                 self.send_header('Access-Control-Allow-Origin', '*')
                 self.end_headers()
                 self.wfile.write(json.dumps({'status': 'error', 'message': 'Payload exceeds 50MB limit'}).encode('utf-8'))
                 return

            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            self.process_image_upload(data)
            image_path = data.get('image_path', '')
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO recipes (title, author, yield, prep_time, image_path, keywords, cookbook_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (data.get('title', 'Untitled'), data.get('author', ''), data.get('yield', ''), data.get('prep_time', ''), image_path, data.get('keywords', ''), data.get('cookbook_id', 1))
                )
                recipe_id = cursor.lastrowid
                
                for ing in data.get('ingredients', []):
                    if ing.get('item'):
                        cursor.execute('INSERT INTO ingredients (recipe_id, amount, unit, item) VALUES (?, ?, ?, ?)',
                            (recipe_id, ing.get('amount', ''), ing.get('unit', ''), ing.get('item', '')))
                
                for i, step in enumerate(data.get('instructions', [])):
                    if step.get('text'):
                        cursor.execute('INSERT INTO instructions (recipe_id, step_number, text) VALUES (?, ?, ?)',
                            (recipe_id, i+1, step.get('text', '')))
                        
                for cat_id in data.get('category_ids', []):
                    cursor.execute('INSERT INTO recipe_categories (recipe_id, category_id) VALUES (?, ?)', (recipe_id, cat_id))
                        
                conn.commit()
                self.send_json({"id": recipe_id, "status": "success"})
            except Exception as e:
                conn.rollback()
                print(e)
                self.send_response(500)
                self.end_headers()
            finally:
                conn.close()

    def do_PUT(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/categories/'):
            cat_id = int(parsed.path.split('/')[-1])
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            try:
                cursor.execute('UPDATE categories SET name=? WHERE id=?', (data.get('name', 'Changed'), cat_id))
                conn.commit()
                self.send_json({"id": cat_id, "status": "success"})
            except sqlite3.IntegrityError:
                self.send_response(400) # Duplicate name
                self.end_headers()
            except Exception as e:
                print(e)
                self.send_response(500)
                self.end_headers()
            finally:
                conn.close()

        elif parsed.path.startswith('/api/cookbooks/'):
            cb_id = int(parsed.path.split('/')[-1])
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            try:
                cursor.execute('UPDATE cookbooks SET name=? WHERE id=?', (data.get('name', 'Changed'), cb_id))
                conn.commit()
                self.send_json({"id": cb_id, "status": "success"})
            except sqlite3.IntegrityError:
                self.send_response(400) # Duplicate name
                self.end_headers()
            except Exception as e:
                print(e)
                self.send_response(500)
                self.end_headers()
            finally:
                conn.close()

        elif parsed.path.startswith('/api/recipes/'):
            path_parts = parsed.path.split('/')
            
            # Check if this is a fast one-column image assigner PUT /api/recipes/<id>/image
            if len(path_parts) == 5 and path_parts[4] == 'image':
                recipe_id = int(path_parts[3])
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)
                
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                try:
                    cursor.execute('UPDATE recipes SET image_path=? WHERE id=?', (data.get('image_path', ''), recipe_id))
                    conn.commit()
                    self.send_json({"status": "success", "id": recipe_id})
                except Exception as e:
                    print(e)
                    self.send_response(500)
                    self.end_headers()
                finally:
                    conn.close()
                return

            recipe_id = int(path_parts[-1])
            content_length = int(self.headers['Content-Length'])
            max_bytes = 50 * 1024 * 1024 # 50MB limit
            if content_length > max_bytes:
                 self.send_response(413) # Payload too large
                 self.send_header('Content-Type', 'application/json')
                 self.send_header('Access-Control-Allow-Origin', '*')
                 self.end_headers()
                 self.wfile.write(json.dumps({'status': 'error', 'message': 'Payload exceeds 50MB limit'}).encode('utf-8'))
                 return

            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            self.process_image_upload(data)
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            try:
                if 'image_path' in data:
                    cursor.execute(
                        'UPDATE recipes SET title=?, author=?, yield=?, prep_time=?, image_path=?, keywords=?, cookbook_id=? WHERE id=?',
                        (data.get('title', 'Untitled'), data.get('author', ''), data.get('yield', ''), data.get('prep_time', ''), data['image_path'], data.get('keywords', ''), data.get('cookbook_id', 1), recipe_id)
                    )
                else:
                    cursor.execute(
                        'UPDATE recipes SET title=?, author=?, yield=?, prep_time=?, keywords=?, cookbook_id=? WHERE id=?',
                        (data.get('title', 'Untitled'), data.get('author', ''), data.get('yield', ''), data.get('prep_time', ''), data.get('keywords', ''), data.get('cookbook_id', 1), recipe_id)
                    )
                
                cursor.execute('DELETE FROM ingredients WHERE recipe_id=?', (recipe_id,))
                for ing in data.get('ingredients', []):
                    if ing.get('item'):
                        cursor.execute('INSERT INTO ingredients (recipe_id, amount, unit, item) VALUES (?, ?, ?, ?)',
                            (recipe_id, ing.get('amount', ''), ing.get('unit', ''), ing.get('item', '')))
                
                cursor.execute('DELETE FROM instructions WHERE recipe_id=?', (recipe_id,))
                for i, step in enumerate(data.get('instructions', [])):
                    if step.get('text'):
                        cursor.execute('INSERT INTO instructions (recipe_id, step_number, text) VALUES (?, ?, ?)',
                            (recipe_id, i+1, step.get('text', '')))
                        
                cursor.execute('DELETE FROM recipe_categories WHERE recipe_id=?', (recipe_id,))
                for cat_id in data.get('category_ids', []):
                    cursor.execute('INSERT INTO recipe_categories (recipe_id, category_id) VALUES (?, ?)', (recipe_id, cat_id))
                        
                conn.commit()
                self.send_json({"id": recipe_id, "status": "success"})
            except Exception as e:
                conn.rollback()
                print(e)
                self.send_response(500)
                self.end_headers()
            finally:
                conn.close()

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/categories/'):
             cat_id = int(parsed.path.split('/')[-1])
             conn = sqlite3.connect(DB_PATH)
             cursor = conn.cursor()
             try:
                 cursor.execute('DELETE FROM categories WHERE id = ?', (cat_id,))
                 conn.commit()
                 self.send_json({"status": "success"})
             except Exception as e:
                 conn.rollback()
                 print(e)
                 self.send_response(500)
                 self.end_headers()
             finally:
                 conn.close()

        elif parsed.path.startswith('/api/cookbooks/'):
             cb_id = int(parsed.path.split('/')[-1])
             conn = sqlite3.connect(DB_PATH)
             cursor = conn.cursor()
             try:
                 cursor.execute('DELETE FROM cookbooks WHERE id = ?', (cb_id,))
                 # Move orphaned recipes to default cookbook (ID 1)
                 cursor.execute('UPDATE recipes SET cookbook_id = 1 WHERE cookbook_id = ?', (cb_id,))
                 conn.commit()
                 self.send_json({"status": "success"})
             except Exception as e:
                 conn.rollback()
                 print(e)
                 self.send_response(500)
                 self.end_headers()
             finally:
                 conn.close()

        elif parsed.path.startswith('/api/recipes/'):
            recipe_id = int(parsed.path.split('/')[-1])
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            try:
                cursor.execute('DELETE FROM ingredients WHERE recipe_id = ?', (recipe_id,))
                cursor.execute('DELETE FROM instructions WHERE recipe_id = ?', (recipe_id,))
                cursor.execute('DELETE FROM recipe_categories WHERE recipe_id = ?', (recipe_id,))
                cursor.execute('DELETE FROM recipes WHERE id = ?', (recipe_id,))
                conn.commit()
                self.send_json({"status": "success"})
            except Exception as e:
                conn.rollback()
                print(e)
                self.send_response(500)
                self.end_headers()
            finally:
                conn.close()

if __name__ == '__main__':
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, RecipeHandler)
    print("Serving API and App on port 8080...")
    httpd.serve_forever()
