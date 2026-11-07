"""Third round of the ending's pictures (docs/全片修改清单3.md, group A). All Codex, all with the sheet. Run: gen_a3.py prefix ...; existing files are skipped."""
import concurrent.futures as cf
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "work" / "gen"))
import prompts as P  # noqa: E402

spec = importlib.util.spec_from_file_location("gen_end", ROOT / "work/eye/key6/gen_end.py")
GE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GE)

OUT = ROOT / "work/eye/key6/end3"
SHEET = P.SHEET
RAW05 = "assets/gen/raw/p05_face_close.png"
REFG = "work/eye/key6/end3/ref_wind_g.png"
T2 = "work/eye/key6/end3/t2_pick.png"
NEVER = GE.NEVER
KEEP = GE.KEEP

TILT = ("Only one thing changes: she has tilted her head a little towards the viewer's right, about seven degrees, as a girl does in the moment before a small smile, still looking straight at the viewer. "
        "The whole head turns together round the base of her neck as one thing: face, eyes, nose, mouth, bangs, hair clips, headband, bow and the hair all lean with it; the top of her head and the bow move clearly to the viewer's right and the chin moves slightly to the viewer's left. "
        "Her face keeps the same size, the same slim shape and the same big eyes, both irises looking straight at the viewer, gaze parallel, with the same white highlights and teal tiers. The face stays frontal; it is a tilt of the head in the plane of the picture, not a turn. "
        "Her neck, the scarf wound round it, the end of the scarf, the collar, the blouse and the neckerchief stay exactly where they are, line for line. The hair keeps the same light wind as in Attached Image 2, the clumps on the viewer's right blowing out to the right with their sharp points. The whole bow stays inside the picture with a margin at the top. ")
WIND_T = ("Her head stays exactly where it is, tilted as it is, and her face, eyes, mouth, headband, bow, neck, the scarf's wrap, collar and blouse stay exactly as in Attached Image 2, line for line. One moment later the steady light wind from the viewer's left has moved only this, clearly enough to see, with the same few bold clumps each with one sharp point: ")
LOOP = {
    "lp1": "the hair clumps on the viewer's right lift higher and reach a little further out to the right, their points rising; the tip of the lowest bang is pushed a little to the right; the end third of the scarf rises a little, its tip turning up.",
    "lp2": "the hair clumps on the viewer's right sink a little and swing in closer to her, their points curling outward; the bang's tip falls back; the end third of the scarf sinks a little lower with a soft new bend in it, its tip trailing.",
    "lp3": "the hair clumps on the viewer's right are ruffled by a small puff, the upper clump higher, the lower clump lower, their points parting; the end third of the scarf stretches a little further right and straightens a little.",
}
CW_RULE = ("Her face stays exactly as it is, line for line: face outline, eyes, eyebrows, nose, flat mouth, hair clips, ears. Only the wind from the viewer's left has changed the hair: the same few bold simple clumps each ending in one sharp point, the same line and the same flat colour, no thin strands. ")
CW = {
    "cw1": "A wind has just begun. The tips of the hair on the viewer's right lift and swing a little out to the right, the lowest points rising. The tips on the viewer's left swing a little in towards her neck. The end of the long bang on the viewer's right moves a little to the right.",
    "cw2": "A moderate wind. The hair on the viewer's right swings out to the right, its clumps coming away from her neck, the points clearly raised and curving up. The hair on the viewer's left is pushed in against her cheek, its points swept inward towards the chin. The bangs lift a little at their ends, blown to the right.",
    "cw3": "A strong wind. The hair on the viewer's right streams out to the right at a low slant, its clumps longer and thinner towards their points. The hair on the viewer's left is pressed flat against her cheek and its points are swept under her chin to the right. The bangs lift and are pushed to the right, showing a little more of her forehead.",
    "cw4": "The strongest gust, almost too strong to keep her eyes open. The hair on the viewer's right streams out nearly level to the right edge of the picture. The hair on the viewer's left is pressed hard against her cheek, its ends thrown across under her chin to the right. The bangs are thrown up and to the right, showing more of her forehead above the eyebrows.",
}
HAND = ("Draw one single hand of the girl in the attached character sheet. Attached Image 1 is her character sheet, Attached Image 2 is this same hand as it stands in the film and Attached Image 3 enlarges how her hands and cuffs are designed on the sheet. Keep Attached Image 2's picture shape, pose, angle, place and size: the left hand seen from the back, coming in from the lower right, the fingers pointing to the upper left, fingertips at the same place near the top of the picture, the cuff and sleeve at the same place running off the bottom edge. "
        "The change: the hand is much slimmer. At its widest the hand is clearly narrower than the navy cuff; the wrist narrower still, sitting loose inside the cuff; the whole hand about four times as long as it is wide. Long thin tapered fingers held close together, longer than the palm, the silhouette a long narrow leaf. The thumb is one small slim shape lying close along the side of the hand. "
        "The fingers are separated only by short thin lines near the tips. No nails, knuckles, tendons, veins, creases or shading. Flat cream skin #FEEEDD. The cuff is a navy band #2B3052 with exactly one thin white line. Plain white sleeve, no fold lines. 3:2 landscape, flat solid pure green #00FF00 background everywhere around the hand, nothing else.")

JOBS = {}
for n in range(1, 7):
    JOBS[f"t2_{n}"] = (KEEP + " " + TILT, [SHEET, REFG, "assets/gen/cut/p01_bust_front.png"])
for k, v in CW.items():
    for n in range(1, 5):
        JOBS[f"{k}_{n}"] = (GE.CLOSE + " " + CW_RULE + v, [SHEET, RAW05])
