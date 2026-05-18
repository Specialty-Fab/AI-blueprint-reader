import pandas as pd

def build_job_traveler(title_block, dimensions, gdnt):
    rows = []

    for key, value in title_block.items():
        rows.append({
            "section": "title_block",
            "field": key,
            "value": value
        })

    for item in dimensions:
        rows.append({
            "section": "dimension",
            "field": item.get("type", ""),
            "value": item.get("raw_text", "")
        })

    for item in gdnt:
        rows.append({
            "section": "gdnt",
            "field": item.get("type", ""),
            "value": item.get("raw_text", "")
        })

    return pd.DataFrame(rows)
