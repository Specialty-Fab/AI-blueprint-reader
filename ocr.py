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
            confidence = data["conf"][i]

            try:
                confidence = float(confidence)
            except ValueError:
                confidence = 0.0

            words.append({
                "text": text,
                "confidence": confidence,
                "x": data["left"][i],
                "y": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i],
            })

    return words
