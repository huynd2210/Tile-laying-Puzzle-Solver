import os
import subprocess
import time

def run_app():
    """Reset the database and run the Flask app"""
    
    # First, reset the database
    print("=== Resetting Database ===")
    subprocess.run(["python", "reset_db.py"], check=True)
    
    # Then start the Flask app
    print("\n=== Starting Flask App ===")
    subprocess.run(["python", "app.py"])

if __name__ == "__main__":
    run_app() 