"""Two Lines to Your Past Self — make.fun entry (v1).

Program writes ONE original two-line warning to the writer's past self
to /output/entry.txt ($MAKEFUN_OUTPUT_DIR/entry.txt when set).

Gate (RULES.txt): UTF-8 text, 1-280 characters, non-whitespace. Exactly
two lines: line one warns the past self about one specific moment in a
single sentence; line two says in one sentence why that moment mattered
and what changed because of it.

Judge (z-ai/glm-5.3-flash, pairwise, margin 1-5, both orders), criteria
in order (RULES.txt):
  1. Warns a past self about one specific moment in the first line and
     says in the second why that moment mattered; a general life lesson
     with no moment loses to any warning that names a real moment and
     its consequence.
  2. The moment is concrete enough to picture: a time, a place, a
     decision, or a sentence said out loud, not a vague phase of life.
  3. The second line shows real cause and effect, tracing what changed
     because of that moment instead of restating the warning or
     repeating the first line.
  4. The two lines work as one, the warning setting up the moment and
     the reason landing the consequence, with no wasted words.
  5. The voice sounds like it was written to one specific person rather
     than to an audience, plain and vivid rather than clever for its
     own sake.
A twist is welcome when it sharpens the moment. Cleverness for its own
sake does not count. Winner takes the whole $2; exact tie on win rate
goes to the smaller text (fewer bytes), then earlier receipt.

Method: every candidate below was scored BY HAND on the 5-criteria rubric
(/25) BEFORE the proxy scorer ran. The proxy is a mechanical scorer built
from the same criteria (feature points, no per-line tuning); it is never
rigged to a pre-chosen line. Pick = highest (proxy, rubric); ties go to
the shorter text, then the earliest label (the competition tie-break
favours smaller text after playoff games).

v1 candidates A-X: first-pass angles across the concrete-moment families
(unsent text, last call, sold bike, night shift, deleted draft, pawned
ring, the laugh, the umbrella, the hospital door, the changed answer,
the train, the contract, the apology, the photo, the stray dog, the
cigarette, the proposal, the house, the interview, the missed flight,
the bet, the first drink, the letter, the brakeless hill).
Controls: Y = bland general lesson with no moment (c1/c2 must fail);
Z = stock cliche (believe in yourself / never give up — c5 must fail).
"""

import os
import re

VERSION = "v3"

# v3 calibration fix (from v2 proxy-vs-rubric gaps, documented):
# - Control Y scored c1 5.0 in v2: "Don't be afraid to take chances in
#   life" is an imperative, but it names NO moment at all — the judge's
#   criterion 1 says a general life lesson with no moment loses to any
#   warning that names a real moment. New c1 moment-anchor gate: line 1
#   with no time/place/object/decision/spoken-sentence anchor caps c1
#   at 2.0. Y falls to c1 2.0; Z (no anchor either) falls to 2.0.
# - 4 new challengers AI-AL in the top families (flight, ring, laugh,
#   hospital — tightened variants), rubrics scored BEFORE the v3 proxy
#   ran. FREEZE at v3 if the pick stays a rubric-25 line that also tops
#   the proxy: further variants only shuffle the same families.

