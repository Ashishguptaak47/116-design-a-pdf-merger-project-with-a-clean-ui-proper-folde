import argparse
import sys
import os
from pdf_merger.core import PDFMergerEngine, PDFItem


def run_cli(args: argparse.Namespace) -> int:
    if not args.inputs:
        print("Error: At least one input PDF must be provided with -i/--inputs.", file=sys.stderr)
        return 1

    ranges = args.ranges or []
    items = []
    for i, path in enumerate(args.inputs):
        if not os.path.exists(path):
            print(f"Error: Input file does not exist: {path}", file=sys.stderr)
            return 1
        item = PDFMergerEngine.inspect_file(path)
        if i < len(ranges):
            item.page_range = ranges[i]
        items.append(item)

    output = args.output or "merged_output.pdf"
    print(f"Merging {len(items)} file(s) into '{output}'...")
    
    def cli_progress(current: int, total: int) -> None:
        print(f"  [{current}/{total}] {items[current-1].filename}")

    try:
        pages = PDFMergerEngine.merge(
            items=items,
            output_path=output,
            add_bookmarks=args.bookmarks,
            progress_cb=cli_progress,
        )
        print(f"Done! Successfully generated '{output}' with {pages} page(s).")
        return 0
    except Exception as e:
        print(f"Merge failed: {e}", file=sys.stderr)
        return 1


def run_gui() -> None:
    import tkinter as tk
    from pdf_merger.gui import PDFMergerApp

    root = tk.Tk()
    app = PDFMergerApp(root)
    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PDF Merger Suite - Merge and organize PDF documents effortlessly."
    )
    parser.add_argument("-i", "--inputs", nargs="+", help="Path to one or more PDF input files.")
    parser.add_argument("-o", "--output", help="Output PDF file path.")
    parser.add_argument(
        "--ranges",
        nargs="+",
        help="Page ranges per file matching --inputs (e.g. '1-3' 'all' '2,4').",
    )
    parser.add_argument(
        "--bookmarks",
        action="store_true",
        help="Generate bookmarks based on source filenames.",
    )
    parser.add_argument("--cli", action="store_true", help="Force CLI mode even without inputs.")

    args = parser.parse_args()

    if args.inputs or args.cli:
        sys.exit(run_cli(args))
    else:
        run_gui()


if __name__ == "__main__":
    main()
