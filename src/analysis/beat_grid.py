"""Fine constant-tempo beat grid by comb search over the onset envelope.

The song is programmed at a fixed tempo, so one (period, phase) explains every beat.
Score = mean onset strength sampled at grid points; refine globally, then check drift
per 30 s window. Updates work/analysis/audio.json (beats, bars, bpm).
"""
import json
from pathlib import Path

import librosa
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
WAV = ROOT / "work" / "analysis" / "song.wav"
AJ = ROOT / "work" / "analysis" / "audio.json"


def main():
    y, sr = librosa.load(WAV, sr=22050, mono=True)
    hop = 64
    env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop, aggregate=np.median)
    env = env / env.max()
    fps = sr / hop
    t_env = np.arange(len(env)) / fps
    t0, t1 = 22.0, 232.0  # band playing

    def score(P, ph, a=t0, b=t1):
        g = np.arange(ph + np.ceil((a - ph) / P) * P, b, P)
        return np.interp(g, t_env, env).mean()

    best = (-1, None, None)
    for P in np.arange(0.4560, 0.4680, 0.00005):
        for ph in np.arange(0, P, 0.004):
            s = score(P, ph)
            if s > best[0]:
                best = (s, P, ph)
    s, P, ph = best
    for P2 in np.arange(P - 0.0001, P + 0.0001, 0.000005):
        for ph2 in np.arange(ph - 0.006, ph + 0.006, 0.0005):
            s2 = score(P2, ph2)
            if s2 > s:
                s, P, ph = s2, P2, ph2
    print(f"period {P:.5f}s  bpm {60/P:.3f}  phase {ph:.4f}  score {s:.3f}")
    # drift check: best local phase offset in 30 s windows
    for a in range(0, 240, 30):
        offs = np.arange(-0.04, 0.0405, 0.002)
        sc = [score(P, ph + o, a, a + 30) for o in offs]
        print(f"  {a:3d}-{a+30:3d}s best offset {offs[int(np.argmax(sc))]*1000:+5.0f} ms")
    aj = json.loads(AJ.read_text())
    dur = aj["duration"]
    grid = ph + P * np.arange(0, int(dur / P) + 1)
    grid = grid[grid < dur]
    # bar phase: compare with ASS line starts (lines start on bar downbeats in this song)
    ass_starts = [22.70, 24.54, 26.39, 28.24, 30.05, 31.90, 33.75, 35.59]
    k = []
    for t in ass_starts:
        i = int(np.argmin(np.abs(grid - t)))
        k.append(i % 4)
    bar_phase = max(set(k), key=k.count)
    bars = grid[bar_phase::4]
    aj.update({"bpm": 60 / P, "beat_period": P, "beat0": float(ph), "bar_phase": bar_phase,
               "beats": [round(float(x), 4) for x in grid], "bars": [round(float(x), 4) for x in bars]})
    AJ.write_text(json.dumps(aj, indent=1))
    print("bar phase votes", k, "-> bars start", bars[:3], "bar", 4 * P)
    for t in ass_starts:
        d = bars[np.argmin(np.abs(bars - t))] - t
        print(f"  ASS line {t:6.2f} nearest bar off {d*1000:+5.0f} ms")


if __name__ == "__main__":
    main()
