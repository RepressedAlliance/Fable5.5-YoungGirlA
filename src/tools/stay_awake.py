"""Hold a Windows 'system required' request while this project's overnight renders run. Changes no settings;
the request ends with this process. usage: stay_awake.py HOURS"""
import ctypes
import sys
import time

ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
hours = float(sys.argv[1]) if len(sys.argv) > 1 else 8
ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
end = time.time() + hours * 3600
while time.time() < end:
    time.sleep(60)
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
