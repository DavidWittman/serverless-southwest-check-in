import os
import sys

# Add ../src to the path so we can import project-local packages without src.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