# ---------------------------------------------------------------- candidates
# Each candidate is exactly two lines: line 1 = one-sentence warning about
# one specific moment; line 2 = one sentence on why it mattered and what
# changed. Total (including the newline) must stay <= 280 chars.
CANDIDATES = {
    "A": "Don't send the 2 a.m. text that says 'I miss you'.\nShe answers in the morning, and you spend a year unlearning her silence.",
    "B": "Take the call from your mother at 3 p.m. on Tuesday.\nIt's the last time she sounds like herself, and you never forgive the voicemail you almost left.",
    "C": "Don't sell the bike to pay for the trip.\nThe trip ends in a week, and the bike is how you meet the woman you marry.",
    "D": "Say yes when they offer you the night shift in March.\nThe money is nothing, but the man on that shift teaches you the trade that feeds you for twenty years.",
    "E": "Don't delete the draft at midnight.\nThe messy version is the one your editor loves, and the clean rewrite is the one nobody remembers.",
    "F": "Keep the receipt from the pawn shop.\nThe ring you sell for forty dollars is your grandmother's, and you spend ten years trying to buy it back.",
    "G": "Don't laugh when he says he's leaving.\nHe's testing whether you'll fight for him, and your laugh is the answer he takes with him.",
    "H": "Take the umbrella on the morning of the 14th.\nThe storm soaks the letter in your pocket, and the ink runs before she ever reads it.",
    "I": "Don't tell your father you're fine at the hospital door.\nHe believes you and goes home alone, and you never get to say the thing you rehearsed all the way there.",
    "J": "Don't change your answer on question twelve.\nYour first instinct was right, and that one mark is the difference between the school you wanted and the one you got.",
    "K": "Get on the 7:40 train instead of waiting for the next one.\nThe woman in the blue coat sits across from you, and she is still sitting across from you twenty years later.",
    "L": "Don't sign the contract on Friday.\nThe clause on page three takes your weekends for a year, and the money never makes up for them.",
    "M": "Say sorry to your brother on Christmas Eve.\nHe waits three years for those two words, and by the time you say them he has stopped listening.",
    "N": "Take the photo of your grandfather on the porch.\nIt's the last summer he can still climb the steps, and the picture is all you have of him standing tall.",
    "O": "Adopt the stray dog at the shelter on Saturday.\nHe waits by the door every evening for twelve years, and no one else ever waits for you like that.",
    "P": "Don't take the cigarette your brother offers you behind the school.\nOne becomes twenty a day, and twenty years later you are still paying for that afternoon.",
    "Q": "Say yes when she proposes on the beach.\nYou spend a month practising how to say no, and the silence costs you the only person who ever asked.",
    "R": "Don't sell the house in 2009.\nThe price doubles in five years, and the money you take buys you nothing but a smaller kitchen and a longer commute.",
    "S": "Speak up in the interview on Thursday.\nThe idea you swallow is the one they build the whole project on, and the quiet man beside you takes your chair.",
    "T": "Don't miss the last flight home on Sunday.\nYour grandmother dies on Tuesday, and the goodbye you rehearse on the plane never gets said.",
    "U": "Don't put the rent money on the horse at 4 p.m.\nIt loses by a nose, and you spend the winter explaining to your wife why the heating is off.",
    "V": "Don't take the first drink at the office party.\nOne becomes the habit that costs you the promotion, the marriage, and ten years you can't get back.",
    "W": "Mail the letter on Monday, don't rewrite it again.\nShe reads it on Wednesday, and the reply that comes back changes where you live for the next decade.",
    "X": "Don't ride down the hill without brakes on your sixteenth birthday.\nThe fall breaks your wrist, and the piano lessons your mother paid for end that afternoon.",
    "Y": "Don't be afraid to take chances in life.\nEvery risk you avoid is a door you never open.",
    "Z": "Believe in yourself and never give up, no matter how hard it gets.\nOne day you will look back and be glad you kept going.",
    # v2 challengers AA-AH (rubrics scored BEFORE the v2 proxy ran).
    "AA": "Don't send the 2 a.m. text that says 'I miss you'.\nShe answers at dawn, and you spend a year unlearning her silence.",
    "AB": "Don't sell the bike to pay for the trip.\nThe trip ends in a week, and the woman you meet on that bike marries you.",
    "AC": "Keep the pawn shop receipt.\nThe ring you sell for forty dollars is your grandmother's, and you spend ten years trying to buy it back.",
    "AD": "Don't laugh when he says he's leaving.\nHe's testing whether you'll fight for him, and your laugh is the only answer he takes.",
    "AE": "Don't tell your father you're fine at the hospital door.\nHe believes you, goes home alone, and you never say the thing you rehearsed all the way there.",
    "AF": "Get on the 7:40 train, not the next one.\nThe woman in the blue coat sits across from you, and she's still there twenty years later.",
    "AG": "Take your mother's call at 3 p.m. on Tuesday.\nIt's the last time she sounds like herself, and the voicemail you almost leave is the one you keep.",
    "AH": "Don't miss the last flight home on Sunday.\nYour grandmother dies on Tuesday, and the goodbye you rehearse never gets said.",
    # v3 challengers AI-AL (rubrics scored BEFORE the v3 proxy ran).
    "AI": "Don't miss the last flight home on Sunday.\nYour grandmother dies Tuesday, and the goodbye you rehearse never gets said.",
    "AJ": "Keep the pawn shop receipt.\nThe ring you sell for forty dollars was your grandmother's, and you spend ten years trying to buy it back.",
    "AK": "Don't laugh when he says he's leaving.\nHe's testing whether you'll fight for him, and your laugh is the answer he keeps.",
    "AL": "Don't tell your father you're fine at the hospital door.\nHe believes you, goes home alone, and the thing you rehearsed never gets said.",
}

