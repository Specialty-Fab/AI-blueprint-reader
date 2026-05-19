import pandas as pd


def build_qc_report(dimensions):
    rows = []

    for index, item in enumerate(dimensions, start=1):
        dim_type = item.get("type", "").title()
        callout = item.get("raw_text", "")

        rows.append({
            "qc_id": f"QC-{index:03}",
            "dimension_type": dim_type,
            "dimension_callout": callout,
            "qc_check_required": "Yes",
            "qc_status": "Needs Check",
            "measured_value": "",
            "pass_fail": "",
            "inspector_notes": ""
        })

    return pd.DataFrame(rows)
