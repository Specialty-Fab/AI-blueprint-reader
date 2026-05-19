import cv2
import numpy as np
from PIL import Image, ImageEnhance


def preprocess_image(image):
    # Convert to grayscale
    gray_image = image.convert("L")

    # Boost contrast before OpenCV processing
    contrast = ImageEnhance.Contrast(gray_image).enhance(1.8)
    sharp = ImageEnhance.Sharpness(contrast).enhance(1.6)

    img = np.array(sharp)

    # Light denoise only, so small text survives
    denoised = cv2.fastNlMeansDenoising(
        img,
        None,
        7,
        7,
        21
    )

    # Adaptive threshold for uneven scans
    cleaned = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        15,
        8
    )

    # Tiny morphological open to remove specks without eating letters
    kernel = np.ones((1, 1), np.uint8)

    cleaned = cv2.morphologyEx(
        cleaned,
        cv2.MORPH_OPEN,
        kernel
    )

    return Image.fromarray(cleaned)
