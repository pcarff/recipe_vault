# Recipe Vault (MasterCook 15 Migration)

Welcome to the **Recipe Vault**! This project is a completely modern, lightning-fast, and standalone web application built from the ground up to replace legacy MasterCook software. It securely migrates and stores all your recipes, ingredients, instructions, and images natively without relying on proprietary binary formats.

## 🚀 Key Features Built
* **Native SQLite Database:** All 1,400+ recipes, categories, and cookbooks have been successfully parsed out of MasterCook `.mz2` / `.mx2` XML exports and mapped to a relational SQL database.
* **Modern Web Interface:** A responsive, beautiful Single Page Application (SPA) designed with HTML5, Vanilla JavaScript, and TailwindCSS.
* **Instant Text Search & Filtering:** Filter your entire database instantly by exact text queries, overarching Categories, or isolating specific Cookbooks.
* **Full CRUD Editing System:** Add, edit, or delete recipes freely. Features dynamic rows for ingredients and instructions.
* **"Rapid Image Assigner":** A specialized flashcard dashboard that utilizes smart text-filtering to rapidly link 400+ unassigned legacy images to their rightful recipes with a single click.
* **MZ2 Cookbook Importer:** Drag and drop legacy MasterCook `.mz2` export files directly into the browser. The backend instantly parses the XML nodes and safely ingests all the recipes into the database under a new Cookbook.
* **1-Click Backup & Restore:** Instantly package the entire SQLite database and your entire raw Image library into a portable `.zip` file for safekeeping, and restore it from any computer.

## 💻 Tech Stack
* **Backend:** Native Python 3.10+ (No frameworks required. Uses a lightweight `http.server` subclass with pure SQLite bindings to handle REST API POST/GET operations over port 8080).
* **Frontend:** HTML5, Vanilla JavaScript, TailwindCSS (Runs over port 8000).

---

## 🛠 Installation & Usage Instructions

This application is built to be **100% Cross-Platform**. Since it only relies on Python's standard libraries, there are no complex `pip installs` necessary.

### 🐧 Running on Ubuntu Linux & 🍏 macOS
1. **Clone the repository:**
   ```bash
   git clone https://github.com/pcarff/recipe_vault.git
   cd recipe_vault
   ```
2. **Make the launch script executable:**
   ```bash
   chmod +x start_app.sh
   ```
3. **Launch the application:**
   ```bash
   ./start_app.sh
   ```
   *The script will automatically boot the backend Python API, launch the frontend server, and open `http://localhost:8000` in your default web browser!*

### 🪟 Running on Windows 11
1. Open the `ModernRecipeApp` folder.
2. Double-click the **`start_app.bat`** file.
3. Windows will open a command prompt running the background services and seamlessly open your browser to the application interface.

---

## 📁 System Architecture Summary
* `/data/recipes.db`: Your live database. Back this up frequently!
* `/data/images/`: The folder where all uploaded or re-assigned images are securely copied to protect them from deletion.
* `/backend/server.py`: The brains of the operation. Houses the SQLite connectors, the REST API endpoints, the base64 decoding buffers, and the MZ2 XML parsing algorithms.
* `/frontend/index.html`: The monolithic Single Page Application UI.

**Enjoy your freshly migrated cookbook! 🪄**
