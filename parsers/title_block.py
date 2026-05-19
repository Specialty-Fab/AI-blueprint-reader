import re


def clean_value(value):
    if not value:
        return ""

    value = value.strip()
    value = re.sub(r"\s+", " ", value)
    value = value.strip(":-#| ")

    return value


def find_field(text, labels):
    lines = text.splitlines()

    for line in lines:
        clean_line = clean_value(line)

        for label in labels:
            pattern = rf"\b{re.escape(label)}\b\s*[:#\-]?\s*(.+)$"
            match = re.search(pattern, clean_line, re.IGNORECASE)

            if match:
                return clean_value(match.group(1))

    joined_text = " ".join(lines)

    for label in labels:
        pattern = rf"\b{re.escape(label)}\b\s*[:#\-]?\s*([A-Z0-9][A-Z0-9\-_.\/ ]{{0,50}})"
        match = re.search(pattern, joined_text, re.IGNORECASE)

        if match:
            return clean_value(match.group(1))

    return ""


def extract_title_block(text):
    return {
        "part_number": find_field(text, [
            "PART NO",
            "PART NUMBER",
            "PART",
            "P/N",
            "PN"
        ]),
        "drawing_number": find_field(text, [
            "DRAWING NO",
            "DRAWING NUMBER",
            "DRAWING",
            "DWG NO",
            "DWG"
        ]),
        "revision": find_field(text, [
            "REVISION",
            "REV"
        ]),
        "material": find_field(text, [
            "MATERIAL",
            "MATL",
            "MAT"
        ]),
        "finish": find_field(text, [
            "FINISH",
            "SURFACE FINISH",
            "COATING",
            "PLATING"
        ]),
        "units": find_field(text, [
            "UNITS",
            "UNIT"
        ]),
        "scale": find_field(text, [
            "SCALE"
        ]),
        "sheet": find_field(text, [
            "SHEET"
        ]),
        "description": find_field(text, [
            "DESCRIPTION",
            "DESC",
            "TITLE"
        ]),
        "customer": find_field(text, [
            "CUSTOMER",
            "CLIENT"
        ]),
        "date": find_field(text, [
            "DATE"
        ]),
        "drawn_by": find_field(text, [
            "DRAWN BY",
            "DRAWN",
            "DRN"
        ]),
        "checked_by": find_field(text, [
            "CHECKED BY",
            "CHECKED",
            "CHK"
        ])
    }
