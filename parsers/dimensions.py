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


def clean_text(text):
    return (
        text.upper()
        .replace("O", "0")
        .replace("Ø", "DIA")
        .replace("⌀", "DIA")
        .strip()
    )


def get_word(words, index):
    if 0 <= index < len(words):
        return words[index].get("text", "").strip()
    return ""


def get_nearby_context(words, index, window=3):
    start = max(index - window, 0)
    end = min(index + window + 1, len(words))

    return " ".join(
        words[i].get("text", "")
        for i in range(start, end)
    ).upper()


def is_weld_spec(text):
    return bool(re.fullmatch(r"\d+-\d+-\d+", text.strip()))


def is_weight_context(words, index):
    context = get_nearby_context(words, index, window=5)

    return any(word in context for word in WEIGHT_WORDS)


def is_weld_context(words, index):
    context = get_nearby_context(words, index, window=2)

    return any(word in context for word in WELD_WORDS)


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
        "confidence": min(
            float(item.get("confidence", 0))
            for item in items
        )
    }


def add_dimension(results, dim_type, raw_text, items):
    raw_text = raw_text.strip()

    if not raw_text:
        return

    existing = [
        row["raw_text"]
        for row in results
    ]

    if raw_text in existing:
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


def words_are_close(first, second, max_x_gap=85, max_y_gap=22):
    first_x = int(first.get("x", 0))
    first_y = int(first.get("y", 0))
    first_w = int(first.get("width", 0))

    second_x = int(second.get("x", 0))
    second_y = int(second.get("y", 0))

    x_gap = second_x - (first_x + first_w)
    y_gap = abs(second_y - first_y)

    return x_gap <= max_x_gap and y_gap <= max_y_gap


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

        # 281 DIA HOLE / 154 DIA HOLE
        if is_number(text):
            next_1 = get_word(clean_words, i + 1)
            next_2 = get_word(clean_words, i + 2)

            next_1_clean = clean_text(next_1)
            next_2_clean = clean_text(next_2)

            if (
                next_1_clean == "DIA"
                and i + 1 < len(clean_words)
                and words_are_close(item, clean_words[i + 1])
            ):
                merged_items = [
                    item,
                    clean_words[i + 1]
                ]

                merged_text = f"{text} DIA"

                if (
                    next_2_clean == "HOLE"
                    and i + 2 < len(clean_words)
                    and words_are_close(clean_words[i + 1], clean_words[i + 2])
                ):
                    merged_items.append(clean_words[i + 2])
                    merged_text += " HOLE"

                add_dimension(
                    results,
                    "diameter",
                    merged_text,
                    merged_items
                )

                continue

        # DIA 281 / DIA 154
        if upper == "DIA" and i + 1 < len(clean_words):
            next_text = get_word(clean_words, i + 1)

            if is_number(next_text):
                add_dimension(
                    results,
                    "diameter",
                    f"DIA {next_text}",
                    [
                        item,
                        clean_words[i + 1]
                    ]
                )

                continue

        # 30°, 45°, 60°
        if re.fullmatch(r"\d+\s*°", text):
            if not is_weld_context(clean_words, i):
                add_dimension(
                    results,
                    "angle",
                    text.replace(" ", ""),
                    [item]
                )

            continue

        # OCR often drops degree symbol
        if text in ["30", "45", "60", "90"]:
            if not is_weld_context(clean_words, i):
                add_dimension(
                    results,
                    "angle",
                    f"{text}°",
                    [item]
                )

            continue

        # 285.8R / R285.8
        if re.fullmatch(r"\d+(\.\d+)?R", upper):
            add_dimension(
                results,
                "radius",
                text,
                [item]
            )

            continue

        if re.fullmatch(r"R\d+(\.\d+)?", upper):
            add_dimension(
                results,
                "radius",
                text,
                [item]
            )

            continue

        # 285.8 + R
        if is_number(text) and i + 1 < len(clean_words):
            next_1 = clean_text(get_word(clean_words, i + 1))

            if (
                next_1 == "R"
                and words_are_close(item, clean_words[i + 1])
            ):
                add_dimension(
                    results,
                    "radius",
                    f"{text}R",
                    [
                        item,
                        clean_words[i + 1]
                    ]
                )

                continue

        # 34 x 3
        if is_number(text) and i + 2 < len(clean_words):
            middle = get_word(clean_words, i + 1).lower()
            last = get_word(clean_words, i + 2)

            if (
                middle in ["x", "×"]
                and is_number(last)
                and words_are_close(item, clean_words[i + 1])
                and words_are_close(clean_words[i + 1], clean_words[i + 2])
                and not is_weld_context(clean_words, i)
            ):
                add_dimension(
                    results,
                    "feature_size",
                    f"{text} x {last}",
                    [
                        item,
                        clean_words[i + 1],
                        clean_words[i + 2]
                    ]
                )

                continue

        # 1800 trim dimension, but not unit weight
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
