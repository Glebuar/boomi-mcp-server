import sys
from pathlib import Path

# Ensure src layout is discoverable when running tests via importlib mode
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
