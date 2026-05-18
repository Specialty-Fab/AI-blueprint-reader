import re

def extract_dimensions(text):
    patterns = [
        ("linear", r"\b\d+\.\d+\s*(?:±|\+/-)\s*\.?\d+\b"),
        ("diameter", r"(?:Ø|⌀|DIA)\s*\d+\.\d+"),
        ("radius", r"\bR\s*\d+\.\d+"),
        ("angle", r"\b\d+\s*(?:°|DEG)\b"),
        ("thread", r"\b\d+\/\d+-\d+\s*(?:UNC|UNF)?\b"),
        ("edge_break", r"\.?\d+\s*-\s*\.?\d+"),
    ]

    results = []

    for dim_type, pattern in patterns:
        for match in re.findall(pattern, text, re.IGNORECASE):
            results.append({
                "type": dim_type,
                "raw_text": match.strip()
            })

    return results
