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

uploaded = st.file_uploader(
    "Upload blueprint image",
    type=["png", "jpg", "jpeg"]
)

if uploaded:

    image = Image.open(uploaded)

    st.image(
        image,
        caption="Blueprint Preview",
        use_container_width=True
    )

    st.subheader("OCR Processing")

    words = run_ocr(image)

    full_text = " ".join([
        w["text"] for w in words
    ])

    st.success(
        f"OCR found {len(words)} text elements"
    )

    st.subheader("Title Block")

    title_block = extract_title_block(full_text)

    st.json(title_block)

    st.subheader("Dimensions")

    dimensions = extract_dimensions(full_text)

    st.json(dimensions)

    st.subheader("GD&T")

    gdnt = extract_gdnt(full_text)

    st.json(gdnt)

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
