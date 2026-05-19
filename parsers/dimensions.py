import re


def classify_dimension(text):
    text_upper = text.upper()

    if "DIA" in text_upper or "Ø" in text_upper or "⌀" in text_upper:
        return "diameter"

    if "R" in text_upper and re.search(r"\bR\s*\d+", text_upper):
        return "radius"

    if "DEG" in text_upper or "°" in text_upper:
        return "angle"

    if re.search(r"\d+\s*/\s*\d+", text_upper):
        return "fraction"

    if re.search(r"\d+\.\d+", text_upper):
        return "linear"

    if re.search(r"\b\d+\b", text_upper):
        return "numeric"

    return "dimension"


def looks_like_dimension(text):
    text_upper = text.upper().strip()

    patterns = [
        r"\b\d+\.\d+\b",
        r"\b\d+\s*/\s*\d+\b",
        r"\b\d+\s*(?:°|DEG)\b",
        r"\b\d+\s*DIA\b",
        r"\bDIA\s*\d+\b",
        r"\b\d+\s*R\b",
        r"\bR\s*\d+\b",
        r"\b\d+\s*\+\s*/\s*-\s*\d+\b",
        r"\b\d+\s*-\s*\d+\b",
    ]

    if any(re.search(pattern, text_upper) for pattern in patterns):
        return True

    if any(token in text_upper for token in ["DIA", "HOLE", "R", "TYP", "REF"]):
        return bool(re.search(r"\d", text_upper))

    return False


def extract_dimensions(text_or_words):
    results = []

    if isinstance(text_or_words, list):
        for item in text_or_words:
            raw_text = item.get("text", "").strip()

            if not raw_text:
                continue

            if looks_like_dimension(raw_text):
                results.append({
                    "type": classify_dimension(raw_text),
                    "raw_text": raw_text,
                    "x": item.get("x", 0),
                    "y": item.get("y", 0),
                    "width": item.get("width", 80),
                    "height": item.get("height", 24),
                    "confidence": item.get("confidence", 0)
                })

        return results

    text = text_or_words

    patterns = [
        ("linear", r"\b\d+\.\d+\s*(?:±|\+/-)?\s*\.?\d*\b"),
        ("diameter", r"(?:Ø|⌀|DIA)\s*\d+\.\d+|\b\d+\s*DIA\b"),
        ("radius", r"\bR\s*\d+\.\d+|\bR\s*\d+\b"),
        ("angle", r"\b\d+\s*(?:°|DEG)\b"),
        ("fraction", r"\b\d+\s*/\s*\d+\b"),
        ("edge_break", r"\.?\d+\s*-\s*\.?\d+"),
    ]

    for dim_type, pattern in patterns:
        for match in re.findall(pattern, text, re.IGNORECASE):
            if isinstance(match, tuple):
                match = " ".join(match)

            results.append({
                "type": dim_type,
                "raw_text": str(match).strip(),
                "x": 0,
                "y": 0,
                "width": 80,
                "height": 24,
                "confidence": 0
            })

    return results
