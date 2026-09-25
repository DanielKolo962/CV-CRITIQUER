import io

import pytest
from PyPDF2 import PdfWriter

from main import (
    detect_file_type,
    extract_text_from_file,
    extract_text_from_txt,
)


class FakeUploadedFile:
    def __init__(self, name, content):
        self.name = name
        self._content = content

    def getvalue(self):
        return self._content


def make_pdf(text="Test CV"):
    buffer = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(buffer)
    return buffer.getvalue()


def test_utf8_txt_is_detected_and_extracted():
    content = "Daniel Kolo\nAI Engineer\nPython"
    file_bytes = content.encode("utf-8")

    assert detect_file_type(file_bytes) == "txt"
    assert extract_text_from_txt(file_bytes) == content


def test_utf16_txt_is_detected_and_extracted():
    content = "Daniel Kolo\nAI Engineer\nPython"
    file_bytes = content.encode("utf-16")

    assert detect_file_type(file_bytes) == "txt"
    assert extract_text_from_txt(file_bytes) == content


def test_pdf_signature_not_at_byte_zero_is_detected():
    file_bytes = b"header-data" + b"%PDF-1.7" + b"fake-pdf-content"

    assert detect_file_type(file_bytes) == "pdf"


def test_empty_file_has_specific_error():
    uploaded_file = FakeUploadedFile("cv.txt", b"")

    with pytest.raises(ValueError, match="This file is empty"):
        extract_text_from_file(uploaded_file)


def test_pdf_renamed_as_txt_has_mismatch_error():
    pdf_bytes = b"%PDF-1.7 fake pdf content"
    uploaded_file = FakeUploadedFile("cv.txt", pdf_bytes)

    with pytest.raises(ValueError, match="named as a TXT file"):
        extract_text_from_file(uploaded_file)


def test_txt_renamed_as_pdf_has_mismatch_error():
    txt_bytes = b"Daniel Kolo\nAI Engineer\nPython"
    uploaded_file = FakeUploadedFile("cv.pdf", txt_bytes)

    with pytest.raises(ValueError, match="named as a PDF file"):
        extract_text_from_file(uploaded_file)


def test_unsupported_file_type_has_error():
    binary_bytes = bytes(range(256))
    uploaded_file = FakeUploadedFile("cv.txt", binary_bytes)

    with pytest.raises(ValueError, match="We couldn't read this file"):
        extract_text_from_file(uploaded_file)


def test_image_only_pdf_has_specific_error():
    pdf_bytes = make_pdf()
    uploaded_file = FakeUploadedFile("scanned.pdf", pdf_bytes)

    with pytest.raises(ValueError, match="couldn't find any text"):
        extract_text_from_file(uploaded_file)
