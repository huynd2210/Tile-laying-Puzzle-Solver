import sqlite3

def check_database_direct():
    """Use direct SQL queries to examine database structure and content"""
    try:
        conn = sqlite3.connect('polyomino.db')
        cursor = conn.cursor()
        
        # Check for any libraries with 'patchwork' in the name
        print("=== CHECKING FOR PATCHWORK LIBRARIES ===")
        cursor.execute("SELECT * FROM libraries WHERE id LIKE '%patchwork%' OR name LIKE '%Patchwork%'")
        patchwork_libs = cursor.fetchall()
        if patchwork_libs:
            print(f"Found {len(patchwork_libs)} patchwork libraries:")
            for lib in patchwork_libs:
                print(f"  {lib}")
        else:
            print("No patchwork libraries found in the database.")
        
        # Check for pieces associated with any patchwork library
        print("\n=== CHECKING FOR PATCHWORK PIECES ===")
        cursor.execute("SELECT * FROM pieces WHERE library_id LIKE '%patchwork%'")
        patchwork_pieces = cursor.fetchall()
        if patchwork_pieces:
            print(f"Found {len(patchwork_pieces)} pieces in patchwork libraries:")
            for piece in patchwork_pieces:
                print(f"  {piece}")
        else:
            print("No pieces found in patchwork libraries.")
        
        # Get table names to check for any other related tables
        print("\n=== ALL DATABASE TABLES ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  {table[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database directly: {str(e)}")

if __name__ == "__main__":
    check_database_direct() 