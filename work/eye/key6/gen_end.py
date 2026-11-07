"""The new ending's pictures, every one drawn by Codex from the master or from the close-up. Run: gen_end.py [group ...]; existing files are skipped."""
import concurrent.futures as cf
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "work" / "gen"))
import prompts as P  # noqa: E402

D = ROOT / "work" / "eye" / "key6"
OUT = D / "end"
MASTER = "work/eye/key6/cand_c2.png"
SHEET = P.SHEET
BUST = "assets/gen/cut/p01_bust_front.png"
RAW05 = "assets/gen/raw/p05_face_close.png"
PAINT05 = "work/eye/key6/ref_p05_paint.png"
EYELIT = "work/eye/key6/ref_eyes_lit.png"
LIT = "work/eye/key6/end/lit_pick.png"       # the master with the lit eyes, once chosen
NEVER = P.NEVER + " " + P.KEY

KEEP = " ".join([
    P.IDENTITY, P.DRAW, P.LARGE, P.SHEET_RULE,
    "Attached Image 2 is this exact picture as it stands, a finished drawing. Redraw this same picture with the same framing, the same size and place of everything: the head, the slim face shape, "
    "the nose, the eyebrows, the hair, the two hair clips, the bow, the scarf, the navy collar and the white blouse, with the same ink line and the same flat colours, line for line, as if traced. "
    "The picture stays the same shape and the figure does not move, shrink or turn in it. The background stays flat pure green.",
])
FACE_KEEP = "Everything else stays exactly as in Attached Image 2, including the hair, the wind in it and the scarf end."
CLOSED = ("Change only her two eyes: both eyes are now gently and fully closed, because the wind has just hit her. Each closed eye is one calm, confident curved ink line with real brush pressure, "
          "as heavy as the upper lash line of the open eye: it lies low, where the lower part of the open eye was, sagging gently in the middle like a shallow bowl, thin at the inner end and thicker towards the outer end, "
          "with one small lash flick at the outer corner as on the open eye. No iris, no white of the eye, no second lid line, nothing else: where the eye was there is now plain flat skin. The two eyes mirror each other. The eyebrows stay where they are. ")
HALF = ("Change only her two eyes: both eyes are half open, on their way to opening. The same heavy upper lash line has come down so that it crosses the iris just above the pupil's middle: the top half of each iris is hidden by the lid and only "
        "the lower half of the iris shows, with its dark pupil cut by the lid and its pale crescent at the bottom. The irises stay in the very same place and size as in Attached Image 2, both looking straight at the viewer, the same way. "
        "Plain flat skin above the lash line where the upper part of the eye was. There is no white highlight in the iris. The lower edge of the eye is unchanged. The eyebrows stay where they are. ")
FLAT = "Change only her mouth: it is one short flat straight ink line with slightly tapered ends and no curve at all, calm and blank, like the mouth in Attached Image 3 and on the model sheet, the same length as the smile line and centred under her nose. "
MID = "Change only her mouth: it is one short ink line with hardly any curve, only the slightest beginning of a smile, half way between a dead straight line and the small smile in Attached Image 2: the ends lift just a hair. The same length, centred under her nose. "

# the lit eyes: the same eye as the master's, with the iris of the eye that has just been lit in the close-up
LIT_EYES = ("Attached Image 3 is only a reference for the irises: it shows the same girl's two eyes enormous, just after the light has come into them. Change only the inside of her two irises in Attached Image 2 so they carry that same light, scaled down: "
            "the iris is built of a few flat hard-edged tiers of teal, curved like the bottom of a bowl: a deep dark teal across the top, then #0B7C93, then a bright #35A7BC, then a pale #8CD7DF crescent at the very bottom; a dark oval pupil; "
            "one distinctive white highlight stroke high on the viewer's left of each iris, a slanting brush stroke with a heavy rounded head and a small notched, tapered tail, the same shape in both eyes, exactly as in Attached Image 3; "
            "one small round white dot high on the viewer's right of the iris; two or three tiny white flecks low on the viewer's right. Keep it hard-edged and few: no gradient, no glow, no extra rings. "
            "The eye's own outline, its upper lash line, the lash flick, the size and shape of the iris, the white of the eye and the place of the iris stay exactly as in Attached Image 2. Both eyes look straight at the viewer, the same way, gaze parallel. ")
