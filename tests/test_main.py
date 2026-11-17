import os
import pytest
from pypdf import PdfReader, PdfWriter
from pdf_merger.core import PDFMergerEngine, PDFItem, parse_page_ranges


def _create_dummy_pdf(filepath: str, num_pages: int) -> str:
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=100, height=100)
    with open(filepath, "wb") as f:
        writer.write(f)
    return filepath


def test_parse_page_ranges_all():
    assert parse_page_ranges("all", 5) == [0, 1, 2, 3, 4]
    assert parse_page_ranges("", 3) == [0, 1, 2]


def test_parse_page_ranges_custom():
    assert parse_page_ranges("1, 3, 5", 5) == [0, 2, 4]
    assert parse_page_ranges("2-4", 6) == [1, 2, 3]
    assert parse_page_ranges("1-2, 5", 5) == [0, 1, 4]


def test_parse_page_ranges_invalid():
    with pytest.raises(ValueError):
        parse_page_ranges("0", 5)
    with pytest.raises(ValueError):
        parse_page_ranges("5-2", 5)
    with pytest.raises(ValueError):
        parse_page_ranges("abc", 5)


def test_inspect_file(tmp_path):
    pdf_path = str(tmp_path / "doc1.pdf")
    _create_dummy_pdf(pdf_path, 4)

    item = PDFMergerEngine.inspect_file(pdf_path)
    assert item.filename == "doc1.pdf"
    assert item.total_pages == 4
    assert item.file_size_kb > 0


def test_merge_success(tmp_path):
    pdf1 = str(tmp_path / "doc1.pdf")
    pdf2 = str(tmp_path / "doc2.pdf")
    out_pdf = str(tmp_path / "merged.pdf")

    _create_dummy_pdf(pdf1, 3)
    _create_dummy_pdf(pdf2, 2)

    item1 = PDFItem(path=pdf1, filename="doc1.pdf", total_pages=3, page_range="1-2")
    item2 = PDFItem(path=pdf2, filename="doc2.pdf", total_pages=2, page_range="all")

    total_pages = PDFMergerEngine.merge([item1, item2], out_pdf, add_bookmarks=True)
    assert total_pages == 4  # 2 from doc1 + 2 from doc2
    assert os.path.exists(out_pdf)

    reader = PdfReader(out_pdf)
    assert len(reader.pages) == 4
    assert len(reader.outline) == 2


def test_merge_empty_list(tmp_path):
    out_pdf = str(tmp_path / "empty.pdf")
    with pytest.raises(ValueError, match="No PDF files"):
        PDFMergerEngine.merge([], out_pdf)
