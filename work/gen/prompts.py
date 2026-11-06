"""Prompts for every generated image. Only characters and components, never a full picture."""

IDENTITY = (
    "Character: Kagamine Rin, an ordinary 14-year-old Japanese junior-high girl, 152 cm, realistic slim "
    "14-year-old proportions, not chibi and not adult. Attached Image 1 is her final model sheet: match it exactly. "
    "Bright yellow-blonde chin-length bob with bangs (#FEE45F); two small parallel white hair clips on the bangs on "
    "viewer's left; one big stiff white ribbon bow on top of her head, exactly two loops and one small square knot, "
    "no ribbon tails, on a white headband; big round eyes with flat teal irises (#218EA3), not navy; fair skin. "
    "Plain school uniform: white long-sleeved sailor blouse, navy collar with one thin white line, small yellow "
    "neckerchief, navy knee-length skirt, black tights, brown loafers, plain charcoal scarf. Modest, ordinary student. "
    "Acting: a black bar covers her eyes in most of the film, so any feeling the shot asks for goes into her mouth, jaw and "
    "the angle of her head; her eyes alone never carry it."
)

DRAW = (
    "Drawing: the same hand as the model sheet: bold graphic design with thick-thin ink brush outlines, as in a "
    "stylish auteur animated film; shapes simplified with strong silhouettes and very few inner lines. Flat paint, "
    "exactly one hard-edged shadow tone per material. Hair is one bold silhouette with a few sharp clumps at the ends. "
    "Slightly imperfect ink line with real brush pressure, so it feels drawn by a person and not traced by a computer."
)

# Root cause (docs/问题根因清单.md, "手又老又恐怖"): the text only asked for correct anatomy, and the sheet's hands are small and
# hang at her sides, so any hand near the camera fell back to a realistic adult hand. This rule goes into every picture of her.
HANDS = (
    "Her hands, whenever any part of one is visible: exactly the hands on the model sheet, drawn in the same simple way as "
    "her face. Small, slim and young: a narrow palm, a narrow wrist, thin tapering fingers with simple rounded tips. Flat cream "
    "skin (the same colour as her face) with a clean outer ink line. Nothing is drawn inside the hand: no palm creases, no "
    "knuckle or finger-joint lines, no tendons, no veins, no fingernails. One clean ink line separates fingers that touch. At "
    "most one simple hard-edged shadow shape on the whole hand. A hand close to the camera gets bigger but never gets more "
    "detailed. Four fingers and one thumb wherever all are in view. The cuff is a navy band with exactly one thin white line. "
    "Measure by that cuff: the wrist is clearly narrower than the cuff and sits loose inside it; the hand at its widest is no wider "
    "than the cuff; from wrist to fingertip it is about two cuff widths. The silhouette is slightly faceted and tapers to its end, "
    "as on the sheet; no spiky creases at the fork of the thumb. Skin #FEEEDD, shadow shape pale warm tan #F3D2B5, never pink. These "
    "rules hold whatever any other attached picture of a hand shows or any other words here say."
)

# Added with large=True: pictures the film shows bigger than about half the screen.
LARGE = (
    "This drawing is shown very large on screen. It stays exactly as simple as the model sheet and adds nothing the sheet does "
    "not have: no extra lines, no texture, no rendering, no realism, no mascot conventions (no pink blush, no chibi or cute "
    "rounded proportions, no fat mitten hands). Its beauty comes only from a confident thick-thin ink line with clean tapered "
    "ends, elegant slim proportions, well designed shapes and clean hard-edged shadow shapes."
)

NEVER = (
    "Must NOT have: hair broken into many thin strands or flyaway hairs; many fold lines on clothes; soft glow, "
    "airbrushed gradients or soft shadow; dirty lines or muddy colour; glossy hair sheen; sparkling eyes or star-shaped "
    "catchlights; blush gradients or pink cheeks; a bow with more than two loops; extra fingers; realistic, adult, large or bony hands, fingernails, or lines inside a hand; text, letters, logos or watermarks."
)

# The owner's diagnosis, 2026-11-06: pictures made with the model sheet as reference have almost no AI look; what goes wrong is
# that a simple style comes out ugly when a picture drifts from the sheet and is then shown large. So every drawing of her gets
# the sheet as Image 1 (see refs() below) and these rules, and is judged against the sheet.
SHEET_RULE = (
    "The model sheet decides. Stay true to it and do not improve on it: no pink blush, no mascot or chibi conventions, no realism, "
    "no rendered detail, nothing it does not have. Any other attached picture only gives pose and framing unless the text says otherwise."
)

SHEET = "docs/人设_定稿_c.png"
SHEET_HAND = "work/gen/ref_sheet_hand.png"   # the sheet's own hands, cropped and enlarged
# a picture that is nothing but a hand also gets the sheet's hands enlarged, as the last attached image
HAND_ONLY = ("h0", "h1", "h2", "h3", "h4", "p06", "p07", "p08")
SLEEVE_END = (
    "The white sleeve is loose cloth with slack in it, plain and empty where it leaves the picture: any fold line or shadow stays close to the cuff "
    "and stops well before the edge of the picture, because the sleeve is carried on past the edge in the film."
)

KEY = (
    "Background: perfectly flat solid pure green #00FF00 from edge to edge, with no shadow, no gradient, no floor and "
    "no other objects, because the figure will be cut out. No frame or border."
)

HEAD_W = 'Attached image: this exact hand and sleeve, the same left hand with the palm facing us, the same drawing, ink line, skin, navy cuff band with one white line and white sleeve, no fingernails visible because we see the palm side. Keep the thumb on the same side of the hand relative to the fingers as in the attached image: when the fingers point up and to the left the thumb is on the LOWER LEFT side of the palm, below the fingers. '
HEAD_B = ("Attached image: only for the drawing style, the ink line, skin colour, navy cuff band with one white line and white sleeve. Do not copy its pose: that one shows the palm. "
          "New drawing: the left hand and forearm of a slim 14-year-old girl, seen from the BACK of the hand: she is touching her own face, so the palm faces away from us and we look at the back of her hand, the knuckles and the fingernails. "
          "A small slender girl's hand with long thin fingers, not a man's hand, not a mitten. The four fingers are held together in a soft row, never spread, each finger clearly separate with a clean line between them, a little curved towards the surface so that only the pads touch; every fingertip shows a small clean oval fingernail with a paler tip. Small soft knuckle marks and two thin tendon lines on the back of the hand. The thumb is on the UPPER side of the hand, above the index finger, tucked in close and mostly hidden behind the hand, only its side showing. "
          "The hand is narrow: the back of the hand is no wider than four slim fingers. There is a clear turn at the wrist. The cuff sits loose round the wrist with the wrist coming out of it, and the sleeve is soft cloth with two or three folds at the cuff and a bend along the forearm, its outline tapering and not straight, widening towards the elbow; it runs off the edge of the picture. "
          "The hand fills most of the picture, with the fingertips well inside the picture on the left. Exactly four fingers and one thumb. ")
H31 = ("Attached Image 1 is her model sheet; the last attached image enlarges the sheet's own hands: draw the hand exactly in that manner, only with the fingers holding a pen. Same thick clean black outline, same navy cuff band with one white line, same white blouse sleeve. Draw only the hand, the sleeve and the pen, without paper. Exactly five fingers. ")
H31B = ("Attached Image 1 is her model sheet; the last attached image enlarges the sheet's own hands. Attached Image 2 is this same hand, sleeve and pen: keep exactly its drawing, its outline, its colours, its proportions, its place and size in the picture, the same forearm angle, the same sleeve and the same pen. Draw only the hand, the sleeve and the pen, without paper. Exactly five fingers. ")
H32 = H31.replace(", only with the fingers holding a pen", ", only seen from above").replace("the sleeve and the pen, without paper", "and the sleeve")
H32B = H31B.replace("this same hand, sleeve and pen", "this same hand and sleeve").replace(", the same sleeve and the same pen", " and the same sleeve").replace("the sleeve and the pen, without paper", "and the sleeve")
SPRINT = "Sprinting flat out, chin forward, leaning forward about 25 degrees, with real effort: arms pumping hard and close to the body like a real runner, NEVER held out to the sides, never spread like wings, hands closed in loose fists, no spread fingers. Her hair and scarf ends fly straight back, the bag lifts and bounces behind her hip on its strap. Mouth a little open. "
BASE = dict(identity=True, draw=True, never=True, key=True)


def a(subject, **kw):
    return {**BASE, "subject": subject, **kw}


def style(subject):
    """A different artist's rendition: keeps who she is, drops the model sheet's drawing style."""
    return {
        "identity": False, "draw": False, "never": False, "key": False, "subject": (
            "Attached Image 1 only tells you who she is: a 14-year-old Japanese school girl with a yellow-blonde "
            "chin-length bob with bangs, teal eyes, one big white two-loop ribbon bow on top of her head on a white "
            "headband, two parallel white hair clips on the bangs, white sailor blouse with navy collar, small yellow "
            "neckerchief, charcoal scarf. Keep those features recognisable but do NOT copy the drawing style of Image 1. "
            "Her eyes must be drawn fully visible and wide open, looking straight at the viewer, with nothing covering "
            "them. Modest, ordinary student. No text, letters, logos or watermark anywhere. "
            + subject
        ),
    }


