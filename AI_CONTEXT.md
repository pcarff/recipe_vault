# Antigravity AI Context Sync

**Date:** February 27, 2026
**Project:** Recipe Vault (MasterCook 15 Migration)
**Status:** MVP Finished & Deployed

## To My Future Self (Antigravity on Ubuntu)
If you are reading this, the user has successfully cloned this repository onto their new Ubuntu Linux machine and resumed development. Here is exactly what we have built so far and how the architecture works so you don't break anything:

### 1. The Architecture Rules (CRITICAL)
* **Zero External Frameworks:** The backend is written in pure Python 3.10+ using a custom subclass of `http.server.SimpleHTTPRequestHandler`. Do **NOT** try to install Flask, FastAPI, or Django. You must write raw byte-handling logic in `server.py` `do_GET` and `do_POST`.
* **Zero Node.js:** The frontend is a pure HTML, Vanilla JS, and TailwindCSS via CDN architecture `index.html`. Do **NOT** use React, Vue, npm, or Webpack.
* **Database:** It strictly uses `sqlite3` natively. The DB is stored at `data/recipes.db`.

### 2. Core Features Implemented
* **MasterCook MZ2 Import:** In `/api/import_mz2`, we use `xml.etree` to parse legacy XML files natively and insert them dynamically. Base64 XML buffers are passed from the browser natively using `FileReader.readAsDataURL()`.
* **Images:** Uploaded images are stored in `data/images/`. We have a `Rapid Assigner` modal in `index.html` that lets the user swipe through unassigned photos and natively maps them via `PUT /api/recipes/<id>/image`.
* **Cookbooks & Categories:** Recipes are fully relational to a `cookbooks` table and a many-to-many `categories` table.
* **ZIP Backups:** `/api/backup` generates a `.zip` in-memory using `io.BytesIO` containing the database and images, throwing it to the browser as a download attachment.

### 3. Next Steps
The user just completed the massive migration from Windows MasterCook 15 to this local web app. 
Do not suggest rewriting the stack. Read `server.py` and `index.html` closely to match the existing coding style (raw DOM manipulation and Python `send_response` loops) when assisting them with any new features!
