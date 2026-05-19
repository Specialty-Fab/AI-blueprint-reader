import re


WELD_WORDS = [
    "GMAW", "GTAW", "WELD", "ROOT", "PASS", "PASSES",
    "SEAL", "NOTE", "SEE", "MIN"
]

WEIGHT_WORDS = [
    "WT", "WEIGHT", "KGS", "KG", "LBS", "LB", "UNIT"
]


def normalize(text):
    return text.upper().replace("O", "0").strip()


def is_bad_context(text):
    upper = text.upper()

    if any(word in upper for word in WELD_WORDS):
        return True

    if any(word in upper for word in WEIGHT_WORDS):
        return True

    if re.search(r"\d+-\d+-\d+", upper):
        return True

    return False


def merge_box(items):
    x1 = min(int(item.get("x", 0)) for item in items)
    y1 = min(int(item.get("y", 0)) for item in items)
    x2 = max(int(item.get("x", 0)) + int(item.get("width", 0)) for item in items)
    y2 = max(int(item.get("y", 0)) + int(item.get("height", 0)) for item in items)

    return {
        "x": x1,
        "y": y1,
        "width": x2 - x1,
        "height": y2 - y1,
        "confidence": min(float(item.get("confidence", 0)) for item in items)
    }


def add_result(results, dim_type, raw_text, items):
    raw_text = raw_text.strip()

    if not raw_text:
        return

    if raw_text in [row["raw_text"] for row in results]:
        return

    box = merge_box(items)

    results.append({
        "type": dim_type,
        "raw_text": raw_text,
        "x": box["x"],
        "y": box["y"],
        "width": box["width"],
        "height": box["height"],
        "confidence": box["confidence"]
    })


def group_words_into_lines(words, y_tolerance=16):
    sorted_words = sorted(
        words,
        key=lambda item: (
            int(item.get("y", 0)),
            int(item.get("x", 0))
        )
    )

    lines = []

    for word in sorted_words:
        text = word.get("text", "").strip()

        if not text:
            continue

        y = int(word.get("y", 0))

        placed = False

        for line in lines:
            line_y = line["y"]

            if abs(y - line_y) <= y_tolerance:
                line["words"].append(word)
                line["y"] = int((line["y"] + y) / 2)
                placed = True
                break

        if not placed:
            lines.append({
                "y": y,
                "words": [word]
            })

    for line in lines:
        line["words"] = sorted(
            line["words"],
            key=lambda item: int(item.get("x", 0))
        )

    return lines


def extract_from_line(results, line_words):
    line_text = " ".join([
        word.get("text", "").strip()
        for word in line_words
    ])

    clean = normalize(line_text)

    if is_bad_context(clean):
        return

    # Hole diameters: 281 DIA HOLE, 154 DIA HOLE
    for match in re.finditer(r"\b\d+(\.\d+)?\s+DIA\s+HOLE\b", clean):
        add_result(
            results,
            "diameter",
            match.group(0),
            line_words
        )

    # Diameter without HOLE
    for match in re.finditer(r"\b\d+(\.\d+)?\s+DIA\b", clean):
        if "HOLE" not in match.group(0):
            add_result(
                results,
                "diameter",
                match.group(0),
                line_words
            )

    # Angles: 30°, 60°, 45°
    for match in re.finditer(r"\b(30|45|60|90)\s*°?\b", clean):
        add_result(
            results,
            "angle",
            f"{match.group(1)}°",
            line_words
        )

    # Radius: 285.8R or 285.8 R
    for match in re.finditer(r"\b\d+(\.\d+)?\s*R\b", clean):
        add_result(
            results,
            "radius",
            match.group(0).replace(" ", ""),
            line_words
        )

    # Feature size: 34 x 3
    for match in re.finditer(r"\b\d+(\.\d+)?\s*[xX×]\s*\d+(\.\d+)?\b", clean):
        add_result(
            results,
            "feature_size",
            match.group(0).replace("×", "x"),
            line_words
        )

    # Large linear: 1800, but not weight/title block
    for match in re.finditer(r"\b\d{3,5}\b", clean):
        value = match.group(0)

        if value in ["186"]:
            continue

        add_result(
            results,
            "linear",
            value,
            line_words
        )


def extract_dimensions(words):
    results = []

    lines = group_words_into_lines(words)

    for line in lines:
        extract_from_line(
            results,
            line["words"]
        )

    return results
