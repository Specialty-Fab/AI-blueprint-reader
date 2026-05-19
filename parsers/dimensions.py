def extract_dimensions(words):
    results = []

    for i, item in enumerate(words):

        text = item.get("text", "").strip()
        upper = text.upper()

        if not text:
            continue

        if is_weld_spec(text):
            continue

        if is_weight_context(words, i):
            continue

        if is_weld_context(words, i):
            continue

        # ---------------------------------------------------
        # 154 DIA HOLE / 281 DIA HOLE
        # ---------------------------------------------------

        if is_number(text):

            next_1 = get_word(words, i + 1).upper()
            next_2 = get_word(words, i + 2).upper()

            if next_1 == "DIA":

                merged_items = [item, words[i + 1]]

                merged_text = f"{text} DIA"

                if next_2 == "HOLE":
                    merged_items.append(words[i + 2])
                    merged_text += " HOLE"

                add_dimension(
                    results,
                    "diameter",
                    merged_text,
                    merged_items
                )

                continue

        # ---------------------------------------------------
        # 30° / 45° / 60°
        # ---------------------------------------------------

        if re.fullmatch(r"\d+\s*°", text):

            add_dimension(
                results,
                "angle",
                text.replace(" ", ""),
                [item]
            )

            continue

        # OCR sometimes strips degree symbol
        if text in ["30", "45", "60", "90"]:

            add_dimension(
                results,
                "angle",
                f"{text}°",
                [item]
            )

            continue

        # ---------------------------------------------------
        # 285.8R
        # ---------------------------------------------------

        if re.fullmatch(r"\d+(\.\d+)?R", upper):

            add_dimension(
                results,
                "radius",
                text,
                [item]
            )

            continue

        # OCR split radius: 285.8 + R
        if is_number(text):

            next_1 = get_word(words, i + 1).upper()

            if next_1 == "R":

                add_dimension(
                    results,
                    "radius",
                    f"{text}R",
                    [item, words[i + 1]]
                )

                continue

        # ---------------------------------------------------
        # 34 x 3
        # ---------------------------------------------------

        if is_number(text):

            middle = get_word(words, i + 1).lower()
            last = get_word(words, i + 2)

            if middle in ["x", "×"] and is_number(last):

                add_dimension(
                    results,
                    "feature_size",
                    f"{text} x {last}",
                    [item, words[i + 1], words[i + 2]]
                )

                continue

        # ---------------------------------------------------
        # 1800
        # ---------------------------------------------------

        if re.fullmatch(r"\d{3,5}", text):

            add_dimension(
                results,
                "linear",
                text,
                [item]
            )

            continue

    return results
