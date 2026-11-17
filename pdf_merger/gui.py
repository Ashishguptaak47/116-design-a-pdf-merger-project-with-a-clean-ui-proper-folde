import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import List
from .core import PDFItem, PDFMergerEngine, parse_page_ranges


class PDFMergerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("PDF Merger Professional")
        self.root.geometry("880x560")
        self.root.minsize(720, 420)

        self.items: List[PDFItem] = []
        self._configure_styles()
        self._build_ui()

    def _configure_styles(self) -> None:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("Treeview", rowheight=28, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("TButton", padding=5, font=("Segoe UI", 9))
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Status.TLabel", font=("Segoe UI", 8))

    def _build_ui(self) -> None:
        # Top toolbar
        toolbar = ttk.Frame(self.root, padding="10 10 10 5")
        toolbar.pack(fill=tk.X)

        ttk.Button(toolbar, text="Add Files", command=self.add_files).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Add Folder", command=self.add_folder).pack(side=tk.LEFT, padx=3)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        ttk.Button(toolbar, text="Move Up", command=lambda: self.move_item(-1)).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Move Down", command=lambda: self.move_item(1)).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Set Pages", command=self.edit_page_range).pack(side=tk.LEFT, padx=3)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        ttk.Button(toolbar, text="Remove", command=self.remove_selected).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=3)

        # Central List Treeview
        center_frame = ttk.Frame(self.root, padding="10 5 10 5")
        center_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("idx", "filename", "pages", "range", "size", "path")
        self.tree = ttk.Treeview(center_frame, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("idx", text="#")
        self.tree.heading("filename", text="File Name")
        self.tree.heading("pages", text="Total Pages")
        self.tree.heading("range", text="Selected Pages")
        self.tree.heading("size", text="Size (KB)")
        self.tree.heading("path", text="Full Path")

        self.tree.column("idx", width=35, anchor=tk.CENTER)
        self.tree.column("filename", width=220, anchor=tk.W)
        self.tree.column("pages", width=80, anchor=tk.CENTER)
        self.tree.column("range", width=110, anchor=tk.CENTER)
        self.tree.column("size", width=80, anchor=tk.E)
        self.tree.column("path", width=280, anchor=tk.W)

        tree_scroll = ttk.Scrollbar(center_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<Double-1>", lambda event: self.edit_page_range())

        # Bottom Options & Controls
        bottom_panel = ttk.Frame(self.root, padding="10 5 10 10")
        bottom_panel.pack(fill=tk.X)

        self.bookmark_var = tk.BooleanVar(value=True)
        bookmark_chk = ttk.Checkbutton(
            bottom_panel,
            text="Generate Document Bookmarks / Table of Contents",
            variable=self.bookmark_var,
        )
        bookmark_chk.pack(side=tk.LEFT, pady=5)

        self.merge_btn = ttk.Button(
            bottom_panel,
            text="Merge PDFs",
            style="Action.TButton",
            command=self.run_merge,
        )
        self.merge_btn.pack(side=tk.RIGHT, padx=5)

        # Status bar and Progress bar
        status_frame = ttk.Frame(self.root, padding="10 0 10 6")
        status_frame.pack(fill=tk.X)
        self.status_var = tk.StringVar(value="Ready. Add PDF files to begin.")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress = ttk.Progressbar(status_frame, mode="determinate", length=180)
        self.progress.pack(side=tk.RIGHT)

    def refresh_tree(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for i, item in enumerate(self.items):
            self.tree.insert(
                "",
                tk.END,
                iid=str(i),
                values=(i + 1, item.filename, item.total_pages, item.page_range, item.file_size_kb, item.path),
            )
        self.status_var.set(f"{len(self.items)} file(s) in queue.")

    def add_files(self) -> None:
        files = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
        )
        if not files:
            return
        for f in files:
            self._safe_append_file(f)
        self.refresh_tree()

    def add_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select Folder containing PDFs")
        if not folder:
            return
        pdf_files = sorted([
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith(".pdf") and os.path.isfile(os.path.join(folder, f))
        ])
        if not pdf_files:
            messagebox.showinfo("No PDFs", "No PDF files found in selected directory.")
            return
        for p in pdf_files:
            self._safe_append_file(p)
        self.refresh_tree()

    def _safe_append_file(self, file_path: str) -> None:
        try:
            item = PDFMergerEngine.inspect_file(file_path)
            self.items.append(item)
        except Exception as e:
            messagebox.showwarning("File Skipped", f"Cannot load '{os.path.basename(file_path)}':\n{e}")

    def _get_selected_index(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            return None
        return int(sel[0])

    def move_item(self, delta: int) -> None:
        idx = self._get_selected_index()
        if idx is None:
            return
        new_idx = idx + delta
        if 0 <= new_idx < len(self.items):
            self.items[idx], self.items[new_idx] = self.items[new_idx], self.items[idx]
            self.refresh_tree()
            self.tree.selection_set(str(new_idx))

    def edit_page_range(self) -> None:
        idx = self._get_selected_index()
        if idx is None:
            messagebox.showinfo("Select File", "Please select a file to edit its page range.")
            return
        item = self.items[idx]
        val = simpledialog.askstring(
            "Page Range",
            f"Enter pages for '{item.filename}' (total {item.total_pages} pages):\nExamples: 'all', '1-3', '1, 3, 5-7'",
            initialvalue=item.page_range,
            parent=self.root,
        )
        if val is None:
            return
        try:
            parse_page_ranges(val, item.total_pages)
            item.page_range = val.strip()
            self.refresh_tree()
            self.tree.selection_set(str(idx))
        except Exception as err:
            messagebox.showerror("Invalid Range", str(err))

    def remove_selected(self) -> None:
        idx = self._get_selected_index()
        if idx is not None:
            self.items.pop(idx)
            self.refresh_tree()

    def clear_all(self) -> None:
        if self.items and messagebox.askyesno("Clear All", "Remove all files from list?"):
            self.items.clear()
            self.refresh_tree()

    def run_merge(self) -> None:
        if not self.items:
            messagebox.showwarning("Empty List", "Please add at least one PDF file.")
            return

        out_path = filedialog.asksaveasfilename(
            title="Save Merged PDF As",
            defaultextension=".pdf",
            filetypes=[("PDF File", "*.pdf")],
        )
        if not out_path:
            return

        self.progress["maximum"] = len(self.items)
        self.progress["value"] = 0
        self.merge_btn.configure(state=tk.DISABLED)

        try:
            def update_progress(current: int, total: int) -> None:
                self.progress["value"] = current
                self.status_var.set(f"Processing {current}/{total} documents...")
                self.root.update_idletasks()

            total_pages = PDFMergerEngine.merge(
                items=self.items,
                output_path=out_path,
                add_bookmarks=self.bookmark_var.get(),
                progress_cb=update_progress,
            )
            self.status_var.set(f"Successfully saved {total_pages} pages to {os.path.basename(out_path)}.")
            messagebox.showinfo("Success", f"Merge Complete!\nTotal Pages: {total_pages}\nFile: {out_path}")
        except Exception as err:
            messagebox.showerror("Merge Error", f"Failed to merge PDFs:\n{err}")
            self.status_var.set("Merge failed.")
        finally:
            self.merge_btn.configure(state=tk.NORMAL)
            self.progress["value"] = 0
