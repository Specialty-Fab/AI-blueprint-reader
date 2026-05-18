from pdf2image import convert_from_bytes


def load_pdf(uploaded_file):

    pages = convert_from_bytes(
        uploaded_file.read()
    )

    return pages
