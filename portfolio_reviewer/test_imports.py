import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
print(f"Parent directory: {parent_dir}")
print(f"Contents: {list(parent_dir.iterdir())}")

sys.path.insert(0, str(parent_dir))

# Try importing
try:
    from schemas.rubric import RubricVersion
    print("✓ Successfully imported schemas.rubric!")
except Exception as e:
    print(f"✗ Failed to import: {e}")