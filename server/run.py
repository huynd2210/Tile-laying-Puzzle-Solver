import os
import subprocess
import sys


def run_app():
    """Run the Flask app from server package."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    instance_dir = os.path.join(root_dir, 'instance')
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')
    subprocess.run([sys.executable, app_path])


if __name__ == "__main__":
    run_app()


