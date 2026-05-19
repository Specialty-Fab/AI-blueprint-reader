import pandas as pd


def build_qc_report(dimensions):
    rows = []

    for index, item in enumerate(dimensions, start=1):
        rows.append({
            "qc_id": f"QC-{index:03}",
            "dimension_type": item.get("type", "").title(),
            "callout": item.get("raw_text", ""),
            "status": "Needs QC Check",
            "inspector_notes": ""
        })

    return pd.DataFrame(rows)
