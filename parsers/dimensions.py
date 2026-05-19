import re


VALID_DIMENSION_PATTERNS = [

    # decimal dimensions
    r"\b\d+\.\d+\b",

    # integer dimensions
    r"\b\d+\b",

    # fractions
    r"\b\d+\s*/\s*\d+\b",

    # diameter callouts
    r"\b\d+\s*DIA\b",
    r"\bDIA\s*\d+\b",

    # radius
    r"\b\d+(\.\d+)?R\b",
    r"\bR\d+(\.\d+)?\b",

    # angles
    r"\b\d+\s*°\b",
    r"\b\d+\s*DEG\b",

    # x by x dimensions
    r"\b\d+\s*x\s*\d+\b",

    # plus minus tolerance
    r"\b±\s*\d+\.\d+\b",
]


EXCLUDED_WORDS = [

    "GMAW",
    "WELD",
    "ROOT",
    "PASS",
    "SEAL",
    "NOTE",
    "SEE",
    "MIN",
    "REF",
    "ITEM",
    "TYP",
    "REQD",
    "REQUIRED",
]


def is_real_dimension(text):

    text_upper = text.upper().strip()

    if len(text_upper) < 2:
        return False

    for bad in EXCLUDED_WORDS:

        if bad in text_upper:
            return False

    has_pattern = any(
        re.search(pattern, text_upper)
        for pattern in VALID_DIMENSION_PATTERNS
    )

    if not has_pattern:
        return False

    return True


def classify_dimension(text):

    text_upper = text.upper()

    if "DIA" in text_upper:
        return "diameter"

    if "°" in text_upper or "DEG" in text_upper:
        return "angle"

    if "R" in text_upper:
        return "radius"

    if "X" in text_upper:
        return "feature_size"

    if "/" in text_upper:
        return "fraction"

    return "linear"


def extract_dimensions(words):

    dimensions = []

    for item in words:

        raw_text = item.get(
            "text",
            ""
        ).strip()

        if not raw_text:
            continue

        if not is_real_dimension(raw_text):
            continue

        dimensions.append({

            "type": classify_dimension(raw_text),

            "raw_text": raw_text,

            "x": item.get("x", 0),

            "y": item.get("y", 0),

            "width": item.get("width", 80),

            "height": item.get("height", 24),

            "confidence": item.get("confidence", 0)
        })

    return dimensions
