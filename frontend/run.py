import os
import subprocess
import sys

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_app():
    """Run the Flask app without resetting the database"""
    
    # Get the parent directory
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Make sure instance directory exists
    instance_dir = os.path.join(parent_dir, 'instance')
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
    
    # Start the Flask app
    print("=== Starting Flask App ===")
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
    subprocess.run([sys.executable, app_path])

if __name__ == "__main__":
    run_app() 