NO_HL = ("Change only the inside of her two irises: every white mark in them is gone: no white stroke, no white dot, no white flecks. The teal tiers and the dark pupil continue cleanly where the white marks were. The eye's outline, its lash line, the iris's size and place and every tier stay exactly as in Attached Image 2. ")
HALF_LIT = ("Change only her two eyes: both eyes are half open, on their way to opening. The same heavy upper lash line has come down in its own arched curve, still rounded like the top of the eye and never a straight bar, so that its middle crosses the iris just above the pupil's middle: the top half of each iris is hidden by the lid and only "
            "the lower half of the iris shows, with its teal tiers, the pale crescent at the bottom and the dark pupil cut by the lid, exactly as they are in Attached Image 2. The irises stay in the very same place and size, both looking straight at the viewer, the same way. "
            "Plain flat skin above the lash line where the upper part of the eye was. There are no white marks in the iris. The lower edge of the eye is unchanged. The eyebrows stay where they are. ")

WIND_RULE = (
    "Her face, her head's position, the bow's knot, the blouse and the collar stay exactly where they are. The small closed-mouth smile and the eyes stay exactly as in Attached Image 2. "
    "Only the wind has changed, and the wind changes only these: the ends of her hair, the ends of her bangs, the end of the scarf. The same few bold simple clumps as in Attached Image 2, each with one sharp point, keeping one strong silhouette; the same one hard-edged shadow tone in the hair. "
    "The wind comes from the viewer's left and the hair and scarf blow to the viewer's right. The whole bow, all her hair and the whole scarf end are inside the picture with a margin. The scarf stays wrapped round her neck as in Attached Image 2 and its end is one complete soft strip of cloth with a clean end. "
    "The bow keeps exactly two stiff pointed loops and one small square knot. "
)
WIND = {
    "w1": "This is the strongest moment, a violent gust, clearly stronger than in Attached Image 2. The hair on the viewer's right streams out almost level and the clumps stretch out further, the points thin and fast. The bangs lift and are thrown to the right. The hair on the viewer's left is pressed in against her cheek, its ends swept towards the right under her jaw. The scarf end is straight and taut, streaming out level with its end flicking up. The tips of the bow's loops lean a little to the right.",
    "w2": "A strong gust, a little stronger than in Attached Image 2. The hair on the viewer's right streams out to the right, the clumps rising slightly, a sharp point on each. The bangs are pushed to the right. The hair on the viewer's left sweeps inward. The scarf end flies out to the right in one long wave. The tips of the bow's loops lean slightly to the right.",
    "w3": "The gust is passing: a wind a little weaker than in Attached Image 2. The hair on the viewer's right blows to the right but has started to droop, each clump coming out at a downward slant with its point curving up. The bangs lift less. The scarf end flies to the right, sagging in the middle.",
    "w4": "A moderate wind, clearly weaker than in Attached Image 2. The hair on the viewer's right hangs out at about forty-five degrees below level, the clumps shorter in reach, the points curving outward. The bangs fall nearly in their usual place, only their ends displaced to the right. The hair on the viewer's left hangs almost straight. The scarf end hangs out to the lower right in a slack curve, across the collar and past the shoulder.",
    "w5": "A light wind dying away. The hair has mostly fallen as on the model sheet; on the viewer's right the ends still swing out a little to the right, the points lifting. The bangs are in their usual place on the sheet with only their tip moved a little. The scarf end hangs down over her chest and shoulder on the viewer's right, drifting slightly to the right, relaxed.",
    "w6": "Only a light breath of air. The hair hangs as on the model sheet and in Attached Image 3, a bob with its sharp points; only the very points on the viewer's right lift a little to the right. The bangs lie as on the model sheet. The scarf end hangs down loosely on the viewer's right side of her chest, its tip just stirred to the right. Everything has come to rest but is not quite still.",
}

