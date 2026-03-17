import sys
import os

# Add project root to sys.path so that tests can import backend.* and server.*
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
