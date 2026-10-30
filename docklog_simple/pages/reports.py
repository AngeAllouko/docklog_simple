"""Reports: spending by vessel and by equipment for a date range."""
import sqlite3
import tkinter as tk
from datetime import date

import database as db
from helpers import *

VESSEL_HEADINGS = ("Vessel", "Maintenance Jobs", "Total Cost (₹)")
EQUIPMENT_HEADINGS = ("Equipment", "Vessel", "Jobs", "Total Cost (₹)")


class ReportsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.report = None  # last report, kept for the CSV export
        page_heading(self, "Reports & Analytics",
                     "Analyze maintenance expenditure by vessel and equipment")

        today = date.today()
        filters = tk.Frame(self, bg=PANEL, padx=14, pady=12)
        filters.pack(fill="x", padx=28, pady=(0, 10))

        tk.Label(filters, text="From (YYYY-MM-DD)", bg=PANEL, fg=MUTED,
                 font=font(9)).grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.start_entry = make_entry(filters, width=15)
        self.start_entry.grid(row=1, column=0, padx=5, ipady=6)
        self.start_entry.insert(0, today.replace(day=1).isoformat())

        tk.Label(filters, text="To (YYYY-MM-DD)", bg=PANEL, fg=MUTED,
                 font=font(9)).grid(row=0, column=1, sticky="w", padx=5, pady=4)
        self.end_entry = make_entry(filters, width=15)
        self.end_entry.grid(row=1, column=1, padx=5, ipady=6)
        self.end_entry.insert(0, today.isoformat())

        make_button(filters, "Generate Report", self.generate).grid(
            row=1, column=2, padx=(12, 5))
        make_button(filters, "Export CSV", self.export, "secondary").grid(
            row=1, column=3, padx=5)

        self.message = tk.Label(filters, bg=PANEL, fg=RED, font=font(9))
        self.message.grid(row=2, column=0, columnspan=4, sticky="w",
                          padx=5, pady=(6, 0))

        self.results = tk.Frame(self, bg=BG)
        self.results.pack(fill="both", expand=True)
        self.generate()

    def generate(self):
        start = self.start_entry.get().strip()
        end = self.end_entry.get().strip()
        try:
            if parse_date(start) > parse_date(end):
                raise ValueError
        except ValueError:
            self.message.configure(
                text="Enter valid dates in YYYY-MM-DD format, "
                     "and make sure From is not after To.")
            return
        self.message.configure(text="")

        try:
            summary, by_vessel, by_equipment = db.report_data(start, end)
        except sqlite3.Error as error:
            self.message.configure(text=f"Report error: {error}")
            return
        self.report = (start, end, by_vessel, by_equipment)

        for widget in self.results.winfo_children():
            widget.destroy()

        jobs, total = summary
        average = f"avg {money(total / jobs)} per job" if jobs else ""
        card_row(self.results, [
            ("Period", f"{start}  →  {end}", MUTED, ""),
            ("Maintenance Jobs", jobs, ACCENT, ""),
            ("Total Spending", money(total), ACCENT, average),
        ])

        if not by_vessel:
            tk.Label(self.results, text="No maintenance records found for this period.",
                     bg=BG, fg=MUTED, font=font(10)).pack(anchor="w", padx=30, pady=14)
            return

        section_title(self.results, "Spending by Vessel")
        vessel_tree = make_tree(self.results, ("vessel", "jobs", "cost"),
                                VESSEL_HEADINGS, (240, 180, 200), pady=(4, 6))
        for r in by_vessel:
            insert_row(vessel_tree, (r[0], r[1], f"{r[2]:,.2f}"))

        section_title(self.results, "Spending by Equipment")
        equipment_tree = make_tree(self.results, ("name", "vessel", "jobs", "cost"),
                                   EQUIPMENT_HEADINGS, (200, 170, 100, 170),
                                   pady=(4, 14))
        for r in by_equipment:
            insert_row(equipment_tree, (r[0], r[1], r[2], f"{r[3]:,.2f}"))

    def export(self):
        if self.report is None:
            return
        start, end, by_vessel, by_equipment = self.report
        if save_csv("report",
                    [("Spending by Vessel", VESSEL_HEADINGS, by_vessel),
                     ("Spending by Equipment", EQUIPMENT_HEADINGS, by_equipment)],
                    first_line=f"Period: {start} to {end}"):
            self.app.refresh_statusbar("Report exported.")
