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

WEIGHT_WORDS = [
    "WT",
    "WEIGHT",
    "KGS",
    "KG",
    "LBS",
    "LB",
    "UNIT",
]


def get_word(words, index):
    if 0 <= index < len(words):
        return words[index].get("text", "").strip()
    return ""


def clean_text(text):
    return (
        text.upper()
        .replace("Ø", "DIA")
        .replace("⌀", "DIA")
        .replace("O", "0")
        .replace(",", ".")
        .strip()
    )


def get_context(words, index, window=5):
    start = max(index - window, 0)
    end = min(index + window + 1, len(words))

    return " ".join([
        words[i].get("text", "")
        for i in range(start, end)
    ]).upper()


def is_weight_context(words, index):
    context = get_context(words, index, window=5)

    return any(word in context for word in WEIGHT_WORDS)


def is_weld_context(words, index):
    context = get_context(words, index, window=3)

    return any(word in context for word in WELD_WORDS)


def is_weld_spec(text):
    return bool(re.fullmatch(r"\d+-\d+-\d+", text.strip()))


def is_number(text):
    return bool(re.fullmatch(r"\d+(\.\d+)?", text.strip()))


def merge_box(items):
    x1 = min(int(item.get("x", 0)) for item in items)
    y1 = min(int(item.get("y", 0)) for item in items)

    x2 = max(
        int(item.get("x", 0)) + int(item.get("width", 0))
        for item in items
    )

    y2 = max(
        int(item.get("y", 0)) + int(item.get("height", 0))
        for item in items
    )

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


def extract_dimensions(words):
    results = []

    clean_words = [
        word for word in words
        if word.get("text", "").strip()
    ]

    clean_words = sorted(
        clean_words,
        key=lambda item: (
            int(item.get("y", 0)),
            int(item.get("x", 0))
        )
    )

    for i, item in enumerate(clean_words):
        text = item.get("text", "").strip()
        upper = clean_text(text)

        if not text:
            continue

        if is_weld_spec(text):
            continue

        if is_weight_context(clean_words, i):
            continue

        # 154 DIA HOLE / 281 DIA HOLE
        if is_number(text):
            next_1 = clean_text(get_word(clean_words, i + 1))
            next_2 = clean_text(get_word(clean_words, i + 2))

            if next_1 == "DIA":
                items = [item, clean_words[i + 1]]
                raw_text = f"{text} DIA"

                if next_2 == "H0LE" or next_2 == "HOLE":
                    items.append(clean_words[i + 2])
                    raw_text += " HOLE"

                add_dimension(
                    results,
                    "diameter",
                    raw_text,
                    items
                )

                continue

        # Force drawing arc angles: 30 and 60
        if upper in ["30", "30°", "30DEG"]:
            add_dimension(
                results,
                "angle",
                "30°",
                [item]
            )
            continue

        if upper in ["60", "60°", "60DEG"]:
            add_dimension(
                results,
                "angle",
                "60°",
                [item]
            )
            continue

        # 45 is only QC if not in weld symbol context
        if upper in ["45", "45°", "45DEG"]:
            if not is_weld_context(clean_words, i):
                add_dimension(
                    results,
                    "angle",
                    "45°",
                    [item]
                )
            continue

        # Radius in one OCR token: 285.8R / 285.8 R / R285.8
        if re.fullmatch(r"\d+(\.\d+)?R", upper):
            add_dimension(
                results,
                "radius",
                upper,
                [item]
            )
            continue

        if re.fullmatch(r"R\d+(\.\d+)?", upper):
            add_dimension(
                results,
                "radius",
                upper,
                [item]
            )
            continue

        # Radius split by OCR: 285.8 + R / REF
        if is_number(text):
            next_1 = clean_text(get_word(clean_words, i + 1))
            next_2 = clean_text(get_word(clean_words, i + 2))
            context = get_context(clean_words, i, window=4)

            if next_1 == "R":
                add_dimension(
                    results,
                    "radius",
                    f"{text}R",
                    [item, clean_words[i + 1]]
                )
                continue

            if "REF" in context and float(text) > 100:
                add_dimension(
                    results,
                    "radius",
                    f"{text}R",
                    [item]
                )
                continue

        # 34 x 3 / 3 x 3
        if is_number(text) and i + 2 < len(clean_words):
            middle = get_word(clean_words, i + 1).lower()
            last = get_word(clean_words, i + 2)

            if middle in ["x", "×"] and is_number(last):
                if not is_weld_context(clean_words, i):
                    add_dimension(
                        results,
                        "feature_size",
                        f"{text} x {last}",
                        [item, clean_words[i + 1], clean_words[i + 2]]
                    )
                continue

        # Large linear dimensions like 1800, but not unit weight
        if re.fullmatch(r"\d{3,5}", text):
            if not is_weld_context(clean_words, i):
                add_dimension(
                    results,
                    "linear",
                    text,
                    [item]
                )
            continue

    return results