HER = (
    "Character: Kagamine Rin, an ordinary 14-year-old Japanese girl, 152 cm, realistic slim 14-year-old proportions, "
    "not chibi and not adult. Attached Image 1 is her final model sheet: match its face, hair, bow and drawing style "
    "exactly, but NOT its clothes. Bright yellow-blonde chin-length bob with bangs (#FEE45F); two small parallel white "
    "hair clips on the bangs on viewer's left; one big stiff white ribbon bow on top of her head, exactly two loops and "
    "one small square knot, no tails, on a white headband; big round eyes with flat teal irises (#218EA3); fair skin; "
    "the same plain calm face. Clothing is modest and age-appropriate, fully covering, nothing revealing."
)


def rumour(outfit, pose):
    """One rumour about her: same person, same drawing, a different life."""
    return {"identity": False, "draw": True, "never": True, "key": True, "subject": (
        HER + "\nThis picture: full figure from head to shoes, whole bow visible, generous margin all around, at the same "
        f"scale as the model sheet. Outfit: {outfit} Pose: {pose} Face calm and blank in every case. Flat graphic "
        "costume with very few fold lines, the whole design readable from its silhouette."
    )}


def run(moment):
    """One drawing of the run in section 08. Attached Image 2 pins the outfit, the bag, the size and the line."""
    return a(
        "Shot: full figure seen exactly from the side, moving to the viewer's right. Attached Image 2 shows this same girl "
        "in another moment of the same run: match it exactly: the same drawing style and line weight, the same size of "
        "head and body, the same hair shape pushed back, the same bow, the same uniform, the same plain charcoal scarf wrapped "
        "tight around her neck with its two short ends trailing behind, and the same navy rectangular school bag on one dark "
        "strap over her shoulder. The pose is different, as follows. " + moment + " Both legs in black tights and both brown "
        "loafers are clearly separate and anatomically correct, with knees bending the right way. Her whole figure, the bag "
        "and the scarf all fit inside the picture with a generous margin on every side. Do not draw the ground, motion lines, "
        "impact marks, sweat drops or anything else, only her.",
        refs=["assets/gen/raw/g01_run.png"])


SHOE_BASE = (
    "Attached Image 2 is the drawing to match: the same drawing style and line weight, the same navy pleated skirt, black tights, white sleeve with navy cuff, seen exactly from the side, "
    "feet near the bottom of a wide landscape picture, the crop starts at her waist at the top edge so that no head and no chest are in the picture, toes point to the viewer's left. "
    "The indoor shoes are Japanese school uwabaki: a plain white canvas slip-on with a flat pale sole and a solid teal-blue #1E9CC8 rubber toe cap, no laces. Simple clean hands with five fingers. "
)
WALK_SIDE = (
    "She is walking away to the viewer's left, one calm ordinary pace, seen exactly from the side, both feet in the indoor shoes, no loafers in this picture. "
    "One hand carries the navy rectangular school bag by its two handles on the far side of her legs, only partly seen. "
)
DESK_BASE = (
    "Attached Image 2 is the drawing to match: the same drawing style and line weight, the same hair, bow, hair clips, charcoal scarf, navy sailor collar and white blouse with navy cuffs. "
    "Shot: she sits on a school chair at a desk, seen from behind and from her right side, a three-quarter back view from slightly above, wide landscape picture, cropped just below the hips at the bottom edge, with a generous margin at the sides and above the bow. "
    "Only the back of her head, her hair, her right ear and the very edge of her cheek are seen, no eyes visible, no face. Do not draw the desk, the chair or anything else, only her. "
)


# ---- second hand pass (docs/问题根因清单.md, "手又老又恐怖"): the old pictures only give the framing, h21 and h31 give the hand ----
PUSH4 = ("Attached Image 1 is her model sheet; the last attached image enlarges the sheet's own hands. Attached Image 3 is the first drawing of this same push, already finished: "
         "copy its drawing exactly: the same ink line, the same flat cream skin with nothing drawn inside the hand, the same size of hand, the same navy cuff band as wide as there with its one white line, the same plain white sleeve. "
         "Attached Image 2 is the old drawing of this moment and only shows where things go: the height and slope of the arm in the picture, and where the fingertips end; its hand, fingernails, joint lines and thin cuff are wrong and must not be copied. "
         "Side view at floor level, the sleeve enters from the left edge and runs off it as plain empty cloth. No paper and no floor. ")
MARKER4 = ("Attached Image 1 is her model sheet; the last attached image enlarges the sheet's own hands: draw the hand exactly in that manner, only gripping a marker. Attached Image 3 is another finished hand of hers and shows the standard: "
           "its ink line, its flat cream skin, one calm back of the hand, a few small simple finger shapes, its navy cuff band with one white line, in the same proportion of hand to cuff. "
           "Attached Image 2 is the old drawing and only gives the framing: keep the place, size and angle of the marker, the place of the cuff, the path of the white sleeve with its elbow and where it leaves the picture. Its hand with knuckles, joint lines and fingernails is wrong and must not be copied. "
           "The marker stays a thick plain black marker with a blunt tip, its tip the leftmost thing in the picture. The fist is small: at its widest no wider than the cuff. It reads as one simple rounded shape with three or four finger shapes wrapped round the marker, separated by clean single lines, tapering to rounded tips, no fingernails and no joint marks. The sleeve keeps at most three simple ink fold strokes at the inside of the elbow and one hard-edged pale grey shadow on the underside; nothing else on it. Exactly as many fingers as are really in view, never more than five. ")
MARKER5 = ("Attached Image 1 is her model sheet; the last attached image enlarges the sheet's own hands: draw the hand exactly in that manner, only gripping a marker. Attached Image 2 is another finished hand of hers and shows the standard: "
           "its ink line, its flat cream skin, one calm back of the hand, a few small simple finger shapes, its navy cuff band with one white line, and the same proportion of hand to cuff; it holds a thin pen and this one holds a thick marker. "
           "The marker is a thick plain black marker with a blunt tip and one lighter hard-edged stripe of shine at most; its tip is the leftmost thing in the whole picture. "
           "The hand is a small girl's hand and not a glove: the fist is small, at its widest no wider than the cuff, with a clearly narrower wrist coming out of the cuff with a little gap around it. Three or four slim finger shapes wrap round the marker, separated by clean single lines, tapering to rounded tips; no fingernails, no joint marks, no puffy mitten shapes, no thick cartoon outline: the same line weight as on the model sheet's hands. "
           "The sleeve is the model sheet's sleeve: thin soft loose cloth, full and slack, gathered into the cuff so that it puffs out over the cuff and is clearly wider than the cuff there. There is NO elbow in the picture: only the forearm, in one easy line, tapering very slightly narrower towards the cuff, its two outlines never parallel and never ruler-straight, with a little slack in them. Two or three short fold strokes where the cloth gathers at the cuff, one simple hard-edged pale grey shadow along the underside that stops well before the edge of the picture, and nothing else on it. It must not look like a smooth tube, a pipe or a sausage. The hand and cuff are large in the picture, about a third of its width from the marker's tip to the cuff. Exactly as many fingers as are really in view, never more than five. ")
UWABAKI = ("Attached Image 3 shows the one design of her indoor shoes, empty on the left and worn on the right: a Japanese school uwabaki, plain white canvas body, a solid teal-blue #1E9CC8 toe cap with a round curved edge, a flat pale warm grey sole, a small loop tab at the heel, "
           "and ONE white elastic band straight across the instep, with the dark opening seen in front of it and behind it; on her foot, the black tights show in the opening in front of and behind that band. Every shoe in this picture is exactly this design. ")
KEEP_SHOES = ("Attached Image 2 is this exact picture as it stands: keep its framing, skirt, bag, sleeves, hands and legs exactly as they are, line for line, down to the ankles, with black tights, and keep each shoe exactly where it is: the same place, angle, length and sole line. " + UWABAKI +
              "Redraw ONLY the two indoor shoes to this design, each seen at its own angle. No text. ")