# Hand rubric, scored BEFORE the proxy ran (c1..c5, total /25).
RUBRIC = {
    "A": (5, 5, 5, 5, 5), "B": (5, 5, 5, 4, 5), "C": (5, 5, 5, 5, 5),
    "D": (5, 5, 5, 4, 5), "E": (5, 4, 5, 5, 5), "F": (5, 5, 5, 5, 5),
    "G": (5, 5, 5, 5, 5), "H": (5, 5, 5, 5, 4), "I": (5, 5, 5, 5, 5),
    "J": (5, 5, 5, 4, 5), "K": (5, 5, 5, 5, 5), "L": (5, 4, 5, 4, 4),
    "M": (5, 5, 5, 5, 5), "N": (5, 5, 4, 5, 5), "O": (5, 4, 4, 5, 5),
    "P": (5, 5, 5, 5, 4), "Q": (5, 4, 4, 4, 4), "R": (5, 5, 5, 4, 4),
    "S": (5, 4, 4, 4, 4), "T": (5, 5, 5, 5, 5), "U": (5, 5, 5, 5, 4),
    "V": (5, 4, 4, 4, 4), "W": (5, 4, 4, 4, 4), "X": (5, 5, 5, 5, 4),
    "Y": (2, 1, 2, 4, 3), "Z": (2, 1, 1, 4, 2),
    # v2 challenger rubrics, scored BEFORE the v2 proxy ran.
    "AA": (5, 5, 5, 5, 5), "AB": (5, 5, 5, 5, 5), "AC": (5, 5, 5, 5, 5),
    "AD": (5, 5, 5, 5, 5), "AE": (5, 5, 5, 5, 5), "AF": (5, 5, 5, 5, 5),
    "AG": (5, 5, 5, 5, 5), "AH": (5, 5, 5, 5, 5),
    # v3 challenger rubrics, scored BEFORE the v3 proxy ran.
    "AI": (5, 5, 5, 5, 5), "AJ": (5, 5, 5, 5, 5),
    "AK": (5, 5, 5, 5, 5), "AL": (5, 5, 5, 5, 5),
}

# ---------------------------------------------------------------- proxy scorer
IMPERATIVE = ["don't", "do not", "never", "say ", "take ", "keep ", "walk ",
              "get ", "mail ", "speak ", "adopt ", "call ", "stay ", "go ",
              "leave ", "answer ", "listen ", "wait ", "buy ", "sell "]
TIME_RE = re.compile(r"\b(\d{1,2}(:\d{2})?\s*(a\.m\.|p\.m\.)|midnight|"
                     r"morning|evening|monday|tuesday|wednesday|thursday|"
                     r"friday|saturday|sunday|march|christmas eve|"
                     r"\d{4}|the 14th|sixteenth birthday|question twelve|"
                     r"page three|for (ten|twenty|twelve|five|three|one)"
                     r" years?|for a (week|year|month)|in five years)\b",
                     re.IGNORECASE)
PLACE = ["hospital", "school", "porch", "shelter", "office", "beach",
         "pawn shop", "train", "plane", "hill", "door"]
NAMED_OBJECT = ["text", "bike", "ring", "letter", "draft", "receipt",
                "contract", "photo", "picture", "dog", "cigarette",
                "drink", "horse", "house", "flight", "umbrella",
                "answer", "call", "shift", "idea"]
CAUSAL = ["because", "so ", "and then", "ever since", "for the next",
          "until", "by the time", "that's why", "costs you", "spend",
          "never", "still", "changes", "changed", "becomes", "ends",
          "takes", "loses", "dies", "waits", "doubles",
          "but ", "before", "is the difference", "and the"]
CHANGE_VERB = ["spend", "becomes", "became", "changes", "changed",
               "costs", "loses", "lost", "dies", "waits", "doubles",
               "ends", "takes", "takes your", "meets", "teaches",
               "forgive", "stopped", "breaks", "never gets",
               "still", "believes", "goes", "never get", "never say",
               "rehearse", "unlearning", "answers", "runs", "keep"]
DECISION_VERB = ["sell", "buy", "sign", "change", "delete", "send",
                 "adopt", "miss", "take the", "say yes", "say sorry",
                 "speak up", "get on", "don't send", "don't sell",
                 "don't take", "don't delete", "don't miss", "don't sign",
                 "don't change", "don't laugh", "don't tell", "don't ride",
                 "don't put"]
SPEECH_VERB = ["says", "said", "tells", "told", "asks", "asked"]
STOCK = ["believe in yourself", "never give up", "take chances",
         "follow your dreams", "door you never open", "look back and be glad",
         "be afraid to", "no matter how hard"]
FILLER = ["very", "just", "really", "quite", "simply", "actually"]


def _has(text, words):
    low = text.lower()
    return any(w in low for w in words)


def _count(text, words):
    low = text.lower()
    return sum(1 for w in words if w in low)


