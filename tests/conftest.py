"""Test configuration for pytest."""

import sys
from pathlib import Path

# Add the src directory to Python path so tests can import scraper modules
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
