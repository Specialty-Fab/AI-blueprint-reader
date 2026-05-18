# AI Blueprint Reader

A Streamlit MVP that reads blueprint images, extracts title block data, detects dimensions and GD&T candidates, flags low-confidence OCR, and exports job traveler files.

## Features

- Upload blueprint images
- OCR blueprint text
- Extract title block fields
- Detect dimensions
- Detect GD&T candidates
- Review low-confidence OCR
- Edit title block fields before export
- Export job traveler CSV
- Export reviewed JSON

## Project Structure

```text
app.py
ocr.py
requirements.txt

parsers/
  title_block.py
  dimensions.py
  gdnt.py

exporters/
  job_traveler.py