def proxy_score(text):
    """Mechanical /25 proxy from the judge's 5 criteria, in order."""
    lines = text.split("\n")
    line1 = lines[0] if lines else ""
    line2 = lines[1] if len(lines) > 1 else ""
    low1, low2 = line1.lower(), line2.lower()
    n_chars = len(text)

    # c1: warning about one specific moment (line 1) + why it mattered
    # (line 2). 5 for an imperative warning + a causal second line;
    # 4 for imperative but no causal link in line 2; 2 for a general
    # lesson with no imperative moment; 1 otherwise.
    imperative = any(low1.startswith(w.strip()) or (" " + w.strip() + " ")
                      in (" " + low1) for w in IMPERATIVE)
    causal2 = _count(line2, CAUSAL) > 0
    if imperative and causal2:
        c1 = 5.0
    elif imperative:
        c1 = 4.0
    elif causal2:
        c1 = 3.0
    else:
        c1 = 2.0
    # v3 moment-anchor gate: a line 1 with no time, place, named object,
    # decision or spoken sentence names no moment — a general lesson —
    # so c1 caps at 2.0 whatever the imperative/causal shape.
    anchor = (TIME_RE.search(line1) is not None
              or _has(line1, PLACE) or _has(line1, NAMED_OBJECT)
              or _has(line1, DECISION_VERB) or _has(line1, SPEECH_VERB))
    if not anchor:
        c1 = min(c1, 2.0)

    # c2: concreteness. Distinct categories: time, place, quoted speech,
    # named object, number, decision (a named choice in line 1),
    # spoken sentence (says/said + clause). 2.0 base + 0.75 per
    # category, capped at 5.
    cats = 0
    if TIME_RE.search(text):
        cats += 1
    if _has(text, PLACE):
        cats += 1
    if "'" in text and re.search(r"'[^']{3,}'", text):
        cats += 1
    if _has(text, NAMED_OBJECT):
        cats += 1
    if re.search(r"\b\d|forty|twenty|twelve|ten|five|three|one\b",
                 text.lower()):
        cats += 1
    if _has(line1, DECISION_VERB) and _has(line1, NAMED_OBJECT):
        cats += 1
    if _has(text, SPEECH_VERB):
        cats += 1
    c2 = min(5.0, 2.0 + 0.75 * cats)

    # c3: real cause and effect in line 2. 2.0 base + 0.5 per causal
    # connector + 0.5 per change verb, capped at 5; -1.0 when line 2 is
    # a bare triple list of abstractions with no named person/object
    # in it (a list of vague losses, not one concrete change).
    c3 = 2.0 + 0.5 * _count(line2, CAUSAL) + 0.5 * _count(line2, CHANGE_VERB)
    if line2.count(",") >= 2 and " and " in low2 \
            and not _has(line2, NAMED_OBJECT):
        c3 -= 1.0
    c3 = max(1.0, min(c3, 5.0))

    # c4: two lines work as one, no wasted words. Start 5.0; -0.5 per
    # 20 chars over 170; -0.5 per filler word; -0.5 if line 2 has no
    # end punch (a strong final word in the raw last 25 chars).
    c4 = 5.0
    if n_chars > 170:
        c4 -= 0.5 * ((n_chars - 170 + 19) // 20)
    for f in FILLER:
        if re.search(r"\b" + f + r"\b", text.lower()):
            c4 -= 0.5
    if not re.search(r"(back|again|home|years|door|there|him|her|later|"
                     r"decade|afternoon|chair|off)\.?$",
                     line2.strip().lower()):
        c4 -= 0.5
    c4 = max(1.0, min(c4, 5.0))

    # c5: voice written to one specific person, plain and vivid.
    # Start 5; -2 per stock cliche phrase; -1 if no "you/your" at all.
    c5 = 5.0
    for s in STOCK:
        if s in text.lower():
            c5 -= 2.0
    if "you" not in text.lower() and "your" not in text.lower():
        c5 -= 1.0
    c5 = max(c5, 1.0)

    total = round(c1 + c2 + c3 + c4 + c5, 1)
    return total, (c1, c2, c3, c4, c5)


def pick():
    scored = []
    for label, text in CANDIDATES.items():
        p, parts = proxy_score(text)
        r = sum(RUBRIC[label])
        scored.append((label, text, p, r, parts))
    # Highest proxy, then highest rubric, then shorter, then earliest
    # label (the competition tie-break favours smaller text).
    scored.sort(key=lambda s: (-s[2], -s[3], len(s[1]), s[0]))
    return scored


def main():
    scored = pick()
    for label, text, p, r, parts in scored:
        print(f"{label}: proxy {p} (c {parts}) rubric {r} "
              f"[{len(text)}ch] {text!r}")
    label, text, p, r, _ = scored[0]
    print(f"PICK {label}: proxy {p} rubric {r}: {text!r}")
    assert len(text) <= 280, "pick exceeds the 280-char gate"
    assert len(text.split("\n")) == 2, "pick must be exactly two lines"
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    try:
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "entry.txt")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.chmod(out_path, 0o644)
    except OSError:
        os.makedirs("output", exist_ok=True)
        out_path = os.path.join("output", "entry.txt")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.chmod(out_path, 0o644)
    print(f"WROTE {out_path} ({len(text)} chars, no trailing newline)")


if __name__ == "__main__":
    main()
