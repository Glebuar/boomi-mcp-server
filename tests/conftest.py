import sys
from pathlib import Path

# Ensure src layout is discoverable when running tests via importlib mode
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
