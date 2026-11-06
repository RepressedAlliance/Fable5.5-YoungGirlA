"""Pictures for the 2D sections (group C of docs/全片修改清单3.md). They use the rules in prompts.py and are registered into its ASSETS.
usage: prompts_c.py TAKES ID [ID ...]  -> assets/gen/raw/<ID>.t<k>.png; the chosen take is then copied to <ID>.png."""
import concurrent.futures as cf
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work" / "gen"))
import prompts as P  # noqa: E402

RAW = "assets/gen/raw/"


def inb(prev, nxt, moment, sprint=False, tired=False):
    """An in-between of the run in section 08: the drawings on both sides of it pin everything but the pose."""
    return P.a(
        "Shot: full figure seen exactly from the side, moving to the viewer's right. This is one in-between drawing for hand-drawn "
        "animation. Attached Image 2 and Attached Image 3 are the finished drawings just before and just after this one in the same "
        "run. Match them exactly: the same drawing style and line weight, the same size of head and body with no change of scale, the "
        "same face and open mouth or closed mouth as they have, the same hair shape pushed back by the wind, the same bow, the same "
        "uniform, the same plain charcoal scarf with its two short ends trailing behind, and the same navy rectangular school bag on "
        "one dark strap over her shoulder, on the same side of her. Draw the head at the same size and the same lean as in those two. "
        "Everything that moves is part way between the two drawings; nothing is new. " + moment + " Both legs in black tights and both "
        "brown loafers are clearly separate and anatomically correct, with knees bending the right way. Her whole figure, the bag and "
        "the scarf all fit inside the picture with a generous margin on every side. Do not draw the ground, motion lines, impact marks, "
        "sweat drops or anything else, only her.",
        refs=[RAW + prev + ".png", RAW + nxt + ".png"])


def land(side, other):
    return (f"THE LANDING: her {side} leg has swung forward and is coming down: its loafer is just touching the ground ahead of her hips, "
            f"knee almost straight, all her weight about to come on to it. Her {other} leg, stretched out behind a moment ago, is now bending, "
            "its thigh coming down and its lower leg lifting behind her. Both arms are on their way between the two drawings, elbows bent.")


def off(side, other):
    return (f"THE PUSH-OFF: her {side} leg, the one on the ground, now reaches back behind her hips with the knee nearly straight, pushing off: "
            f"the toe of its loafer is still on the ground and the heel has lifted. Her {other} knee is swinging forward and up, the thigh nearly level, "
            "the lower leg folded under it. Both arms are on their way between the two drawings, elbows bent.")


def tired(s):
    return "She is exhausted, head hanging forward, arms low and loose, a heavy short stride with low feet. " + s


