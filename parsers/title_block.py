import re

def find_after(text, labels):
    for label in labels:
        pattern = rf"{label}[:\s\-#]*([A-Z0-9][A-Z0-9\-_.\/ ]{{0,40}})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""

def extract_title_block(text):
    return {
        "part_number": find_after(text, ["PART NO", "PART NUMBER", "PN", "P/N"]),
        "drawing_number": find_after(text, ["DRAWING NO", "DRAWING", "DWG NO", "DWG"]),
        "revision": find_after(text, ["REVISION", "REV"]),
        "material": find_after(text, ["MATERIAL", "MATL"]),
        "finish": find_after(text, ["FINISH"]),
        "units": find_after(text, ["UNITS"]),
        "scale": find_after(text, ["SCALE"]),
    }
