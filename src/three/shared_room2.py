"""Timing for room2: the same room straight after the knocking, with sheets coming in under the door."""
from shared_room import *  # noqa: F401,F403
import shared_room as _R

T0, T1 = _R.T1, _R.T2


def frames_all():
    return list(range(0, int(round((T1 - T0) * 60)), 2))   # the film runs at 30 fps
