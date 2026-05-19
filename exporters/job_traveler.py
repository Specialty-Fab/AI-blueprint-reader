import pandas as pd


def build_job_traveler(title_block, dimensions, gdnt):
    rows = []

    for key, value in title_block.items():
        rows.append({
            "section": "Title Block",
            "field": key.replace("_", " ").title(),
            "value": value
        })

    for item in dimensions:
        rows.append({
            "section": "Dimensions",
            "field": item.get("type", "").title(),
            "value": item.get("raw_text", "")
        })

    for item in gdnt:
        rows.append({
            "section": "GD&T",
            "field": item.get("type", "").title(),
            "value": item.get("raw_text", "")
        })

    return pd.DataFrame(rows)
