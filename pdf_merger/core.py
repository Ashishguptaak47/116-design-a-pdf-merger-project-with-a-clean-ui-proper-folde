import os
from dataclasses import dataclass
from typing import Callable, List, Optional
from pypdf import PdfReader, PdfWriter


@dataclass
class PDFItem:
    path: str
    filename: str
    total_pages: int
    page_range: str = "all"
    file_size_kb: float = 0.0


def parse_page_ranges(range_str: str, max_pages: int) -> List[int]:
    """Parses human-friendly page strings (1-based) into 0-based index list.

    Examples:
        'all' -> [0, 1, ..., max_pages-1]
        '1, 3-5, 8' -> [0, 2, 3, 4, 7]
    """
    normalized = (range_str or "all").strip().lower()
    if normalized in ("", "all", "*"):
        return list(range(max_pages))

    pages: set[int] = set()
    segments = [s.strip() for s in normalized.split(",") if s.strip()]

    for segment in segments:
        if "-" in segment:
            parts = segment.split("-")
            if len(parts) != 2:
                raise ValueError(f"Invalid range syntax: '{segment}'")
            start_str, end_str = parts[0].strip(), parts[1].strip()
            start = int(start_str) if start_str else 1
            end = int(end_str) if end_str else max_pages
            if start < 1 or end < 1:
                raise ValueError("Page numbers must be 1 or greater.")
            if start > end:
                raise ValueError(f"Start page {start} cannot exceed end page {end}.")
            for p in range(start, min(end, max_pages) + 1):
                pages.add(p - 1)
        else:
            p = int(segment)
            if p < 1:
                raise ValueError("Page numbers must be 1 or greater.")
            if p <= max_pages:
                pages.add(p - 1)

    result = sorted(pages)
    if not result:
        raise ValueError(f"No valid pages resolved from '{range_str}' (doc has {max_pages} pages).")
    return result


class PDFMergerEngine:
    """Core processor for reading, validating, and merging PDFs."""

    @staticmethod
    def inspect_file(file_path: str) -> PDFItem:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        size_kb = round(os.path.getsize(file_path) / 1024, 1)
        reader = PdfReader(file_path)
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                raise ValueError(f"File is password protected: {os.path.basename(file_path)}")

        total_pages = len(reader.pages)
        if total_pages == 0:
            raise ValueError(f"File has no pages: {os.path.basename(file_path)}")

        return PDFItem(
            path=file_path,
            filename=os.path.basename(file_path),
            total_pages=total_pages,
            page_range="all",
            file_size_kb=size_kb,
        )

    @staticmethod
    def merge(
        items: List[PDFItem],
        output_path: str,
        add_bookmarks: bool = True,
        progress_cb: Optional[Callable[[int, int], None]] = None,
    ) -> int:
        if not items:
            raise ValueError("No PDF files provided to merge.")

        out_dir = os.path.dirname(os.path.abspath(output_path))
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        writer = PdfWriter()
        total_files = len(items)
        accumulated_pages = 0

        for idx, item in enumerate(items):
            reader = PdfReader(item.path)
            if reader.is_encrypted:
                reader.decrypt("")

            page_indices = parse_page_ranges(item.page_range, item.total_pages)
            bookmark_target_page = accumulated_pages

            for page_idx in page_indices:
                writer.add_page(reader.pages[page_idx])
                accumulated_pages += 1

            if add_bookmarks and page_indices:
                outline_title = os.path.splitext(item.filename)[0]
                writer.add_outline_item(
                    title=outline_title,
                    page_number=bookmark_target_page
                )

            if progress_cb:
                progress_cb(idx + 1, total_files)

        with open(output_path, "wb") as f_out:
            writer.write(f_out)

        return accumulated_pages
