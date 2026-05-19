import re


EXCLUDED_CONTEXT_WORDS = [
    "GMAW",
    "GTAW",
    "WELD",
    "ROOT",
    "PASS",
    "PASSES",
    "SEAL",
    "NOTE",
    "SEE",
    "MIN",
]


def nearby_text(words, index, window=4):
    start = max(index - window, 0)
    end = min(index + window + 1, len(words))

    return " ".join([
        words[i].get("text", "")
        for i in range(start, end)
    ]).upper()


def is_near_weld_callout(words, index):
    context = nearby_text(words, index)

    return any(
        bad_word in context
        for bad_word in EXCLUDED_CONTEXT_WORDS
    )


def is_real_dimension_text(text):
    text_upper = text.upper().strip()

    if len(text_upper) < 2:
        return False

    # Remove obvious weld spec numbers like 3-6-79 and 3-6-102
    if re.fullmatch(r"\d+-\d+-\d+", text_upper):
        return False

    # Remove bare item balloons / note numbers
    if re.fullmatch(r"\d{1,2}", text_upper):
        return False

    patterns = [
        r"\b\d+\.\d+\b",
        r"\b\d+\s*DIA\b",
        r"\bDIA\s*\d+\b",
        r"\b\d+(\.\d+)?R\b",
        r"\bR\d+(\.\d+)?\b",
        r"\b\d+\s*°\b",
        r"\b\d+\s*DEG\b",
        r"\b\d+\s*/\s*\d+\b",
        r"\b\d+\s*x\s*\d+\b",
    ]

    return any(
        re.search(pattern, text_upper)
        for pattern in patterns
    )


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

    for index, item in enumerate(words):
        raw_text = item.get("text", "").strip()

        if not raw_text:
            continue

        if is_near_weld_callout(words, index):
            continue

        if not is_real_dimension_text(raw_text):
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
