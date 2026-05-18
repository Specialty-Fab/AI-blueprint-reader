import streamlit as st
from PIL import Image

from ocr import run_ocr
from parsers.title_block import extract_title_block
from parsers.dimensions import extract_dimensions
from parsers.gdnt import extract_gdnt
from exporters.job_traveler import build_job_traveler

st.set_page_config(
    page_title="AI Blueprint Reader",
    layout="wide"
)

st.title("AI Blueprint Reader")
st.caption("Upload a blueprint, review uncertain reads, then export a job traveler.")

uploaded = st.file_uploader(
    "Upload blueprint image",
    type=["png", "jpg", "jpeg"]
)

if uploaded:

    image = Image.open(uploaded)

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

        words = run_ocr(image)

        low_confidence = [
            w for w in words
            if w["confidence"] < 85
        ]

        full_text = " ".join([
            w["text"] for w in words
        ])

        st.metric("OCR Text Items", len(words))
        st.metric("Needs Review", len(low_confidence))

        if low_confidence:
            st.warning("Some OCR results need human review.")
        else:
            st.success("All OCR items passed confidence review.")

    st.divider()

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

    with tab_review:
        st.subheader("Review Required")

        if low_confidence:
            st.dataframe(
                low_confidence,
                use_container_width=True
            )
        else:
            st.success("No low-confidence OCR items found.")

    with tab_title:
        st.subheader("Title Block Fields")
        st.json(title_block)

    with tab_dims:
        st.subheader("Detected Dimensions")
        st.json(dimensions)

    with tab_gdnt:
        st.subheader("GD&T Candidates")
        st.json(gdnt)

    with tab_export:
        st.subheader("Job Traveler Export")

        traveler = build_job_traveler(
            title_block,
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
else:
    st.info("Upload a blueprint image to begin.")
