import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def preprocess_image(image):

    # Convert to grayscale
    gray = image.convert("L")

    # Increase contrast
    contrast = ImageEnhance.Contrast(gray).enhance(2.2)

    # Slight sharpen
    sharp = ImageEnhance.Sharpness(contrast).enhance(2.4)

    # Extra edge sharpening
    sharp = sharp.filter(
        ImageFilter.SHARPEN
    )

    img = np.array(sharp)

    # Very light denoise
    denoised = cv2.fastNlMeansDenoising(
        img,
        None,
        4,
        7,
        21
    )

    # Adaptive threshold tuned for blueprints
    thresh = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        21,
        4
    )

    # Small morphology cleanup
    kernel = np.ones((1, 1), np.uint8)

    cleaned = cv2.morphologyEx(
        thresh,
        cv2.MORPH_CLOSE,
        kernel
    )

    return Image.fromarray(cleaned)
