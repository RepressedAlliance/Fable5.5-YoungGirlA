"""Log GPU power and temperature every 10 s while a job runs; stop the job's Blender if the GPU gets too hot.
usage: gpu_watch.py LOG.csv   (runs until killed)"""
import subprocess
import sys
import time

LIMIT_C = 90
Q = "timestamp,utilization.gpu,power.draw,temperature.gpu,clocks.gr,memory.used"
with open(sys.argv[1], "a", encoding="utf-8") as f:
    while True:
        line = subprocess.run(["nvidia-smi", f"--query-gpu={Q}", "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
        f.write(line + "\n")
        f.flush()
        try:
            temp = int(line.split(",")[3])
        except (IndexError, ValueError):
            temp = 0
        if temp >= LIMIT_C:
            f.write(f"TOO HOT {temp}, stopping blender\n")
            f.flush()
            subprocess.run(["taskkill", "/IM", "blender.exe", "/F"], capture_output=True)
        time.sleep(10)