SCARF_FLOAT = ("The end of the scarf still floats out to the viewer's right in one slack, lazy S-curve, from where it leaves her neck on the viewer's right, a little below the shoulder line of her hair; the whole strip, tip included, stays above the height where the navy collar's white line reaches her shoulder, well inside the upper part of the picture and well inside the picture on the right. It does not hang down over her chest. ")
WIND["b4"] = "A moderate wind, clearly weaker than in Attached Image 2. The hair on the viewer's right hangs out at about forty-five degrees below level, the clumps shorter in reach, the points curving outward. The bangs fall nearly in their usual place, only their ends displaced to the right. The hair on the viewer's left hangs almost straight. " + SCARF_FLOAT + "It sags more than in Attached Image 2 and reaches less far."
WIND["b5"] = "A light wind dying away. The hair has mostly fallen as on the model sheet and in Attached Image 3; on the viewer's right the ends still swing out a little to the right, the points lifting. The bangs are in their usual place on the sheet with only their tip moved a little. " + SCARF_FLOAT + "It is slow and low, reaching only about as far as her hair's points plus a little."
WIND["b6"] = "Only a light breath of air, but the air is still moving. The hair hangs as on the model sheet and in Attached Image 3, a bob with its sharp points; only the very points on the viewer's right lift a little to the right. The bangs lie as on the model sheet. " + SCARF_FLOAT + "It is the slackest it can be while still floating, its tip just lifted."
CLOSE = " ".join([
    P.IDENTITY, P.DRAW, P.LARGE, P.SHEET_RULE,
    "Attached Image 2 is this exact picture as it stands, a huge close-up of her face. Redraw this same wide picture with exactly the same framing and scale, the same place of everything: face outline, nose, flat mouth line, hair, the lines of the bangs, "
    "hair clips and eyebrows, with the same ink line and same flat colours, line for line, as if traced. The face does not move, shrink or turn. The background around her hair stays flat pure green.",
])
CLOSE_C = ("Change only her two eyes: both eyes are now fully closed because the wind has hit her. Each closed eye is one calm, heavy curved ink line with real brush pressure, as thick as the upper lash line of the open eye: it lies low, where the lower part of the open eye was, "
           "sagging gently in the middle like a shallow bowl, thin at the inner end and thicker towards the outer end, with one small lash flick at the outer corner. No iris, no white, no second lid line, nothing else: where the eye was there is now plain flat skin. The two mirror each other. ")
CLOSE_H = ("Change only her two eyes: she is starting to shut them against the wind: both are half closed. The same heavy upper lash line has come down so that it crosses each iris just above the pupil's middle; the top half of the iris is hidden, the lower half shows with the same colours as in Attached Image 2, including the pale bottom bands. "
           "The irises stay in exactly the same place and size. Plain flat skin above the lash line where the upper part of the eye was. The lower edge of the eye is unchanged. ")
CLOSE_N = ("Change only her two eyes: she is shutting them against the wind: both nearly closed. The heavy upper lash line has come far down, leaving only a thin sliver of each iris's bottom showing above the lower edge of the eye, the same pale teal as in Attached Image 2. Plain flat skin above the lash line where the upper part of the eye was. ")

JOBS = {}
for n in range(1, 5):
    JOBS[f"closed_{n}"] = (KEEP + " " + CLOSED + FACE_KEEP, [SHEET, MASTER])
    JOBS[f"half_{n}"] = (KEEP + " " + HALF + FACE_KEEP, [SHEET, MASTER])
    JOBS[f"lit_{n}"] = (KEEP + " " + LIT_EYES + FACE_KEEP, [SHEET, MASTER, EYELIT])
    JOBS[f"nohl_{n}"] = (KEEP + " " + NO_HL + FACE_KEEP, [SHEET, LIT])
    JOBS[f"hlit_{n}"] = (KEEP + " " + HALF_LIT + FACE_KEEP, [SHEET, LIT])
for n in range(1, 4):
    JOBS[f"flat_{n}"] = (KEEP + " " + FLAT + FACE_KEEP, [SHEET, MASTER, BUST])
    JOBS[f"mid_{n}"] = (KEEP + " " + MID + FACE_KEEP, [SHEET, MASTER])
