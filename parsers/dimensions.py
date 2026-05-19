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


def get_context(words, index, window=3):
    start = max(index - window, 0)
    end = min(index + window + 1, len(words))

    return " ".join([
        words[i].get("text", "")
        for i in range(start, end)
    ]).upper()


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
    box = merge_box(items)

    results.append({
        "type": dim_type,
        "raw_text": raw_text.strip(),
        "x": box["x"],
        "y": box["y"],
        "width": box["width"],
        "height": box["height"],
        "confidence": box["confidence"]
    })


def is_weld_context(context):
    return any(word in context for word in WELD_WORDS)


def extract_dimensions(words):
    results = []
    used_indexes = set()

    for i, item in enumerate(words):
        text = item.get("text", "").strip()
        upper = text.upper()

        if not text:
            continue

        context = get_context(words, i)

        # Skip obvious weld/process areas
        if is_weld_context(context):
            continue

        # Skip weld spec numbers like 3-6-79 or 3-6-102
        if re.fullmatch(r"\d+-\d+-\d+", upper):
            continue

        # Pattern: 154 DIA HOLE / 281 DIA HOLE
        if re.fullmatch(r"\d+(\.\d+)?", upper):
            next_1 = words[i + 1].get("text", "").upper() if i + 1 < len(words) else ""
            next_2 = words[i + 2].get("text", "").upper() if i + 2 < len(words) else ""

            if next_1 == "DIA":
                items = [item, words[i + 1]]

                raw_text = f"{text} DIA"

                if next_2 == "HOLE":
                    items.append(words[i + 2])
                    raw_text += " HOLE"

                add_dimension(results, "diameter", raw_text, items)
                used_indexes.update([i, i + 1, i + 2])
                continue

        # Pattern: DIA 154
        if upper == "DIA" and i + 1 < len(words):
            next_text = words[i + 1].get("text", "").strip()

            if re.fullmatch(r"\d+(\.\d+)?", next_text):
                add_dimension(
                    results,
                    "diameter",
                    f"DIA {next_text}",
                    [item, words[i + 1]]
                )
                used_indexes.update([i, i + 1])
                continue

        # Angles: 30°, 60°, or OCR split as 30 / 60 near arc
        if re.fullmatch(r"\d+°", upper) or re.fullmatch(r"\d+\s*DEG", upper):
            add_dimension(results, "angle", text, [item])
            used_indexes.add(i)
            continue

        if re.fullmatch(r"\d{2,3}", upper):
            # Keep likely angle numbers, but not balloon numbers
            if upper in ["30", "45", "60", "90", "120", "180"]:
                add_dimension(results, "angle", f"{text}°", [item])
                used_indexes.add(i)
                continue

        # Radius: 285.8R or R285.8
        if re.fullmatch(r"\d+(\.\d+)?R", upper) or re.fullmatch(r"R\d+(\.\d+)?", upper):
            add_dimension(results, "radius", text, [item])
            used_indexes.add(i)
            continue

        # Feature size like 34 x 3
        if re.fullmatch(r"\d+(\.\d+)?", upper) and i + 2 < len(words):
            middle = words[i + 1].get("text", "").lower()
            last = words[i + 2].get("text", "")

            if middle in ["x", "×"] and re.fullmatch(r"\d+(\.\d+)?", last):
                add_dimension(
                    results,
                    "feature_size",
                    f"{text} x {last}",
                    [item, words[i + 1], words[i + 2]]
                )
                used_indexes.update([i, i + 1, i + 2])
                continue

        # Large linear dimensions like 1800
        if re.fullmatch(r"\d{3,5}", upper):
            add_dimension(results, "linear", text, [item])
            used_indexes.add(i)
            continue

    return results
