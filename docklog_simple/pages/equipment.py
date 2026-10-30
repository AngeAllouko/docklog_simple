"""Equipment list: search, filter, add, edit, delete."""
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

import database as db
from forms import open_equipment_form
from helpers import *


class EquipmentPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        page_heading(self, "Equipment",
                     "Register, search, edit, and remove equipment  ·  "
                     "Ctrl+N to add, Delete to remove, click a header to sort")

        # Toolbar: search box, status filter, buttons
        toolbar = tk.Frame(self, bg=BG)
        toolbar.pack(fill="x", padx=28, pady=(0, 8))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.populate())
        make_entry(toolbar, textvariable=self.search_var, width=24).pack(
            side="left", ipady=7, padx=(0, 8))

        self.filter_var = tk.StringVar(value="All")
        filter_box = ttk.Combobox(toolbar, textvariable=self.filter_var,
                                  values=["All"] + STATUSES,
                                  state="readonly", width=18)
        filter_box.pack(side="left", ipady=4, padx=(0, 8))
        filter_box.bind("<<ComboboxSelected>>", lambda e: self.populate())

        make_button(toolbar, "+ Add Equipment", self.add).pack(side="left", padx=3)
        make_button(toolbar, "Edit Selected", self.edit, "secondary").pack(side="left", padx=3)
        make_button(toolbar, "Delete Selected", self.delete, "danger").pack(side="left", padx=3)

        self.count_label = tk.Label(toolbar, bg=BG, fg=MUTED, font=font(9))
        self.count_label.pack(side="right")

        self.tree = make_tree(
            self, ("id", "name", "vessel", "location", "status", "date", "due"),
            ("ID", "Equipment", "Vessel", "Location", "Status",
             "Next Maintenance", "Due"),
            (45, 190, 135, 135, 165, 140, 110))
        self.tree.bind("<Double-1>", lambda e: self.edit())
        self.tree.bind("<Delete>", lambda e: self.delete())
        self.winfo_toplevel().bind("<Control-n>", lambda e: self.add())

        self.populate()

    def populate(self):
        """Fill the table using the current search text and status filter."""
        self.tree.delete(*self.tree.get_children())
        rows = db.fetch_equipment(self.search_var.get(), self.filter_var.get())

        for id_, name, vessel, location, status, next_date in rows:
            insert_row(
                self.tree,
                (id_, name, vessel, location, f"● {status}", next_date,
                 due_text(status, next_date)),
                row_tag(status, next_date), iid=str(id_))

        self.count_label.configure(text=f"{len(rows)} record(s)")

    def saved(self, message):
        self.populate()
        self.app.refresh_statusbar(message)

    def selected_record(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection",
                                   "Please select an equipment record first.")
            return None
        return db.get_equipment(int(selection[0]))  # the row id is the DB id

    def add(self):
        open_equipment_form(self.winfo_toplevel(), on_saved=self.saved)

    def edit(self):
        record = self.selected_record()
        if record:
            open_equipment_form(self.winfo_toplevel(), record, on_saved=self.saved)

    def delete(self):
        record = self.selected_record()
        if not record:
            return
        if not messagebox.askyesno(
                "Confirm Deletion",
                f"Delete {record[1]}?\n\n"
                "Its associated maintenance history will also be deleted."):
            return
        try:
            db.delete_equipment(int(record[0]))
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))
            return
        self.saved("Equipment and its history were deleted.")
