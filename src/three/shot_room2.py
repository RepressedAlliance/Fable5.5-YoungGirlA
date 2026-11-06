"""Same room as shot_room, straight after: sheets of paper slide in under the door, one by one."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import shared_room2 as S2  # noqa: E402
import shot_room  # noqa: E402

if __name__ == "__main__":
    shot_room.run(S2, "room2", True)