for k, v in WIND.items():
    for n in range(1, 5):
        JOBS[f"{k}_{n}"] = (KEEP + " " + WIND_RULE + v, [SHEET, MASTER, BUST])
for n in range(1, 4):
    JOBS[f"cc_{n}"] = (CLOSE + " " + CLOSE_C, [SHEET, RAW05])
    JOBS[f"ch_{n}"] = (CLOSE + " " + CLOSE_H, [SHEET, PAINT05])
    JOBS[f"cn_{n}"] = (CLOSE + " " + CLOSE_N, [SHEET, PAINT05])

BREATH = "work/eye/key6/end/breath_pick.png"
BKEEP = " ".join([P.IDENTITY, P.DRAW, P.LARGE, P.SHEET_RULE,
    "Attached Image 2 is this exact picture as it stands, a finished drawing. Redraw this same picture, line for line, as if traced: everything stays exactly where it is and the same shape: head, face, eyes, mouth, bow, bangs, hair, scarf wrap, collar, blouse. The picture stays the same shape. The background stays flat pure green. One moment later a breath of air has moved only this, by a small amount: "])
for k, v in {"l1": "the end third of the scarf floats a little higher, its tip turning up; the two lowest hair points on the viewer's right lift a very little to the right.",
             "l2": "the end third of the scarf has sunk a little lower, with a soft new bend in it, its tip trailing; the hair points on the viewer's right hang a very little lower and closer in.",
             "l3": "the end third of the scarf has drifted a little further to the right and straightened a little; the hair points on the viewer's right swing a very little further out; the tip of the lowest bang moves a tiny amount to the right."}.items():
    for n in range(1, 4):
        JOBS[f"{k}_{n}"] = (BKEEP + v, [SHEET, BREATH])

for n in range(1, 4):
    JOBS[f"sc_{n}"] = (KEEP + " " + CLOSED + FACE_KEEP + " The mouth stays exactly as it is.", [SHEET, "work/eye/key6/end/ref_gust.png"])
    JOBS[f"sh_{n}"] = (KEEP + " " + HALF_LIT + FACE_KEEP + " The mouth stays exactly as it is.", [SHEET, "work/eye/key6/end/ref_strong.png"])

for n in range(1, 5):
    JOBS[f"xm_{n}"] = (KEEP + " " + WIND_RULE + "Attached Image 3 is this same picture a moment later, when the wind has weakened: draw the moment exactly half way between Attached Image 2 and Attached Image 3. Each clump of hair on the viewer's right reaches about half way between where it is in the two pictures and droops half as much; the bangs are half way; the end of the scarf is half way between its two positions, with the same simple shape.", [SHEET, "work/eye/key6/end/w2_3.png", "work/eye/key6/end/w3_2.png"])

for k, t in (("b", "sb"), ("c", "sk")):
    for n in range(1, 4):
        JOBS[f"{t}_{n}"] = (KEEP + " " + CLOSED + FACE_KEEP + " The mouth stays exactly as it is.", [SHEET, f"work/eye/key6/end/ref_wind_{k}.png"])


def one(name):
    out = OUT / f"{name}.png"
    if out.exists():
        return f"skip {name}"
    prompt, refs = JOBS[name]
    pf = OUT / f"{name}.txt"
    pf.write_text(prompt + " " + NEVER, encoding="utf-8")
    cmd = [sys.executable, str(ROOT / "src" / "tools" / "codex_gen.py"), str(out), str(pf)]
    for r in refs:
        cmd += ["--ref", str(ROOT / r)]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return f"{name} {'ok' if out.exists() else 'FAILED ' + (r.stderr or r.stdout)[-200:]}"


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    want = sys.argv[1:]
    skip = ("nohl", "hlit", "l1", "l2", "l3", "sc_", "sh_", "xm_", "sb_", "sk_")
    names = [j for j in JOBS if (any(j.startswith(w) for w in want) if want else not j.startswith(skip))]
    with cf.ThreadPoolExecutor(12) as ex:
        for line in ex.map(one, names):
            print(line, flush=True)
    print("ALL DONE", flush=True)
