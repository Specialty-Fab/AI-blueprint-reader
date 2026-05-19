import re


WELD_WORDS = [
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


def get_word(words, index):
    if 0 <= index < len(words):
        return words[index].get("text", "").strip()
    return ""


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


def add_dimension(results, dim_type, raw_text, items):
    raw_text = raw_text.strip()

    if not raw_text:
        return

    if raw_text in [item["raw_text"] for item in results]:
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


def has_weld_context(words, index, window=3):
    start = max(index - window, 0)
    end = min(index + window + 1, len(words))

    context = " ".join(
        words[i].get("text", "")
        for i in range(start, end)
    ).upper()

    return any(word in context for word in WELD_WORDS)


def is_number(text):
    return bool(re.fullmatch(r"\d+(\.\d+)?", text.strip()))


def is_weld_spec(text):
    return bool(re.fullmatch(r"\d+-\d+-\d+", text.strip()))


def extract_dimensions(words):
    results = []

    for i, item in enumerate(words):
        text = item.get("text", "").strip()
        upper = text.upper()

        if not text:
            continue

        if is_weld_spec(text):
            continue

        # Diameter callouts like: 154 DIA HOLE / 281 DIA HOLE
        if is_number(text):
            next_1 = get_word(words, i + 1).upper()
            next_2 = get_word(words, i + 2).upper()

            if next_1 == "DIA":
                items = [item, words[i + 1]]
                raw_text = f"{text} DIA"

                if next_2 == "HOLE":
                    items.append(words[i + 2])
                    raw_text += " HOLE"

                add_dimension(results, "diameter", raw_text, items)
                continue

        # Diameter callouts like: DIA 154
        if upper == "DIA" and i + 1 < len(words):
            next_text = get_word(words, i + 1)

            if is_number(next_text):
                add_dimension(
                    results,
                    "diameter",
                    f"DIA {next_text}",
                    [item, words[i + 1]]
                )
                continue

        # Angles like 30°, 60°, 45°
        if re.fullmatch(r"\d+°", text):
            add_dimension(results, "angle", text, [item])
            continue

        if text in ["30", "45", "60", "90", "120", "180"]:
            if not has_weld_context(words, i):
                add_dimension(results, "angle", f"{text}°", [item])
            continue

        # Radius like 285.8R or R285.8
        if re.fullmatch(r"\d+(\.\d+)?R", upper) or re.fullmatch(r"R\d+(\.\d+)?", upper):
            add_dimension(results, "radius", text, [item])
            continue

        # Feature size like 34 x 3 or 3 x 3
        if is_number(text) and i + 2 < len(words):
            middle = get_word(words, i + 1).lower()
            last = get_word(words, i + 2)

            if middle in ["x", "×"] and is_number(last):
                if not has_weld_context(words, i):
                    add_dimension(
                        results,
                        "feature_size",
                        f"{text} x {last}",
                        [item, words[i + 1], words[i + 2]]
                    )
                continue

        # Fraction dimensions like 3/8
        if re.fullmatch(r"\d+/\d+", text):
            if not has_weld_context(words, i):
                add_dimension(results, "fraction", text, [item])
            continue

        # Large linear dims like 1800 or 186
        if re.fullmatch(r"\d{3,5}", text):
            if not has_weld_context(words, i):
                add_dimension(results, "linear", text, [item])
            continue

    return results
