"""Find every place a person's card passes through the set, from the kept data passes (work/render/<shot>_exr).

Where a card only stands in front of or behind something, the depth jumps at the edge between them. Where it goes through
something, the depth runs on across that edge. So: pairs of neighbouring pixels, one on a card (material index 2) and one on
the set, with nearly the same depth. Feet standing on a floor touch it the same way; those are told apart by the set's surface
facing up and lying at floor height, and reported separately as contacts.

usage: clip_scan.py [shot ...]      writes work/qc/clipscan/<shot>.txt and an overlay picture for each flagged frame
"""
import multiprocessing as mp
import os
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "npr")]
OUT = ROOT / "work" / "qc" / "clipscan"
TOL = 0.004          # metres of depth per metre of distance: closer than this counts as touching
MIN_PX = 6           # supersampled pixels of touching edge before a frame is reported


def scan(path):
    import comp
    try:
        p = comp.read_exr(path)
    except Exception as e:
        return path, None, str(e)
    ma = np.rint(p["IndexMA"]).astype(int)
    d = p["Depth"].astype(np.float32)
    nz = p["Normal"][..., 2]
    pz = np.nan_to_num(p["Position"][..., 2])
    a = p["Alpha"] if p["Alpha"].ndim == 2 else p["Alpha"][..., 0]
    valid = (a > 0.5) & np.isfinite(d) & (d < 1e4)
    card = valid & (ma == 2)
    setp = valid & (ma != 2)
    hits = np.zeros(d.shape, bool)
    kinds = {"through": 0, "seat": 0}
    for axis in (0, 1):
        if axis == 1:
            c0, c1, s0, s1, d0, d1 = card[:, :-1], card[:, 1:], setp[:, :-1], setp[:, 1:], d[:, :-1], d[:, 1:]
            n0, n1, z0, z1 = nz[:, :-1], nz[:, 1:], pz[:, :-1], pz[:, 1:]
        else:
            c0, c1, s0, s1, d0, d1 = card[:-1], card[1:], setp[:-1], setp[1:], d[:-1], d[1:]
            n0, n1, z0, z1 = nz[:-1], nz[1:], pz[:-1], pz[1:]
        close = np.abs(d0 - d1) < TOL * np.minimum(d0, d1)
        for cm, sm, sn, sz in ((c0 & s1, None, n1, z1), (s0 & c1, None, n0, z0)):
            m = cm & close
            upright = np.abs(sn) < 0.6
            # a surface facing up: a floor under feet, or a seat, desk or step under a body
            up = ~upright
            through = m & upright
            seat = m & up & (sz > 0.12)
            kinds["through"] += int(through.sum())
            kinds["seat"] += int(seat.sum())
            sl = (slice(None), slice(0, -1)) if axis == 1 else (slice(0, -1), slice(None))
            hits[sl] |= through | seat
    return path, kinds, hits


def main():
    shots = sys.argv[1:] or sorted(p.name[:-4] for p in (ROOT / "work" / "render").glob("*_exr"))
    OUT.mkdir(parents=True, exist_ok=True)
    for shot in shots:
        files = sorted((ROOT / "work" / "render" / f"{shot}_exr").glob("f*.exr"))
        lines = []
        with mp.get_context("spawn").Pool(int(os.environ.get("SCAN_WORKERS", "10"))) as pool:
            for path, kinds, hits in pool.imap(scan, files, chunksize=2):
                if kinds is None:
                    lines.append(f"{Path(path).name} UNREADABLE {hits}")
                    continue
                n = kinds["through"] + kinds["seat"]
                if n >= MIN_PX:
                    lines.append(f"{Path(path).name} through={kinds['through']} seat={kinds['seat']}")
                    png = ROOT / "work" / "render" / f"{shot}_png" / (Path(path).stem + ".png")
                    im = cv2.imread(str(png))
                    if im is not None:
                        # grown first, so a one-pixel line survives the shrink to the picture's size
                        h = cv2.dilate(hits.astype(np.uint8) * 255, np.ones((7, 7), np.uint8))
                        h = cv2.resize(h, (im.shape[1], im.shape[0]), interpolation=cv2.INTER_AREA)
                        im[h > 0] = (0, 0, 255)
                        cv2.imwrite(str(OUT / f"{shot}_{Path(path).stem}.jpg"), im, [cv2.IMWRITE_JPEG_QUALITY, 85])
        (OUT / f"{shot}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(shot, len(files), "frames,", len(lines), "flagged", flush=True)


if __name__ == "__main__":
    main()
