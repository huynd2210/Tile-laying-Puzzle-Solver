import sqlite3
import json

def check_database():
    """Run SELECT queries on the database and print the results"""
    try:
        # Connect to the database
        conn = sqlite3.connect('polyomino.db')
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        # Get total library count
        cursor.execute("SELECT COUNT(*) FROM libraries")
        lib_count = cursor.fetchone()[0]
        
        # Get total piece count
        cursor.execute("SELECT COUNT(*) FROM pieces")
        piece_count = cursor.fetchone()[0]
        
        print(f"DATABASE SUMMARY: {lib_count} libraries, {piece_count} total pieces\n")
        
        # Query libraries table
        print("=== LIBRARIES ===")
        cursor.execute("SELECT * FROM libraries ORDER BY name")
        libraries = cursor.fetchall()
        
        for lib in libraries:
            print(f"ID: {lib['id']}, Name: {lib['name']}, Editable: {lib['editable']}")
        
        print("\n=== PIECE COUNTS BY LIBRARY ===")
        for lib in libraries:
            cursor.execute("SELECT COUNT(*) FROM pieces WHERE library_id = ?", (lib['id'],))
            count = cursor.fetchone()[0]
            print(f"Library '{lib['name']}' has {count} pieces")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {str(e)}")

if __name__ == "__main__":
    check_database() 