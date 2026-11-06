"""Room2 uses the same painter as the room: time decides everything."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from paint_room import paint_time  # noqa: E402,F401