ASSETS = {
    # ---- fourteen rumours: same drawing, different clothes and a different pose each ----
    "w01_honor": rumour(
        "a perfectly neat school uniform: white sailor blouse, navy collar, small yellow neckerchief, knee-length navy "
        "skirt, round glasses, white socks, brown loafers.",
        "standing very straight, hugging a stack of three thick books to her chest with both arms."),
    "w02_delinquent": rumour(
        "an old-style delinquent uniform: very long ankle-length navy skirt, short loose sailor blouse over a dark shirt, "
        "a plain white surgical mask under her chin, flat shoes with crushed heels.",
        "slouching with one hand in her skirt pocket and a school bag slung over her shoulder, leaning back."),
    "w03_rich": rumour(
        "an elegant high-collar long-sleeved cream dress to the shins with a wide-brim hat tied behind the bow, white "
        "gloves, small white shoes.",
        "standing poised, both gloved hands holding a small handbag in front of her."),
    "w04_gothic": rumour(
        "a modest long-sleeved black gothic lolita dress to the shins with a high collar and simple white trim, black "
        "stockings, heavy black platform shoes.",
        "standing stiffly side-on to the viewer with her head turned to the front, holding a closed black parasol."),
    "w05_shut_in": rumour(
        "a huge shapeless grey hoodie with the sleeves covering her hands, loose grey sweatpants, one sandal on and worn socks.",
        "hunched forward with her arms wrapped around herself, knees turned in, standing on one foot and rubbing the other foot against her shin."),
    "w06_athlete": rumour(
        "a plain orange track jacket zipped to the neck, matching long track pants with a white side stripe, running shoes.",
        "in a mid-stride running pose, seen from the side, arms pumping, knees up, hair and bow pushed back by the speed."),
    "w07_idol": rumour(
        "a modest pastel idol stage costume: long-sleeved frilled jacket buttoned to the neck, knee-length layered skirt, "
        "white leggings and boots, with a matching headset microphone.",
        "one arm raised straight up pointing to the sky, the other on her hip, in a stiff performance pose with a blank face."),
    "w08_artist": rumour(
        "a paint-stained canvas smock over a long-sleeved striped shirt, long brown trousers, big round headphones around her neck, sneakers.",
        "holding a large sketchbook open in one arm and a brush in the other hand, looking at the viewer."),
    "w09_delivery": rumour(
        "a plain work outfit: blue cap on the back of her head behind the bow, blue long-sleeved work jacket, long dark work trousers, rubber boots.",
        "walking forward, carrying a big bundle of tied newspapers under one arm."),
    "w10_shrine": rumour(
        "a traditional shrine maiden outfit: white kimono top and long red hakama trousers to the ankles, white tabi socks and sandals.",
        "holding a long-handled bamboo broom upright with both hands, standing still."),
    "w11_farmer": rumour(
        "a straw hat hanging on her back, long-sleeved work shirt, baggy indigo farmer's trousers, rubber boots, cotton work gloves.",
        "carrying a large white radish over her shoulder like a bat."),
    "w12_hero": rumour(
        "a home-made superhero costume worn over a fully covering long-sleeved tracksuit: a red cape, a yellow belt, red rain boots.",
        "heroic stance with both fists on her hips and the cape spread out behind her, feet apart."),
    "w13_detective": rumour(
        "an oversized beige trench coat buttoned to the neck and reaching her ankles, a small deerstalker hat tied behind the bow, brown shoes.",
        "peering through a big magnifying glass held in one hand, leaning forward."),
    "w14_alien": rumour(
        "a bulky white retro astronaut space suit with a round open glass helmet around her head, the bow squashed inside the helmet and still clearly visible, big white boots and gloves.",
        "one glove raised in a small blank wave."),
    # ---- full film ----
    "t01_candid_turn": a("Shot: a long-lens candid picture: full figure walking along a street with a school bag on her shoulder, her head turned back over her shoulder towards the viewer, body seen from the side. Blank face."),
    "t02_candid_gate": a("Shot: three-quarter back view from a distance, she is walking away with a school bag in one hand, head slightly down, full figure. Her face turned slightly so the cheek shows."),
    "t03_candid_hand": a(
        "Attached Image 2 is this exact picture as it stands: keep its framing, size, head, face, eyes, bow, hair, ear, scarf, "
        "blouse, sleeve and cuff exactly as they are, line for line. Shot: bust and waist, she raises one hand with the open palm "
        "towards the viewer to block the camera, partly covering her chin, head turned aside. Blank face. Redraw ONLY the open hand, in the "
        "same place and pose with the same spread fingers, about ten percent smaller and slimmer than in Image 2, and in the model "
        "sheet's drawing: all the lines inside the palm and across the fingers of Image 2 are gone, leaving one calm cream shape with a "
        "clean thick-thin outline, and one simple hard-edged darker cream shadow shape at the heel of the palm by the cuff.",
        large=True, refs=["assets/gen/raw/t03_candid_hand.png"]),
    "g01_run": a("Shot: full figure from the side running fast to the viewer's right, long stride, front knee high, arms pumping, leaning forward. Hair and bow pushed back by the speed. Blank face, side view, school bag bouncing behind."),
    "g02_run": a("Shot: full figure from the side running to the viewer's right, both feet off the ground in mid stride, arms wide, leaning far forward, about to lose balance. Hair and scarf flying behind. Side view."),
    "g03_run": a("Shot: full figure from the side stumbling forward to the viewer's right, one foot catching, arms thrown forward, scarf flying up. Side view."),
    "g04_run": a("Shot: full figure from the side, running tired to the viewer's right, shoulders dropped, arms low, short stride, head hanging. Side view."),
    "g05_stand": a("Shot: full figure from the side, standing still facing the viewer's right, arms hanging, head tilted up looking at something very high above her. Side view. Very still."),
    # ---- the run in section 08, one drawing per half beat: one model, one bag, one scarf ----
    "g11_run": run("CONTACT. Her NEAR leg (the one closest to the viewer) is straight down under her hips, its loafer flat on the ground and taking all her weight, knee a little bent. Her FAR leg is folded behind her with the heel kicked up towards her bottom. Her far arm swings forward with a loose fist, her near arm swings back with the elbow bent. Torso leans forward about 10 degrees."),
    "g12_run": run("FLIGHT: both feet off the ground. Her NEAR leg is stretched out behind her, toes just left the ground. Her FAR knee is driven forward and high. Her near arm swings forward with a loose fist, her far arm swings back. Torso leans forward about 15 degrees."),
    "g13_run": run("CONTACT. Her FAR leg (the one furthest from the viewer) is straight down under her hips, its loafer flat on the ground and taking all her weight, knee a little bent. Her NEAR leg is folded behind her with the heel kicked up towards her bottom, clearly drawn in front of the far leg. Her near arm swings forward with a loose fist, her far arm swings back. Torso leans forward about 10 degrees."),
    "g14_run": run("FLIGHT: both feet off the ground. Her FAR leg is stretched out behind her, toes just left the ground. Her NEAR knee is driven forward and high. Her far arm swings forward with a loose fist, her near arm swings back. Torso leans forward about 15 degrees."),
    "g15_run": run("Running flat out and starting to lose control. CONTACT: her NEAR loafer lands flat on the ground ahead of her hips, knee bent. Her FAR leg trails behind, heel up. She leans far forward, about 30 degrees; both arms are flung out wide, the front one reaching ahead with the fingers spread, the back one thrown behind. Mouth a little open."),
    "g16_run": run("Running flat out and starting to lose control. FLIGHT: a huge stride with both feet off the ground, NEAR leg stretched far ahead with the toes up, FAR leg stretched far behind. She leans far forward; both arms are flung out wide with the fingers spread. Mouth a little open."),
    "g17_run": run("Running flat out and starting to lose control. CONTACT: her FAR loafer lands flat on the ground ahead of her hips, knee bent. Her NEAR leg trails behind, heel up, clearly drawn in front. She leans far forward, about 30 degrees; both arms are flung out wide, the near arm reaching ahead with the fingers spread, the far arm thrown behind. Mouth a little open."),
    "g18_run": run("Running flat out and starting to lose control. FLIGHT: a huge stride with both feet off the ground, FAR leg stretched far ahead with the toes up, NEAR leg stretched far behind. She leans far forward; both arms are flung out wide with the fingers spread. Mouth a little open."),
    "g21_trip": run("STUMBLE, first moment: the toe of her front loafer has just caught on the ground and stays there, that leg straight and sloping forward; her other leg is swinging up behind her. Her body has carried on and pitches forward about 35 degrees, both arms thrown forward with the fingers spread. Mouth open."),
    "g22_trip": run("STUMBLE, falling: she is falling forward, body nearly 55 degrees from upright, one foot still pushing against the ground far behind her, the other leg swinging forward and bent, not yet down. Both arms reach down and forward with the fingers spread, about to catch herself. The bag swings forward over her hip. Mouth open."),
    "g23_trip": run("STUMBLE, catching herself: a deep lurching lunge. Her front loafer has slammed flat on the ground far ahead, front knee deeply bent, rear leg stretched out long behind with only its toes on the ground. Body low and leaning forward, arms flung out to the sides for balance. Head up, mouth open."),
    "g24_trip": run("STUMBLE, recovering: she staggers back up, off balance. One loafer is flat on the ground under her hips, knee bent; the other leg drags behind with the toes on the ground. Her shoulders are dropped and her arms hang low and forward, the bag has slid down to her elbow. Head low."),
    "g31_run": run("EXHAUSTED, still trying to run. CONTACT: her NEAR loafer flat on the ground under her hips, knee bent, her FAR leg only a little off the ground behind her. Shoulders dropped, head hanging, arms hanging low and swinging weakly, loose open hands. The bag strap has slipped down to her elbow and the bag hangs low. The scarf ends hang down, no longer flying. Mouth a small flat line."),
    "g32_run": run("EXHAUSTED, still trying to run. A heavy short stride: both feet just barely off the ground, NEAR leg behind, FAR leg ahead, no knee lift at all. Shoulders dropped, head hanging, arms hanging low, loose open hands. The bag strap has slipped down to her elbow and the bag hangs low. The scarf ends hang down, no longer flying. Mouth a small flat line."),
    "g33_run": run("EXHAUSTED, still trying to run. CONTACT: her FAR loafer flat on the ground under her hips, knee bent, her NEAR leg only a little off the ground behind her, drawn in front of the far leg. Shoulders dropped, head hanging, arms hanging low and swinging weakly, loose open hands. The bag strap has slipped down to her elbow and the bag hangs low. The scarf ends hang down, no longer flying. Mouth a small flat line."),
    "g34_run": run("EXHAUSTED, still trying to run. A heavy short stride: both feet just barely off the ground, FAR leg behind, NEAR leg ahead, no knee lift at all. Shoulders dropped, head hanging, arms hanging low, loose open hands. The bag strap has slipped down to her elbow and the bag hangs low. The scarf ends hang down, no longer flying. Mouth a small flat line."),
    "g41_stand": run("She has stopped. Standing still with both loafers flat on the ground, feet slightly apart, facing the viewer's right. Arms hanging, the bag hanging from one hand by its strap, resting near her ankle. Head tilted up, looking at something very high above her. The scarf ends hang straight down. Very still. Mouth a small flat line."),
    "o01_back_gate": a("Shot: full figure seen directly from behind, walking away from the viewer, a school bag held in one hand at her side, ordinary and relaxed. Only the back of her hair and the bow are seen, no face at all."),
    "o02_shoes": a("Shot: only her lower legs and hands, seen from the side: she is bent over changing shoes at a shoe locker, one hand pulling the heel of a brown loafer on, black tights, skirt hem. No head in the picture."),
    "o03_train_sit": a("Shot: full figure seen from behind and to the side, sitting on a bench seat, looking away out of a window to the viewer's far left, hands on the bag on her lap. Only the back of her head and a sliver of her cheek are seen, no eyes visible. Do not draw the seat, only her."),
    "o04_window": a("Shot: bust and waist seen from behind and slightly to the side, sitting with her chin on one hand, looking away out of a window to the viewer's far left. Back of head, no eyes visible."),
    # ---- she wipes the bar off her own face: the BACK of her left hand is towards us, the finger pads are on her face ----
    "h30_wipe_a": a(HEAD_B + "Drawing 1 of 4: the hand arrives and lands. The fingers point up and to the left at about 40 degrees. The forearm rises from the bottom right corner of the picture.", identity=False, sheet=False, refs=["assets/gen/raw/h10_wipe2_b.png"]),
    "h30_wipe_b": a(HEAD_B + "Drawing 2 of 4: the hand slides to the left, dragging. The fingers point to the left and about 20 degrees up, the fingertips bending in a little towards the surface with the friction, the wrist leading. The forearm rises from the lower right at about 35 degrees.", identity=False, sheet=False, refs=["assets/gen/raw/h10_wipe2_b.png"]),
    "h30_wipe_c": a(HEAD_B + "Drawing 3 of 4: the end of the long slide to the left. The fingers point almost straight to the left, the wrist is bent so the back of the hand is flatter than the forearm. The forearm comes up from the bottom right at about 28 degrees, a clear angle at the wrist.", identity=False, sheet=False, refs=["assets/gen/raw/h10_wipe2_b.png"]),
    "h30_wipe_d": a(HEAD_B + "Drawing 4 of 4: the hand comes away and starts to fall. The wrist has dropped first, the fingers are relaxed and loosely curled, trailing behind the wrist, still pointing up and to the left and still together. The forearm comes from the bottom right corner, steeper than before.", identity=False, sheet=False, refs=["assets/gen/raw/h10_wipe2_b.png"]),
    # ---- outro gate: a walk seen from directly behind, four drawings of one cycle, same size and framing as Image 2
    "o11_walk_a": a("Attached Image 2 is the drawing to match: same figure, same size in the picture, same framing, same top of head and same bag held in the hand on the viewer's right. Shot: full figure seen directly from behind, walking away from the viewer. This drawing of the walk: her LEFT leg (viewer's left) is stepped far forward with that foot flat on the ground higher in the picture, her RIGHT leg (viewer's right) trails behind with its heel lifted and the sole of the loafer showing, near the bottom edge of the figure. Her empty arm swings a little outward, the bag swings slightly. No face at all.", refs=["assets/gen/raw/o01_back_gate.png"]),
    "o11_walk_b": a("Attached Image 2 is the drawing to match: same figure, same size in the picture, same framing, same top of head and same bag held in the hand on the viewer's right. Shot: full figure seen directly from behind, walking away from the viewer. This drawing of the walk: the passing position. She stands on her LEFT leg (viewer's left), straight, foot flat on the ground; her RIGHT knee is bent and that lower leg is lifted behind, its foot off the ground and passing beside the standing ankle, sole showing. Arms close to the body. No face at all.", refs=["assets/gen/raw/o01_back_gate.png"]),
    "o11_walk_c": a("Attached Image 2 is the drawing to match: same figure, same size in the picture, same framing, same top of head and same bag held in the hand on the viewer's right. Shot: full figure seen directly from behind, walking away from the viewer. This drawing of the walk: her RIGHT leg (viewer's right) is stepped far forward with that foot flat on the ground higher in the picture, her LEFT leg (viewer's left) trails behind with its heel lifted and the sole of the loafer showing, near the bottom edge of the figure. The bag swings a little behind, her empty arm a little forward. No face at all.", refs=["assets/gen/raw/o01_back_gate.png"]),
    "o11_walk_d": a("Attached Image 2 is the drawing to match: same figure, same size in the picture, same framing, same top of head and same bag held in the hand on the viewer's right. Shot: full figure seen directly from behind, walking away from the viewer. This drawing of the walk: the passing position. She stands on her RIGHT leg (viewer's right), straight, foot flat on the ground; her LEFT knee is bent and that lower leg is lifted behind, its foot off the ground and passing beside the standing ankle, sole showing. Arms close to the body. No face at all.", refs=["assets/gen/raw/o01_back_gate.png"]),
    # ---- outro lockers: changing shoes, three moments, same size and framing as Image 2 (toes to the viewer's left, no head)
    "o21_shoes_a": a("Attached Image 2 is the drawing to match: same crop from the hips down, same size, same brown loafers and black tights, feet at the same height near the bottom of the picture, toes pointing to the viewer's left. No head in the picture. Moment 1: she is bent over at a shoe locker. Her front foot is flat on the ground. Her rear foot stands on its toes with the heel raised out of the loafer's back, and one hand reaches down with the index finger hooked inside the back of that loafer, a simple clear hand with five fingers; nothing else in the hand. The other hand rests on her thigh. Simple clean hands.", refs=["assets/gen/raw/o02_shoes.png"]),
    "o21_shoes_b": a("Attached Image 2 is the drawing to match: same crop from the hips down, same size, same brown loafers and black tights, feet at the same height near the bottom of the picture, toes pointing to the viewer's left. No head in the picture. Moment 2: both loafers are now flat on the ground, fully on her feet. She is half straightened up, knees a little bent, one hand tugging down the hem of her skirt at the side, the other hand hanging loose in front of the knee. Simple clean hands.", refs=["assets/gen/raw/o02_shoes.png"]),
    "o21_shoes_c": a("Attached Image 2 is the drawing to match: same crop from the hips down, same size, same brown loafers and black tights, feet at the same height near the bottom of the picture, toes pointing to the viewer's left. No head in the picture. Moment 3: she has straightened up and is taking the first step away to the viewer's left: rear foot on its toes about to leave the ground, front leg straight with the loafer flat. Both arms hang relaxed, only the hands and cuffs and the skirt visible. Simple clean hands.", refs=["assets/gen/raw/o02_shoes.png"]),
    # ---- outro, second pass: a day in order. Train: she gets up. Lockers: loafers go in, indoor shoes go on. Classroom: chin on hand, then the paper. ----
    "o31_train_rise": a("Attached Image 2 is the drawing to match: same figure, same size in the picture, same line weight, same uniform, same charcoal scarf, same loafers, seen from the side and a little from behind, facing the viewer's left. Shot: full figure. This drawing: she is getting up from a bench seat. Her hips have just lifted off the seat (do not draw the seat), knees still bent, torso leaning forward over her knees, both loafers flat on the ground. The navy rectangular school bag is no longer on her lap: one hand holds it by its two handles and it hangs in front of her shins. The other hand pushes on her thigh just above the knee. Her head looks ahead and away to the viewer's far left, so that only the back of her head and a sliver of her cheek are seen, no eyes visible.", refs=["assets/gen/raw/o03_train_sit.png"]),
    "o32_train_stand": a("Attached Image 2 is the drawing to match: same figure, same drawing style and line weight, same uniform, same charcoal scarf, same loafers, same navy school bag. Attached Image 3 shows how she looks from directly behind. Shot: full figure, standing upright, both feet flat on the ground, seen three-quarters from behind: she has just stood up and is turning away from the viewer towards the viewer's upper left. The bag hangs by its handles from the hand on the viewer's right. The other arm hangs relaxed. Only the back of her head and the edge of her cheek are seen, no eyes visible, no face.", refs=["assets/gen/raw/o03_train_sit.png", "assets/gen/raw/o01_back_gate.png"]),
    "o41_shoes_put": a("Attached Image 2 is this exact picture as it stands: keep its framing, skirt, sleeve, hand, bag, the pair of loafers and the indoor shoes exactly as they are, line for line. Redraw ONLY her two feet and ankles in black tights, so that they read as two separate feet and not one black lump: the near foot stays exactly where it is; the far foot stands a little ahead of it and higher in the picture, with its own complete clean outline and a clear gap of empty background between the two feet up to the toes, the two ankles clearly apart. Each foot has one simple hard-edged dark grey lighter shape along its top, the same on both. Behind the loafers, at the hand, there is only the background.", refs=["assets/gen/raw/o41_shoes_put.png"]),
    "o42_shoes_step": a(KEEP_SHOES + "Her lifted foot and the empty shoe under it stay as they are; the empty shoe shows the band with the dark opening, and the shoe she is wearing shows the band with black tights in the opening.", refs=["assets/gen/raw/o42_shoes_step.png", "work/gen/fix3/ref_uwabaki.png"]),
    "o43_shoes_heel": a("Attached Image 2 is this exact picture as it stands: keep its framing, skirt, sleeves, cuffs, bag and legs exactly as they are, line for line, and keep each shoe exactly where it is: the same place, angle, length and sole line. " + UWABAKI + "Redraw the two indoor shoes to this design, and redraw her near hand, which comes down from the cuff in the same place with the index finger hooked inside the back of that shoe at the heel, easing it on: a small slim hand as on the model sheet, no wider than the cuff, about two cuff widths long, a narrow wrist, one calm cream shape with thin tapering fingers and simple rounded tips, no claw, no knuckle or joint lines, no fingernails, only clean single lines between fingers that touch. No text.", refs=["assets/gen/raw/o43_shoes_heel.png", "work/gen/fix3/ref_uwabaki.png"]),
    "o44_walk_a": a(KEEP_SHOES, refs=["assets/gen/raw/o44_walk_a.png", "work/gen/fix3/ref_uwabaki.png"]),
    "o44_walk_b": a(KEEP_SHOES, refs=["assets/gen/raw/o44_walk_b.png", "work/gen/fix3/ref_uwabaki.png"]),
    "o44_walk_c": a(KEEP_SHOES, refs=["assets/gen/raw/o44_walk_c.png", "work/gen/fix3/ref_uwabaki.png"]),
    "o44_walk_d": a(KEEP_SHOES, refs=["assets/gen/raw/o44_walk_d.png", "work/gen/fix3/ref_uwabaki.png"]),
    "o51_desk_chin": a(DESK_BASE + "This drawing: she is sitting with her chin in her hand, gazing out of a window to the viewer's far left. Her right arm is on the viewer's right: the point of the elbow is planted low at the lower right of the figure, the forearm rises almost straight up from it, and the hand cups her jaw from below, seen from behind. Her head is turned away from us towards the viewer's left. The underside of the elbow is drawn clearly and ends there, because it rests on a desk top that is added later.", refs=["assets/gen/raw/o04_window.png"]),
    "o52_desk_mid": a(DESK_BASE + "This drawing: she has just taken her chin off her hand. Her head has started to turn down and forward, still away from us. Her right arm on the viewer's right has dropped: the elbow is still low at the lower right, the forearm now slants forward and down at about forty-five degrees away from us, the hand open and half hidden, on its way down to the desk.", refs=["assets/gen/raw/o04_window.png"]),
    "o53_desk_press": a(DESK_BASE + "This drawing: she is looking down at something on her desk, head bowed and facing away from us, only the back of her head, the bow and her hair are seen. Her right arm on the viewer's right reaches forward away from us, the forearm almost flat, and the open hand presses flat down at the lower right of the figure, palm down, fingers spread a little, the back of the hand visible. Nothing is under the hand in this picture.", refs=["assets/gen/raw/o04_window.png"]),
    # ---- the last act, second pass ----
    "h10_wipe_a": a("Shot: only her left hand and white blouse sleeve with a navy cuff band with one white line, entering from the bottom right corner of the picture. We see the PALM side of the hand, as if she is pressing it against a window pane from the other side of the glass, reaching up and to the left. The four fingers are together, gently straight, pointing to the upper left; the soft pads of the index and middle fingertips are pressed flat on the glass; the thumb lies relaxed beside the palm, NOT sticking out, tucked close. The sleeve carries on and runs off the bottom right edge of the picture. Slim 14-year-old hand, exactly five fingers, one hard-edged shadow tone.", identity=False, sheet=False, refs=["assets/gen/cut/p08_hand_arm.png"]),
    "h10_wipe_b": a("Shot: only her left hand and white blouse sleeve with a navy cuff band with one white line, entering from the right edge of the picture, lower right. We see the PALM side of the hand, as if it is sliding across a window pane from the other side of the glass, moving to the left, wiping. The four fingers are together and point to the left and a little up, dragged by friction: the fingertips bend back slightly, pads pressed flat on the glass; the thumb is tucked close to the palm, NOT sticking out. No fingernails are visible, because we see the palm side. The sleeve runs off the right edge of the picture. Slim 14-year-old hand, exactly five fingers, one hard-edged shadow tone.", identity=False, sheet=False, refs=["assets/gen/cut/p08_hand_arm.png"]),
    "h10_wipe_c": a("Shot: only her left hand and white blouse sleeve with a navy cuff band with one white line, entering from the right edge of the picture. We see the PALM side of the hand at the end of a wiping movement across a window pane from the other side of the glass. The four fingers are together and point straight to the left, nearly level, the wrist bent so the palm has turned a little; the fingertip pads are pressed flat; the thumb trails close beside the palm, NOT sticking out. No fingernails are visible anywhere, because we see the palm side. The sleeve runs off the right edge of the picture. Slim 14-year-old hand, exactly five fingers, one hard-edged shadow tone.", identity=False, sheet=False, refs=["assets/gen/cut/p08_hand_arm.png"]),
    "h10_wipe_d": a("Shot: only her left hand and white blouse sleeve with a navy cuff band with one white line, entering from the bottom right corner of the picture. We see the PALM side of the hand coming away after wiping a window pane: the wrist has dropped, the four fingers relax, slightly bent toward us, pointing up and to the left, the finger pads facing us; the thumb is relaxed and close to the palm, NOT sticking out. No fingernails are visible anywhere, because we see the palm side. The sleeve runs off the bottom right edge of the picture. Slim 14-year-old hand, exactly five fingers, one hard-edged shadow tone.", identity=False, sheet=False, refs=["assets/gen/cut/p08_hand_arm.png"]),
    "h11_strike_a": a("Attached image: this hand and pen, the same drawing style, ink line, skin and black ballpoint pen; draw only the hand and sleeve, without the paper. Short forearm: the cuff of her white school blouse comes right up to the wrist, a navy cuff band with one white line, then the white sleeve. New pose, seen from straight above a desk: the right hand writing, the arm reaching far out to the left, coming in from the bottom right corner at a low angle; the pen tip is at the far upper left of the hand and pressed on the paper, about to pull a ruled line toward the right; the wrist is straight and stretched, the pen leans back over the knuckles toward the right. Fingers relaxed around the pen. Exactly five fingers. The sleeve runs off the bottom right edge of the picture.", identity=False, sheet=False, refs=["work/gen/ref_handpen.png"]),
    "h11_strike_b": a("Attached image: this hand and pen, the same drawing style, ink line, skin and black ballpoint pen; draw only the hand and sleeve, without the paper. Short forearm: the cuff of her white school blouse comes right up to the wrist, a navy cuff band with one white line, then the white sleeve. New pose, seen from straight above a desk: the right hand in the middle of pulling a straight line across the paper from left to right. The arm comes in from the bottom right of the picture; the pen tip is to the left of the hand, pressed down, the fingers tight, the wrist a little bent. Exactly five fingers. The sleeve runs off the bottom edge of the picture.", identity=False, sheet=False, refs=["work/gen/ref_handpen.png"]),
    "h11_strike_c": a("Attached image: this hand and pen, the same drawing style, ink line, skin and black ballpoint pen; draw only the hand and sleeve, without the paper. Short forearm: the cuff of her white school blouse comes right up to the wrist, a navy cuff band with one white line, then the white sleeve. New pose, seen from straight above a desk: the right hand at the end of pulling a line from left to right: the hand is drawn in close to the body, the fingers bent, the wrist bent back and rotated, the pen more upright with its tip just left of the fingers, pressed on the paper. The arm comes up from the bottom edge of the picture. Exactly five fingers. The sleeve runs off the bottom edge.", identity=False, sheet=False, refs=["work/gen/ref_handpen.png"]),
    "h12_close_a": a("Attached image: this hand and pen, the same drawing style, ink line, skin and black ballpoint pen; draw only the hand and the pen, without paper. Close-up, much larger, seen from above a desk: the thumb, index and middle fingers holding the pen, entering from the right of the picture, the wrist and arm running off the bottom right edge. The pen points to the left and down; its silver tip is in the left third of the picture, fully inside the picture with clear margin around it, hovering. The fingers are still and careful. Thick-thin ink line, one hard-edged shadow tone.", identity=False, sheet=False, refs=["work/gen/ref_handpen.png"]),
    "h12_close_b": a("Attached image: this hand and pen, the same drawing style, ink line, skin and black ballpoint pen; draw only the hand and the pen, without paper. Close-up, much larger, seen from above a desk: the thumb, index and middle fingers holding the pen, entering from the right of the picture, the wrist and arm running off the bottom right edge. The pen points to the left and down, more upright than resting, pressed firmly, the fingertips whiter with the pressure and the knuckle of the index finger raised; its silver tip is in the left third of the picture, fully inside the picture with clear margin around it. Thick-thin ink line, one hard-edged shadow tone.", identity=False, sheet=False, refs=["work/gen/ref_handpen.png"]),
    "h13_adult_crayon_a": a("Shot: only a grown man's big right hand and forearm, with a dark charcoal suit sleeve and a white shirt cuff, entering from the bottom right corner of the picture, seen from above a desk. He holds a short stubby orange wax crayon with its paper wrapper, the way an adult awkwardly draws for a small child, tip pointing down and to the left, the crayon tip well inside the picture. Thick adult fingers, short clean nails, a plain middle-aged hand with no ring. The sleeve runs off the bottom right edge. Exactly five fingers.", identity=False),
    "h13_adult_crayon_b": a("Shot: only a grown man's big right hand and forearm, with a dark charcoal suit sleeve and a white shirt cuff, entering from the right edge of the picture, lower right, seen from above a desk. He presses a short stubby orange wax crayon with its paper wrapper on to the paper, colouring, the way an adult awkwardly draws for a small child, wrist turned, tip pointing to the left and down, the crayon tip well inside the picture. Thick adult fingers, short clean nails, a plain middle-aged hand with no ring. The sleeve runs off the right edge. Exactly five fingers.", identity=False),
    "h10_wipe2_a": a(HEAD_W + "New pose: the whole hand is turned so the fingers point to the upper left at about 45 degrees, the forearm enters from the bottom right corner of the picture and the sleeve runs off the bottom right edge. The four fingers are together, gently straight, the pads of the index and middle fingertips pressed flat as if on a window pane. The thumb lies close along the palm on its lower left side.", identity=False, sheet=False, refs=["assets/gen/raw/h10_wipe_c.t2.png"]),
    "h10_wipe2_b": a(HEAD_W + "New pose: the hand is turned so the fingers point to the left and about 20 degrees up, the forearm comes from the lower right and the sleeve runs off the right part of the bottom edge. The hand is sliding to the left across a window pane and the fingertips bend back a little with the friction, pads pressed flat. The thumb lies close along the palm on its lower side.", identity=False, sheet=False, refs=["assets/gen/raw/h10_wipe_c.t2.png"]),
    "h10_wipe2_d": a(HEAD_W + "New pose: the hand is coming away after wiping. The wrist has dropped, the forearm enters from the bottom right corner and the sleeve runs off the bottom right edge. The four fingers point up and to the left, relaxed and a little apart, slightly bent toward us with the finger pads facing us. The thumb is relaxed on the lower left side of the palm.", identity=False, sheet=False, refs=["assets/gen/raw/h10_wipe_c.t2.png"]),
    "h10_wipe2_c": a(HEAD_W.replace("when the fingers point up and to the left the thumb is on the LOWER LEFT side of the palm, below the fingers. ", "the thumb is on the lower side of the palm, below the fingers. ") + "New pose: at the end of a long wiping movement to the left. The fingers point to the left and only slightly up, nearly level. The forearm rises from the lower right at a shallow angle of about 28 degrees, coming in from the bottom right corner, and the wrist is bent so the hand is flatter than the forearm. The sleeve runs off the bottom right edge. The pads of the fingers are pressed flat as if on a window pane. The thumb lies close along the palm on its lower side.", identity=False, sheet=False, refs=["assets/gen/raw/h10_wipe2_b.png"]),
    "h31_pen_rest": a(H31 + "Attached Image 2 is the guide for this drawing: the silhouette, the size and place of the hand, of the cuff, of the sleeve are all right, and so is the proportion of the hand to the cuff; keep them. Redraw it cleanly as a finished drawing with one confident thick-thin ink line, in the manner of the sheet, correcting anything distorted or doubled, with no stretched streaks on the sleeve. Pose: seen from straight above a desk, a pen held ready but not writing, the fingers slack and undecided. The sleeve runs off the bottom right corner of the picture. A thin plain black ballpoint pen with a cap, a silver band and a small clip: its silver tip is the leftmost thing in the whole picture, pointing left and a little down; the shaft passes through the fork of the thumb. The back of the hand faces up and is one simple clean shape. Only three small simple finger shapes show near the tip: the thumb lying along the pen, the index finger on top of the pen, the middle finger under it; the last two fingers are hidden under the hand. Behind the pen in the fork of the thumb the skin is one flat tan shadow shape, with no gap to see through.", identity=False, refs=["work/gen/fix3/hands_raw/guide_h31.png"]),
    "h31_pen_write": a(H31B + "New moment: the same hand now pressing the pen on the paper to write. The fingers close a very little, the index finger arches very slightly, the pen is a little steeper, its tip still the leftmost thing in the picture.", identity=False, refs=["work/gen/fix3/hands_raw/h31_pen_rest.png"]),
    "h31_pen_lift": a(H31B + "New moment, a small change only: the same hand has lifted away from the paper and pulled back a little. The pen is about ten degrees flatter than in Image 2 and no more, its tip still the leftmost thing in the picture. The fingers have loosened: the index finger has risen a very little off the pen, staying close to it. The same few simple finger shapes as in Image 2, no additional fingers showing, nothing spread.", identity=False, refs=["work/gen/fix3/hands_raw/h31_pen_rest.png"]),
    "h31_pen_tight": a(H31B + "New moment: she has made up her mind. The fingers have closed firmly on the pen, the small simple shapes of the fingers bunch closer and the back of the hand arches a little, the wrist turned very slightly in. It stays the same small hand, never a fist, no bigger than before. The fork of the thumb stays exactly as in Attached Image 2: one flat tan shadow shape behind the pen with a clean closed outline, no extra curled or spiky strokes near the thumb. The pen tip is still the leftmost thing in the picture.", identity=False, refs=["work/gen/fix3/hands_raw/h31_pen_rest.png"]),
    "h32_place_a": a(H32 + "Attached Image 2 is the guide for this drawing: the silhouette, the size and place of the hand, of the cuff, of the sleeve are all right, and so is the proportion of the hand to the cuff; keep them. Redraw it cleanly as a finished drawing with one confident thick-thin ink line, in the manner of the sheet, correcting anything distorted or doubled, with no stretched streaks on the sleeve. Pose: seen from straight above a desk, her LEFT hand comes in from the bottom left corner of the picture, the back of the hand facing up, the sleeve running off the bottom left corner of the picture with plain empty cloth, its outline loose and not ruler-straight. The fingers point to the upper right, together and gently straight, the tips of the index and middle fingers pressing flat down, as if sliding a sheet of paper forward along a desk. The fingertips stay where the guide has them, near the top right of the picture. Only two or three clean lines separate the fingers. The thumb lies tucked close beside the hand on its lower right side, one simple shape. Do not draw the paper or the desk.", identity=False, refs=["work/gen/fix3/hands_raw/guide_h32.png"]),
    "h32_place_b": a(H32B + "New moment, a small change only: the same left hand starting to lift off after putting something down. The fingers stay together exactly as in Image 2, only relaxed: the fingertips curl a very little, so the fingers look a little shorter, with the same three clean lines between them and one small gap at most. The thumb moves a little away from the hand. The fingertips stay near the top right of the picture, no fingers spread. Do not draw the paper or the desk.", identity=False, refs=["work/gen/fix3/hands_raw/h32_place_a.png"]),
    "g51_run": run(SPRINT + "CONTACT. Her NEAR loafer lands flat on the ground just ahead of her hips, knee a little bent, taking all her weight. Her FAR leg trails far behind with the heel kicked up high. Her FAR arm is pumped forward with the elbow bent at a right angle and a tight fist by her chin; her NEAR arm is driven straight back with the elbow bent at a right angle and a tight fist by her hip."),
    "g52_run": run(SPRINT + "FLIGHT: a huge stride with both feet well off the ground. Her NEAR leg stretched far behind her with the toes pointed, her FAR knee driven forward and high. Her NEAR arm is pumped forward with the elbow bent at a right angle and a tight fist by her chin; her FAR arm is driven back with the elbow bent at a right angle."),
    "g53_run": run(SPRINT + "CONTACT. Her FAR loafer lands flat on the ground just ahead of her hips, knee a little bent, taking all her weight. Her NEAR leg trails far behind with the heel kicked up high, clearly drawn in front of the far leg. Her NEAR arm is pumped forward with the elbow bent at a right angle and a tight fist by her chin; her FAR arm is driven straight back with the elbow bent at a right angle."),
    "g54_run": run(SPRINT + "FLIGHT: a huge stride with both feet well off the ground. Her FAR leg stretched far behind her with the toes pointed, her NEAR knee driven forward and high. Her FAR arm is pumped forward with the elbow bent at a right angle and a tight fist by her chin; her NEAR arm is driven back with the elbow bent at a right angle."),
    "h01_pen": a("Shot: only a right hand and white sleeve with navy cuff coming in from the bottom right, holding a plain black ballpoint pen the way one writes, pen tip pointing down and to the left, hovering. The sleeve carries on and runs off the bottom edge of the picture. Slim hand, exactly five fingers.", identity=False),
    "h02_pen_low": a("Shot: only a right hand and white sleeve with navy cuff coming in from the bottom right, holding a plain black ballpoint pen pressed down, tip touching, writing, wrist low and the fingers tight. The sleeve carries on and runs off the bottom edge of the picture. Slim hand, exactly five fingers.", identity=False),
    "h03_push": a("Shot: only a hand and white sleeve seen from the side at floor level, entering from the left, fingertips pushing a small sheet of white paper forward along the floor to the right. The sleeve runs off the left edge of the picture. Do not draw a floor or a door, only hand, sleeve and paper. Exactly five fingers.", identity=False),
    "h04_marker": a("Shot: only a right hand and white sleeve with navy cuff coming in from the bottom right, gripping a thick black marker pen tightly in a fist-like tense grip, writing, tip pointing down and to the left. The sleeve runs off the bottom edge of the picture. Exactly five fingers.", identity=False),
    "k01_flowers": {"identity": False, "draw": False, "never": False, "key": False, "sheet": False, "subject": "Two simple flowers drawn by a five-year-old child in thick wax crayon on plain white paper: wobbly round yellow centres, five uneven pink petals on one and five uneven orange petals on the other, a scribbled green stem each, side by side. Charming and clumsy, real crayon texture, nothing else on the paper, no text."},
    # ---- candidates for the opened eyes: only the irises get used, warped into the drawn eyes ----
    "e01_eyes_shining": {
        "identity": False, "draw": False, "never": False, "key": False, "sheet": False,
        "refs": ["assets/gen/raw/p05_face_close.png"], "subject": (
            "Attached Image 1 is a finished close-up of a character's face. Redraw exactly this same picture with the same "
            "composition, same lines, same flat colours and the same face, and change ONLY the two irises: they must now be "
            "beautiful, alive and shining, painted by a top Japanese animation key artist. Hand-painted flat shapes with crisp "
            "hard edges, no airbrush and no blur: a deep teal shadow under the upper lash, the iris lightening downward through "
            "#048396, #218EA3 and #5BB8CA in clean hand-cut shapes, a few irregular light flecks, and a sharp irregular highlight "
            "with a hand-drawn shape, not a plain white circle. No stars, no hearts, no generic moe sparkle. Same for both eyes "
            "but not perfectly mirrored. Keep the solid green background.")},
    "e02_eyes_shining": {
        "identity": False, "draw": False, "never": False, "key": False, "sheet": False,
        "refs": ["assets/gen/raw/p05_face_close.png"], "subject": (
            "Attached Image 1 is a finished close-up of a character's face. Redraw exactly this same picture with the same "
            "composition, lines and flat colours, and change ONLY the two irises, in the manner of a stylish auteur animated film "
            "with a bold print-like graphic look. The irises are made of only four flat colours (#048396, #218EA3, #5BB8CA, #B0E8EA) "
            "in bold simple shapes with crisp edges, with a dark pupil and a window-like reflection of bright light in each eye, as "
            "if she has just looked up towards a bright window. They should look wet, awake and full of light, while staying flat and "
            "graphic. No gradients, no glow, no stars. Keep the solid green background.")},
    "e03_paintover": {
        "identity": False, "draw": False, "never": False, "key": False, "sheet": False,
        "refs": ["work/eye/base_face.png"], "subject": open(__file__.replace("prompts.py", "../eye/prompt_paintover.txt"), encoding="utf-8").read()},
    "e04_paintover": {
        "identity": False, "draw": False, "never": False, "key": False, "sheet": False,
        "refs": ["work/eye/base_face.png"], "subject": open(__file__.replace("prompts.py", "../eye/prompt_paintover.txt"), encoding="utf-8").read()},
    # ---- story shots ----
    "p07_hand_wipe": a(
        "Shot: only her right hand and white blouse cuff with its navy cuff band, entering from the bottom right corner, "
        "reaching up and to the left, large in the frame. The thumb is extended and pressed flat, as if rubbing something "
        "away with the pad of the thumb; the four fingers are curled lightly into the palm. Seen from the front. Slim "
        "14-year-old hand with exactly five fingers, simple and well drawn, one hard-edged shadow tone. Nothing else in the "
        "picture: no face, no hair.",
        identity=False),
    "p01_bust_front": a(
        "Shot: bust portrait, perfectly frontal and symmetrical posture, head and shoulders down to mid chest, the whole "
        "bow visible with margin above it, face calm and blank, mouth one short flat line, looking straight into the "
        "lens. Portrait fills the frame. Large image, very clean lines. No shadow tone on the face."),
    "p02_seated_high": a(
        "Shot: full figure of her sitting upright on an invisible chair, seen from the front and from about 35 degrees "
        "above, as if the camera is high up at the front of a classroom. Back straight, both arms straight down, hands "
        "resting together on her lap, knees together, feet side by side on the ground. She stares straight ahead, "
        "blank, not at the viewer. Do not draw a chair, a desk or anything else, only her. The skirt falls flat and simple "
        "over her knees, not flared. Strong afternoon sun from the viewer's upper RIGHT: one hard-edged shadow tone only "
        "on the viewer's LEFT side of hair, neck, blouse and skirt, flat paint with no gradient on the sleeves."),
    "p03_phone_over_shoulder": a(
        "Attached Image 2 is this exact picture as it stands: keep its wide 16:9 framing, the back of her head, bow, hair clips, "
        "scarf, shoulders and the phone exactly where and how they are, line for line, and keep its colours. The phone is a plain "
        "black smartphone held sideways in LANDSCAPE orientation, its screen solid flat pure magenta #FF00FF because it will be replaced. "
        "Attached Image 3 shows the model sheet's hands enlarged: this is how her hands are drawn. Redraw ONLY her two hands, her cuffs and the "
        "sleeves below them. The hands in Image 2 are wrong: too long, too thin and bony, like an old person's, with long fingers running up the sides of the phone, lines and "
        "ridges all over them and a long bare forearm. Hers are a 14-year-old girl's hands: small, short and soft in shape, simple, young. The cuffs come up much closer to the phone: each navy cuff with its one "
        "white line sits just below the lower corner of the phone, about one cuff's width below it, and its sleeve comes up with it, thin loose cloth, plain and slack, a little wider than the cuff. No bare forearm is seen. "
        "From the cuff a short narrow wrist goes into a small rounded hand that holds the short end of the phone from behind: the fingers are hidden behind the phone and no fingertip shows anywhere: on the outer side the hand's edge is one smooth simple curve from the wrist up to where it meets the phone. "
        "One short slim thumb, tapering to a rounded tip and no longer than the cuff is wide, lies on the screen near that end, at the same height as in Image 2. "
        "Each hand is one calm simple shape with a clean outer line and nothing at all drawn inside it; the fork of the thumb is one smooth curve. Exactly one simple hard-edged lighter shape along the top of the thumb. "
        "The phone is much wider than a hand is long. Night palette: a dark room, the hands in cold navy-grey tones with one hard-edged lighter "
        "shape where the screen light hits, the same tones as Image 2.",
        large=True, refs=["work/gen/fix5/p03_current.png", "work/gen/fix3/sheet_hands.png"]),
    "p04_face_lit_by_phone": a(
        "Attached Image 2 is this exact picture as it stands: keep its framing and size, bow, hair, hair clips, ears, scarf, collar, the deep cold navy palette and every hard-edged shape of pale cold blue light exactly as they are, line for line. "
        "She is alone in a dark room at night, lit only by a phone below her face, reading what people say about her. This is the most painful moment of the film and a black bar will cover her eyes, so everything is in the lower face. Redraw ONLY these three things of her face: "
        "NOSE: exactly the sheet's nose, one very small dot-like tick just under the eye line, no longer than a third of the mouth's width; no bright patch hanging from it and no pointed shape of light. "
        "BROWS: thin short tapered single lines as on the sheet, high up and mostly hidden by the bangs, far thinner than the eye's lash line, nothing that could be read as a closed eye. "
        "MOUTH: small as on the sheet, tightly pressed shut, the thick-thin line pulled slightly downward at both corners, with the lower lip drawn in a little: a short tiny ink tick under the centre of the line. It must not be one flat straight line and must not be open, no teeth. "
        "Keep her eyes where they are, open and looking down, all of her eyes and lashes inside the same band of the face.",
        large=True, refs=["assets/gen/raw/p04_face_lit_by_phone.png"]),
    "p05_face_close": a(
        "Shot: extreme close-up of her face, perfectly frontal and symmetrical, framed from just above the eyebrows-bangs "
        "line and hair to just below the chin; the face fills the height of the frame. Eyes wide open, large and round, "
        "looking straight into the lens, with flat plain teal irises with no highlight at all, no reflection, no pupil "
        "detail: empty and hollow. Upper lashes are one solid bold black shape. Thin simple eyebrows. Mouth one short "
        "flat line. Extremely clean large drawing, lines crisp at high resolution. No shadow tone on the face."),
    "p06_hand_pinch": a(
        "Shot: only her right hand and white blouse cuff with its navy cuff band, entering from the bottom right corner, "
        "reaching up and to the left. Thumb and index finger pinch together as if peeling a strip of tape off something; "
        "the other three fingers relaxed and curled. Seen from the front. Slim 14-year-old hand with exactly five fingers, "
        "simple and well drawn, one hard-edged shadow tone. Nothing else in the picture: no face, no hair, no tape.",
        identity=False),
    # ---- the fourteen versions of her, each by a different imagined hand ----
    "r01_id_photo": style(
        "Rendition: a stiff ID-photo portrait painted in flat dull realistic tones, harsh frontal flash, pale blue-grey "
        "backdrop, shoulders square, expressionless, head and shoulders only, centred."),
    "r02_shoujo_manga": style(
        "Rendition: a single panel from a 1980s shoujo manga, black ink and screentone only, no colour, floating "
        "flowers behind her, huge dramatic eyes with many highlights, hair with big flowing ink shapes. Bust, three-quarter view."),
    "r03_crayon": style(
        "Rendition: a drawing by a five-year-old child in wax crayon on white paper: wobbly lines, potato-shaped head, "
        "huge bow, stick arms, yellow scribble hair, a scribbled sun in a corner. Charming and funny. Full figure."),
    "r04_police_sketch": style(
        "Rendition: a police composite sketch in soft graphite on off-white paper, monochrome, frontal head and shoulders, "
        "cold and unflattering, careful shading, no colour at all."),
    "r05_court_sketch": style(
        "Rendition: a Japanese courtroom sketch in loose colored pencil on cream paper, she sits on a bench in profile "
        "three-quarter view from the side with her hands on her knees, hasty lines, a blank background with a few hatching strokes."),
    "r06_sticker": style(
        "Rendition: a messaging-app sticker meme: extremely simplified chibi head with a smug dead-pan smirk, thick black "
        "outline, flat colours, thick white die-cut border around the silhouette, on a plain light grey background."),
    "r08_pixel": style(
        "Rendition: a 16-colour 1990s video game portrait in strict pixel art, each pixel clearly visible on a coarse grid "
        "about 64 by 64 pixels, frontal bust, limited palette, plain dark blue background."),
    "r09_ukiyoe": style(
        "Rendition: an Edo-period ukiyo-e woodblock print of her as a bust portrait: flat areas of colour, elegant black "
        "keylines, subtle woodgrain in the colour, a pale beige paper and a plain mica-grey background."),
    "r10_gacha": style(
        "Rendition: a glossy mobile-game gacha card illustration: over-the-top pretty anime rendering, sparkles, light "
        "beams, floating ribbons, magical glowing background, heroic bust pose, fully clothed in the same school uniform."),
    "r11_oil": style(
        "Rendition: a pompous classical oil portrait in the manner of a Baroque court painter: visible heavy brushwork, "
        "dark brown background, dramatic side light, a dignified three-quarter bust, the school uniform painted very seriously."),
    "r12_chalk": style(
        "Rendition: a quick doodle in white and yellow chalk on a dark green school blackboard, smudged, simple cartoon "
        "lines, a bust portrait, as if a classmate drew it during a break."),
    "r13_stencil": style(
        "Rendition: a black spray-paint stencil on a grey concrete wall, hard stencil shapes with bridges and overspray "
        "specks, only black paint with a splash of yellow on the hair, frontal bust."),
    "r15_class_photo": {"identity": False, "draw": False, "never": False, "key": False, "subject": (
        "An old faded black-and-white class photograph of a Japanese primary school's graduating class, taken in the 2010s on cheap film and "
        "printed small: soft focus, visible film grain, slightly low contrast, a little faded. About forty 12-year-old children in dark "
        "school uniforms stand in four rows on steps in front of a plain concrete school building with windows, seen from straight in front "
        "and a little from afar, all facing the camera. Each child is a different height and has a different face, hairstyle and posture, "
        "like real children: some short hair, some long, some with glasses, a few looking slightly away, one laughing; shadows from the "
        "afternoon sun. Hand-painted in monochrome ink wash in the manner of a well-observed Japanese animated film's photograph prop, "
        "believable but not photo-real. Attached Image 1 only tells you who one of the children is: in the second row from the top, a little to the right of the "
        "centre, one girl with a chin-length light-blonde bob and one big white two-loop ribbon bow on her head, wearing the same dark uniform, "
        "her face plain. The whole picture is monochrome; her hair is simply the lightest hair in the photo. No text, no caption, no frame, no border.")},
    "r14_tabloid": style(
        "Rendition: a coarse grainy black-and-white newspaper picture taken from far away with a telephoto lens, as if "
        "drawn in heavy ink wash: she is walking and turning her head toward the viewer, half-length, an out-of-focus "
        "school gate behind her, harsh contrast, monochrome."),
    "h11_marker_floor": a(MARKER5 + "Shot: seen from above, a right hand and forearm writing on the floor with a tense grip, marker tip pointing down and to the left. The forearm comes in from the right, sloping up to the right a little, and the sleeve leaves through the RIGHT edge of the picture.", identity=False, refs=["assets/gen/cut/h44_tight.png"]),
    "h12_marker_door": a(MARKER5 + "Shot: a right hand and forearm reaching up to write on a door, seen from behind her arm, a tense grip, marker tip pointing up and to the left. The forearm comes up from the lower right, and the sleeve leaves through the BOTTOM edge of the picture, towards its right end.", identity=False, refs=["assets/gen/cut/h44_tight.png"]),
    "h13_marker_tired": a(MARKER5 + "Shot: seen from above, a right hand and forearm that has stopped writing. The hand has gone slack: the fingers hold the marker loosely, the wrist has dropped, the marker tip still rests at the left, pointing down and to the left. The forearm comes in from the right, and the sleeve leaves through the RIGHT edge of the picture.", identity=False, refs=["assets/gen/cut/h44_rest.png"]),
    "h21_push_a": a("Attached Image 2 only shows the framing, the cuff and the pose, not how to draw the hand: same side view at floor level, same place and size of the cuff in the picture, same white sleeve with the navy cuff and its one white line, entering from the left edge. There is NO paper and NO floor drawn this time. Drawing 1 of a push along the floor, the start: the elbow is bent and raised, so the forearm slopes down from the upper left, the wrist is high, the fingers are bent down and the fingertips press on an invisible floor line, thumb tucked underneath. The sleeve runs off the left edge. Exactly five fingers.", identity=False, refs=["assets/gen/raw/h21_push_a.png"]),
    "h22_push_b": a(PUSH4 + "Drawing 2 of the push, the middle: the forearm lies low, almost level, the wrist has come down, the hand is flat and the straight fingers slide forward on an invisible floor line, thumb alongside as one simple shape. Exactly five fingers at most, only clean single lines between them.", identity=False, refs=["assets/gen/raw/h22_push_b.png", "work/gen/fix3/hands_raw/h21_push_a.png"]),
    "h23_push_c": a(PUSH4 + "Drawing 3 of the push, the end: the arm is stretched out completely flat along the floor as far as it reaches, the cuff pulled back a little from the wrist, the fingers straight with only the tips touching an invisible floor line, the hand has just let go. Exactly five fingers at most, only clean single lines between them.", identity=False, refs=["assets/gen/raw/h23_push_c.png", "work/gen/fix3/hands_raw/h21_push_a.png"]),
}


