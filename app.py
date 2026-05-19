import json

import streamlit as st
from PIL import Image, ImageDraw

from ocr import run_ocr
from parsers.title_block import extract_title_block
from parsers.dimensions import extract_dimensions
from parsers.gdnt import extract_gdnt
from exporters.job_traveler import build_job_traveler
from exporters.qc_report import build_qc_report
from utils.image_preprocess import preprocess_image


def draw_review_box(image, item, label="Review this area", color="red"):

    marked = image.convert("RGB").copy()
    draw = ImageDraw.Draw(marked)

    x = int(item.get("x", 0))
    y = int(item.get("y", 0))
    width = int(item.get("width", 0))
    height = int(item.get("height", 0))

    padding = 8

    box = [
        max(x - padding, 0),
        max(y - padding, 0),
        x + width + padding,
        y + height + padding,
    ]

    draw.rectangle(box, outline=color, width=4)

    draw.text(
        (box[0], max(box[1] - 22, 0)),
        label,
        fill=color
    )

    return marked


def draw_qc_callouts(image, dimensions, checked_status=None):

    marked = image.convert("RGB").copy()
    draw = ImageDraw.Draw(marked)

    checked_status = checked_status or {}

    for index, item in enumerate(dimensions, start=1):

        x = int(item.get("x", 0))
        y = int(item.get("y", 0))
        width = int(item.get("width", 80))
        height = int(item.get("height", 24))

        qc_id = f"QC-{index:03}"

        checked = checked_status.get(
            qc_id,
            False
        )

        color = "green" if checked else "orange"

        mark = "✓" if checked else "□"

        padding = 10

        box = [
            max(x - padding, 0),
            max(y - padding, 0),
            x + width + padding,
            y + height + padding,
        ]

        draw.rectangle(
            box,
            outline=color,
            width=4
        )

        draw.text(
            (box[0], max(box[1] - 24, 0)),
            f"{mark} {qc_id}",
            fill=color
        )

    return marked


st.set_page_config(
    page_title="AI Blueprint Reader",
    layout="wide"
)

st.title("AI Blueprint Reader")

st.caption(
    "Upload a blueprint image, review OCR results, edit fields, and generate QC reports."
)

uploaded = st.file_uploader(
    "Upload blueprint image",
    type=["png", "jpg", "jpeg"]
)

