"""Beat grid, bar grid, loudness curve and section boundaries for the song.

Output: work/analysis/audio.json
"""
import json
from pathlib import Path

import librosa
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
WAV = ROOT / "work" / "analysis" / "song.wav"
OUT = ROOT / "work" / "analysis" / "audio.json"


def main():
    y, sr = librosa.load(WAV, sr=22050, mono=True)
    dur = len(y) / sr
    hop = 256
    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset, sr=sr, hop_length=hop, tightness=400)
    bt = librosa.frames_to_time(beats, sr=sr, hop_length=hop)
    # straight-line fit of beat times -> steady grid (the song is programmed, tempo is constant)
    idx = np.arange(len(bt))
    keep = np.ones(len(bt), bool)
    for _ in range(4):
        a, b = np.polyfit(idx[keep], bt[keep], 1)
        res = bt - (a * idx + b)
        keep = np.abs(res) < 0.035
    period = a
    bpm = 60.0 / period
    # phase: choose bar offset (0..3) whose beats carry the most low-frequency onset energy
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    low = S[freqs < 150].sum(axis=0)
    lowd = np.maximum(0, np.diff(low, prepend=low[0]))
    grid = b + period * np.arange(-8, int(dur / period) + 8)
    grid = grid[(grid >= 0) & (grid < dur)]
    gfr = librosa.time_to_frames(grid, sr=sr, hop_length=hop)
    gfr = np.clip(gfr, 0, len(lowd) - 1)
    strength = np.array([lowd[max(0, f - 2): f + 3].max() for f in gfr])
    phase_score = [strength[k::4].mean() for k in range(4)]
    ph = int(np.argmax(phase_score))
    bars = grid[ph::4]
    # loudness (RMS dB) at 10 Hz
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=2205)[0]
    rms_db = librosa.amplitude_to_db(rms, ref=np.max)
    # section novelty from chroma + mfcc self-similarity, peaks snapped to bars
    hop2 = 512
    mf = librosa.feature.mfcc(y=y, sr=sr, hop_length=hop2, n_mfcc=20)
    ch = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop2)
    feat = np.vstack([librosa.util.normalize(mf, axis=1), ch])
    bar_fr = librosa.time_to_frames(bars, sr=sr, hop_length=hop2)
    bar_fr = bar_fr[bar_fr < feat.shape[1]]
    sync = librosa.util.sync(feat, bar_fr, aggregate=np.median)
    nov = np.zeros(sync.shape[1])
    for i in range(1, sync.shape[1] - 1):
        L = sync[:, max(0, i - 2):i].mean(axis=1)
        R = sync[:, i:i + 2].mean(axis=1)
        nov[i] = np.linalg.norm(L - R)
    bar_times = librosa.frames_to_time(bar_fr, sr=sr, hop_length=hop2)
    order = np.argsort(-nov)
    cand = sorted(float(bar_times[i]) for i in order[:24])
    res = {
        "duration": dur,
        "bpm": bpm,
        "beat_period": period,
        "beat0": float(b),
        "bar_phase": ph,
        "beats": [round(float(x), 4) for x in grid],
        "bars": [round(float(x), 4) for x in bars],
        "rms_db_10hz": [round(float(x), 2) for x in rms_db],
        "section_candidates": [round(x, 3) for x in cand],
        "librosa_tempo": float(np.atleast_1d(tempo)[0]),
        "beat_fit_inliers": int(keep.sum()),
        "beat_count": int(len(bt)),
    }
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"bpm {bpm:.3f} (librosa {res['librosa_tempo']:.1f}), period {period:.4f}s, bar {4*period:.3f}s, "
          f"inliers {keep.sum()}/{len(bt)}, bar phase {ph}, first bar {bars[0]:.3f}")
    print("section candidates:", " ".join(f"{x:.2f}" for x in cand))
    # coarse loudness profile per 4 bars
    for i in range(0, len(bars) - 1, 4):
        t0 = bars[i]
        t1 = bars[min(i + 4, len(bars) - 1)]
        seg = rms_db[int(t0 * 10):int(t1 * 10)]
        print(f"{t0:7.2f}-{t1:7.2f}  {seg.mean():6.1f} dB")


if __name__ == "__main__":
    main()