# Hands by design different here: a grown man's hand, and the wipe drawings another pass is redoing with their own text.
NO_HAND_RULE = {"h13_adult_crayon_a", "h13_adult_crayon_b"} | {f"h30_wipe_{x}" for x in "abcd"}


def refs(aid):
    """What gets attached, in order. Her drawings always carry the sheet: first by default, last when the text leans on another
    drawing (sheet=False). A picture of only a hand also ends with the sheet's hands enlarged."""
    s = ASSETS[aid]
    out = list(s.get("refs", []))
    if s.get("sheet", True):
        out.insert(0, SHEET)
        if s.get("draw") and aid not in NO_HAND_RULE and aid.startswith(HAND_ONLY):
            out.append(SHEET_HAND)
    elif s.get("draw"):
        out.append(SHEET)
    return out


def build(aid):
    s = ASSETS[aid]
    parts = [s["subject"]]
    if s.get("identity"):
        parts.insert(0, IDENTITY)
    if s.get("draw"):
        parts.append(DRAW)
        parts.append(SHEET_RULE)
        if aid not in NO_HAND_RULE:
            parts.append(HANDS)
            if aid.startswith(HAND_ONLY):
                parts.append(SLEEVE_END)
        # gen_batch.py attaches the sheet last for pictures that lean on another drawing of the same hand
        if not s.get("sheet", True):
            parts.append("The last attached image is her model sheet: it decides how she is drawn.")
    if s.get("large"):
        parts.append(LARGE)
    if s.get("key"):
        parts.append(KEY)
    if s.get("never"):
        parts.append(NEVER)
    return "\n".join(parts)
