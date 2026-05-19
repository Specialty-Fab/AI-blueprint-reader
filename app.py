import json

import streamlit as st
from PIL import Image

from ocr import run_ocr
from parsers.title_block import extract_title_block
from parsers.dimensions import extract_dimensions
from parsers.gdnt import extract_gdnt
from exporters.job_traveler import build_job_traveler
from utils.image_preprocess import preprocess_image

st.set_page_config(
    page_title="AI Blueprint Reader",
    layout="wide"
)

st.title("AI Blueprint Reader")
st.caption("Upload a blueprint image, review uncertain reads, edit fields, then export a job traveler.")

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
            with st.spinner("Cleaning image and reading blueprint..."):
                processed_image = preprocess_image(image)
                words = run_ocr(processed_image)

        except Exception as error:
            st.error("OCR failed. Check that Tesseract is installed and available.")
            st.exception(error)
            st.stop()

        low_confidence = [
            w for w in words
            if w.get("confidence", 0) < 85
        ]

        full_text = " ".join([
            w.get("text", "")
            for w in words
        ])

        st.metric("OCR Text Items", len(words))
        st.metric("Needs Review", len(low_confidence))

        if low_confidence:
            st.warning("Some OCR results need human review.")
        else:
            st.success("All OCR items passed confidence review.")

    st.divider()

    with st.expander("Show processed OCR image"):
        st.image(
            processed_image,
            caption="Image cleaned for OCR",
            use_container_width=True
        )

    tab_review, tab_title, tab_dims, tab_gdnt, tab_export = st.tabs([
        "Review",
        "Title Block",
        "Dimensions",
        "GD&T",
        "Export"
    ])

    title_block = extract_title_block(full_text)
    dimensions = extract_dimensions(full_text)
    gdnt = extract_gdnt(full_text)

    reviewed_items = []

    with tab_review:
        st.subheader("Review Required")
        st.caption("These are OCR reads that may need a quick human check before export.")

        if low_confidence:
            st.warning(
                f"{len(low_confidence)} items need review. Most may be tiny marks, broken letters, or low-quality scan areas."
            )

            for index, item in enumerate(low_confidence, start=1):
                text = item.get("text", "")
                confidence = item.get("confidence", 0)

                with st.expander(
                    f"Review item {index}: '{text}' - {confidence:.0f}% confidence"
                ):
                    corrected_text = st.text_input(
                        "Correct this text if needed",
                        value=text,
                        key=f"review_text_{index}"
                    )

                    st.progress(
                        min(max(confidence / 100, 0), 1)
                    )

                    st.caption(
                        f"Location on print: X {item.get('x', '')}, "
                        f"Y {item.get('y', '')}, "
                        f"Width {item.get('width', '')}, "
                        f"Height {item.get('height', '')}"
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
            st.success("No low-confidence OCR items found.")

    with tab_title:
        st.subheader("Title Block Fields")
        st.caption("Edit these before exporting the job traveler.")

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
            st.info("No dimensions detected yet.")

    with tab_gdnt:
        st.subheader("GD&T Candidates")

        if gdnt:
            st.json(gdnt)
        else:
            st.info("No GD&T candidates detected yet.")

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
            "reviewed_low_confidence_items": reviewed_items
        }

        st.download_button(
            "Download Reviewed JSON",
            json.dumps(reviewed_data, indent=2),
            file_name="reviewed_extraction.json",
            mime="application/json"
        )

else:
    st.info("Upload a blueprint image to begin.")
