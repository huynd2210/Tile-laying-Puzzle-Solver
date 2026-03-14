from flask import Flask, render_template
from flask_cors import CORS
import os
import sys

# Ensure project root on path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from server.json_storage import (
    current_iso_time,
    ensure_storage_initialized,
    load_libraries_index,
    save_libraries_index,
)

app = Flask(__name__, static_folder=os.path.join(ROOT_DIR, 'frontend', 'static'), template_folder=os.path.join(ROOT_DIR, 'frontend', 'templates'))
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)
CORS(app)

# Import and register blueprints
from server.routes.solve_api import solve_api
from server.routes.libraries_api import libraries_api

app.register_blueprint(solve_api)
app.register_blueprint(libraries_api)

def _ensure_builtin_library():
    libraries = load_libraries_index()
    if not any(lib.get('id') == 'builtin' for lib in libraries):
        libraries.append({
            'id': 'builtin',
            'name': 'Built-in Pieces',
            'editable': False,
            'created_at': current_iso_time(),
            'updated_at': current_iso_time()
        })
        save_libraries_index(libraries)

def initialize_storage():
    ensure_storage_initialized()
    _ensure_builtin_library()

@app.route('/')
def index():
    return render_template('index.html')

def create_app():
    initialize_storage()
    return app

if __name__ == '__main__':
    initialize_storage()
    app.run(debug=True)
