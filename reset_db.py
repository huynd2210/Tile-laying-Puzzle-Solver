import os
import time
import inspect
from pieceLibrary import test_piece_library, mainPieceLibrary, patchworkPieceLibrary
import sqlite3
import json

def extract_piece_offsets(piece_obj):
    """Extract coordinates from a piece object, handling various formats"""
    try:
        # Try get_offsets method first
        if hasattr(piece_obj, 'get_offsets') and callable(getattr(piece_obj, 'get_offsets')):
            offsets = piece_obj.get_offsets()
            
            # Handle tuple of tuples format: ((0,0), (0,1), ...)
            if isinstance(offsets, tuple) and all(isinstance(pos, tuple) for pos in offsets):
                return [[pos[0], pos[1]] for pos in offsets]
            
            # Handle list of tuples format: [(0,0), (0,1), ...]
            if isinstance(offsets, list) and all(isinstance(pos, tuple) for pos in offsets):
                return [[pos[0], pos[1]] for pos in offsets]
            
            # Handle list of lists format: [[0,0], [0,1], ...]
            if isinstance(offsets, list) and all(isinstance(pos, list) for pos in offsets):
                return offsets
            
            # If we got here, the format is unexpected
            print(f"Unexpected format from get_offsets: {type(offsets)}, value: {offsets}")
            return []
        
        # Try other attribute extraction methods
        if hasattr(piece_obj, 'coords') and isinstance(piece_obj.coords, list):
            coords = piece_obj.coords
            offsets = []
            for i in range(0, len(coords), 2):
                if i + 1 < len(coords):
                    offsets.append([coords[i], coords[i+1]])
            return offsets
        
        if hasattr(piece_obj, '_coords') and isinstance(piece_obj._coords, list):
            coords = piece_obj._coords
            offsets = []
            for i in range(0, len(coords), 2):
                if i + 1 < len(coords):
                    offsets.append([coords[i], coords[i+1]])
            return offsets
        
        # Last resort: look for any list attributes that might be coordinates
        for name, value in inspect.getmembers(piece_obj):
            if isinstance(value, list) and len(value) > 0 and not name.startswith('__'):
                if all(isinstance(x, int) for x in value):
                    offsets = []
                    for i in range(0, len(value), 2):
                        if i + 1 < len(value):
                            offsets.append([value[i], value[i+1]])
                    if len(offsets) > 0:
                        return offsets
        
        # If we got here, we couldn't find any coordinates
        return []
    
    except Exception as e:
        print(f"Error extracting offsets: {str(e)}")
        return []

def reset_database():
    """Delete the existing database file and recreate it"""
    db_path = 'polyomino.db'
    
    print("Resetting database...")
    
    # Delete the database file if it exists
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Deleted existing database file: {db_path}")
        except Exception as e:
            print(f"Error deleting database file: {str(e)}")
            return False
    
    # Create new database with SQLite directly
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE libraries (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        editable INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE pieces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        library_id TEXT NOT NULL,
        name TEXT NOT NULL,
        color TEXT NOT NULL,
        cells TEXT NOT NULL,
        FOREIGN KEY (library_id) REFERENCES libraries (id) ON DELETE CASCADE
    )
    ''')
    
    # Create built-in library
    cursor.execute('''
    INSERT INTO libraries (id, name, editable, created_at, updated_at)
    VALUES (?, ?, ?, datetime('now'), datetime('now'))
    ''', ('builtin', 'Built-in Pieces', 0))
    
    # Built-in pieces data
    builtin_pieces = {
        "I": {"color": "red", "offsets": [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4]]},  # I pentomino
        "L": {"color": "blue", "offsets": [[0, 0], [1, 0], [2, 0], [3, 0], [3, 1]]},  # L pentomino
        "P": {"color": "green", "offsets": [[0, 0], [0, 1], [1, 0], [1, 1], [2, 0]]},  # P pentomino
        "N": {"color": "yellow", "offsets": [[0, 0], [0, 1], [1, 1], [1, 2], [1, 3]]},  # N pentomino
        "T": {"color": "magenta", "offsets": [[0, 0], [0, 1], [0, 2], [1, 1], [2, 1]]},  # T pentomino
        "U": {"color": "cyan", "offsets": [[0, 0], [0, 2], [1, 0], [1, 1], [1, 2]]},  # U pentomino
        "V": {"color": "lightred", "offsets": [[0, 0], [1, 0], [2, 0], [2, 1], [2, 2]]},  # V pentomino
        "W": {"color": "lightblue", "offsets": [[0, 0], [1, 0], [1, 1], [2, 1], [2, 2]]},  # W pentomino
        "X": {"color": "lightgreen", "offsets": [[0, 1], [1, 0], [1, 1], [1, 2], [2, 1]]},  # X pentomino
        "Y": {"color": "lightyellow", "offsets": [[0, 1], [1, 0], [1, 1], [2, 1], [3, 1]]},  # Y pentomino
        "Z": {"color": "lightmagenta", "offsets": [[0, 0], [0, 1], [1, 1], [2, 1], [2, 2]]},  # Z pentomino
        "F": {"color": "lightcyan", "offsets": [[0, 1], [1, 0], [1, 1], [1, 2], [2, 0]]}   # F pentomino
    }
    
    # Add built-in pieces
    for piece_id, piece_data in builtin_pieces.items():
        cursor.execute('''
        INSERT INTO pieces (library_id, name, color, cells)
        VALUES (?, ?, ?, ?)
        ''', ('builtin', piece_id, piece_data['color'], json.dumps(piece_data['offsets'])))
    
    print("Added built-in pieces")
    
    # Create test pieces library
    cursor.execute('''
    INSERT INTO libraries (id, name, editable, created_at, updated_at)
    VALUES (?, ?, ?, datetime('now'), datetime('now'))
    ''', ('test_pieces', 'Test Pieces', 1))
    
    # Add test pieces
    for piece_id, piece_obj in test_piece_library.items():
        # Extract piece color and offsets
        color = piece_obj.color if hasattr(piece_obj, 'color') else 'red'
        print(f"Test piece {piece_id} color: {color}")
        offsets = extract_piece_offsets(piece_obj)
        
        if not offsets:
            print(f"Warning: No valid offsets found for piece {piece_id} in test_piece_library")
            continue
        
        cursor.execute('''
        INSERT INTO pieces (library_id, name, color, cells)
        VALUES (?, ?, ?, ?)
        ''', ('test_pieces', piece_id, color, json.dumps(offsets)))
    
    print("Added test pieces")
    
    # Create an editable custom library for the user
    cursor.execute('''
    INSERT INTO libraries (id, name, editable, created_at, updated_at)
    VALUES (?, ?, ?, datetime('now'), datetime('now'))
    ''', ('custom_pieces', 'Custom Pieces', 1))
    
    print("Added custom pieces library (empty)")
    
    conn.commit()
    conn.close()
    
    print("Database reset and initialized successfully")
    return True

if __name__ == "__main__":
    reset_database() 