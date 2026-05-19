import re


def extract_gdnt(text):
    patterns = [
        ("position", r"(?:⌖|POSITION|POS)\s*\.?\d+\.?\d*\s*[A-Z]?\s*[A-Z]?"),
        ("flatness", r"(?:⌔|FLATNESS)\s*\.?\d+\.?\d*"),
        ("parallelism", r"(?:∥|PARALLELISM)\s*\.?\d+\.?\d*\s*[A-Z]?"),
        ("perpendicularity", r"(?:⊥|PERPENDICULARITY)\s*\.?\d+\.?\d*\s*[A-Z]?"),
        ("profile", r"(?:⌒|PROFILE)\s*\.?\d+\.?\d*"),
        ("datum", r"\bDATUM\s+[A-Z]\b"),
    ]

    results = []

    for gdnt_type, pattern in patterns:
        for match in re.findall(pattern, text, re.IGNORECASE):
            results.append({
                "type": gdnt_type,
                "raw_text": match.strip()
            })

    return results
