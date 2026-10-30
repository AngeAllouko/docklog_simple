"""Maintenance history: record, delete, export to CSV."""
import sqlite3
import tkinter as tk
from tkinter import messagebox

import database as db
from forms import open_maintenance_form
from helpers import *

HEADINGS = ("Log ID", "Equipment", "Vessel", "Date", "Description",
            "Cost (₹)", "Outcome")


class MaintenanceLogPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        page_heading(self, "Maintenance Log",
                     "Record service work, costs, and outcomes  ·  "
                     "Ctrl+N to record")

        toolbar = tk.Frame(self, bg=BG)
        toolbar.pack(fill="x", padx=28, pady=(0, 8))
        make_button(toolbar, "+ Record Maintenance", self.add).pack(side="left", padx=(0, 5))
        make_button(toolbar, "Delete Selected", self.delete, "danger").pack(side="left", padx=5)
        make_button(toolbar, "Export CSV", self.export, "secondary").pack(side="left", padx=5)

        self.tree = make_tree(
            self, ("id", "equipment", "vessel", "date", "description",
                   "cost", "outcome"),
            HEADINGS, (55, 175, 120, 100, 220, 100, 155))
        self.tree.bind("<Delete>", lambda e: self.delete())
        self.winfo_toplevel().bind("<Control-n>", lambda e: self.add())
        self.populate()

    def populate(self):
        self.tree.delete(*self.tree.get_children())
        for r in db.fetch_maintenance():
            tag = "followup" if r[7] == "Requires Follow-up" else ""
            insert_row(self.tree,
                       (r[0], r[2], r[3], r[4], r[5], f"{r[6]:,.2f}", r[7]),
                       tag, iid=str(r[0]))

    def saved(self, message):
        self.populate()
        self.app.refresh_statusbar(message)

    def add(self):
        equipment = db.fetch_equipment()
        if not equipment:
            messagebox.showwarning("No Equipment",
                                   "Register equipment before recording maintenance.")
            return
        open_maintenance_form(self.winfo_toplevel(), equipment, on_saved=self.saved)

    def delete(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection",
                                   "Select a maintenance record first.")
            return
        log_id = int(selection[0])
        if not messagebox.askyesno("Confirm Deletion",
                                   f"Delete maintenance record #{log_id}?"):
            return
        try:
            db.delete_maintenance(log_id)
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))
            return
        self.saved("Maintenance record deleted.")

    def export(self):
        rows = [(r[0], r[2], r[3], r[4], r[5], r[6], r[7])
                for r in db.fetch_maintenance()]
        if save_csv("maintenance_log", [("Maintenance Log", HEADINGS, rows)]):
            self.app.refresh_statusbar(f"Exported {len(rows)} record(s).")
