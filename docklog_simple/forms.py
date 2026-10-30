"""The two pop-up forms: add/edit equipment, and record maintenance."""
import math
import sqlite3
import tkinter as tk
from datetime import date, timedelta
from tkinter import ttk

import database as db
from helpers import *


class Form(tk.Toplevel):
    """A pop-up window with labelled fields, an error line and buttons."""

    def __init__(self, parent, title, subtitle):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)
        self.bind("<Escape>", lambda e: self.destroy())

        self.entries = []               # every text field, in order
        self.message = tk.StringVar()   # the red error line

        tk.Frame(self, bg=BG, width=480, height=1).pack()  # sets the width
        tk.Label(self, text=title, bg=BG, fg=TEXT,
                 font=font(20, "bold")).pack(anchor="w", padx=28, pady=(20, 2))
        tk.Label(self, text=subtitle, bg=BG, fg=MUTED,
                 font=font(9)).pack(anchor="w", padx=29)
        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="x", padx=30)

    def add_entry(self, label, value=""):
        tk.Label(self.body, text=label, bg=BG, fg=MUTED,
                 font=font(9)).pack(anchor="w", pady=(10, 3))
        entry = make_entry(self.body)
        entry.pack(fill="x", ipady=7)
        entry.insert(0, value)
        self.entries.append(entry)
        return entry

    def add_combo(self, label, variable, values):
        tk.Label(self.body, text=label, bg=BG, fg=MUTED,
                 font=font(9)).pack(anchor="w", pady=(10, 3))
        combo = ttk.Combobox(self.body, textvariable=variable,
                             values=values, state="readonly")
        combo.pack(fill="x", ipady=3)
        return combo

    def error(self, text="", field=None):
        """Show an error (and outline the field in red). No text = clear."""
        for entry in self.entries:
            entry.configure(highlightbackground=BORDER, highlightcolor=ACCENT)
        self.message.set(text)
        if field is not None:
            field.configure(highlightbackground=RED, highlightcolor=RED)
            field.focus_set()

    def show(self, save_command, save_text="Save"):
        """Add the buttons, centre the window and make it modal."""
        tk.Label(self, textvariable=self.message, bg=BG, fg=RED,
                 font=font(9), wraplength=420,
                 justify="left").pack(anchor="w", padx=30, pady=(12, 0))
        buttons = tk.Frame(self, bg=BG)
        buttons.pack(fill="x", padx=30, pady=(10, 22))
        make_button(buttons, save_text, save_command).pack(side="left", padx=(0, 8))
        make_button(buttons, "Cancel", self.destroy, "secondary").pack(side="left")
        self.bind("<Return>", lambda e: save_command())

        self.update_idletasks()
        parent = self.master
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_reqwidth()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.wait_visibility()
        self.grab_set()
        self.entries[0].focus_set()


def open_equipment_form(parent, record=None, on_saved=None):
    """Add equipment, or edit it when `record` is given."""
    editing = record is not None
    form = Form(parent, "Edit Equipment" if editing else "Add Equipment",
                "Update the equipment details." if editing
                else "Register a new piece of equipment.")

    name = form.add_entry("Equipment Name", record[1] if editing else "")
    vessel = form.add_entry("Vessel", record[2] if editing else "")
    location = form.add_entry("Location", record[3] if editing else "")
    next_date = form.add_entry(
        "Next Maintenance (YYYY-MM-DD)",
        record[5] if editing else date.today().isoformat())
    status = tk.StringVar(value=record[4] if editing else "Operational")
    form.add_combo("Status", status, STATUSES)

    def save():
        form.error()
        for entry, label in [(name, "Equipment name"), (vessel, "Vessel"),
                             (location, "Location"),
                             (next_date, "Next maintenance date")]:
            if not entry.get().strip():
                form.error(f"{label} is required.", entry)
                return

        try:
            parse_date(next_date.get().strip())
        except ValueError:
            form.error("Use a valid date in YYYY-MM-DD format.", next_date)
            return

        values = (name.get().strip(), vessel.get().strip(),
                  location.get().strip(), status.get(),
                  next_date.get().strip())
        try:
            if editing:
                db.update_equipment(int(record[0]), *values)
            else:
                db.insert_equipment(*values)
        except sqlite3.Error as error:
            form.error(f"Database error: {error}")
            return

        form.destroy()
        if on_saved:
            on_saved("Equipment saved.")

    form.show(save)
    return form


def open_maintenance_form(parent, equipment, on_saved=None):
    """Record a maintenance job for one of the equipment rows."""
    form = Form(parent, "Record Maintenance",
                "Log a maintenance job and optionally update the equipment.")

    choices = [f"{r[0]} | {r[1]} | {r[2]}" for r in equipment]
    chosen = tk.StringVar(value=choices[0])
    form.add_combo("Equipment", chosen, choices)

    job_date = form.add_entry("Maintenance Date (YYYY-MM-DD)",
                              date.today().isoformat())
    work = form.add_entry("Work Performed")
    cost = form.add_entry("Cost (₹)", "0")
    outcome = tk.StringVar(value="Completed")
    form.add_combo("Outcome", outcome, OUTCOMES)

    update = tk.BooleanVar(value=True)
    tk.Checkbutton(form.body, text="Update equipment status and next maintenance date",
                   variable=update, bg=BG, fg=TEXT, selectcolor=INPUT_BG,
                   activebackground=BG, activeforeground=TEXT,
                   font=font(9)).pack(anchor="w", pady=(14, 0))

    new_status = tk.StringVar(value="Operational")
    status_box = form.add_combo("New Equipment Status", new_status, STATUSES)
    next_date = form.add_entry("Next Maintenance Date (YYYY-MM-DD)",
                               (date.today() + timedelta(days=30)).isoformat())

    def toggle(*_):  # grey out the two fields when the box is unticked
        status_box.configure(state="readonly" if update.get() else "disabled")
        next_date.configure(state="normal" if update.get() else "disabled")

    update.trace_add("write", toggle)

    def save():
        form.error()

        try:
            parse_date(job_date.get().strip())
        except ValueError:
            form.error("Use a valid maintenance date (YYYY-MM-DD).", job_date)
            return

        if not work.get().strip():
            form.error("Describe the work performed.", work)
            return

        try:
            cost_value = float(cost.get().strip())
            if cost_value < 0 or not math.isfinite(cost_value):
                raise ValueError
        except ValueError:
            form.error("Cost must be a non-negative number.", cost)
            return

        status_to_save = next_to_save = None
        if update.get():
            try:
                parse_date(next_date.get().strip())
            except ValueError:
                form.error("Enter a valid next maintenance date.", next_date)
                return
            status_to_save = new_status.get()
            next_to_save = next_date.get().strip()

        equipment_id = int(chosen.get().split(" | ")[0])
        try:
            db.add_maintenance(equipment_id, job_date.get().strip(),
                               work.get().strip(), cost_value, outcome.get(),
                               status_to_save, next_to_save)
        except sqlite3.Error as error:
            form.error(f"Database error: {error}")
            return

        form.destroy()
        if on_saved:
            on_saved("Maintenance record saved.")

    form.show(save, "Save Record")
    return form
