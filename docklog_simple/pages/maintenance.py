"""Equipment whose maintenance is due today or already overdue."""
import tkinter as tk
from datetime import date

import database as db
from helpers import *


class MaintenancePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        page_heading(self, "Maintenance",
                     "Review equipment with maintenance due or overdue")

        today = date.today().isoformat()
        records = [r for r in db.fetch_equipment()
                   if r[5] <= today and r[4] != "Under Maintenance"]

        tk.Label(self, text=f"{len(records)} equipment record(s) due or overdue",
                 bg=BG, fg=ORANGE if records else GREEN,
                 font=font(11, "bold")).pack(anchor="w", padx=28, pady=(0, 5))

        tree = make_tree(
            self, ("id", "name", "vessel", "location", "status", "date", "due"),
            ("ID", "Equipment", "Vessel", "Location", "Status",
             "Next Maintenance", "Due"),
            (45, 190, 135, 135, 165, 140, 110))
        for id_, name, vessel, location, status, next_date in records:
            insert_row(tree, (id_, name, vessel, location, f"● {status}",
                              next_date, due_text(status, next_date)),
                       row_tag(status, next_date))
