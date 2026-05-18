import pytesseract
from PIL import Image

def run_ocr(image: Image.Image):

    data = pytesseract.image_to_data(
        image,
        output_type=pytesseract.Output.DICT
    )

    words = []

    for i, text in enumerate(data["text"]):

        if text.strip():

            words.append({
                "text": text,
                "confidence": float(data["conf"][i]),
                "x": data["left"][i],
                "y": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i],
            })

    return words