NEW = {
    # the first run: two steps of eight drawings, four of them in Image 2/3 already
    "g61_run": inb("g14_run", "g11_run", land("NEAR", "FAR")),
    "g62_run": inb("g11_run", "g12_run", off("NEAR", "FAR")),
    "g63_run": inb("g12_run", "g13_run", land("FAR", "NEAR")),
    "g64_run": inb("g13_run", "g14_run", off("FAR", "NEAR")),
    # flat out
    "g71_run": inb("g54_run", "g51_run", land("NEAR", "FAR")),
    "g72_run": inb("g51_run", "g52_run", off("NEAR", "FAR")),
    "g73_run": inb("g52_run", "g53_run", land("FAR", "NEAR")),
    "g74_run": inb("g53_run", "g54_run", off("FAR", "NEAR")),
    # the stumble
    "g25_trip": inb("g21_trip", "g22_trip", "THE TOE HAS CAUGHT: her body has pitched further forward than in Image 2, arms flung forward, her front foot still held back by the ground behind her, her other knee starting to swing through under her."),
    "g26_trip": inb("g22_trip", "g23_trip", "CATCHING HERSELF: she is falling forward low, her front leg reaching far out, its loafer about to slam flat on the ground, knee opening; the back leg straightening out behind her, its toe still on the ground; arms out for balance."),
    "g29_trip": inb("g23_trip", "g27_trip", "THE MOMENT AFTER SHE CATCHES HERSELF, a third of the way from Image 2 to Image 3. Her front loafer stays flat where it was, the back leg still long behind with its toe on the ground. Her body has started to come up. Both arms are falling: the back arm has dropped from level to about 35 degrees below level, the front arm likewise, each only part way towards Image 3. The bag is swinging on its strap: it is still behind her, no longer flying out level but dropping, hanging at the back of her skirt below the level of her waist, the strap running from her shoulder down across her back to the bag."),
    "g29b_trip": inb("g23_trip", "g27_trip", "THE MOMENT AFTER SHE CATCHES HERSELF, a third of the way from Image 2 to Image 3, with the bag a little further on its swing. Her front loafer stays flat where it was, the back leg still long behind with its toe on the ground. Her body has started to come up. Both arms are falling, each only part way towards Image 3. The bag is dropping on its strap, overlapping the back edge of her skirt below the level of her waist."),
    "g30_trip": inb("g23_trip", "g27_trip", "GETTING UP, two thirds of the way from Image 2 to Image 3. Her front loafer stays flat where it was, knee bent; the back leg has begun to bend, its toe on the ground. Her body is nearly as high as in Image 3. Both arms have nearly fallen to where they are in Image 3. The bag has swung down and in: it is against the back of her hip and thigh, overlapping the back edge of her skirt, on its way round to where it is in Image 3, the strap running from her shoulder straight down to it."),
    "g27_trip": inb("g23_trip", "g24_trip", "GETTING UP: out of the deep lunge, her body comes up about half way, front knee bent over her front loafer flat on the ground, her back leg starting to come forward with its toe dragging; her arms fall back towards her sides; head stays down."),
    "g28_trip": inb("g24_trip", "g31_run", "STAGGERING ON: tired now, head hanging, shoulders dropped, arms loose and low, one loafer flat on the ground under her hips, knee bent, her other leg coming through low with its toe almost dragging."),
    # worn out
    "g35_run": inb("g34_run", "g31_run", tired(land("NEAR", "FAR"))),
    "g36_run": inb("g31_run", "g32_run", tired(off("NEAR", "FAR"))),
    "g37_run": inb("g32_run", "g33_run", tired(land("FAR", "NEAR"))),
    "g38_run": inb("g33_run", "g34_run", tired(off("FAR", "NEAR"))),
    # section 03: the three photographs, drawn again in her own drawing
    "r21_id": P.a(
        "This is a passport-style ID photograph of her as a prop in the film, drawn exactly in the manner of the model sheet, not painted and not photographic. Portrait format. "
        "Her head and shoulders from straight in front, square on and centred, looking straight into the lens, a plain empty face with a short straight mouth. Both eyes fully "
        "visible and level. Backdrop: one perfectly flat pale blue-grey #C4D2DA from edge to edge, with one hard-edged slightly darker shape of her own flash shadow on the right. "
        "Skin is one flat cream colour with one hard-edged shadow shape under the chin, no gradient at all, no skin rendering, no realism.", key=False, large=True),
    "r22_candid": P.a(
        "This is a snapshot taken from far away with a long lens and printed in black and white in a cheap weekly magazine, as a prop in the film, drawn exactly in the manner of the model sheet, not painted and not photographic. "
        "Landscape format. She is seen from the hips up, walking to the left with her school bag on one shoulder, her head turned over her shoulder towards the viewer, caught by surprise, mouth a little open, both eyes visible. "
        "Behind her a school gate of plain vertical iron bars and a plain wall, a few simple shapes only, no detail. The whole picture is monochrome and made of only four flat tones with hard edges: black ink line, white, a light grey and a dark grey. "
        "Hair light grey, skin white, skirt and collar dark grey, wall light grey, gate bars dark grey. No gradient, no blur, no airbrush, no grain, no photographic shading anywhere.", key=False),
    "r23_class": P.a(
        "This is an old black-and-white class photograph as a prop in the film, drawn exactly in the manner of the model sheet, not painted and not photographic. Landscape format. "
        "About thirty 12-year-old Japanese children in dark school uniforms stand in four rows on steps in front of a plain school building with a row of plain windows, all facing the camera, seen from straight in front. "
        "Each child is a very simple little drawing with the same simple face as the model sheet, a different height and a different simple hair shape: bobs, plaits, short boys' hair, one with glasses, one laughing, one looking aside. All faces are clear and simply drawn, eyes as two small dark marks. "
        "In the second row from the top, a little right of the centre, stands the one girl who is her: a chin-length bob with bangs and one big stiff two-loop white ribbon bow on top of her head on a white headband; her head is the same size as the others', her eyes level and clearly placed; hers is the lightest hair in the picture. "
        "The whole picture is monochrome and made of only four flat tones with hard edges: black ink line, white, a light grey and a dark grey. Faces white, uniforms dark grey, other children's hair black or dark grey, her hair light grey, building light grey. No gradient, no blur, no film grain, no photographic shading anywhere. "
        "Not more than thirty children; leave clear space between heads.", key=False, identity=False),
    # section 11b: the push under the door, by the hand rule. The arm is carried on past the left edge in the film
    "h41_push_a": P.a(
        "Attached Image 2 only shows the framing and the action, not how to draw the hand: a side view at floor level, a white sleeve with a navy cuff and one white line entering from the left edge. There is NO paper and NO floor drawn. "
        "Drawing 1 of a push along the floor, the start: the forearm slopes gently down from the upper left, the wrist a little raised, a small slim hand bent down at the wrist so the rounded fingertips press on an invisible floor line. Only the fingers' outer shape shows; thumb tucked behind. "
        "The whole hand from wrist to fingertip is about two cuff widths long and no wider than the cuff. The sleeve runs off the left edge.", identity=False, refs=[RAW + "h21_push_a.png"]),
    "h41_push_b": P.a(
        "Attached Image 2 only shows the framing and the action, not how to draw the hand: a side view at floor level, a white sleeve with a navy cuff and one white line entering from the left edge. There is NO paper and NO floor drawn. "
        "Drawing 2 of a push along the floor, the middle: the forearm lies low, nearly level, the wrist has come down, a small slim hand lies flat with the rounded fingertips sliding forward on an invisible floor line. Fingers together as one simple tapering shape with at most one clean line separating them. "
        "The whole hand from wrist to fingertip is about two cuff widths long and no wider than the cuff. The sleeve runs off the left edge.", identity=False, refs=[RAW + "h22_push_b.png"]),
    "h41_push_c": P.a(
        "Attached Image 2 only shows the framing and the action, not how to draw the hand: a side view at floor level, a white sleeve with a navy cuff and one white line entering from the left edge. There is NO paper and NO floor drawn. "
        "Drawing 3 of a push along the floor, the end: the arm is stretched out flat along the floor as far as it reaches, the cuff pulled back a little from the wrist, a small slim hand with straight fingers, only the rounded tips touching an invisible floor line; the hand has just let go. Fingers together as one simple tapering shape with at most one clean line separating them. "
        "The whole hand from wrist to fingertip is about two cuff widths long and no wider than the cuff. The sleeve runs off the left edge.", identity=False, refs=[RAW + "h23_push_c.png"]),
}
P.ASSETS.update(NEW)


def gen(aid, k):
    out = ROOT / RAW / f"{aid}.t{k}.png"
    if out.exists():
        return f"SKIP {out.name}"
    refs = [ROOT / r for r in P.refs(aid)]
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(P.build(aid))
        pf = f.name
    cmd = [sys.executable, str(ROOT / "src" / "tools" / "codex_gen.py"), str(out), pf]
    for r in refs:
        cmd += ["--ref", str(r)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    Path(pf).unlink(missing_ok=True)
    return f"{aid}.t{k}: {p.stdout.strip()[:90]}"


if __name__ == "__main__":
    takes = int(sys.argv[1])
    ids = list(NEW) if sys.argv[2:] == ["all"] else sys.argv[2:]
    jobs = [(i, k) for k in range(1, takes + 1) for i in ids]
    with cf.ThreadPoolExecutor(10) as ex:
        for r in ex.map(lambda q: gen(*q), jobs):
            print(r, flush=True)
