"""Accurate Malayalam (script) for user-facing text. Deterministic templates built from analysis facts — no model in the loop,
so the Malayalam is always correct. Gemma supplies English (+ Manglish) flavour; this supplies the മലയാളം."""
from __future__ import annotations

FINGERS_ML = {"thumb": "തള്ളവിരൽ", "index": "ചൂണ്ടുവിരൽ", "middle": "നടുവിരൽ", "ring": "മോതിരവിരൽ", "pinky": "ചെറുവിരൽ"}
FINGERS_ML_IDX = ["തള്ളവിരൽ", "ചൂണ്ടുവിരൽ", "നടുവിരൽ", "മോതിരവിരൽ", "ചെറുവിരൽ"]

LABELS_ML = {
    "app": "താളം", "ashaan_says": "ആശാൻ പറയുന്നു", "free_flow": "സ്വതന്ത്രമായി വായിക്കൂ", "learn": "പഠിക്കൂ", "practice": "പരിശീലനം",
    "listen": "കേൾക്കൂ", "play": "വായിക്കൂ", "stop": "നിർത്തൂ", "tempo": "വേഗം", "instrument": "വാദ്യം", "phrase": "ഭാഗം",
    "perfect": "കൃത്യം", "good": "നല്ലത്", "late": "വൈകി", "early": "നേരത്തെ", "wrong_finger": "തെറ്റായ വിരൽ", "miss": "വിട്ടുപോയി",
    "start_tempo": "താളം തുടങ്ങൂ", "analyze": "വിശകലനം ചെയ്യൂ", "compose": "രചിക്കൂ", "your_turn": "ഇനി നിങ്ങളുടെ ഊഴം",
    "well_done": "വളരെ നന്നായി!", "try_again": "വീണ്ടും ശ്രമിക്കൂ",
}

_ERROR_ML = {
    "late": "അടികൾ കുറച്ച് വൈകിയാണ് വരുന്നത്.",
    "early": "അടികൾ കുറച്ച് നേരത്തെയാണ് വരുന്നത്.",
    "wrong_finger": "ചില അടികൾ തെറ്റായ വിരൽ കൊണ്ടാണ്.",
    "missed": "ചില അടികൾ വിട്ടുപോയി.",
    "extra": "ആവശ്യമില്ലാത്ത അധിക അടികളുണ്ട്.",
    "none": "എല്ലാ അടികളും കൃത്യമായിരുന്നു!",
}
_FIX_ML = {
    "late": "അടുത്ത അടിക്ക് നേരത്തെ തയ്യാറാകൂ; കണ്ണ് അല്ല, കാത് താളത്തിൽ വെക്കൂ.",
    "early": "ധൃതി വേണ്ട; ഓരോ അടിയും താളത്തിൽ വീഴാൻ കാത്തിരിക്കൂ.",
    "wrong_finger": "ഓരോ അക്ഷരത്തിനും ഏത് വിരൽ എന്ന് ഒന്നുകൂടി നോക്കൂ; പതുക്കെ വായിക്കൂ.",
    "missed": "വേഗം കുറച്ച്, ഒരു അടിയും വിടാതെ വായിക്കൂ.",
    "extra": "കൈ അയഞ്ഞിരിക്കട്ടെ; ആവശ്യമുള്ള അടികൾ മാത്രം.",
    "none": "ഇതേ കൃത്യതയോടെ വേഗം കൂട്ടി നോക്കാം.",
}


def _join_ml(items: list[str]) -> str:
    return items[0] if len(items) == 1 else "ഉം ".join(items[:-1]) + "ഉം " + items[-1] + "ഉം"


def coach_ml(accuracy_pct: float, dominant_error: str, weak_fingers: list[str], weak_syllables: list[str],
             recommended_bpm: float, phrase_index: int | None, stars: int | None = None) -> str:
    """Correct, natural Malayalam coaching built from deterministic facts."""
    parts = []
    if accuracy_pct >= 90:
        parts.append("വളരെ നന്നായി! കൃത്യത " + f"{int(accuracy_pct + 0.5)}%.")
    elif accuracy_pct >= 70:
        parts.append("നന്നായി വരുന്നു. കൃത്യത " + f"{int(accuracy_pct + 0.5)}%.")
    else:
        parts.append("കുഴപ്പമില്ല, പരിശീലിച്ചാൽ ശരിയാകും. കൃത്യത " + f"{int(accuracy_pct + 0.5)}%.")
    parts.append(_ERROR_ML.get(dominant_error, _ERROR_ML["none"]))
    fingers = [FINGERS_ML.get(f, f) for f in weak_fingers[:2]]
    if fingers and dominant_error != "none":
        syl = f" ('{'/'.join(weak_syllables[:2])}' എന്നിടത്ത്)" if weak_syllables else ""
        parts.append(_join_ml(fingers) + " ശ്രദ്ധിക്കൂ" + syl + ".")
    parts.append(_FIX_ML.get(dominant_error, _FIX_ML["none"]))
    drill = f"അടുത്തത്: {int(round(recommended_bpm))} bpm-ൽ"
    drill += f" {phrase_index + 1}-ാം ഭാഗം വായിക്കൂ." if phrase_index is not None else " വീണ്ടും വായിക്കൂ."
    parts.append(drill)
    return " ".join(parts)


def structure_ml(thaalam: str, beats_per_cycle: int, notes: int, confidence: float) -> str:
    conf = "ഉറപ്പാണ്" if confidence >= 0.75 else "ഏകദേശം ശരിയാണ്" if confidence >= 0.5 else "ഊഹം മാത്രമാണ്"
    return f"താളം: {thaalam} — ഒരു ആവർത്തനത്തിൽ {beats_per_cycle} അക്ഷരങ്ങൾ. {notes} അടികൾ കണ്ടെത്തി. ഈ കണ്ടെത്തൽ {conf}."