if uploaded:

    image = Image.open(uploaded).convert("RGB")

    left_col, right_col = st.columns([1.2, 1])

    with left_col:

        st.subheader("Blueprint Preview")

        st.image(
            image,
            caption="Uploaded Blueprint",
            use_container_width=True
        )

    with right_col:

        st.subheader("Extraction Summary")

        try:

            with st.spinner(
                "Cleaning image and reading blueprint..."
            ):

                processed_image = preprocess_image(image)

                words = run_ocr(processed_image)

        except Exception as error:

            st.error(
                "OCR failed. Check that Tesseract is installed and available."
            )

            st.exception(error)

            st.stop()

        low_confidence = [
            w for w in words
            if w.get("confidence", 0) < 85
        ]

        full_text = "\n".join([
            w.get("text", "")
            for w in words
            if w.get("text", "").strip() != ""
        ])

        st.metric(
            "OCR Text Items",
            len(words)
        )

        st.metric(
            "Needs Review",
            len(low_confidence)
        )

        if low_confidence:

            st.warning(
                "Some OCR results need human review."
            )

        else:

            st.success(
                "All OCR items passed confidence review."
            )

    st.divider()

    with st.expander("Show processed OCR image"):

        st.image(
            processed_image,
            caption="Image cleaned for OCR",
            use_container_width=True
        )

    tab_review, tab_title, tab_dims, tab_qc, tab_gdnt, tab_export = st.tabs([
        "Review",
        "Title Block",
        "Dimensions",
        "QC Report",
        "GD&T",
        "Export"
    ])

    title_block = extract_title_block(full_text)

    dimensions = extract_dimensions(words)

    gdnt = extract_gdnt(full_text)

    reviewed_items = []

    qc_checked_items = []

    qc_checked_status = {}

    with tab_review:

        st.subheader("Review Required")

        if low_confidence:

            for index, item in enumerate(
                low_confidence,
                start=1
            ):

                text = item.get("text", "")

                confidence = item.get(
                    "confidence",
                    0
                )

                with st.expander(
                    f"Review item {index}: '{text}' - {confidence:.0f}% confidence"
                ):

                    corrected_text = st.text_input(
                        "Correct this text if needed",
                        value=text,
                        key=f"review_text_{index}"
                    )

                    st.progress(
                        min(
                            max(confidence / 100, 0),
                            1
                        )
                    )

                    marked_image = draw_review_box(
                        processed_image,
                        item
                    )

                    st.image(
                        marked_image,
                        caption=f"Location for review item {index}",
                        use_container_width=True
                    )

                    approved = st.checkbox(
                        "Reviewed and approved",
                        key=f"review_approved_{index}"
                    )

                    reviewed_items.append({
                        "original_text": text,
                        "corrected_text": corrected_text,
                        "confidence": confidence,
                        "approved": approved,
                        "x": item.get("x", ""),
                        "y": item.get("y", ""),
                        "width": item.get("width", ""),
                        "height": item.get("height", "")
                    })

        else:

            st.success(
                "No low-confidence OCR items found."
            )

    with tab_title:

        st.subheader("Title Block Fields")

        edited_title_block = {}

        for key, value in title_block.items():

            edited_title_block[key] = st.text_input(
                key.replace("_", " ").title(),
                value
            )

    with tab_dims:

        st.subheader("Detected Dimensions")

        if dimensions:

            st.json(dimensions)

        else:

            st.info(
                "No dimensions detected yet."
            )

    with tab_qc:

        st.subheader("QC Dimension Report")

        st.caption(
            "Orange boxes need checking. Green boxes are checked."
        )

        if dimensions:

            qc_report = build_qc_report(
                dimensions
            )

            for index, item in enumerate(
                dimensions,
                start=1
            ):

                qc_id = f"QC-{index:03}"

                callout = item.get(
                    "raw_text",
                    ""
                )

                dim_type = item.get(
                    "type",
                    ""
                ).title()

                with st.expander(
                    f"{qc_id} | {dim_type} | {callout}"
                ):

                    checked = st.checkbox(
                        "QC checked",
                        key=f"qc_checked_{index}"
                    )

                    qc_checked_status[qc_id] = checked

                    measured_value = st.text_input(
                        "Measured value",
                        key=f"qc_measured_{index}"
                    )

                    pass_fail = st.selectbox(
                        "Pass / Fail",
                        [
                            "Needs Check",
                            "Pass",
                            "Fail"
                        ],
                        key=f"qc_pass_fail_{index}"
                    )

                    notes = st.text_input(
                        "Inspector notes",
                        key=f"qc_notes_{index}"
                    )

                    qc_checked_items.append({
                        "qc_id": qc_id,
                        "dimension_type": dim_type,
                        "dimension_callout": callout,
                        "qc_checked": checked,
                        "measured_value": measured_value,
                        "pass_fail": pass_fail,
                        "inspector_notes": notes
                    })

            qc_preview = draw_qc_callouts(
                processed_image,
                dimensions,
                qc_checked_status
            )

            st.image(
                qc_preview,
                caption="QC callouts on processed drawing",
                use_container_width=True
            )

            st.dataframe(
                qc_report,
                use_container_width=True
            )

        else:

            st.info(
                "No dimensions detected yet."
            )

    with tab_gdnt:

        st.subheader("GD&T Candidates")

        if gdnt:

            st.json(gdnt)

        else:

            st.info(
                "No GD&T candidates detected yet."
            )

    with tab_export:

        st.subheader("Job Traveler Export")

        traveler = build_job_traveler(
            edited_title_block,
            dimensions,
            gdnt
        )

        st.dataframe(
            traveler,
            use_container_width=True
        )

        st.download_button(
            "Download Job Traveler CSV",
            traveler.to_csv(index=False),
            file_name="job_traveler.csv",
            mime="text/csv"
        )

        reviewed_data = {
            "title_block": edited_title_block,
            "dimensions": dimensions,
            "gdnt": gdnt,
            "reviewed_low_confidence_items": reviewed_items,
            "qc_report": qc_checked_items
        }

        st.download_button(
            "Download Reviewed JSON",
            json.dumps(
                reviewed_data,
                indent=2
            ),
            file_name="reviewed_extraction.json",
            mime="application/json"
        )

else:

    st.info(
        "Upload a blueprint image to begin."
    )
