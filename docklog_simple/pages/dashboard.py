"""Dashboard: summary cards, two charts and the latest maintenance jobs."""
import tkinter as tk
from datetime import date

import database as db
from charts import draw_cost_chart, draw_status_chart, make_chart
from helpers import *


class DashboardPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        page_heading(self, "Dashboard",
                     "Equipment status, maintenance activity, and cost overview")

        equipment = db.fetch_equipment()
        logs = db.fetch_maintenance()
        today = date.today().isoformat()
        month_start = date.today().replace(day=1).isoformat()

        def count(status):
            return sum(1 for r in equipment if r[4] == status)

        total = len(equipment)
        operational = count("Operational")
        under_maintenance = count("Under Maintenance")
        out_of_service = count("Out of Service")
        overdue = sum(1 for r in equipment if is_overdue(r[4], r[5]))

        month_logs = [r for r in logs if month_start <= r[4] <= today]
        month_cost = sum(r[6] for r in month_logs)
        share = f"{operational / total * 100:.0f}% of equipment" if total else "—"

        card_row(self, [
            ("Total Equipment", total, ACCENT, f"{out_of_service} out of service"),
            ("Operational", operational, GREEN, share),
            ("Under Maintenance", under_maintenance, ORANGE, "work in progress"),
            ("Overdue", overdue, RED,
             "need attention" if overdue else "all on schedule"),
            ("This Month", money(month_cost), ACCENT,
             f"{len(month_logs)} job(s) logged"),
        ])

        # Two charts side by side
        charts = tk.Frame(self, bg=BG)
        charts.pack(fill="x", padx=28, pady=(0, 14))
        charts.grid_columnconfigure(0, weight=1, uniform="charts")
        charts.grid_columnconfigure(1, weight=1, uniform="charts")

        left = make_panel(charts, "Equipment Status")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        make_chart(left, draw_status_chart, [
            ("Operational", operational, STATUS_COLORS["Operational"]),
            ("Under Maintenance", under_maintenance, STATUS_COLORS["Under Maintenance"]),
            ("Out of Service", out_of_service, STATUS_COLORS["Out of Service"]),
        ]).pack(fill="x")

        right = make_panel(charts, "Maintenance Cost, Last 6 Months (₹)")
        right.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        make_chart(right, draw_cost_chart, db.monthly_costs(6)).pack(fill="x")

        # Latest jobs
        section_title(self, "Recent Maintenance Activity", pady=(4, 0))
        tree = make_tree(
            self,
            ("id", "equipment", "vessel", "date", "description", "cost", "outcome"),
            ("Log ID", "Equipment", "Vessel", "Date", "Description",
             "Cost (₹)", "Outcome"),
            (55, 175, 120, 100, 220, 100, 150), pady=(8, 16))
        for r in logs[:6]:
            tag = "followup" if r[7] == "Requires Follow-up" else ""
            insert_row(tree, (r[0], r[2], r[3], r[4], r[5], f"{r[6]:,.2f}", r[7]), tag)