for n in range(1, 7):
    JOBS[f"hand_{n}"] = (HAND, [SHEET, "work/eye/key6/end3/ref_hand.png", P.SHEET_HAND])
# after t2_pick exists
for n in range(1, 5):
    JOBS[f"tc_{n}"] = (KEEP + " " + GE.CLOSED + GE.FACE_KEEP + " The mouth stays exactly as it is.", [SHEET, T2])
    JOBS[f"th_{n}"] = (KEEP + " " + GE.HALF_LIT.replace("There are no white marks in the iris.", "The white highlight stroke high in the iris is hidden by the lid; any small white flecks low in the iris stay.") + GE.FACE_KEEP + " The mouth stays exactly as it is.", [SHEET, T2])
    JOBS[f"tflat_{n}"] = (KEEP + " " + GE.FLAT.replace("like the mouth in Attached Image 3 and on the model sheet", "like the mouth on the model sheet") + GE.FACE_KEEP, [SHEET, T2])
    JOBS[f"tmid_{n}"] = (KEEP + " " + GE.MID + GE.FACE_KEEP, [SHEET, T2])
    for key, part in (("t1a", "one third of the way from Attached Image 3 to Attached Image 2"), ("t1b", "two thirds of the way from Attached Image 3 to Attached Image 2")):
        JOBS[f"{key}_{n}"] = (KEEP + " " + GE.CLOSED + "Also, her mouth is one short flat straight ink line, calm, no curve. And her head is " + part + ": Attached Image 2 has the head tilted, Attached Image 3 is the same drawing with the head still upright. Head, face, bow, bangs and hair all lie at that point between the two pictures, and the neck, scarf wrap, collar and blouse stay as they are in both. ", [SHEET, T2, REFG])
for n in range(1, 5):
    for key, v in (("lc", GE.CLOSE_C), ("lh", GE.CLOSE_H), ("ln", GE.CLOSE_N)):
        JOBS[f"{key}_{n}"] = (GE.CLOSE + " " + v + "Her hair, blown by the wind, stays exactly as in Attached Image 2.", [SHEET, "work/eye/key6/end3/ref_cw_paint.png"])
CW_MID = ("Attached Image 2 is this picture at one moment and Attached Image 3 is the same picture a moment later, when the wind has grown. Draw the moment exactly half way between them. Each clump of her hair reaches about half way between where it is in the two pictures, the same bold simple clumps each with one sharp point; the bangs are half way between too. ")
for key, a_, b_ in (("cab", "cw1_1", "cw2_1"), ("cbc", "cw2_1", "cw3_1"), ("ccd", "cw3_1", "cw4_1"), ("c0a", "RAW", "cw1_1")):
    for n in range(1, 5):
        ra = RAW05 if a_ == "RAW" else f"work/eye/key6/end3/{a_}.png"
        JOBS[f"{key}_{n}"] = (GE.CLOSE + " " + CW_RULE + CW_MID, [SHEET, ra, f"work/eye/key6/end3/{b_}.png"])
for n in range(1, 5):
    JOBS[f"cde_{n}"] = (GE.CLOSE + " " + CW_RULE + "One moment later in the same strong gust: each streaming clump on the viewer's right has flicked a little, the upper ones a little higher and the lower ones a little lower, their points further on, with the same simple shapes and the same reach. The bangs lift a very little more.", [SHEET, "work/eye/key6/end3/cw4_1.png"])
HANDW = ("Draw one single hand of the girl in the attached character sheet. Attached Image 1 is her character sheet, Attached Image 2 is this hand as it stands now and Attached Image 3 enlarges how her hands and cuffs are designed on the sheet. Keep Attached Image 2 exactly: its picture shape, pose, angle, place and size, the slim leaf-shaped hand, the fingers, the thumb, the short lines between the fingers near the tips, the cuff and the sleeve. "
         "Change only the wrist: now it pinches in too hard like the neck of a bottle. The hand narrows gently and evenly into a slim wrist that is about two thirds as wide as the hand at its widest and goes straight into the navy cuff without any narrow neck. The wrist is still narrower than the cuff. The outline from the widest part of the hand to the cuff is one long calm line on each side. Flat cream skin, no lines inside, 3:2 landscape, flat solid pure green #00FF00 background everywhere around the hand, nothing else.")
for n in range(1, 7):
    JOBS[f"handw_{n}"] = (HANDW, [SHEET, "work/eye/key6/end3/hand_1.png", P.SHEET_HAND])
for k, v in LOOP.items():
    for n in range(1, 5):
        JOBS[f"{k}_{n}"] = (KEEP + " " + WIND_T + v, [SHEET, T2])


def one(name):
    out = OUT / f"{name}.png"
    if out.exists():
        return f"skip {name}"
    prompt, refs = JOBS[name]
    pf = OUT / f"{name}.txt"
    pf.write_text(prompt + ("" if name.startswith("hand") else " " + NEVER), encoding="utf-8")
    cmd = [sys.executable, str(ROOT / "src" / "tools" / "codex_gen.py"), str(out), str(pf)]
    for r in refs:
        cmd += ["--ref", str(ROOT / r)]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return f"{name} {'ok' if out.exists() else 'FAILED ' + (r.stderr or r.stdout)[-200:]}"


if __name__ == "__main__":
    want = sys.argv[1:]
    names = [j for j in JOBS if any(j.startswith(w) for w in want)]
    with cf.ThreadPoolExecutor(14) as ex:
        for line in ex.map(one, names):
            print(line, flush=True)
    print("ALL DONE", flush=True)
