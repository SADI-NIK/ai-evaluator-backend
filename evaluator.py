import unicodedata
import string
from rapidfuzz import fuzz

# ─── Synonyms & Abbreviations Dictionary ──────────────────────────────────────
SYNONYMS = {
    # Units
    "kilogram": ["kg", "kgs"],
    "gram": ["g", "gm", "gms"],
    "meter": ["m", "mtr"],
    "centimeter": ["cm"],
    "millimeter": ["mm"],
    "kilometer": ["km", "kms"],
    "second": ["sec", "s"],
    "minute": ["min", "mins"],
    "hour": ["hr", "hrs", "h"],
    "newton": ["n"],
    "joule": ["j"],
    "watt": ["w"],
    "ampere": ["amp", "amps", "a"],
    "volt": ["v"],
    "kelvin": ["k"],
    "celsius": ["c", "°c"],
    "fahrenheit": ["f", "°f"],
    "liter": ["l", "litre", "litres", "liters"],
    "milliliter": ["ml", "millilitre"],
    "kilometer per hour": ["kmph", "km/h", "kph"],
    "meter per second": ["m/s", "mps"],

    # Common science words
    "acceleration": ["acc"],
    "velocity": ["vel"],
    "frequency": ["freq"],
    "temperature": ["temp"],
    "pressure": ["press"],
    "resistance": ["res"],
    "potential difference": ["pd", "voltage"],
    "electromotive force": ["emf"],
    "deoxyribonucleic acid": ["dna"],
    "ribonucleic acid": ["rna"],
    "adenosine triphosphate": ["atp"],
    "carbon dioxide": ["co2"],
    "oxygen": ["o2"],
    "hydrogen": ["h2"],
    "water": ["h2o"],
    "sodium chloride": ["nacl", "salt"],
    "hydrochloric acid": ["hcl"],
    "sulfuric acid": ["h2so4"],

    # Math
    "approximately": ["approx"],
    "greater than": [">"],
    "less than": ["<"],

    # Aviation - Virus SW80 Document
    "above ground level": ["agl"],
    "revolutions per minute": ["rpm"],
    "never exceed speed": ["vne"],
    "air speed indicator": ["asi"],
    "exhaust gas temperature": ["egt"],
    "capacitor discharge ignition": ["cdi"],
    "engine management system": ["ems"],
    "aqueous film forming foam": ["afff"],
    "parachute rescue system": ["prs"],
    "global positioning system": ["gps"],
    "maximum take off weight": ["mtow"],
    "maximum landing weight": ["mlw"],
    "visual flight rules": ["vfr"],
    "instrument flight rules": ["ifr"],
    "instrument meteorological conditions": ["imc"],
    "air traffic control": ["atc"],
    "very high frequency": ["vhf"],
    "outside air temperature": ["oat"],
    "manifold pressure": ["map"],
    "battery management system": ["bms"],
    "mean aerodynamic chord": ["mac"],
    "horsepower": ["hp"],
    "nautical mile": ["nm", "nmi"],
    "knots": ["kts", "kt"],
    "feet per minute": ["fpm", "ft/min"],
    "ampere hour": ["ah", "amp hour"],
    "alternating current": ["ac"],
    "liquid crystal display": ["lcd"],
    "quasi nautical height": ["qnh"],
    "lift to drag": ["l/d"],

    # NCC Air Wing SD/SW Handbook
    "indian air force": ["iaf"],
    "national cadet corps": ["ncc"],
    "unmanned aerial vehicle": ["uav", "uavs"],
    "light combat aircraft": ["lca"],
    "hindustan aeronautics limited": ["hal"],
    "light combat helicopter": ["lch"],
    "multi role tanker transport": ["mrtt"],
    "air officer commanding": ["aoc"],
    "central air command": ["cac"],
    "eastern air command": ["eac"],
    "southern air command": ["sac"],
    "south western air command": ["swac"],
    "western air command": ["wac"],
    "training command": ["tc"],
    "maintenance command": ["mc"],
    "air chief marshal": ["acm"],
    "air marshal": ["am"],
    "air vice marshal": ["avm"],
    "air commodore": ["air cdre"],
    "group captain": ["gp capt"],
    "wing commander": ["wg cdr"],
    "squadron leader": ["sqn ldr"],
    "flight lieutenant": ["flt lt"],
    "flying officer": ["fg offr"],
    "pilot officer": ["plt offr"],
    "master warrant officer": ["mwo"],
    "warrant officer": ["wo"],
    "junior warrant officer": ["jwo"],
    "pakistan air force": ["paf"],
    "surface to air missile": ["sam"],
    "air to air missile": ["aam"],
    "air to ground missile": ["agm"],
    "beyond visual range": ["bvr"],
    "electronic warfare": ["ew"],
    "search and rescue": ["sar"],
    "short take off and landing": ["stol"],
    "vertical take off and landing": ["vtol"],
    "high altitude long endurance": ["hale"],
    "medium altitude long endurance": ["male"],
    "radar cross section": ["rcs"],
    "helicopter launched nag": ["helina"],
}

# Build reverse lookup: "kg" -> "kilogram"
REVERSE_SYNONYMS = {}
for canonical, alternatives in SYNONYMS.items():
    for alt in alternatives:
        REVERSE_SYNONYMS[alt.lower()] = canonical.lower()

def normalize_synonyms(text: str) -> str:
    words = text.split()
    normalized = []
    for word in words:
        normalized.append(REVERSE_SYNONYMS.get(word.lower(), word.lower()))
    return " ".join(normalized)

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.translate(str.maketrans("", "", string.punctuation))
    filler_words = {"the", "a", "an", "is", "are", "of"}
    words = text.split()
    words = [w for w in words if w not in filler_words]
    text = " ".join(words)
    text = normalize_synonyms(text)
    return text

def is_correct(student_answer: str, correct_answer: str, threshold: int = 80) -> bool:
    cleaned_student = clean_text(student_answer)
    cleaned_correct = clean_text(correct_answer)
    if not cleaned_student:
        return False
    score = fuzz.ratio(cleaned_student, cleaned_correct)
    return score >= threshold

def evaluate_question(student_answers: list, answer_key: list, total_marks: float) -> dict:
    num_blanks = len(answer_key)
    marks_per_blank = total_marks / num_blanks if num_blanks > 0 else 0
    results = []
    correct_count = 0

    for i, correct in enumerate(answer_key):
        student_ans = student_answers[i] if i < len(student_answers) else ""
        correct_flag = is_correct(student_ans, correct)
        if correct_flag:
            correct_count += 1
        results.append({
            "blank": i + 1,
            "student": student_ans,
            "correct": correct,
            "is_correct": correct_flag
        })

    marks_obtained = round(correct_count * marks_per_blank, 2)
    return {
        "marks_obtained": marks_obtained,
        "total_marks": total_marks,
        "correct_count": correct_count,
        "total_blanks": num_blanks,
        "results": results
    }